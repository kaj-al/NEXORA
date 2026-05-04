import firebase_admin
from firebase_admin import credentials,firestore
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

# firebase
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# session add
@app.post("/add-sessions")
def add_session(id:str,topic:str,format:str,time:int):
    db.collections("users").document("id").collection("sessions").add({
        "topic":topic,
        "format":format,
        "time":time,
        "date":str(datetime.now().date())
    })
    return{"status":"success"}

# session get
@app.get("/get-sessions")
def get_session(id:str):
    docs = db.collections("users").document("id").collection("sessions").stram()
    data = []
    for doc in docs:
        data.append(doc.to_dict())
    return data

