from firebase_admin import firestore
from fire_client import get_firestore_client, verify_id_token as firebase_verify_id_token
from functools import lru_cache
from datetime import datetime, timezone
import uuid


@lru_cache(maxsize=1)
def get_firestore_client_cached():
    return get_firestore_client()


def verify_id_token(id_token: str):
    try:
        return firebase_verify_id_token(id_token)
    except Exception as e:
        print(f"Token verification failed: {e}")
        return {"error": str(e)}


def get_user_doc_ref(user_id: str):
    return get_firestore_client_cached().collection("users").document(user_id)


def ensure_user_profile(user_info: dict):
    if not user_info or "localId" not in user_info:
        return None

    user_id = user_info["localId"]
    doc_ref = get_user_doc_ref(user_id)
    profile = {
        "email": user_info.get("email"),
        "display_name": user_info.get("displayName"),
        "last_login": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    existing = doc_ref.get()
    if not existing.exists:
        profile["created_at"] = datetime.now(timezone.utc)
        profile["login_count"] = 1
    else:
        profile["login_count"] = firestore.Increment(1)

    doc_ref.set(profile, merge=True)
    return doc_ref


def start_user_session(user_id: str, started_from: str = "app") -> str:
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    session_doc = {
        "session_id": session_id,
        "user_id": user_id,
        "started_from": started_from,
        "start_time": now,
        "last_seen": now,
        "event_count": 0,
        "active": True,
        "duration_seconds": 0,
    }
    get_user_doc_ref(user_id).collection("sessions").document(session_id).set(session_doc)
    return session_id


def update_user_session(user_id: str, session_id: str, event_type: str, metadata: dict | None = None):
    now = datetime.now(timezone.utc)
    session_ref = get_user_doc_ref(user_id).collection("sessions").document(session_id)
    update_data = {
        "last_seen": now,
        "last_event_type": event_type,
        "event_count": firestore.Increment(1),
        "updated_at": now,
    }
    if metadata:
        update_data["metadata"] = metadata
    session_ref.set(update_data, merge=True)


def end_user_session(user_id: str, session_id: str):
    session_ref = get_user_doc_ref(user_id).collection("sessions").document(session_id)
    session_snapshot = session_ref.get()
    if not session_snapshot.exists:
        return

    session_data = session_snapshot.to_dict() or {}
    start_time = session_data.get("start_time")
    now = datetime.now(timezone.utc)
    duration_seconds = 0
    if start_time:
        duration_seconds = int((now - start_time).total_seconds())

    session_ref.set({
        "end_time": now,
        "duration_seconds": duration_seconds,
        "active": False,
        "last_seen": now,
    }, merge=True)


def log_user_event(user_id: str, event_type: str, metadata: dict | None = None, session_id: str | None = None):
    if not user_id:
        return

    now = datetime.now(timezone.utc)
    event_payload = {
        "event_type": event_type,
        "timestamp": now,
        "metadata": metadata or {},
    }
    if session_id:
        event_payload["session_id"] = session_id
        update_user_session(user_id, session_id, event_type, metadata)

    get_user_doc_ref(user_id).collection("activity").add(event_payload)


def get_recent_activity(user_id: str, limit: int = 20):
    activity_ref = get_user_doc_ref(user_id).collection("activity")
    query = activity_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
    return [doc.to_dict() for doc in query.stream()]


def get_recent_sessions(user_id: str, limit: int = 10):
    sessions_ref = get_user_doc_ref(user_id).collection("sessions")
    query = sessions_ref.order_by("start_time", direction=firestore.Query.DESCENDING).limit(limit)
    return [doc.to_dict() for doc in query.stream()]


def get_user_analytics(user_id: str):
    sessions = get_recent_sessions(user_id, limit=20)
    activities = get_recent_activity(user_id, limit=50)
    return {
        "sessions": sessions,
        "activity": activities,
    }
