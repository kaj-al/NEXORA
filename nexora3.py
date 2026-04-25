
import streamlit as st
import tempfile
import os
import requests
import random
from config import llm_model,model_size,openrouter_key_input
from tab1 import call_openrouter,load_whisper_model, download_audio_fast, extract_audio
from tab4 import documentation,youtube,papers
from transcription import process_audio


# ============ CACHE & SESSION STATE INITIALIZATION ============
@st.cache_resource
def load_whisper_model_cached(size):
    return load_whisper_model(size)

@st.cache_data(ttl=3600)
def get_resources(query, level):
    """Cache resource queries for 1 hour"""
    videos = youtube(query)
    docs = documentation(query)
    papers_list = papers(query)
    return {"videos": videos, "docs": docs, "papers": papers_list}

# Initialize session state
def init_session_state():
    if "tab_index" not in st.session_state:
        st.session_state.tab_index = 0
    if "transcript" not in st.session_state:
        st.session_state.transcript = None
    if "generated_notes" not in st.session_state:
        st.session_state.generated_notes = None
    if "study_plan" not in st.session_state:
        st.session_state.study_plan = None
    if "assessment_result" not in st.session_state:
        st.session_state.assessment_result = None

init_session_state()

# Callback functions 
def on_generate_notes():
    st.session_state.generating_notes = True

def on_generate_plan():
    st.session_state.generating_plan = True

def on_generate_assessment():
    st.session_state.generating_assessment = True

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Nexora", layout="wide", initial_sidebar_state="expanded")
st.markdown(
    "<h1 style='text-align:center; color:#E75480; font-family: \"Hero\", \"Tan Aegan\", sans-serif; margin-bottom: 0.5rem;'>✨ NEXORA - NEXT GEN NOTES AURA ✨</h1>",
    unsafe_allow_html=True,
)

# ---------------- STYLE ---------------- 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tangerine:wght@400;700&display=swap');

