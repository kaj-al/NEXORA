import tempfile
import os
from moviepy import VideoFileClip
import whisper
from langchain_groq import ChatGroq
from faster_whisper import WhisperModel
import requests 
import yt_dlp
from pathlib import Path
from pydub import AudioSegment
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

# def speech_text(audio_path):
#     @st.cache_resource
#     def load_translation_model():
#         return WhisperModel("tiny", device="cpu", compute_type="int8")
    
#     print(f"[TRANSLATION] Starting speech-to-text transcription for: {audio_path}")
#     model = load_translation_model()
#     print("[TRANSLATION] Whisper model loaded successfully")
#     segments, info = model.transcribe(audio_path, language="en", beam_size=1)
#     text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
#     print(f"[TRANSLATION] Transcription completed. Length: {len(text)} characters")
#     return text

# def trans_txt(txt,target_lang):
#     print(f"[TRANSLATION] Starting text translation to language code: {target_lang}")
#     print(f"[TRANSLATION] Text length to translate: {len(txt)} characters")
#     translator = GoogleTranslator(source="auto", target=target_lang)
#     translated = translator.translate(txt)
#     print(f"[TRANSLATION] Translation completed. Translated text length: {len(translated)} characters")
#     return translated


# # translation
# whisper_model = WhisperModel("tiny", compute_type="int8")
# llm = ChatGroq(model="llama3-8b-8192")

# def transcribe(audio_path):
#     segments, _ = whisper_model.transcribe(audio_path,beam_size=1,vad_filter=True)
#     return " ".join([seg.text for seg in segments])

# def fast_translate_chunks(text, target_lang):
#     text = text[:2000]
#     chunks = [text[i:i+500] for i in range(0, len(text), 500)]

#     def process(chunk):
#         return llm.invoke(f"Translate into {target_lang}:\n{chunk}").content

#     with ThreadPoolExecutor(max_workers=4) as executor:
#         results = list(executor.map(process, chunks))

#     return " ".join(results)

# def text_to_speech(text, lang_code):

#     tts = gTTS(text=text, lang=lang_code)

#     output_file = "translated_audio.mp3"
#     tts.save(output_file)

#     return output_file

# def audio_to_translated_audio(audio_path, target_lang, lang_code):

#     transcript = transcribe(audio_path)

#     translated_text = fast_translate_chunks(transcript, target_lang)

#     audio_file = text_to_speech(translated_text, lang_code)

#     return transcript, translated_text, audio_file
# # def translate_speech_to_speech(audio_path, target_lang_code):
# #     """
# #     Complete speech-to-speech translation pipeline
# #     Input: Audio file (speech in any language)
# #     Output: Audio file (speech in target language)
# #     """
# #     print("\n" + "="*70)
# #     print("SPEECH-TO-SPEECH TRANSLATION STARTED")
# #     print("="*70)
    
# #     try:
# #         print("\n[STEP 1/2] Translating audio internally to target language...")
# #         from faster_whisper import WhisperModel as _WhisperModel
# #         _model = _WhisperModel("tiny", device="cpu", compute_type="int8")
# #         segments, info = _model.transcribe(audio_path, task="translate", beam_size=1)
# #         translated_text = " ".join(segment.text for segment in segments).strip()
# #         print(f"[INTERNAL TRANSLATION] Translated text length: {len(translated_text)} characters")

# #         # Synthesize translated text to audio (handles long text by chunking)
# #         print("\n[STEP 2/2] Synthesizing translated speech to audio file...")
# #         output_audio_path = txt_speech(translated_text, target_lang_code)
# #         print(f"[TEXT-TO-SPEECH] ✓ Audio generated: {output_audio_path}")
        
# #         print("\n" + "="*70)
# #         print("SPEECH-TO-SPEECH TRANSLATION COMPLETED SUCCESSFULLY!")
# #         print(f"INPUT:  Audio (speech) in source language")
# #         print(f"OUTPUT: Audio (speech) in target language")
# #         print("="*70 + "\n")
        
# #         return output_audio_path
        
# #     except Exception as e:
# #         print(f"\n ERROR in speech-to-speech translation: {str(e)}")
# #         print("="*70 + "\n")
# #         raise


# def save_audio(uploaded_audio):
#         with tempfile.NamedTemporaryFile(delete=False,suffix=".wav") as temp:
#             temp.write(uploaded_audio.read())
#             return temp.name
    
