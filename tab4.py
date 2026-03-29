
import requests 
import os
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

# def papers(query):
#     search = arxiv.Search(query=query,max_results=5)

#     papers = []

#     for result in search.results():
#         papers.append({
#             "title":result.title,
#             "url":result.entry_id
#         })

#     return papers

def documentation(query):
    url = "https://google.serper.dev/search"
    payload = {"q": query + "tutorial documentation"}
    headers = {
        "X-API-KEY" : os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json"
    }
    response = requests.post(url,json=payload,headers=headers)
    data = response.json()
    results = data.get("organic",[])
    docs = []
    for r in results[:5]:
        docs.append({
            "title":r.get("title","No Title"),
            "url":r.get("link","#")
        })
    return docs  

def youtube(query):
    ydl_opts = {
        "quiet":False,
        "extract_flat":True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(
            f"ytsearch10:{query}",
            download=False
        )
    videos = []
    for entry in results["entries"]:
        id = entry.get("id")
        videos.append({
            "title":entry.get("title"),
            "url":f"https://www.youtube.com/watch?v={id}",
            "duration":entry.get("duration"), #convert in minutes and seconds
            "channel":entry.get("uploader"),
            "thumbnail":entry.get("thumbnail"),
        })
    return videos




 
    