import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId
from typing import List, Optional
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Event, RsvpRequest

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# --------- Event Endpoints ---------

@app.post("/api/events", response_model=dict)
def create_event(event: Event):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    inserted_id = create_document("event", event)
    return {"id": inserted_id}

@app.get("/api/events", response_model=List[dict])
def list_events(tag: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filter_query = {}
    if tag:
        filter_query["tags"] = {"$in": [tag]}
    if q:
        filter_query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"location": {"$regex": q, "$options": "i"}},
        ]

    docs = get_documents("event", filter_query, limit)
    # Convert ObjectId to string
    for d in docs:
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
    return docs

@app.get("/api/events/{event_id}", response_model=dict)
def get_event(event_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        doc = db["event"].find_one({"_id": ObjectId(event_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Event not found")
        doc["id"] = str(doc.pop("_id"))
        return doc
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event id")

@app.post("/api/events/{event_id}/rsvp", response_model=dict)
def rsvp_event(event_id: str, payload: RsvpRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        # ensure event exists
        existing = db["event"].find_one({"_id": ObjectId(event_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Event not found")
        rsvp = {
            "event_id": ObjectId(event_id),
            "name": payload.name,
            "email": payload.email,
            "created_at": datetime.utcnow(),
        }
        res = db["rsvp"].insert_one(rsvp)
        return {"id": str(res.inserted_id)}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event id")

@app.get("/api/events/{event_id}/rsvps", response_model=List[dict])
def list_rsvps(event_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        cursor = db["rsvp"].find({"event_id": ObjectId(event_id)}).limit(200)
        docs = list(cursor)
        for d in docs:
            d["id"] = str(d.pop("_id"))
            d["event_id"] = str(d["event_id"])  # stringify
        return docs
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event id")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
