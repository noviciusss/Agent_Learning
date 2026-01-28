import time
import streamlit as st
from agno.agent import Agent 
from agno.tools.hackernews import HackerNewsTools
from agno.tools.websearch import WebSearchTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.groq import Groq
from agno.tools import tool
from agno.run.agent import RunOutputEvent
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import os

load_dotenv()

st.set_page_config(page_title='Research Report Generator',layout='wide')
st.title('Research Report Generator')
st.markdown('Generate comprehensive research reports on any topic using Hacker News data.')

topic = st.text_input('Enter your research topic:', key='topic_input')
@tool
def fetch_url_text(url:str)-> dict:
    """Fetch the web page and return cleaned text for research.
    
    Args:
        url: A valid URL string (must start with http:// or https://)
    
    Returns:
        Dictionary with url, text content, and status information
    """
    try:
        r= requests.get(url, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
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
        return {"url": url, "text": text[:3000]}    
    except Exception as e:
        return {"url": url,"ok":False,"status":None,"error": str(e)}

def build_agent():
    return Agent(
            name = 'Research Report Generator Agent',
            model=Groq(id="llama-3.3-70b-versatile"), 
            tools=[DuckDuckGoTools(), fetch_url_text],
        instructions=[
            "You are a research agent that creates concise, well-cited reports.",
            "",
            "## Research Process:",
            "1. Use duckduckgo_search to find relevant articles about the topic",
            "2. From the search results, identify 2-3 most relevant URLs",
            "3. Use fetch_url_text to read content from those URLs",
            "4. Synthesize findings into a structured report",
            "",
            "## Report Structure:",
            "# Summary",
            "Write 2-3 sentences summarizing key insights [with](url) [citations](url)",
            "",
            "# Key Findings",
            "- Finding 1 [source](url)",
            "- Finding 2 [source](url)", 
            "- Finding 3 [source](url)",
            "",
            "# Sources",
            "List all URLs referenced",
            "",
            "## Constraints:",
            "- Fetch maximum 2-3 URLs to stay within token limits",
            "- Keep total report under 1500 words",
            "- If a URL fails (ok=False), skip and try another",
            "- Every claim must have a URL citation",
        ],
                # show_tool_calls=True,
                markdown=True,)
    
with st.sidebar:
    st.header("About")
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
        agent = build_agent()
        with st.spinner("Researching...."):
            try:
                start_time = time.time()
                result = agent.run(topic)
                end_time = time.time()
                elapsed = end_time - start_time
                st.success(f"Research completed in {elapsed:.1f} seconds")
                st.subheader("Research Report")
                st.markdown(result.content)
            except Exception as e:
                st.error(f"Error during research: {str(e)}")
                st.stop()   
                

    