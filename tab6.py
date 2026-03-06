from langchain_community.embeddings import HuggingFaceEmbeddings
import os
from langchain_community.llms import Ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.chains import PebbloRetrievalQA
from langchain.vectors import FAISS # type: ignore

VECTORSTORE_PATH = "vectorstore/nexora_faiss"

def get_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def vectorstore():
    loader = DirectoryLoader("documents/",glob="**/*.txt")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    split = splitter.split_documents(docs)
    
    # create vectorstore
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(split,embeddings)

    # save to disk
    os.makedirs("vectorstore",exist_ok=True)
    vectorstore.save_local(VECTORSTORE_PATH)
    return vectorstore

def llm():
    return Ollama(model="llama3.1")  #llama3.1:8b-q4

# connect llm and vectorstore
def qa_chain():
    llm = llm()
    vectorstore = vectorstore()
    # top 3
    retriever = vectorstore.as_retriever(search_kwargs={"k":3})
    chain = PebbloRetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff" , 
        retriever=retriever,
        return_source_documents=True
    )
    return chain