# def split(audio_path, chunk_min=2):
#         audio = AudioSegment.from_file(audio_path)
#         chunk_len = chunk_min * 60 * 1000
#         chunks = []
#         for i in range(0, len(audio), chunk_len):
#             chunk = audio[i:i + chunk_len]
#             chunk_path = f"{audio_path}_chunk_{i}.wav"
#             chunk.export(chunk_path, format="wav")
#             chunks.append(chunk_path)
#         return chunks
    
# # def load_model():
# #     return whisper.load_model("base")
# # model = load_model()

# # def transcribe(chunk_path):
# #     url = os.getenv("OPENROUTER_AUDIO_URL", "https://openrouter.ai/api/v1/audio/transcriptions")
# #     headers = {
# #         "Authorization": f"Bearer {openrouter_key_input}",
# #         "HTTP-Referer": "http://localhost:8501",
# #         "X-Title": "NEXORA AUDIO TRANSCRIPTION"
# #     }
# #     try:
# #         session = create_requests_session(retries=3, backoff_factor=1)
# #         with open(chunk_path, "rb") as audio_file:
# #             files = {
# #                 "file": audio_file
# #             }
# #             data = {
# #                 "model": "openai/whisper-1",
# #                 "response_format": "text"
# #             }
# #             response = session.post(
# #                 url,
# #                 headers=headers,
# #                 files=files,
# #                 data=data,
# #                 timeout=120
# #             )
# #         if response.status_code != 200:
# #             raise Exception(f"Transcription failed: {response.status_code} - {response.text}")
# #         result = response.text.strip()
# #         if not result:
# #             raise Exception("Transcription returned empty result")
# #         return result
# #     except requests.exceptions.ConnectionError as e:
# #         raise Exception(f"Connection error: Unable to reach OpenRouter API. Please check your internet connection.")
# #     except requests.exceptions.Timeout:
# #         raise Exception(f"Timeout error: The transcription request took too long. Please try again.")
# #     except Exception as e:
# #         raise Exception(f"Transcription error: {str(e)}")
    
# # def transcribe_chunk(chunks):
# #     transcript_parts = [None] * len(chunks)
    
# #     def transcribe_with_retry(idx, chunk_path):
# #         max_retries = 2
# #         for attempt in range(max_retries):
# #             try:
# #                 return idx, transcribe(chunk_path)
# #             except Exception as e:
# #                 if attempt < max_retries - 1:
# #                     print(f"Retrying chunk {idx+1} (attempt {attempt+2}/{max_retries})")
# #                     time.sleep(0.3)
# #                 else:
# #                     print(f"Failed chunk {idx+1} after {max_retries} attempts: {e}")
# #                     return idx, ""
# #         return idx, ""
    
# #     # Use ThreadPoolExecutor for parallel transcription (6 workers for faster processing)
# #     try:
# #         with ThreadPoolExecutor(max_workers=6) as executor:
# #             futures = {executor.submit(transcribe_with_retry, i, chunk): i for i, chunk in enumerate(chunks)}
# #             for future in as_completed(futures):
# #                 try:
# #                     idx, text = future.result()
# #                     transcript_parts[idx] = text + "\n" if text else ""
# #                 except Exception as e:
# #                     print(f"Error in chunk transcription: {str(e)}")
# #                     raise
        
# #         transcript = "".join(filter(None, transcript_parts))
# #         return transcript
# #     except requests.exceptions.ConnectionError as e:
# #         raise Exception(f"Connection error during transcription: Unable to reach OpenRouter API. Please check your internet connection.")
# #     except Exception as e:
# #         raise Exception(f"Error during chunk transcription: {str(e)}")

        
# def generate_notes(transcript):
#     url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
#     headers = {
#         "Authorization": f"Bearer {openrouter_key_input}",
#         "Content-Type": "application/json",
#         "HTTP-Referer": "http://localhost:8501",
#         "X-Title": "NEXORA NOTES GENERATION"
#     }
#     max_chunk_chars = 4000
#     chunks = [transcript[i:i+max_chunk_chars] for i in range(0, len(transcript), max_chunk_chars)]
#     chunk_notes = [None] * len(chunks)

#     def process_chunk(idx, chunk):
#         prompt_messages = [
#             {
#                 "role": "system",
#                 "content": (
#                     "You are an expert study assistant. "
#                     "Convert the provided transcript chunk into concise, structured study notes. "
#                     "Use short headings, bullet points, and a 1-2 sentence summary. Keep the output focused and self-contained for this chunk."
#                 )
#             },
#             {
#                 "role": "user",
#                 "content": f"Chunk {idx+1}/{len(chunks)}:\n\n{chunk}"
#             }
#         ]

