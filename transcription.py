
from faster_whisper import WhisperModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def load_models():
    whisper = WhisperModel(
        "tiny.en",        
        compute_type="int8",
        cpu_threads=8
    )
    llm = ChatOpenAI(
        model="gpt-4o-mini",   
        groq_api_key=os.getenv("OPENROUTER_API_KEY")
    )
    return whisper, llm

whisper_model, llm = load_models()

def transcribe_audio(audio_path):
    segments, _ = whisper_model.transcribe(
        audio_path,
        beam_size=1,
        vad_filter=True
    )
    text = " ".join([seg.text for seg in segments])
    return text

prompt = ChatPromptTemplate.from_template("""
Analyze the transcript and provide:

1. Main topic
2. Subtopics
3. Simple explanation
4. Short structured notes

Transcript:
{text}
""")

def process_audio(audio_path):
    transcript = transcribe_audio(audio_path)
    return transcript