from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date, time, datetime
from enum import Enum


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


class AgendaItemType(str, Enum):
    CEREMONY = "ceremony"
    RECEPTION = "reception"
    ENTERTAINMENT = "entertainment"
    SPEECH = "speech"
    MEAL = "meal"
    BREAK_TIME = "break"
    PHOTO_SESSION = "photo_session"
    OTHER = "other"


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
    id: str
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
    plan: str = Field(..., pattern="^(freemium|starter|plus|full)$")
    location: str
    restaurant_name: Optional[str] = None
    date: date
    time: time
    event_type: str = Field(..., pattern="^(wedding|birthday|baptism|graduation|anniversary|corporate|other)$")
    expected_guests: Optional[int] = Field(None, ge=1)
    description: Optional[str] = Field(None, max_length=1000)


class EventUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = None
    restaurant_name: Optional[str] = None
    date: Optional[date] = None
    time: Optional[time] = None
    event_type: Optional[str] = Field(None, pattern="^(wedding|birthday|baptism|graduation|anniversary|corporate|other)$")
    expected_guests: Optional[int] = Field(None, ge=1)
    description: Optional[str] = Field(None, max_length=1000)


# Event model moved after Agenda model to avoid forward reference


# Agenda Models
class AgendaCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None


class AgendaUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None


class AgendaItemCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    start_time: time = Field(..., description="Start time in HH:MM format")
    end_time: Optional[time] = Field(None, description="End time in HH:MM format")
    location: Optional[str] = Field(None, max_length=200)
    type: AgendaItemType = Field(..., description="Type of agenda item")
    display_order: Optional[int] = Field(None, ge=0, description="Display order (auto-assigned if not provided)")
    is_important: Optional[bool] = Field(False, description="Mark item as important for highlighting")


class AgendaItemUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    start_time: Optional[time] = Field(None, description="Start time in HH:MM format")
    end_time: Optional[time] = Field(None, description="End time in HH:MM format")
    location: Optional[str] = Field(None, max_length=200)
    type: Optional[AgendaItemType] = Field(None, description="Type of agenda item")
    display_order: Optional[int] = Field(None, ge=0, description="Display order")
    is_important: Optional[bool] = Field(None, description="Mark item as important for highlighting")


class AgendaItem(BaseModel):
    id: str
    agenda_id: str
    title: str
    description: Optional[str] = None
    start_time: time
    end_time: Optional[time] = None
    location: Optional[str] = None
    type: str
    display_order: int
    is_important: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Agenda(BaseModel):
    id: str
    event_id: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[AgendaItem] = []

    class Config:
        from_attributes = True


class AgendaResponse(BaseModel):
    agenda: Agenda


# Event model (placed after Agenda to avoid forward reference issues)
class Event(BaseModel):
    id: str
    name: str
    plan: str
    location: str
    restaurant_name: Optional[str] = None
    date: date
    time: time
    event_type: str
    expected_guests: Optional[int] = None
    description: Optional[str] = None
    qr_code_url: Optional[str] = None
    landing_page_url: Optional[str] = None
    photo_count: int = 0
    guest_count: int = 0
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    owner: User
    agenda: Optional[Agenda] = None

    class Config:
        from_attributes = True


class EventsResponse(BaseModel):
    events: List[Event]
    total: int
    has_more: bool


class EventResponse(BaseModel):
    event: Event


class AgendaItemResponse(BaseModel):
    agenda_item: AgendaItem


class ReorderItem(BaseModel):
    item_id: str = Field(..., description="ID of the agenda item")
    display_order: int = Field(..., ge=0, description="New display order for the item")


class AgendaReorderRequest(BaseModel):
    items: List[ReorderItem] = Field(..., min_items=1, description="List of items with new display orders")