#         payload = {
#             "model": "anthropic/claude-3.5-sonnet",
#             "messages": prompt_messages,
#             "temperature": 0.6,
#             "max_tokens": 700
#         }

#         try:
#             session = create_requests_session(retries=3, backoff_factor=1)
#             response = session.post(url, headers=headers, json=payload, timeout=60)
#             if response.status_code != 200:
#                 raise Exception(f"Notes generation failed for chunk {idx+1}: {response.status_code}")
#             result = response.json()
#             chunk_content = result["choices"][0]["message"]["content"]
#             return idx, chunk_content
#         except requests.exceptions.ConnectionError as e:
#             raise Exception(f"Connection error while processing chunk {idx+1}: Unable to reach OpenRouter API. Please check your internet connection.")
#         except requests.exceptions.Timeout:
#             raise Exception(f"Timeout error while processing chunk {idx+1}: The request took too long. Please try again.")
#         except Exception as e:
#             raise Exception(f"Error processing chunk {idx+1}: {str(e)}")

#     # Process chunks in parallel (5 workers for faster generation)
#     try:
#         with ThreadPoolExecutor(max_workers=5) as executor:
#             futures = {executor.submit(process_chunk, i, chunk): i for i, chunk in enumerate(chunks)}
#             for future in as_completed(futures):
#                 idx, content = future.result()
#                 chunk_notes[idx] = content

#         # If only one chunk, return it directly
#         if len(chunk_notes) == 1:
#             return chunk_notes[0]

#         # Consolidate notes
#         consolidation_prompt = (
#             "You are an expert study assistant. Combine the following partial notes into a single, coherent set of study notes. "
#             "Remove duplication, merge related points, order topics logically, and produce a short summary (2-4 sentences) at the top. Keep headings concise and use bullet points."
#         )
#         consolidation_input = "\n\n".join(chunk_notes)
#         consolidation_messages = [
#             {"role": "system", "content": consolidation_prompt},
#             {"role": "user", "content": consolidation_input}
#         ]

#         payload2 = {
#             "model": "anthropic/claude-3.5-sonnet",
#             "messages": consolidation_messages,
#             "temperature": 0.5,
#             "max_tokens": 1000
#         }

#         session = create_requests_session(retries=3, backoff_factor=1)
#         response = session.post(url, headers=headers, json=payload2, timeout=90)
#         if response.status_code != 200:
#             raise Exception(f"Notes consolidation failed: {response.status_code}")
#         result = response.json()
#         return result["choices"][0]["message"]["content"]
#     except requests.exceptions.ConnectionError as e:
#         raise Exception(f"Connection error: Unable to reach OpenRouter API. Please check your internet connection.")
#     except requests.exceptions.Timeout:
#         raise Exception(f"Timeout error: The request took too long. Please try again.")
#     except Exception as e:
#         raise Exception(f"Error generating notes: {str(e)}")
    
# def convert_mp3(input_path):
#         try:
#             audio = AudioSegment.from_file(input_path)
#             if input_path.endswith(".mp3"):
#                 return input_path
#             mp3_path = input_path.replace(".wav", ".mp3")
#             audio.export(mp3_path, format="mp3", bitrate="64k")
#             return mp3_path
#         except Exception as e:
#             print(f"MP3 conversion warning: {e}")
#             return input_path

# def txt_speech(text, target_lang_code):
#     """Synthesize `text` into a single WAV file in `target_lang_code`.
#     This function chunks long text to avoid provider length limits, synthesizes
#     each chunk with gTTS, then concatenates the resulting audio files.
#     Returns path to the final WAV file.
#     """
#     # quick guard
#     if not text:
#         raise ValueError("No text provided for TTS")

#     temp_dir = tempfile.mkdtemp()
#     chunk_size = 3000  # characters per chunk 
#     parts = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
#     part_paths = []

#     for idx, part in enumerate(parts):
#         try:
#             tts = gTTS(text=part, lang=target_lang_code)
#             mp3_path = os.path.join(temp_dir, f"part_{idx}.mp3")
#             tts.save(mp3_path)
#             part_paths.append(mp3_path)
#         except Exception as e:
#             # If fails ,raise with context
#             raise RuntimeError(f"gTTS failed on chunk {idx}: {e}")

#     # Concatenate parts 
#     combined = None
#     for p in part_paths:
#         seg = AudioSegment.from_file(p)
#         if combined is None:
#             combined = seg
#         else:
#             combined += seg

#     if combined is None:
#         raise RuntimeError("TTS produced no audio parts")

#     output_wav = os.path.join(temp_dir, "translated_output.wav")
#     combined.export(output_wav, format="wav")
#     return output_wav
