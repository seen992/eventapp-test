import re
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Generator, Annotated

from fastapi import APIRouter, Depends, Query, Header, HTTPException

from app.api import models
from app.api.services import ContactLogic, DatabaseCleaner
from app.database.db import get_db

api = APIRouter()


def sanitize_tenant_id(tenant_id: str) -> str:
    if not re.match(r"^\w+$", tenant_id):
        raise HTTPException(
            status_code=422,
            detail="Invalid tenant ID. Only alphanumeric characters and underscores are allowed."
        )
    return tenant_id


def get_tenant_id(
        tenant_id: Annotated[str, Header(..., alias="Ts-Tenant-Id")],
) -> str:
    tenant_id = sanitize_tenant_id(tenant_id)
    return tenant_id


def get_tenant_db(
        tenant_id: Annotated[str, Header(..., alias="Ts-Tenant-Id")],
) -> Generator[Session, None, None]:
    tenant_id = get_tenant_id(tenant_id)

    # If validation passes, provide a database session for the specific tenant
    yield from get_db(tenant_id=tenant_id)


@api.get("/health-check")
def health_check():
    return {"HEALTH": "OK"}


@api.delete("/recreate-tables")
def drop_tables(
        tenant_id: str = Depends(get_tenant_id),
        recreate: bool = False,
):
    status, response = DatabaseCleaner().recreate_all_tables(tenant_id=tenant_id, recreate=recreate)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)

    return response


@api.get("/search", response_model=models.ContactsResponse)
def search_contacts(
        query: str = Query(..., min_length=1),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        db: Session = Depends(get_tenant_db)
):
    status, response = ContactLogic().search_contacts(
        db=db,
        query=query,
        offset=offset,
        limit=limit
    )
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.get("", response_model=models.ContactsResponse)
def get_contacts(
        db: Session = Depends(get_tenant_db),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
):
    status, response = ContactLogic().get_contacts(db=db, limit=limit, offset=offset)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.post("", response_model=models.ContactResponse, status_code=201)
def create_contact(
        contact: models.ContactCreate,
        db: Session = Depends(get_tenant_db),
):
    status, response = ContactLogic().create_contact(db=db, contact=contact)
    if status != 201:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.get("/{contact_id}", response_model=models.ContactResponse)
def get_contact(
        contact_id: UUID,
        db: Session = Depends(get_tenant_db),
):
    status, response = ContactLogic().get_contact(db=db, contact_id=contact_id)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.put("/{contact_id}", response_model=models.ContactResponse, status_code=200)
def update_contact(
        contact_id: UUID,
        contact: models.ContactCreate,
        db: Session = Depends(get_tenant_db),
):
    status, response = ContactLogic().update_contact(db=db, contact_id=contact_id, contact=contact)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.delete("/{contact_id}", status_code=200)
def delete_contact(
        contact_id: UUID,
        db: Session = Depends(get_tenant_db),
):
    status, response = ContactLogic().delete_contact(db=db, contact_id=contact_id)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response
