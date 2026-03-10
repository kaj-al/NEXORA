import tempfile
import os
from moviepy import VideoFileClip
import whisper
from faster_whisper import WhisperModel
import requests
import subprocess
from pathlib import Path
from pydub import AudioSegment
import time
from config import openrouter_key_input
from gtts import gTTS
from deep_translator import GoogleTranslator
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
 
def create_requests_session(retries=3, backoff_factor=0.5, timeout=30):
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def call_openrouter(api_key, prompt, model="gpt-4o-mini", temperature=0.2, max_tokens=800):
    url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are Nexora, an assistant that creates concise, structured study notes and study plans from transcripts or user text."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    try:
        session = create_requests_session(retries=3, backoff_factor=1)
        r = session.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code == 200:
            j = r.json()
            # safe navigation
            try:
                return j["choices"][0]["message"]["content"]
            except Exception:
                return r.text
        else:
            return f"ERROR {r.status_code}: {r.text}"
    except requests.exceptions.ConnectionError as e:
        return f"Connection error: Unable to reach OpenRouter API. Please check your internet connection. Details: {str(e)}"
    except requests.exceptions.Timeout:
        return f"Timeout error: The request took too long. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"
    
def load_whisper_model(model_size="base"):
    return whisper.load_model(model_size)

def download_youtube_audio(url):
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "yt_audio.wav")
    command = [
        "yt-dlp",
        "-x",
        "--audio-format","wav",
        "-o",output_path,
        url
    ]
    subprocess.run(command,check=True)
    return output_path

def extract_audio(video_path, audio_ext=".wav"):
    # returns path to audio file
    base = Path(video_path)
    audio_path = str(base.with_suffix(audio_ext))
    clip = VideoFileClip(str(video_path))
    # If audio already exists, overwrite
    clip.audio.write_audiofile(audio_path)
    clip.close()
    return audio_path

def speech_text(audio_path):
    @st.cache_resource
    def load_translation_model():
        return WhisperModel("tiny", device="cpu", compute_type="int8")
    
    print(f"[TRANSLATION] Starting speech-to-text transcription for: {audio_path}")
    model = load_translation_model()
    print("[TRANSLATION] Whisper model loaded successfully")
    segments, info = model.transcribe(audio_path, language="en", beam_size=1)
    text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
    print(f"[TRANSLATION] Transcription completed. Length: {len(text)} characters")
    return text

def trans_txt(txt,target_lang):
    print(f"[TRANSLATION] Starting text translation to language code: {target_lang}")
    print(f"[TRANSLATION] Text length to translate: {len(txt)} characters")
    translator = GoogleTranslator(source="auto", target=target_lang)
    translated = translator.translate(txt)
    print(f"[TRANSLATION] Translation completed. Translated text length: {len(translated)} characters")
    return translated

def translate_speech_to_speech(audio_path, target_lang_code):
    """
    Complete speech-to-speech translation pipeline
    Input: Audio file (speech in any language)
    Output: Audio file (speech in target language)
    """
    print("\n" + "="*70)
    print("SPEECH-TO-SPEECH TRANSLATION STARTED")
    print("="*70)
    
    try:
        print("\n[STEP 1/2] Translating audio internally to target language...")
        from faster_whisper import WhisperModel as _WhisperModel
        _model = _WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, info = _model.transcribe(audio_path, task="translate", beam_size=1)
        translated_text = " ".join(segment.text for segment in segments).strip()
        print(f"[INTERNAL TRANSLATION] Translated text length: {len(translated_text)} characters")

        # Synthesize translated text to audio (handles long text by chunking)
        print("\n[STEP 2/2] Synthesizing translated speech to audio file...")
        output_audio_path = txt_speech(translated_text, target_lang_code)
        print(f"[TEXT-TO-SPEECH] ✓ Audio generated: {output_audio_path}")
        
        print("\n" + "="*70)
        print("SPEECH-TO-SPEECH TRANSLATION COMPLETED SUCCESSFULLY!")
        print(f"INPUT:  Audio (speech) in source language")
        print(f"OUTPUT: Audio (speech) in target language")
        print("="*70 + "\n")
        
        return output_audio_path
        
    except Exception as e:
        print(f"\n ERROR in speech-to-speech translation: {str(e)}")
        print("="*70 + "\n")
        raise

def save_audio(uploaded_audio):
        with tempfile.NamedTemporaryFile(delete=False,suffix=".wav") as temp:
            temp.write(uploaded_audio.read())
            return temp.name
    
def split(audio_path, chunk_min=2):
        audio = AudioSegment.from_file(audio_path)
        chunk_len = chunk_min * 60 * 1000
        chunks = []
        for i in range(0, len(audio), chunk_len):
            chunk = audio[i:i + chunk_len]
            chunk_path = f"{audio_path}_chunk_{i}.wav"
            chunk.export(chunk_path, format="wav")
            chunks.append(chunk_path)
        return chunks
    
def load_model():
    return whisper.load_model("base")
model = load_model()

