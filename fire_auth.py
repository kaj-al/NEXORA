import streamlit as st
import requests
import os
from dotenv import load_dotenv
from activity import ensure_user_profile, verify_id_token

load_dotenv()
API_KEY = os.getenv("FIREBASE_API_KEY")


def signup(email: str, password: str):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True,
    }
    res = requests.post(url, json=payload, timeout=15)
    return res.json()


def login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    payload = {
        "email": email.strip(),
        "password": password,
        "returnSecureToken": True,
    }
    res = requests.post(url, json=payload, timeout=15)
    return res.json()


def logout():
    if "user" in st.session_state:
        st.session_state.pop("user", None)
    if "session_id" in st.session_state:
        st.session_state.pop("session_id", None)
    if "session_start" in st.session_state:
        st.session_state.pop("session_start", None)
    if "activity_history" in st.session_state:
        st.session_state.pop("activity_history", None)
    st.success("You have been logged out.")
    st.experimental_rerun()


def auth_screen():
    st.title("Nexora Login")
    st.markdown("Please sign in or create an account to start tracking your study sessions and activity.")

    mode = st.radio("Authentication mode", ["Login", "Signup"], horizontal=True)

    with st.form("auth_form"):
        email = st.text_input("Email", key="auth_email")
        password = st.text_input("Password", type="password", key="auth_password")
        submitted = st.form_submit_button("Continue")

    if submitted:
        if not email or not password:
            st.warning("Please enter both email and password.")
            return

        if mode == "Signup":
            res = signup(email, password)
            if "idToken" in res:
                ensure_user_profile(res)
                st.success("Account created successfully. You can now log in.")
            else:
                message = res.get("error", {}).get("message", "Signup failed.")
                st.error(message)
        else:
            res = login(email, password)
            if "idToken" in res:
                verified = verify_id_token(res["idToken"])
                if isinstance(verified, dict) and verified.get("error"):
                        st.error(f"Authentication token verification failed: {verified['error']}")
                elif verified:
                        st.session_state.user = {
                            "email": email,
                            "uid": verified["uid"],
                            "localId": verified["uid"],
                            "token": res["idToken"]
                        }
                        st.success("Login successfully")
                        st.rerun()
            else:
                message = res.get("error", {}).get("message", "Login failed.")
                st.error(message)
    
