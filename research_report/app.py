import time
import streamlit as st
from agno.agent import Agent 
from agno.tools.hackernews import HackerNewsTools
from agno.tools.websearch import WebSearchTools

from ddgs import DDGS

from agno.models.groq import Groq
from agno.tools import tool
from agno.run.agent import RunOutputEvent
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import os

load_dotenv()

st.set_page_config(page_title='Research Report Generator',layout='wide')
st.title('Research report generator with web retrieval (DDG) + LLM synthesis')
st.markdown('Generate comprehensive research reports on any topic using Hacker News data.')

topic = st.text_input('Enter your research topic:', key='topic_input')

def fetch_url_text(url: str, timeout: int = 15, max_chars: int = 3000) -> dict:
    """Fetch the web page and return cleaned text for research.
    
    Args:
        url: A valid URL string (must start with http:// or https://)
    
    Returns:
        Dictionary with url, text content, and status information
    """
    try:
        r= requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup(['script', 'style', 'noscript', 'header', 'footer', 'nav', 'aside']):
            tag.decompose()
        
        # Try to get main content
        main = soup.find('main') or soup.find('article') or soup.find('body')
        if main:
            text = " ".join(main.get_text(" ", strip=True).split())
        else:
            text = " ".join(soup.get_text(" ", strip=True).split())
        return {"url": url, "text": text[:max_chars], "ok": True, "status": r.status_code}    
    except Exception as e:
        return {"url": url,"ok":False,"status":None,"error": str(e)}
    
def ddg_search(query: str, max_results: int=5) -> list[dict]:
    """Perform q DuckDuckGo search and return list of result URLs."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            # r typically includes: title, href, body
            results.append(r)
    return results


# def build_agent():
#     return Agent(
#             name = 'Research Report Generator Agent',
#             model=Groq(id="llama-3.3-70b-versatile"), 
#             tools=[DuckDuckGoTools(), fetch_url_text],
#         instructions=[
#             "You are a research agent that creates concise, well-cited reports.",
#             "",
#             "## Research Process:",
#             "1. Use duckduckgo_search to find relevant articles about the topic",
#             "2. From the search results, identify 2-3 most relevant URLs",
#             "3. Use fetch_url_text to read content from those URLs",
#             "4. Synthesize findings into a structured report",
#             "",
#             "## Report Structure:",
#             "# Summary",
#             "Write 2-3 sentences summarizing key insights [with](url) [citations](url)",
#             "",
#             "# Key Findings",
#             "- Finding 1 [source](url)",
#             "- Finding 2 [source](url)", 
#             "- Finding 3 [source](url)",
#             "",
#             "# Sources",
#             "List all URLs referenced",
#             "",
#             "## Constraints:",
#             "- Fetch maximum 2-3 URLs to stay within token limits",
#             "- Keep total report under 1500 words",
#             "- If a URL fails (ok=False), skip and try another",
#             "- Every claim must have a URL citation",
#         ],
#                 # show_tool_calls=True,
#                 markdown=True,)

def build_report_prompt(question:str ,docs :list[dict])->str:
    sources_block = "\n\n".join(f"Source {i+1}: {d['url']}\nContent:\n{d['text']}" for i,d in enumerate(docs))
    urls = "\n".join(d["url"] for d in docs)
    return f"""
    You are a research assistant.

Task: Write a concise, well-cited report using ONLY the provided sources.
If sources conflict or are weak, mention it in Uncertainties. Do not invent facts.

Output format (Markdown):
## Summary
(2–4 sentences)

## Key Findings
- Bullet points (each bullet must include a citation like: (Source: URL))

## Uncertainties
- Bullet points about missing/conflicting info

## Sources
List each URL once.

Question: {question}

Provided sources:
{sources_block}

Allowed citations (must be from these URLs only):
{urls}
""".strip()


with st.sidebar:
    st.header("Settings")
    max_results = st.slider("Search results", 3,10,5)
    max_sources = st.slider("Max URLs to fetch", 2,6,3)
    max_chars_per_source = st.slider("Max chars per URL", 1000,5000,3000, step =500)
    timeout_s = st.slider("Tool timeout (s)", 5,20,10)
    show_sources = st.checkbox("Show fetched sources (debug)", value=True)
    
    st.markdown("""
    This tool generates research reports by:
    1. Searching the web
    2. Fetching relevant articles
    3. Synthesizing findings
    4. Providing cited conclusions
    """)    

if st.button("Run reasearch"):
    if not os.getenv("GROQ_API_KEY"):
        st.error("PLease input the groq api keys")
        st.stop()
    elif not topic:
        st.error("Enter the question.")
        st.stop()
    else :
        with st.spinner("Searching (DuckDuckGo)..."):
            results = ddg_search(topic, max_results=max_results)
            urls = [r.get("href") for r in results if r.get("href")]
            # de-dup, keep order
            urls = list(dict.fromkeys(urls))[:max_sources]
            with st.spinner("Fetching sources..."):
                fetched = [fetch_url_text(u, timeout=timeout_s, max_chars=max_chars_per_source) for u in urls]
                docs = [d for d in fetched if d.get("ok") and d.get("text")]

            if not docs:
                st.error("No readable sources fetched. Try a different query or enable more sources.")
                if show_sources:
                    st.json(fetched)
                st.stop()

            if show_sources:
                with st.expander("Fetched sources (debug)", expanded=False):
                    st.write([{"url": d["url"], "ok": d["ok"], "status": d.get("status")} for d in fetched])

            prompt = build_report_prompt(topic, docs)

            agent = Agent(
                name="Research Report Writer",
                model=Groq(id="llama-3.3-70b-versatile"),
                instructions="Write only the report. Follow the format exactly.",
                markdown=True,
            )

            with st.spinner("Writing report (Groq LLM)..."):
                out = agent.run(prompt) 
                st.subheader("Research Report")
                st.markdown(out.content)  
