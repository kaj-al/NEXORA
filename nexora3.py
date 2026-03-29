
import streamlit as st
import tempfile
import os
import requests
import random
from config import llm_model,model_size,openrouter_key_input
from tab1 import call_openrouter,load_whisper_model, download_audio_fast, extract_audio
from tab4 import documentation,youtube
from transcription import process_audio


# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Nexora",layout="wide")
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
tabs = st.tabs(["Home", "Audio Extraction & Transcription", "Study Notes", "Asessment Paper","Recommendation"])

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
    - Upload a local lecture video or paste a YouTube link → extract audio → transcription .
    - Paste text or lecture transcript to generate *concise study notes, **key points, and **a study plan*.
    - Save generated notes locally .
    - Generate a Assesment Paper.
    - Try Raecommendation for youtube videos and documentations.
    """)

# ---------------- VIDEO Audio TAB ----------------
with tabs[1]:
    st.header("Audio Extraction & Transcription")
    st.write("Upload a video file or provide a YouTube link. Nexora will extract audio and transcribe")
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
                with st.spinner("Downloading audio..."):
                    audio_path = download_audio_fast(yt_url)
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

# Transcription
    file = st.file_uploader("Upload Audio", type=["wav","mp3","m4a"])
    if file:
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp.write(file.read())
        audio_path = temp.name
        st.audio(audio_path)
        if st.button("Generate Transcript"):
            with st.spinner("Processing..."):
                transcript = process_audio(audio_path)
            st.success("Done!")
            st.subheader("Transcript")
            st.write(transcript)

# ---------------- STUDY Notes TAB ----------------
with tabs[2]:
    st.header("Study Notes (Text Input)")
    st.write(f"Paste any lecture transcript or text")
    user_text = st.text_area("Paste transcript or lecture text here", height=240)
    if user_text:
        st.markdown("Options for generation:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate Notes"):
                    with st.spinner("Generating notes..."):
                        prompt = f"Generate structured study notes, key points, and a short summary from this text:\n\n{user_text}"
                        notes_out = call_openrouter(openrouter_key_input, prompt, model=llm_model)
                        st.markdown("Nexora Notes")
                        st.markdown(f"<div class='box' , style='color:black'>{notes_out}</div>",unsafe_allow_html=True)
                        st.download_button("Download Notes", notes_out, file_name="studyzen_notes.txt")
        with col2:
            if st.button("Create Study Plan"):
                    with st.spinner("Creating study plan..."):
                        prompt = f"Create a study plan with daily goals and 5 practice questions based on this content:\n\n{user_text}"
                        plan = call_openrouter(openrouter_key_input, prompt, model=llm_model)
                        st.markdown("Study Plan")
                        st.markdown(f"<div class='box', style='color:black'>{plan}</div>", unsafe_allow_html=True)
        
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

# ----------------- AI Assessment Generator -----------------
with tabs[3]:
    st.markdown("## AI Assessment Paper Generator")
    st.markdown("""
        <p style='color:#22223b; font-size:17px;'>
            Type any subject or topic, and AI will create a quiz or assessment paper with questions, options, and answers.
        </p>
    """, unsafe_allow_html=True)
    topic = st.text_input("Enter Subject or Topic:", placeholder="Topic...")
    difficulty = st.selectbox("Select Difficulty Level:", ["Easy", "Medium", "Hard"])
    num_questions = st.slider("Number of Questions:", 5, 20, 10)
    generate_btn = st.button("Generate Assessment Paper")
    if generate_btn and topic:
        with st.spinner("AI is preparing your assessment paper..."):
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

# # ---------------- ABOUT TAB ----------------
# with tabs[5]:
#     st.header("About Nexora")
#     st.markdown("""
#     *Nexora* combines:
#     - Whisper for transcription (local model)
#     - OpenRouter LLMs for notes & study plans
#     - YouTube & local video support
#     - Lightweight local saving for a simple knowledge base

#     *How to use*
#     1. Choose Video Notes or Study Assistant.
#     2. Gives an assesment.
#     3. Generate, review, save, and download.

#     """)

with tabs[4]:
    st.title("Knowledge Explorer")
    topic = st.text_input("Enter a topic to explore:")
    level = st.selectbox("Select your expertise level:",["School","Senior School","College","Researcher"])
    if st.button("Explore"):
        query = topic + "for " +level + " students"
        videos = youtube(query)
        docs = documentation(query)
        # papers_list = papers(query)
        st.header("YouTube Videos")
        for video in videos:
            col1,col2 = st.columns([1,3])
            with col1:
                if video["thumbnail"]:
                    st.image(video["thumbnail"],width=140)
            with col2:
                st.markdown(f"###[{video['title']}]({video['url']})")
                st.write(f"Channel:{video['channel']}")
                st.write(f"Duration:{video['duration']}")
            st.divider()
            # st.video(video["url"])
        st.header("Documentation")
        for doc in docs:
            st.markdown(f"[{doc['title']}]({doc['url']})")
        # if level in ["College","Researcher"]:
        #     st.header("Research Papers")
        #     for paper in papers_list:
        #         st.markdown(f"[{paper['title']}]({paper['url']})")
            