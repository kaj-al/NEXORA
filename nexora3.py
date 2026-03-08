
import streamlit as st
import tempfile
import os
import requests
from pathlib import Path
import random
import pandas as pd
from config import llm_model,model_size,openrouter_key_input
from tab1 import call_openrouter,load_whisper_model, download_youtube_audio, extract_audio, notes, save_audio, split, transcribe_chunk,  generate_notes, convert_mp3, translate_speech_to_speech
from tab5 import load_data,add,detect_level,get_learning_stats,recommendation
from tab6 import qa_chain

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Nexora", page_icon="📘", layout="wide")
st.title("NEXORA - NEXT GEN NOTES AURA")

# ---------------- STYLE ----------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #EDAFB8; color: #BOC4B1; font-family: 'Inter', sans-serif; }
h1 { color:#a8f0e6; text-align:center; }
.section { background: rgba(255,255,255,0.03); padding: 14px; border-radius: 10px; margin-bottom: 12px; }
.box { background: rgba(255,255,255,0.04); padding: 12px; border-radius: 8px; color:#e6eef8; }
button[title="Run"] { }
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

if "whisper_model_size" not in st.session_state:
    st.session_state["whisper_model_size"] = model_size
if st.session_state["whisper_model_size"] != model_size:
    # reload
    st.session_state["whisper_model_size"] = model_size
    load_whisper_model.cache_clear()
model = load_whisper_model(model_size)

# ---------------- MAIN TABS ----------------
tabs = st.tabs(["Home", "Video Notes", "Study Assistant", "Saved Notes", "Asessment Paper","Analysis","NEXCHAT","About",])

# Pastel Zen Theme + White Tabs Text
st.markdown("""
    <style>
    /* Background and global text color */
    body {
        background-color: #e6eef8; /* Soft pastel blue background */
        color: #1a1a1a;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #4a4e69;  /* Indigo backdrop for tabs */
        border-radius: 12px;
        padding: 0.5rem;
    }

    /* Each tab text */
    .stTabs [data-baseweb="tab"] {
        color: white !important;  /* <-- White text for tabs */
        font-weight: 500;
        border-radius: 10px;
        padding: 0.6rem 1rem;
        transition: all 0.3s ease;
    }

    /* Hover and active tab */
    .stTabs [aria-selected="true"] {
        background-color: #9a8c98; /* Soft lavender for active tab */
        color: white !important;
        font-weight: 600;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #c9ada7;
        color: white !important;
    }

    /* Buttons, inputs and headers */
    .stButton>button {
        background-color: #4a4e69;
        color: white;
        border-radius: 10px;
        border: none;
        transition: 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #9a8c98;
        color: white;
    }

    h1, h2, h3 {
        color: #22223b;
    }

    .stMarkdown {
        color: #1a1a1a;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- HOME ----------------
with tabs[0]:
    st.markdown("<div class='section'><h2>Welcome to NEXORA</h2>"
                "<p style='color:#cfeef0;'>Combine video-based notes (YouTube / upload) and text-based study assistant in one app.</p></div>", unsafe_allow_html=True)
    st.markdown("""
    *Features*
    - Upload a local lecture video or paste a YouTube link → extract audio → Whisper transcription → OpenRouter notes.
    - Paste text or lecture transcript to generate *concise study notes, **key points, and **a study plan*.
    - Save generated notes locally and browse them in "Saved Notes".
    """)

# ---------------- VIDEO NOTES TAB ----------------
with tabs[1]:
    st.header("Video Notes")
    st.write("Upload a video file or provide a YouTube link. Nexora will extract audio, transcribe, and generate study notes.")
    source = st.radio("Source", ["Upload video", "YouTube link"], horizontal=True)

    video_file_path = None
    # upload video
    if source == "Upload video":
        uploaded = st.file_uploader("Upload video file", type=["mp4","mkv","mov","avi"])
        if uploaded is not None:
            tmp_vid = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tmp_vid.write(uploaded.read())
            tmp_vid.flush()
            video_file_path = tmp_vid.name
            st.video(video_file_path)

            # youtube link
    else:
        yt_url = st.text_input("YouTube URL")
        if st.button("Download YouTube audio"):
            try:
                audio_path = download_youtube_audio(yt_url)
                if os.path.exists(audio_path):
                    st.success("downloaded")
                    st.audio(audio_path)
                else: 
                    st.error("not created")
            except Exception as e:
                st.error(f"failed: {e}")

            #  generate audio
    if video_file_path:
        st.markdown("---")
        st.info("Step 1: Extract audio and generate notes.")
        if st.button("Extract audio"):
            audio_file = extract_audio(video_file_path, audio_ext=".wav")
            st.audio(audio_file)
            st.session_state["org_audio"] = audio_file
            st.success("genrated")
        
        if "org_audio" in st.session_state:
            with open(st.session_state["org_audio"], "rb") as audio_file_obj:
                st.download_button(
                    label="Download Extracted Audio",
                    data=audio_file_obj.read(),
                    file_name="extracted_audio.wav",
                    mime="audio/wav"
                )

        if "org_audio" in st.session_state:
            language_map = {
                "Hindi": "hi",
                "English": "en",
                "Japanese": "ja",
                "French": "fr",
                "German": "de",
                "Spanish": "es"
            }
            select_lang = st.selectbox("Select language", list(language_map.keys()))
            if st.button("Translate Speech to Speech"):
                with st.spinner("Processing speech-to-speech translation..."):
                    try:
                        out_audio = translate_speech_to_speech(
                            st.session_state["org_audio"],
                            language_map[select_lang]
                        )
                        st.success(f" Speech translated to {select_lang} successfully!")
                        st.audio(out_audio)
                    except Exception as e:
                        st.error(f"Translation error: {e}")

    # generate notes
    
    uploaded_audio = st.file_uploader("Upload Lecture Audio(MP3 / WAV)", type=["mp3","wav"])
    if uploaded_audio:
        st.audio(uploaded_audio)
        if st.button("Generate transcript and notes"):
            with st.spinner("Processing audio... (this may take 1-2 minutes)"):
                try:
                    audio_path = save_audio(uploaded_audio)
                    audio_path = convert_mp3(audio_path)
                    chunks = split(audio_path, chunk_min=2)
                    
                    with st.spinner("Transcribing audio chunks..."):
                        transcript = transcribe_chunk(chunks)
                    st.session_state["transcript"] = transcript
                    
                    with st.spinner("Generating study notes from transcript..."):
                        notes_content = generate_notes(transcript)
                    
                    st.subheader("TRANSCRIPT")
                    st.text_area("Transcript", transcript, height=250)
                    st.subheader("NOTES")
                    st.markdown(notes_content)
                    st.download_button(
                        "Download Notes",
                        data=notes_content,
                        file_name="Nexora_Notes.txt"
                    )
                    st.success("Notes generated successfully!")
                except Exception as e:
                    st.error(f"Error generating notes: {str(e)}")

    
            
# ---------------- STUDY ASSISTANT TAB ----------------
with tabs[2]:
    st.header("Study Assistant (Text Input)")
    st.write(f"Paste any lecture transcript or text")
    user_text = st.text_area("Paste transcript or lecture text here", height=240)
    if user_text:
        st.markdown("Options for generation:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate Notes (OpenRouter)"):
                if not openrouter_key_input:
                    st.warning("Add OpenRouter API key in sidebar first.")
                else:
                    with st.spinner("Generating notes..."):
                        prompt = f"Generate structured study notes, key points, and a short summary from this text:\n\n{user_text}"
                        notes_out = call_openrouter(openrouter_key_input, prompt, model=llm_model)
                        st.markdown("###AI Notes")
                        st.markdown(f"<div class='box'>{notes_out}</div>", unsafe_allow_html=True)
                        st.download_button("Download Notes", notes_out, file_name="studyzen_notes.txt")
        with col2:
            if st.button("Create Study Plan"):
                if not openrouter_key_input:
                    st.warning("Add OpenRouter API key in sidebar first.")
                else:
                    with st.spinner("Creating study plan..."):
                        prompt = f"Create a study plan with daily goals and 5 practice questions based on this content:\n\n{user_text}"
                        plan = call_openrouter(openrouter_key_input, prompt, model=llm_model)
                        st.markdown("### Study Plan")
                        st.markdown(f"<div class='box'>{plan}</div>", unsafe_allow_html=True)
        

#  Feeling Spontaneous? Get Random Study Tips
        st.subheader("Feeling Spontaneous?")
        if st.button("I need a Study Tip!", use_container_width=True):
            study_tips = [
                "Break your study sessions into 25-minute chunks with 5-minute breaks (Pomodoro Technique).",
                "Use flashcards to memorize key concepts and terms.",
                "Teach what you've learned to someone else—it reinforces your understanding.",
                "Create mind maps to visualize complex topics.",
                "Practice past exam papers to get familiar with the format and timing.",
                "Stay hydrated and take short walks to refresh your mind.",
                "Use mnemonic devices to remember lists or sequences.",
                "Set specific, achievable goals for each study session.",
                "Avoid multitasking—focus on one subject at a time.",
                "Review your notes within 24 hours to improve retention."
            ]
            st.write(f"**Study Tip:** {random.choice(study_tips)}")


# ---------------- SAVED NOTES TAB ----------------
with tabs[3]:
    st.header(" Saved Notes")
    folder = Path("studyzen_saved")
    folder.mkdir(exist_ok=True)
    files = sorted(folder.glob("*.txt"), reverse=True)
    if not files:
        st.info("No saved notes yet.")
    else:
        choice = st.selectbox("Open saved note:", [f.name for f in files])
        if choice:
            content = Path(folder / choice).read_text(encoding="utf-8")
            st.markdown(f"### {choice}")
            st.text_area("Content", content, height=400)
            if st.button("Delete this note"):
                os.remove(folder / choice)
                st.success("Deleted.")
                st.experimental_rerun()

# ----------------- AI Assessment Generator Section -----------------
with tabs[4]:
    st.markdown("## AI Assessment Paper Generator")

    st.markdown("""
        <p style='color:#22223b; font-size:17px;'>
            Type any subject or topic, and AI will create a quiz or assessment paper with questions, options, and answers.
        </p>
    """, unsafe_allow_html=True)

    topic = st.text_input("Enter Subject or Topic:", placeholder="e.g., Machine Learning Basics, Python Loops, DBMS Keys")

    difficulty = st.selectbox("Select Difficulty Level:", ["Easy", "Medium", "Hard"])
    num_questions = st.slider("Number of Questions:", 5, 20, 10)

    generate_btn = st.button("Generate Assessment Paper")

    if generate_btn and topic:
        with st.spinner("AI is preparing your assessment paper... ⏳"):
            try:
                headers = {
                    "Authorization": f"Bearer {openrouter_key_input}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": llm_model,
                    "messages": [
                        {"role": "system", "content": "You are an AI that generates structured educational assessment papers."},
                        {"role": "user", "content": f"Generate a {difficulty.lower()} level quiz with {num_questions} questions on {topic}. Half of questions should have 4 options (A, B, C, D) and specify the correct answer at the end.and half of questions are answer these questions type descriptive questions and specify the right answers at the end of all the desciptive questions with their question number"},
                    ]
                }
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                result = response.json()
                ai_output = result["choices"][0]["message"]["content"]
                st.markdown("### Generated Assessment Paper")
                st.markdown(f"""
                    <div class='assessment-box'>
                        <pre>{ai_output}</pre>
                    </div>
                """, unsafe_allow_html=True)

                st.download_button(
                    label="Download Assessment Paper",
                    data=ai_output,
                    file_name=f"{topic.replace(' ', '_')}_assessment.txt",
                    mime="text/plain"
                )

            except Exception as e:
                st.error(f"Error generating assessment: {e}")  


# ---------------- ABOUT TAB ----------------
with tabs[7]:
    st.header("About Nexora")
    st.markdown("""
    *Nexora* combines:
    - Whisper for transcription (local model)
    - OpenRouter LLMs for notes & study plans
    - YouTube & local video support
    - Lightweight local saving for a simple knowledge base

    *How to use*
    1. Choose Video Notes or Study Assistant.
    2. Gives an assesment.
    3. Generate, review, save, and download.

    """)

with tabs[5]:
    st.header("Nexora - Learning Analytics & Next Support")
    
    data = load_data()
    df = pd.DataFrame(data) if data else pd.DataFrame()

    #Metrics
    if data:
        level,active_days = detect_level(data)
        stats = get_learning_stats(data)
    else:
        level,active_days = "Beginner" , 0
        stats = {"total_entries": 0, "active_days": 0, "formats": {}, "recent_topics": []}
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Level", level)
    col2.metric("Active Days", active_days)
    col3.metric("Total Entries", stats["total_entries"])

    st.divider()

    # Learning breakdown
    if stats["formats"]:
        st.subheader("Learning Formats Distribution")
        col_fmt1, col_fmt2 = st.columns(2)
        with col_fmt1:
            st.bar_chart(pd.Series(stats["formats"]))
        with col_fmt2:
            st.write("**Format Breakdown:**")
            for fmt, count in stats["formats"].items():
                st.write(f"- {fmt}: {count}")

    st.divider()

    # Recent learning with button
    if st.button("View Recent Topics"):
        if stats["recent_topics"]:
            st.subheader("Recent Topics")
            for topic in stats["recent_topics"]:
                st.write(f"• {topic}")
        else:
            st.info("No recent topics yet. Start logging to see your recent learning!")

    st.divider()

    st.subheader("Log learning")
    query = st.text_input("Topic")
    format = st.selectbox("Format",["video","audio","pdf","notes"])
    if st.button("Save"):
        if query and query.strip():
            try:
                add(query, format)
                st.success("Saved")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving: {str(e)}")
        else:
            st.warning("Please enter a topic")
    
    st.divider()

    # AI Recommendations
    st.subheader("AI Learning Recommendations")
    rec_topic = st.text_input("Enter a topic to get recommendations for:")
    if st.button("Get Study Recommendations"):
        if rec_topic and rec_topic.strip():
            with st.spinner("Generating personalized recommendations..."):
                try:
                    rec = recommendation(rec_topic, level)
                    st.markdown(rec)
                except Exception as e:
                    st.error(f"Error generating recommendations: {str(e)}")
        else:
            st.warning("Please enter a topic to get recommendations")

    st.divider()

    st.markdown("""
                ### INSIGHT SUMMARY
                - Analysis is based on transcript, notes and assessment comparison
                - Weak areas are automatically detected
                - Study guidance adapts to learner's understanding level
                - Helps students focus on what matters most
    """)
    
        
with tabs[7]:
    st.header("NEXCHAT")
    st.write("Nexchat!!, Ask Anything")

    chain = qa_chain()

    if "history" not in st.session_state:
        st.session_state.history=[]

    query = st.text_input("Ask question")

    if query:
        with st.spinner("Thinking..."):
            result = chain.run(query)
        st.session_state.history.append({"query":query,"answer":result})
    
    for chat in st.session_state.history[::-1]:
        st.markdown(f"**You:**{chat['query']}")
        st.markdown(f"**Nexora:**{chat['answer']}")
        

    
    
    
    
