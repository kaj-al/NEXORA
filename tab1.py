
import os
from moviepy import VideoFileClip
import whisper
import requests 
import yt_dlp
from pathlib import Path
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


def download_audio_fast(url, output_path="audio.%(ext)s"):
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",  
        "outtmpl": output_path,
        "noplaylist": True,
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",  
            "preferredquality": "192",
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return "audio.wav"

def extract_audio(video_path, audio_ext=".wav"):
    base = Path(video_path)
    audio_path = str(base.with_suffix(audio_ext))
    clip = VideoFileClip(str(video_path))
    clip.audio.write_audiofile(audio_path)
    clip.close()
    return audio_path

