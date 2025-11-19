"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Event -> "event" collection
- Rsvp -> "rsvp" collection (if used separately)
"""

from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import Optional, List
from datetime import datetime

class Event(BaseModel):
    """
    Events collection schema
    Collection name: "event"
    """
    title: str = Field(..., description="Event title", min_length=3, max_length=120)
    description: Optional[str] = Field(None, description="Event description", max_length=5000)
    location: Optional[str] = Field(None, description="Event location")
    starts_at: datetime = Field(..., description="Start date/time (ISO 8601)")
    ends_at: Optional[datetime] = Field(None, description="End date/time (ISO 8601)")
    image_url: Optional[str] = Field(None, description="Cover image URL")
    capacity: Optional[int] = Field(None, ge=1, description="Max attendees")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    organizer_name: Optional[str] = Field(None, description="Organizer display name")

class Attendee(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr

class RsvpRequest(BaseModel):
    name: str
    email: EmailStr

# Example additional schemas (kept for reference)
class User(BaseModel):
    name: str
    email: EmailStr
    address: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=120)
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
