from sqlalchemy import Boolean, Column, String, Text, Integer, ARRAY, ForeignKey, DateTime, Date, Time, Enum, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from app.database.db import Base
from app.utils.config import config_by_name
from datetime import datetime, UTC
from uuid import uuid4
import enum

config = config_by_name["BasicConfig"]


class EventPlan(enum.Enum):
    FREEMIUM = "freemium"
    STARTER = "starter"
    PLUS = "plus"
    FULL = "full"


class EventType(enum.Enum):
    WEDDING = "wedding"
    BIRTHDAY = "birthday"
    BAPTISM = "baptism"
    GRADUATION = "graduation"
    ANNIVERSARY = "anniversary"
    CORPORATE = "corporate"
    OTHER = "other"


class EventStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    DRAFT = "draft"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": config.db_schema}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String, nullable=False, unique=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # Relationship to events
    events = relationship("Event", back_populates="owner")


class Event(Base):
    __tablename__ = "events"
    __table_args__ = {"schema": config.db_schema}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    plan = Column(Enum(EventPlan), nullable=False)
    location = Column(String, nullable=False)
    restaurant_name = Column(String, nullable=True)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    expected_guests = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    qr_code_url = Column(String, nullable=True)
    landing_page_url = Column(String, nullable=True)
    photo_count = Column(Integer, default=0)
    guest_count = Column(Integer, default=0)
    status = Column(Enum(EventStatus), default=EventStatus.DRAFT)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # Foreign key to User
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Relationship to user
    owner = relationship("User", back_populates="events")
