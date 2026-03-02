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
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code == 200:
        j = r.json()
        # safe navigation
        try:
            return j["choices"][0]["message"]["content"]
        except Exception:
            return r.text
    else:
        return f"ERROR {r.status_code}: {r.text}"
    
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

def notes(transcript):
    headers = {
        "Authorization": f"Bearer {openrouter_key_input}",
        "Content-Type": "application/json",
        "HTTP-Referrer": "http://localhost",
        "X-Title": "Nexora"
    }
    payload = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [
            {
                "role": "system",
                "content": "You are an AI that converts lecture audio content into clean, structured study notes."
            },
            {
                "role": "user",
                "content": f"Create concise academic notes from the following lecture audio: \n{transcript}"
            }
        ]
    }
    url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()

    return result["choices"][0]["message"]["content"]


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

def transcribe(chunk_path):
    url = os.getenv("OPENROUTER_AUDIO_URL", "https://openrouter.ai/api/v1/audio/transcriptions")
    headers = {
        "Authorization": f"Bearer {openrouter_key_input}",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "NEXORA AUDIO TRANSCRIPTION"
    }
    with open(chunk_path, "rb") as audio_file:
        files = {
            "file": audio_file
        }
        data = {
            "model": "openai/whisper-1",
            "response_format": "text"
        }
        response = requests.post(
            url,
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )
    if response.status_code != 200:
        raise Exception(f"Transcription failed: {response.status_code} - {response.text}")
    result = response.text.strip()
    if not result:
        raise Exception("Transcription returned empty result")
    return result
    
def transcribe_chunk(chunks):
    transcript_parts = [None] * len(chunks)
    
    def transcribe_with_retry(idx, chunk_path):
        max_retries = 2
        for attempt in range(max_retries):
            try:
                return idx, transcribe(chunk_path)
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Retrying chunk {idx+1} (attempt {attempt+2}/{max_retries})")
                    time.sleep(0.3)
                else:
                    print(f"Failed chunk {idx+1} after {max_retries} attempts: {e}")
                    return idx, ""
        return idx, ""
    
    # Use ThreadPoolExecutor for parallel transcription (6 workers for faster processing)
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(transcribe_with_retry, i, chunk): i for i, chunk in enumerate(chunks)}
        for future in as_completed(futures):
            idx, text = future.result()
            transcript_parts[idx] = text + "\n" if text else ""
    
    transcript = "".join(filter(None, transcript_parts))
    return transcript
        
def generate_notes(transcript):
    url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
    headers = {
        "Authorization": f"Bearer {openrouter_key_input}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "NEXORA NOTES GENERATION"
    }
    max_chunk_chars = 4000
    chunks = [transcript[i:i+max_chunk_chars] for i in range(0, len(transcript), max_chunk_chars)]
    chunk_notes = [None] * len(chunks)

    def process_chunk(idx, chunk):
        prompt_messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert study assistant. "
                    "Convert the provided transcript chunk into concise, structured study notes. "
                    "Use short headings, bullet points, and a 1-2 sentence summary. Keep the output focused and self-contained for this chunk."
                )
            },
            {
                "role": "user",
                "content": f"Chunk {idx+1}/{len(chunks)}:\n\n{chunk}"
            }
        ]

        payload = {
            "model": "anthropic/claude-3.5-sonnet",
            "messages": prompt_messages,
            "temperature": 0.6,
            "max_tokens": 700
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            raise Exception(f"Notes generation failed for chunk {idx+1}: {response.status_code}")
        result = response.json()
        chunk_content = result["choices"][0]["message"]["content"]
        return idx, chunk_content

    # Process chunks in parallel (5 workers for faster generation)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_chunk, i, chunk): i for i, chunk in enumerate(chunks)}
        for future in as_completed(futures):
            idx, content = future.result()
            chunk_notes[idx] = content

    # If only one chunk, return it directly
    if len(chunk_notes) == 1:
        return chunk_notes[0]

    # Consolidate notes
    consolidation_prompt = (
        "You are an expert study assistant. Combine the following partial notes into a single, coherent set of study notes. "
        "Remove duplication, merge related points, order topics logically, and produce a short summary (2-4 sentences) at the top. Keep headings concise and use bullet points."
    )
    consolidation_input = "\n\n".join(chunk_notes)
    consolidation_messages = [
        {"role": "system", "content": consolidation_prompt},
        {"role": "user", "content": consolidation_input}
    ]

    payload2 = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": consolidation_messages,
        "temperature": 0.5,
        "max_tokens": 1000
    }

    response = requests.post(url, headers=headers, json=payload2, timeout=90)
    if response.status_code != 200:
        raise Exception(f"Notes consolidation failed: {response.status_code}")
    result = response.json()
    return result["choices"][0]["message"]["content"]
    
def convert_mp3(input_path):
        try:
            audio = AudioSegment.from_file(input_path)
            if input_path.endswith(".mp3"):
                return input_path
            mp3_path = input_path.replace(".wav", ".mp3")
            audio.export(mp3_path, format="mp3", bitrate="64k")
            return mp3_path
        except Exception as e:
            print(f"MP3 conversion warning: {e}")
            return input_path

def txt_speech(text, target_lang_code):
    """Synthesize `text` into a single WAV file in `target_lang_code`.
    This function chunks long text to avoid provider length limits, synthesizes
    each chunk with gTTS, then concatenates the resulting audio files.
    Returns path to the final WAV file.
    """
    # quick guard
    if not text:
        raise ValueError("No text provided for TTS")

    temp_dir = tempfile.mkdtemp()
    chunk_size = 3000  # characters per chunk 
    parts = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    part_paths = []

    for idx, part in enumerate(parts):
        try:
            tts = gTTS(text=part, lang=target_lang_code)
            mp3_path = os.path.join(temp_dir, f"part_{idx}.mp3")
            tts.save(mp3_path)
            part_paths.append(mp3_path)
        except Exception as e:
            # If fails ,raise with context
            raise RuntimeError(f"gTTS failed on chunk {idx}: {e}")

    # Concatenate parts 
    combined = None
    for p in part_paths:
        seg = AudioSegment.from_file(p)
        if combined is None:
            combined = seg
        else:
            combined += seg

    if combined is None:
        raise RuntimeError("TTS produced no audio parts")

    output_wav = os.path.join(temp_dir, "translated_output.wav")
    combined.export(output_wav, format="wav")
    return output_wav