[data-testid="stAppViewContainer"] { background: #FFE5B4 !important; color: #E75480; font-family: 'Tan Aegan', 'Hero', sans-serif; }
[data-testid="stMainBlockContainer"] { background: #FFE5B4 !important; }
.stMain { background-color: #FFE5B4 !important; }

.section { background: #FFF5E6; padding: 14px; border-radius: 18px; margin-bottom: 16px; box-shadow: 0 18px 40px rgba(0,0,0,0.06); }
.box { background: #FFFFFF; padding: 16px; border-radius: 16px; color:#E75480; box-shadow: 0 14px 32px rgba(0,0,0,0.08); }
.hero { background: rgba(255,255,255,0.96); border-radius: 24px; padding: 28px; margin-bottom: 24px; box-shadow: 0 18px 40px rgba(0,0,0,0.08); }
.hero-title { font-size: 44px; font-weight: 800; line-height: 1.05; margin-bottom: 12px; }
.hero-text { font-size: 18px; color: #7B2C6F; margin-bottom: 20px; }
.feature-card { background: #FFFFFF; border-radius: 18px; padding: 22px; box-shadow: 0 16px 36px rgba(0,0,0,0.08); margin-bottom: 18px; }
.metric-card { background: #FFF5E6; border-radius: 16px; padding: 18px; }
.assessment-box { background: #FFF5E6; border-radius: 16px; padding: 18px; color:#5E3457; white-space: pre-wrap; }
.stButton>button { background-color: #E75480; color: white; border-radius: 10px; border: none; transition: 0.3s ease; font-family: 'Hero', 'Tan Aegan', sans-serif; }
.stButton>button:hover { background-color: #FFE5B4; color: #E75480; }

button[title="Run"] { }
footer { visibility: hidden; }

h1, h2, h3 { color: #E75480; font-family: 'Hero', 'Tan Aegan', sans-serif; }

.stMarkdown { color: #E75480; font-family: 'Hero', 'Tan Aegan', sans-serif; }
</style>
""", unsafe_allow_html=True)

if "whisper_model_size" not in st.session_state:
    st.session_state["whisper_model_size"] = model_size
if st.session_state["whisper_model_size"] != model_size:
    st.session_state["whisper_model_size"] = model_size
    load_whisper_model.cache_clear()
model = load_whisper_model(model_size)

# ---------------- MAIN TABS ----------------
tabs = st.tabs(["Home", "Audio Extraction & Transcription", "Study Notes", "Asessment Paper","Recommendation"])

# Pastel Zen Theme + White Tabs Text
st.markdown("""
    <style>
    /* Smooth fade-in animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes slideDown {
        from { opacity: 0; max-height: 0; padding: 0; }
        to { opacity: 1; max-height: 1000px; padding: inherit; }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Background and global text color */
    body {
        background-color: #FFE5B4 !important; /* Butter cream background */
        color: #E75480;
        font-family: 'Hero', 'Tan Aegan', sans-serif;
    }

    [data-testid="stAppViewContainer"],
    [data-testid="stMainBlockContainer"] {
        background: #FFE5B4 !important;
        animation: fadeIn 0.4s ease-in-out;
    }

    .stMain {
        background-color: #FFE5B4 !important;
    }

    /* Prevent transparency on rerun */
    [data-testid="stDecoration"] {
        display: none !important;
    }

    /* Smooth container animations */
    .element-container {
        animation: slideDown 0.3s ease-out;
    }

    .section, .box, .hero, .feature-card {
        animation: slideDown 0.4s ease-out;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #E75480;  /* Cherry pink for tabs */
        border-radius: 12px;
        padding: 0.5rem;
        animation: fadeIn 0.3s ease-in-out;
    }

    /* Each tab text */
    .stTabs [data-baseweb="tab"] {
        color: white !important;
        font-weight: 500;
        border-radius: 10px;
        padding: 0.6rem 1rem;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        font-family: 'Hero', 'Tan Aegan', sans-serif;
    }

    /* Hover and active tab */
    .stTabs [aria-selected="true"] {
        background-color: #FFE5B4;
        color: #E75480 !important;
        font-weight: 600;
        transform: scale(1.05);
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #FFE5B4;
        color: #E75480 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(231, 84, 128, 0.2);
    }

    /* Smooth button transitions */
    .stButton>button {
        background-color: #E75480;
        color: white;
        border-radius: 10px;
        border: none;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        font-family: 'Hero', 'Tan Aegan', sans-serif;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(231, 84, 128, 0.2);
    }

    .stButton>button:hover {
        background-color: #FFE5B4;
        color: #E75480;
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(231, 84, 128, 0.3);
    }

    .stButton>button:active {
        transform: scale(0.98);
    }

    /* Loading spinner smooth */
    .stSpinner {
        animation: pulse 1.5s ease-in-out infinite;
    }

    /* Headers */
    h1, h2, h3 {
        color: #E75480;
        font-family: 'Hero', 'Tan Aegan', sans-serif;
        animation: fadeIn 0.3s ease-in-out;
    }

    .stMarkdown {
        color: #E75480;
        font-family: 'Hero', 'Tan Aegan', sans-serif;
    }

    /* Form styling */
    .stForm {
        border: 2px solid #E75480 !important;
        border-radius: 16px !important;
        padding: 20px !important;
        background: rgba(255, 255, 255, 0.5) !important;
        animation: slideDown 0.4s ease-out;
    }

    /* Better input field transitions */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        border: 2px solid #E75480 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease;
    }

    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {
        border-color: #FFE5B4 !important;
        box-shadow: 0 0 0 3px rgba(231, 84, 128, 0.1) !important;
    }

    /* Expander smooth transitions */
    .streamlit-expanderHeader {
        transition: all 0.3s ease;
        background-color: #FFF5E6 !important;
        border-radius: 10px !important;
    }

    .streamlit-expanderHeader:hover {
        background-color: #FFE5B4 !important;
    }

    /* Info/success/error messages */
    .stAlert {
        animation: slideDown 0.3s ease-out;
        border-radius: 12px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- HOME ----------------
with tabs[0]:
    st.markdown(
        """
        <div class='hero'>
            <div class='hero-title'>Nexora</div>
            <div class='hero-text'>A deploy-ready study workspace for video lectures, transcription, notes, and AI assessment generation.</div>
            <div style='display:flex;gap:12px;flex-wrap:wrap;'>
                <span style='background:#E75480;color:white;padding:10px 18px;border-radius:999px;font-weight:600;'>Lecture transcription</span>
                <span style='background:#FFE5B4;color:#E75480;padding:10px 18px;border-radius:999px;font-weight:600;'>Study notes</span>
                <span style='background:#E75480;color:white;padding:10px 18px;border-radius:999px;font-weight:600;'>AI assessment</span>
                <span style='background:#FFE5B4;color:#E75480;padding:10px 18px;border-radius:999px;font-weight:600;'>Resource explorer</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='feature-card'>
            <div style='display:flex;gap:16px;flex-wrap:wrap;'>
                <div style='flex:1; min-width:220px; background:#FFF5E6; border-radius:16px; padding:18px;'>
                    <h4>Fast Voice Transcription</h4>
                    <p>Convert audio into text quickly with local and remote support.</p>
                </div>
                <div style='flex:1; min-width:220px; background:#FFF5E6; border-radius:16px; padding:18px;'>
                    <h4>Smart Study Notes</h4>
                    <p>Generate summaries, key points, and plans from your lecture text.</p>
                </div>
                <div style='flex:1; min-width:220px; background:#FFF5E6; border-radius:16px; padding:18px;'>
                    <h4>AI Assessment Builder</h4>
                    <p>Create quizzes and practice papers in one click.</p>
                </div>
                <div style='flex:1; min-width:220px; background:#FFF5E6; border-radius:16px; padding:18px;'>
                    <h4>Recommendation System</h4>
                    <p>Resource recommend for selected topic - Youtube, Documentations, Research Papers</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )




# ---------------- VIDEO Audio TAB ----------------
with tabs[1]:
    st.markdown("""
        <div class='section'>
            <h2>Audio Extraction & Transcription</h2>
            <p>Upload lecture video or paste a YouTube link. Nexora extracts audio, transcribes it and makes it available to download.</p>
        </div>
    """, unsafe_allow_html=True)

    # Audio Source Selection
    source = st.radio("Select Source", ["Upload video", "YouTube link"], horizontal=True, key="audio_source")
    video_file_path = None

    if source == "Upload video":
        uploaded = st.file_uploader("Upload video file", type=["mp4","mkv","mov","avi"], key="video_uploader_tab1")
        if uploaded is not None:
            try:
                tmp_vid = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                tmp_vid.write(uploaded.read())
                tmp_vid.flush()
                video_file_path = tmp_vid.name
                st.video(video_file_path)
                st.success("Video loaded successfully!")

                if st.button("Extract Audio", key="btn_extract_audio_tab1", use_container_width=True):
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    try:
                        status_text.text("Extracting audio...")
                        progress_bar.progress(25)

                        with st.spinner("Processing video..."):
                            audio_file = extract_audio(video_file_path, audio_ext=".wav")

                        progress_bar.progress(75)
                        st.session_state["org_audio"] = audio_file

                        progress_bar.progress(100)
                        status_text.success("Audio extracted successfully!")

                        st.audio(audio_file)

                        with st.container():
                            st.download_button(
                                label="⬇Download Extracted Audio",
                                data=open(audio_file, "rb").read(),
                                file_name="extracted_audio.wav",
                                mime="audio/wav",
                                use_container_width=True
                            )

                    except Exception as e:
                        st.error(f"Extraction failed: {str(e)}")
                    finally:
                        progress_bar.empty()
                        status_text.empty()

            except Exception as e:
                st.error(f"Error loading video: {str(e)}")

    else:
        with st.expander("YouTube Audio Extraction", expanded=True):
            yt_form_col1, yt_form_col2 = st.columns([3, 1])

            with yt_form_col1:
                yt_url = st.text_input("Paste YouTube URL", key="yt_url_tab1", placeholder="https://www.youtube.com/watch?v=...")

            with yt_form_col2:
                download_yt_btn = st.button("⬇Download", key="btn_download_yt_tab1", use_container_width=True)

            if download_yt_btn and yt_url:
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    status_text.text("Downloading audio...")
                    progress_bar.progress(30)

                    with st.spinner("Downloading from YouTube..."):
                        audio_path = download_audio_fast(yt_url)

                    progress_bar.progress(70)

                    if os.path.exists(audio_path):
                        progress_bar.progress(100)
                        status_text.success("Downloaded successfully!")

                        st.audio(audio_path)
                        st.session_state["org_audio"] = audio_path

                        st.download_button(
                            label="⬇Download Audio File",
                            data=open(audio_path, "rb").read(),
                            file_name="youtube_audio.wav",
                            mime="audio/wav",
                            use_container_width=True
                        )
                    else:
                        st.error("Audio file could not be created")

                except Exception as e:
                    st.error(f"Download failed: {str(e)}")
                finally:
                    progress_bar.empty()
                    status_text.empty()

            elif download_yt_btn and not yt_url:
                st.warning("Please enter a YouTube URL")

    # Transcription 
    st.markdown("""
        <div class='section'>
            <h3>Audio Transcription</h3>
            <p>Upload a WAV/MP3/M4A file to convert speech into text. The transcript is displayed below and can be downloaded.</p>
        </div>
    """, unsafe_allow_html=True)

    file = st.file_uploader("Upload Audio File", type=["wav","mp3","m4a"], key="audio_uploader_tab1")
    if file:
        try:
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp.write(file.read())
            audio_path = temp.name
            st.audio(audio_path)

            if st.button("Generate Transcript", key="btn_transcript_tab1", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    status_text.text("Transcribing audio...")
                    progress_bar.progress(25)

                    with st.spinner("Processing audio..."):
                        transcript = process_audio(audio_path)

                    progress_bar.progress(100)
                    status_text.success("Transcription complete!")

                    st.subheader("Your Transcript")
                    st.markdown(f"<div class='box'>{transcript}</div>", unsafe_allow_html=True)

                    st.download_button(
                        "⬇Download Transcript",
                        transcript,
                        file_name="transcript.txt",
                        use_container_width=True
                    )

                except Exception as e:
                    st.error(f"Transcription failed: {str(e)}")
                finally:
                    progress_bar.empty()
                    status_text.empty()

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

# ---------------- STUDY Notes TAB ----------------
with tabs[2]:
    st.markdown("""
        <div class='section'>
            <h2>Study Notes & Plan Generator</h2>
            <p>Paste a transcript or lecture text to generate concise notes, key points, and a custom study plan.</p>
        </div>
    """, unsafe_allow_html=True)

    user_text = st.text_area("Paste transcript or lecture text here", height=260)
    if not user_text:
        st.info("Paste your lecture text above to unlock notes generation and study planning.")
    else:
        st.markdown("""
            <div class='feature-card'>
                <strong>How to use</strong>
                <p>Enter your transcript, then choose whether to generate notes or create a study plan. Both outputs are downloadable.</p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        # Generate Notes
        with col1:
            with st.form("notes_form"):
                st.markdown("###Generate Study Notes")
                notes_submitted = st.form_submit_button("Generate Notes", use_container_width=True)

                if notes_submitted:
                    with st.spinner("✨ Generating your notes..."):
                        try:
                            prompt = f"Generate structured study notes, key points, and a short summary from this text:\n\n{user_text}"
                            notes_out = call_openrouter(openrouter_key_input, prompt, model=llm_model)

                            if notes_out.startswith("ERROR") or notes_out.startswith("Connection"):
                                st.error(f"{notes_out}")
                            else:
                                st.session_state.generated_notes = notes_out
                                st.success("Notes generated successfully!")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

            if st.session_state.generated_notes:
                st.markdown("###Your Study Notes")
                st.markdown(f"<div class='box'>{st.session_state.generated_notes}</div>", unsafe_allow_html=True)
                st.download_button(
                    "Download Notes",
                    st.session_state.generated_notes,
                    file_name="nexora_notes.txt",
                    use_container_width=True
                )

        # Study Plan 
        with col2:
            with st.form("study_plan_form"):
                st.markdown("###Create Study Plan")
                plan_submitted = st.form_submit_button("Create Study Plan", use_container_width=True)

                if plan_submitted:
                    with st.spinner("Creating your study plan..."):
                        try:
                            prompt = f"Create a study plan with daily goals and 5 practice questions based on this content:\n\n{user_text}"
                            plan = call_openrouter(openrouter_key_input, prompt, model=llm_model)

                            if plan.startswith("ERROR") or plan.startswith("Connection"):
                                st.error(f"{plan}")
                            else:
                                st.session_state.study_plan = plan
                                st.success("Study plan created successfully!")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

            if st.session_state.study_plan:
                st.markdown("###Your Study Plan")
                st.markdown(f"<div class='box'>{st.session_state.study_plan}</div>", unsafe_allow_html=True)
                st.download_button(
                    "Download Plan",
                    st.session_state.study_plan,
                    file_name="study_plan.txt",
                    use_container_width=True
                )

        st.markdown("<div class='section'><h3>Study Tips</h3><p>Need a quick productivity tip? Click below for a focused study suggestion.</p></div>", unsafe_allow_html=True)
        if st.button("Get Study Tip!", key="btn_study_tip", use_container_width=True):
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
            st.info(f"{random.choice(study_tips)}")

# ----------------- AI Assessment Generator -----------------
with tabs[3]:
    st.markdown("""
        <div class='section'>
            <h2>AI Assessment Paper Generator</h2>
            <p>Create quizzes, MCQs, and descriptive practice questions tailored to any topic.</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("assessment_form"):
        col1, col2 = st.columns(2)

        with col1:
            topic = st.text_input("Enter subject or topic:", placeholder="e.g. Functions in Algebra")

        with col2:
            difficulty = st.selectbox("Select difficulty level:", ["Easy", "Medium", "Hard"])

        num_questions = st.slider("Number of questions", 5, 20, 10)

        submitted = st.form_submit_button("Generate Assessment Paper", use_container_width=True)

        if submitted and topic:
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                status_text.text("Preparing your assessment paper...")
                progress_bar.progress(25)

                with st.spinner("Generating questions..."):
                    headers = {
                        "Authorization": f"Bearer {openrouter_key_input}",
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "model": llm_model,
                        "messages": [
                            {"role": "system", "content": "You are an AI that generates structured educational assessment papers."},
                            {"role": "user", "content": f"Generate a {difficulty.lower()} level quiz with {num_questions} questions on {topic}. Half of questions should have 4 options (A, B, C, D) and specify the correct answer at the end. The other half should be descriptive questions with model answers."},
                        ]
                    }

                    progress_bar.progress(50)
                    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=120)
                    progress_bar.progress(75)

                    if response.status_code == 200:
                        result = response.json()
                        ai_output = result["choices"][0]["message"]["content"]
                        st.session_state.assessment_result = ai_output

                        progress_bar.progress(100)
                        status_text.success("Assessment paper generated successfully!")

                        st.markdown("###Generated Assessment Paper")
                        st.markdown(f"""
                            <div class='assessment-box'>
                                <pre>{ai_output}</pre>
                            </div>
                        """, unsafe_allow_html=True)

                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            st.download_button(
                                label="Download Assessment Paper",
                                data=ai_output,
                                file_name=f"{topic.replace(' ', '_')}_assessment.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        with col_d2:
                            if st.button("Regenerate", use_container_width=True):
                                st.rerun()
                    else:
                        st.error(f"API Error: {response.status_code}")
                        st.info(response.text)

            except requests.exceptions.Timeout:
                st.error("Request timed out. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("Connection error. Check your internet and API key.")
            except Exception as e:
                st.error(f"Error generating assessment: {str(e)}")
            finally:
                progress_bar.empty()
                status_text.empty()

        elif submitted and not topic:
            st.warning("Please enter a topic before generating the assessment paper.")

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

    st.markdown("""
        <div class='feature-card'>
            <strong>Resource discovery made easy</strong>
            <p>Enter a topic and choose your level to receive curated learning content.</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("resource_form"):
        col1, col2 = st.columns([2, 1])

        with col1:
            topic = st.text_input("Enter a topic to explore:", key="explore_topic", placeholder="e.g., Machine Learning, Photosynthesis")

        with col2:
            level = st.selectbox("Your level:", ["School", "Senior School", "College", "Researcher"])

        explore_btn = st.form_submit_button("Explore Resources", use_container_width=True)

        if explore_btn and topic:
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                status_text.text("Searching for resources...")
                progress_bar.progress(20)

                with st.spinner("Finding the best resources..."):
                    query = topic + " for " + level + " students"

                    progress_bar.progress(40)
                    resources = get_resources(query, level)
                    videos = resources["videos"]

                    progress_bar.progress(60)
                    docs = resources["docs"]

                    progress_bar.progress(80)
                    papers_list = resources["papers"]

                    progress_bar.progress(100)
                    status_text.success(f"Found {len(videos)} videos, {len(docs)} docs, and {len(papers_list)} papers!")

                    # Videos 
                    st.markdown("<div class='section'><h3>Recommended Videos</h3></div>", unsafe_allow_html=True)
                    if videos:
                        for idx, video in enumerate(videos):
                            with st.container():
                                col_v1, col_v2 = st.columns([3, 1])
                                with col_v1:
                                    st.markdown(
                                        f"<div class='box'><strong><a href='{video['url']}' target='_blank'>▶️ {video['title']}</a></strong><br>"
                                        f"<span style='color:#7B2C6F; font-size: 0.9em;'>Channel: {video.get('channel','Unknown')}</span></div>",
                                        unsafe_allow_html=True
                                    )
                    else:
                        st.info("No videos found for this topic.")

                    # Documentation Section
                    st.markdown("<div class='section'><h3>Documentation</h3></div>", unsafe_allow_html=True)
                    if docs:
                        for doc in docs:
                            st.markdown(f"<div class='box'><a href='{doc['url']}' target='_blank'>{doc['title']}</a></div>", unsafe_allow_html=True)
                    else:
                        st.info("No documentation found for this topic.")

                    # Research Papers Section
                    if level in ["College", "Researcher"]:
                        st.markdown("<div class='section'><h3>Research Papers</h3></div>", unsafe_allow_html=True)
                        if papers_list:
                            for paper in papers_list:
                                st.markdown(f"<div class='box'><a href='{paper['url']}' target='_blank'>{paper['title']}</a></div>", unsafe_allow_html=True)
                        else:
                            st.info("No research papers found for this topic.")

            except Exception as e:
                st.error(f"Error searching resources: {str(e)}")
            finally:
                progress_bar.empty()
                status_text.empty()

        elif explore_btn and not topic:
            st.warning("Please enter a topic to explore resources.")