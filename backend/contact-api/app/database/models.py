from sqlalchemy import Boolean, Column, String, Text, Integer, ARRAY, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.database.db import Base
from app.utils.config import config_by_name
from datetime import datetime, UTC
from uuid import uuid4
config = config_by_name["BasicConfig"]


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = {"schema": config.db_schema}

    contact_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    contact_type = Column(String, nullable=False)
    owner = Column(String, nullable=True)
    created_by = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    attributes = Column(JSONB, nullable=True)
    list_of_profile_ids = Column(JSONB, nullable=True)
    date_created = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    date_modified = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
