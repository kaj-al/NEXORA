import whisper
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter

model = whisper.load_model("base")

def transcription(audio):
    result = model.transcribe(audio)
    return result["text"]

def get_llm():
    llm = ChatGroq(api_key="",model="llama3-70b-8192")
    return llm

def gen_notes(transcript):
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000,chunk_overlap=200)
    chunks = splitter.split_text(transcript)
    llm = get_llm()
    notes = ""
    for chunk in chunks:
        prompt = f"""Convert following transcript into structured study notes clarify the wordings and avoid the noise and irregular words:{chunk}"""
        response = llm.invoke(prompt)
        notes += response.content + "\n"
    return notes