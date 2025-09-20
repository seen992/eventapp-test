from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date, time, datetime
from enum import Enum
from uuid import UUID


class EventPlan(str, Enum):
    FREEMIUM = "freemium"
    STARTER = "starter"
    PLUS = "plus"
    FULL = "full"


class EventType(str, Enum):
    WEDDING = "wedding"
    BIRTHDAY = "birthday"
    BAPTISM = "baptism"
    GRADUATION = "graduation"
    ANNIVERSARY = "anniversary"
    CORPORATE = "corporate"
    OTHER = "other"


class EventStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    DRAFT = "draft"


# User Models
class UserCreate(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class User(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user: User


# Event Models
class EventCreate(BaseModel):
    name: str = Field(..., max_length=200)
    plan: EventPlan
    location: str
    restaurant_name: Optional[str] = None
    date: date
    time: time
    event_type: EventType
    expected_guests: Optional[int] = Field(None, ge=1)
    description: Optional[str] = Field(None, max_length=1000)


class EventUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = None
    restaurant_name: Optional[str] = None
    date: Optional[date] = None
    time: Optional[time] = None
    event_type: Optional[EventType] = None
    expected_guests: Optional[int] = Field(None, ge=1)
    description: Optional[str] = Field(None, max_length=1000)


class Event(BaseModel):
    id: UUID
    name: str
    plan: EventPlan
    location: str
    restaurant_name: Optional[str] = None
    date: date
    time: time
    event_type: EventType
    expected_guests: Optional[int] = None
    description: Optional[str] = None
    qr_code_url: Optional[str] = None
    landing_page_url: Optional[str] = None
    photo_count: int = 0
    guest_count: int = 0
    status: EventStatus
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    owner: User

    class Config:
        from_attributes = True


class EventsResponse(BaseModel):
    events: List[Event]
    total: int
    has_more: bool


class EventResponse(BaseModel):
    event: Event
