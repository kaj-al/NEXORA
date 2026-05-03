import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

# for signup
def signup(email,password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
    payload ={
        "email":email,
        "password":password,
        "returnSecureToken":True
    }
    res = requests.post(url,json=payload)
    return res.json()

# for login
def login(email,password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signIn?key={API_KEY}"
    payload ={
        "email":email,
        "password":password,
        "returnSecureToken":True
    }
    res = requests.post(url,json=payload)
    return res.json()
    
