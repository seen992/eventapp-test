from sqlalchemy import Boolean, Column, String, Text, Integer, ARRAY, ForeignKey, DateTime, Date, Time, Enum, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database.db import Base
from app.utils.config import config_by_name
from app.utils.nanoid import generate_user_id, generate_event_id, generate_agenda_id, generate_agenda_item_id
from datetime import datetime, UTC
import enum

config = config_by_name["BasicConfig"]


class User(Base):
    __tablename__ = "users"

    id = Column(String(12), primary_key=True, default=generate_user_id)
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

    id = Column(String(12), primary_key=True, default=generate_event_id)
    name = Column(String(200), nullable=False)
    plan = Column(Enum('freemium', 'starter', 'plus', 'full', name='event_plan'), nullable=False)
    location = Column(String, nullable=False)
    restaurant_name = Column(String, nullable=True)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    event_type = Column(Enum('wedding', 'birthday', 'baptism', 'graduation', 'anniversary', 'corporate', 'other', name='eventtype'), nullable=False)
    expected_guests = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    qr_code_url = Column(String, nullable=True)
    landing_page_url = Column(String, nullable=True)
    photo_count = Column(Integer, default=0)
    guest_count = Column(Integer, default=0)
    status = Column(Enum('active', 'expired', 'draft', name='eventstatus'), default='draft')
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # Foreign key to User (schema is set globally on Base.metadata)
    owner_id = Column(String(12), ForeignKey('users.id'), nullable=False)
    
    # Relationship to user
    owner = relationship("User", back_populates="events")
    
    # Relationship to agenda
    agenda = relationship("Agenda", back_populates="event", uselist=False, cascade="all, delete-orphan")


class AgendaItemType(enum.Enum):
    """Enum for agenda item types"""
    ceremony = "ceremony"
    reception = "reception"
    entertainment = "entertainment"
    speech = "speech"
    meal = "meal"
    break_time = "break"
    photo_session = "photo_session"
    other = "other"


class Agenda(Base):
    __tablename__ = "agendas"

    id = Column(String(12), primary_key=True, default=generate_agenda_id)
    event_id = Column(String(12), ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(200), nullable=False, default='Program događaja')
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # Relationships
    event = relationship("Event", back_populates="agenda")
    items = relationship("AgendaItem", back_populates="agenda", cascade="all, delete-orphan", 
                        order_by="AgendaItem.display_order, AgendaItem.start_time")


class AgendaItem(Base):
    __tablename__ = "agenda_items"

    id = Column(String(12), primary_key=True, default=generate_agenda_item_id)
    agenda_id = Column(String(12), ForeignKey('agendas.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=True)
    location = Column(String(200), nullable=True)
    type = Column(Enum(AgendaItemType), nullable=False)
    display_order = Column(Integer, default=0)
    is_important = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # Relationships
    agenda = relationship("Agenda", back_populates="items")