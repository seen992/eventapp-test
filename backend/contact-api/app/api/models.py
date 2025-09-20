import re
from uuid import UUID
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, field_validator, model_validator, EmailStr


class ContactType(str, Enum):
    private = "private"
    business = "business"

    @classmethod
    def validate(cls, value: str) -> "ContactType":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid contact type: {value}. Must be one of {list(cls)}.")


class Contact(BaseModel):
    first_name: str
    last_name: str
    contact_type: ContactType
    owner: str | None = None
    created_by: str
    attributes: dict[str, str] | None = None

    @field_validator("first_name", "last_name", "created_by")
    def non_empty_and_trimmed(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{info.field_name} must not be empty or whitespace.")
        if len(value) > 100:
            raise ValueError(f"{info.field_name} must not exceed 100 characters.")
        return value


class ContactCreate(Contact):
    email: EmailStr | None = None
    phone: str | None = None

    @model_validator(mode="before")
    def validate_email_and_phone(cls, values):
        if not values.get("email") and not values.get("phone"):
            raise ValueError("At least one of email or phone must be provided.")
        return values

    @field_validator("phone")
    def validate_phone(cls, phone: str) -> str:
        if phone and not re.match(r"^[1-9]\d{7,14}$", phone):
            raise ValueError(
                "Phone number must start with a digit and include 8–15 digits with country code, but no '+'.")
        return phone


class ContactResponse(Contact):
    contact_id: UUID
    full_name: str
    email: str | None = None
    phone: str | None = None
    date_created: datetime
    date_modified: datetime
    list_of_profile_ids: list[UUID] | None = None


class ContactsResponse(BaseModel):
    offset: int
    limit: int
    count: int
    contacts: list[ContactResponse]
