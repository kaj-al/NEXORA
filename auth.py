import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FIREBASE_API_KEY")
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

# ui
def auth_screen():
    st.subheader("Login/Signup")
    email = st.text_input('Email')
    password = st.text_input("Password")
    col1,col2 = st.columns(2)
    with col1:
        if st.button("Signup"):
            res = signup(email,password)
            if "idToken" in res:
                st.success("Account created")
            else:
                st.error(res.get("error",()).get("message"))
    with col2:
        if st.button("Login"):
            res = login(email,password)
            if "idToken" in res:
                st.session_state.user = res
                st.success("Logged in")
                st.rerun()
            else:
                st.error(res.get("error",()).get("message"))
    
