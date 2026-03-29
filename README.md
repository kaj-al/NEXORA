# NORA - Study Notes Generator

A Python application for generating structured study notes from audio transcripts using AI.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_AUDIO_URL=https://openrouter.ai/api/v1/audio/transcriptions
```

### 3. Getting Your API Key

- Register at [OpenRouter](https://openrouter.ai)
- Generate your API key
- Add it to your `.env` file

## Features

- **Audio Transcription**: Convert speech to text using Whisper
- **Study Notes Generation**: AI-powered structured study notes from transcripts
- **YouTube Support**: Download and transcribe audio from YouTube videos
- **Recommendation and tracking**: it detect your level according to the format of studying and store history and recommend the next 5 topics and the sources

## File Structure

- `config.py` - OpenRouter API integration
- `tab1.py` - audio extraction , transcription
-  `notes_generation` - Core transcription , notes generation features
- `tab4.py` - recommendation system 
- `nexora3.py` - Main application entry point
- `.env` - Environment variables (local only, not in git)
- `.gitignore` - Git ignore rules
- `requirements.txt` - Python dependencies

## Running the Application

For the Streamlit app:

```bash
streamlit run nexora3.py
```

## Security Notes

- API keys are stored in `.env` and never committed to git
- Never share your `.env` file or API keys
- Use environment variables for all sensitive data
