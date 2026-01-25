import os
from uuid import uuid4
from dotenv import load_dotenv
from agno.agent import Agent
from agno.run.agent import RunOutputEvent
from agno.models.groq import Groq
from agno.tools.firecrawl import FirecrawlTools
from elevenlabs import ElevenLabs
import streamlit as st

load_dotenv()

st.set_page_config(page_title="Blog to Voice", layout="wide")
st.title("Blog to Voice Agent")

st.sidebar.header("Api keys")
GROQ_API_KEY = st.sidebar.text_input("Groq API Key", value=os.getenv("GROQ_API_KEY") or "",type="password")
ELEVEN_LABS_API_KEY = st.sidebar.text_input("Eleven Labs API Key", value=os.getenv("ELEVEN_LABS_API_KEY") or "",type="password")
FIRECRAWL_API_KEY = st.sidebar.text_input("Firecrawl API Key", value=os.getenv("FIRECRAWL_API_KEY") or "",type="password")

url = st.text_input("Enter the blog URL you want to convert to voice: ")

if st.button("Generate Voice"):
    if not url:
        st.error("Please enter a valid URL.")
    elif not GROQ_API_KEY:
        st.error("Please enter your Groq API Key in the sidebar.")
    elif not ELEVEN_LABS_API_KEY:
        st.error("Please enter your Eleven Labs API Key in the sidebar.")
    else : 
        with st.spinner("Processing..."):
            try: 
                os.environ["GROQ_API_KEY"] = GROQ_API_KEY
                os.environ["FIRECRAWL_API_KEY"] = FIRECRAWL_API_KEY\
                
                agent = Agent(
                    name="Blog to Voice Agent",
                    tools=[FirecrawlTools()],
                    model = Groq(id= "llama-3.3-70b-versatile"),
                    instructions=
                    ["Scrape the blog url and create a concise and engaging summary (max 2000 characters) suitable for a podcast.",
                    "the summary should be in a conversational tone and easy to listen to."],
                )
                response : RunOutputEvent = agent.run(f"Scare and summarize the blog at this blog for a podcast:{url}")
                summary = response.content if hasattr(response, 'content') else "No summary generated."
                
                if summary:
                    client = ElevenLabs(api_key=ELEVEN_LABS_API_KEY)
                    
                    audio_generation = client.text_to_speech.convert(
                        text=summary,
                        voice_id="pNInz6obpgDQGcFmaJgB",
                        model_id = 'eleven_multilingual_v2',)
                    
                    audio_chunks = []
                    for chunk in audio_generation:
                        if chunk :
                            audio_chunks.append(chunk)
                    audio_bytes = b"".join(audio_chunks)
                    
                    st.success("Voice generation complete!")
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    st.download_button(
                        "Download Audio",
                        audio_bytes,
                        "podcast_summary.mp3",
                        "audio/mp3",
                    )
                    with st.expander("Summary Text"):
                        st.write(summary)
                else: st.error("Failed to generate summary from the blog.")
            except Exception as e:
                st.error(f"An error occurred: {e}")