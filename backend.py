from firebase_admin import firestore
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from typing import Optional

from firebase_client import get_firestore_client

app = FastAPI(title="Nexora Backend API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase initialization
db = get_firestore_client()


def verify_user_id(authorization: Optional[str] = Header(None)) -> str:
    """Extract and verify user ID from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # Authorization header format: "Bearer <user_id>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    return parts[1]


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "nexora-backend"}


@app.post("/add-session")
def add_session(
    session_id: str,
    topic: str,
    format_type: str,
    time_spent: int,
    user_id: str = Depends(verify_user_id)
):
    """Add a study session for a user"""
    try:
        doc_ref = db.collection("users").document(user_id).collection("sessions").document(session_id)
        session_data = {
            "session_id": session_id,
            "topic": topic,
            "format": format_type,
            "time_spent": time_spent,
            "date": str(datetime.now(timezone.utc).date()),
            "created_at": datetime.now(timezone.utc),
        }
        doc_ref.set(session_data)
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-sessions")
def get_sessions(user_id: str = Depends(verify_user_id)):
    """Retrieve all sessions for a user"""
    try:
        sessions_ref = db.collection("users").document(user_id).collection("sessions")
        docs = sessions_ref.order_by("created_at", direction=firestore.Query.DESCENDING).limit(50).stream()
        data = [doc.to_dict() for doc in docs]
        return {"status": "success", "sessions": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-user-profile")
def get_user_profile(user_id: str = Depends(verify_user_id)):
    """Get user profile information"""
    try:
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()
        if user_doc.exists:
            return {"status": "success", "profile": user_doc.to_dict()}
        else:
            return {"status": "success", "profile": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/log-event")
def log_event(
    event_type: str,
    metadata: Optional[dict] = None,
    user_id: str = Depends(verify_user_id)
):
    """Log a user activity event"""
    try:
        event_ref = db.collection("users").document(user_id).collection("activity").document()
        event_data = {
            "event_type": event_type,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc),
        }
        event_ref.set(event_data)
        return {"status": "success", "event_type": event_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-analytics")
def get_analytics(user_id: str = Depends(verify_user_id)):
    """Get comprehensive analytics for a user"""
    try:
        # Get recent sessions
        sessions_ref = db.collection("users").document(user_id).collection("sessions")
        sessions = [doc.to_dict() for doc in sessions_ref.limit(20).stream()]
        
        # Get recent activities
        activity_ref = db.collection("users").document(user_id).collection("activity")
        activities = [doc.to_dict() for doc in activity_ref.limit(50).stream()]
        
        # Get user profile
        user_ref = db.collection("users").document(user_id)
        user_profile = user_ref.get().to_dict() if user_ref.get().exists else {}
        
        return {
            "status": "success",
            "profile": user_profile,
            "sessions": sessions,
            "activities": activities,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete-session/{session_id}")
def delete_session(session_id: str, user_id: str = Depends(verify_user_id)):
    """Delete a specific session"""
    try:
        db.collection("users").document(user_id).collection("sessions").document(session_id).delete()
        return {"status": "success", "message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear-activity")
def clear_activity(user_id: str = Depends(verify_user_id)):
    """Clear all activity logs for a user"""
    try:
        activity_ref = db.collection("users").document(user_id).collection("activity")
        docs = activity_ref.limit(100).stream()
        for doc in docs:
            doc.reference.delete()
        return {"status": "success", "message": "Activity cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

