import streamlit as st
from scrapegraph_py import Client
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field,ValidationError
from typing import List, Optional

load_dotenv()

st.title("Web Scraping Ai Agent")
st.caption("This app will allow you to scrape websites using LLM.")

st.sidebar.header("Api Key")
SCRAPEGRAPH_API_KEY = st.sidebar.text_input("Scrapegraph API Key",
                                            value=os.getenv("SCRAPEGRAPH_API_KEY") or " ",
                                            type="password",)
GROQ_API_KEY  = st.sidebar.text_input("Groq API Key", 
                                    value=os.getenv("GROQ_API_KEY") or " ",
                                    type="password")

url = st.text_input("Enter the URL you want to scrape: ")
user_prompt = st.text_area("What do you want AI agent to scare from website?")

#Pydantic schema
class ExtrectedData(BaseModel):
    title: str = Field(description="Title of page or main entity")
    key_points:List[str]= Field(description="Important extracted points")
    prices :Optional[List[str]]= Field(description="List of prices found on page")
    emails:Optional[List[str]]= Field(description="List of emails found on page")
    source_url: str = Field(description="The URL of the page scraped")
    
    
def build_agent_prompt(goal:str,url:str)->str:
    return f"""
    you are a web extraction agent 
    
    goal :{goal}
    Return only valid json that matches the following schema:
    {ExtrectedData.model_json_schema()}
    
    Rules:
    -Extract only information present in page
    - return concise key_points (max 5)
    - source_url must be exaclty: {url}
"""    

# ##usiing streamlit cache ye inbuild hai 
# @st.cache_data(show_spinner=False,ttl=3600)
# def run_smartscraper_chached(
#     SCRAPEGRAPH_API_KEY:str,
#     GROQ_API_KEY:str,
#     website_url: str,
#     final_prompt: str,
#     use_ai_extraction:bool):
#         os.environ["SCRAPEGRAPH_API_KEY"] = SCRAPEGRAPH_API_KEY
#         os.environ["GROQ_API_KEY"] = GROQ_API_KEY
#         client = Client(SCRAPEGRAPH_API_KEY)
        
#         kwargs = {
#             "website_url": website_url,
#             "user_prompt": final_prompt,
#             "extraction_mode": use_ai_extraction,
#         }
#         if use_ai_extraction:
#             kwargs["response_schema"] = ExtrectedData
#         response = client.smartscraper(**kwargs)
#         return response



def safe_get_result(resp) -> dict:
    # Works whether SDK returns dict, Pydantic model, or string JSON
    if resp is None:
        return {}

    # SDK may return dict
    if isinstance(resp, dict):
        return resp.get("result") or {}

    # Sometimes a Pydantic-like object
    if hasattr(resp, "get"):
        try:
            return resp.get("result") or {}
        except Exception:
            pass

    # Worst case: show raw
    return {}


if st.button("Scrape Website"):
    if not url:
        st.error("Please enter a valid URL.")
        st.stop()
    elif not SCRAPEGRAPH_API_KEY:
        st.error("Please enter your Scrapegraph API Key in the sidebar.")
        st.stop()
    elif not GROQ_API_KEY:
            os.environ["SCRAPEGRAPH_API_KEY"] = SCRAPEGRAPH_API_KEY
            os.environ["GROQ_API_KEY"] = GROQ_API_KEY
    
    prompt = build_agent_prompt(user_prompt,url)
    with st.spinner("Scraping..."):
            try:
                client = Client(api_key=SCRAPEGRAPH_API_KEY)
                smart_scaper =response = client.smartscraper(
                    website_url=url,
                    user_prompt=user_prompt,
                    output_schema=ExtrectedData,
                    # extraction_mode=True,
                )
                data = safe_get_result(smart_scaper)
                
                validated_data = ExtrectedData.model_validate(data).model_dump()
                
                st.success("Done")
                st.subheader("Structed Result")
                st.json(validated_data)
                
            except ValidationError as ve:
                st.error("Got esponse but it did not match schema.")
                st.code(str(ve))
                st.subheader("Raw Response")
                st.json(safe_get_result(smart_scaper)) if"smart_scaper"in locals() else None
            except Exception as e:
                st.error("Error occurred during scraping.")
                st.code(str(e))