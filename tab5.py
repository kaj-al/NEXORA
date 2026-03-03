import requests
from config import llm_model, openrouter_key_input
import json
import os
import pandas as pd
from datetime import datetime   

DATA_FILE = "user.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return []
    
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)    

# Add learning record
def add(query, format):
    if not query or not query.strip():
        raise ValueError("Topic cannot be empty")
    if not format:
        raise ValueError("Format must be selected")
    
    data = load_data()
    data.append({
        "query": query.strip(),
        "format": format,
        "time": datetime.now().isoformat(),
    })
    save_data(data)
       
def detect_level(data):
        if not data:
            return "Beginner", 0
        df = pd.DataFrame(data)
        total_entries = len(df)
        active_days = 0
        if "time" in df.columns:
            df["date"] = pd.to_datetime(df["time"]).dt.date
            active_days = df["date"].nunique()
        
        if total_entries < 10:
            level = "Beginner"
        elif total_entries < 30:
            level = "Intermediate"
        else:
            level = "Advanced"
        return level, active_days

def get_learning_stats(data):
    if not data:
        return {
            "total_entries": 0,
            "active_days": 0,
            "formats": {},
            "recent_topics": []
        }
    
    df = pd.DataFrame(data)
    total_entries = len(df)
    
    # Count formats
    formats = df["format"].value_counts().to_dict() if "format" in df.columns else {}
    
    # Get recent topics
    recent_topics = df["query"].tail(5).tolist() if "query" in df.columns else []
    
    # Count active days
    active_days = 0
    if "time" in df.columns:
        df["date"] = pd.to_datetime(df["time"]).dt.date
        active_days = df["date"].nunique()
    
    return {
        "total_entries": total_entries,
        "active_days": active_days,
        "formats": formats,
        "recent_topics": recent_topics
    }

def recommendation(topic, level):
    if not topic or not topic.strip():
        return "Please provide a topic to get recommendations!"
    
    topic = topic.strip()
    prompt = f"""You are an AI learning recommender and advisor.
Student level: {level}
Current topic of interest: {topic}

Based on this topic:
1. Identify 5 related topics to strengthen understanding
2. Explain how each topic connects to '{topic}'
3. Recommend specific resources (articles, videos, courses) for each
4. Provide a learning roadmap starting from this topic
5. Suggest practice exercises or projects"""
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openrouter_key_input}",
                "Content-Type": "application/json",
            },
            json={
                "model": llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1000
            },
            timeout=30
        )
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "Could not generate recommendations at this time."
    except Exception as e:
        return f"Error generating recommendations: {str(e)}"


 
    