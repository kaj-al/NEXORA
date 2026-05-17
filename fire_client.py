import os
import firebase_admin
from firebase_admin import auth, credentials, firestore

FIREBASE_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "firebase.json")


def init_firebase():
    try:
        return firebase_admin.get_app()
    except ValueError:
        if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
            raise FileNotFoundError(
                f"Firebase credentials file not found at {FIREBASE_CREDENTIALS_PATH}"
            )
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        return firebase_admin.initialize_app(cred)


def get_firestore_client():
    init_firebase()
    return firestore.client()


def verify_id_token(id_token: str):
    init_firebase()
    return auth.verify_id_token(id_token)
