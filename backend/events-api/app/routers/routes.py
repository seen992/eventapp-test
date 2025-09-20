from uuid import UUID
from sqlalchemy.orm import Session
from typing import Generator, Annotated

from fastapi import APIRouter, Depends, Query, HTTPException

from app.api import models
from app.api.services import EventLogic, UserLogic, DatabaseCleaner
from app.api.security import get_user_id, get_user_db, get_current_user
from app.database.db import get_db

api = APIRouter()


def get_user_db_session(
    user_id: str = Depends(get_user_db),
) -> Generator[Session, None, None]:
    """
    Get database session for the authenticated user.
    """
    yield from get_db(user_id=user_id)


@api.get("/health-check")
def health_check():
    return {"HEALTH": "OK"}


@api.delete("/recreate-tables")
def drop_tables(
    user_id: str = Depends(get_user_id),
    recreate: bool = False,
):
    status, response = DatabaseCleaner().recreate_all_tables(user_id=user_id, recreate=recreate)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)

    return response


@api.get("/events", response_model=models.EventsResponse)
def get_events(
    db: Session = Depends(get_user_db_session),
    user_id: str = Depends(get_user_id),
    status: str = Query(None, description="Filter by status: active, expired, draft"),
    limit: int = Query(20, ge=1, le=1000, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
):
    status, response = EventLogic().get_events(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
        status=status
    )
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.post("/events", response_model=models.EventResponse, status_code=201)
def create_event(
    event: models.EventCreate,
    db: Session = Depends(get_user_db_session),
    user_id: str = Depends(get_user_id),
):
    status, response = EventLogic().create_event(db=db, event=event, user_id=user_id)
    if status != 201:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.get("/events/{event_id}", response_model=models.EventResponse)
def get_event(
    event_id: UUID,
    db: Session = Depends(get_user_db_session),
    user_id: str = Depends(get_user_id),
):
    status, response = EventLogic().get_event(db=db, event_id=event_id, user_id=user_id)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.put("/events/{event_id}", response_model=models.EventResponse, status_code=200)
def update_event(
    event_id: UUID,
    event: models.EventUpdate,
    db: Session = Depends(get_user_db_session),
    user_id: str = Depends(get_user_id),
):
    status, response = EventLogic().update_event(db=db, event_id=event_id, event=event, user_id=user_id)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.delete("/events/{event_id}", status_code=200)
def delete_event(
    event_id: UUID,
    db: Session = Depends(get_user_db_session),
    user_id: str = Depends(get_user_id),
):
    status, response = EventLogic().delete_event(db=db, event_id=event_id, user_id=user_id)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


# User endpoints
@api.get("/users/profile", response_model=models.UserResponse)
def get_user_profile(
    db: Session = Depends(get_user_db_session),
    user_id: str = Depends(get_current_user),
):
    status, response = UserLogic().get_user(db=db, user_id=user_id)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.put("/users/profile", response_model=models.UserResponse, status_code=200)
def update_user_profile(
    user: models.UserUpdate,
    db: Session = Depends(get_user_db_session),
    user_id: str = Depends(get_current_user),
):
    status, response = UserLogic().update_user(db=db, user_id=user_id, user=user)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.post("/users", response_model=models.UserResponse, status_code=201)
def create_user(
    user: models.UserCreate,
    db: Session = Depends(get_user_db_session),
):
    status, response = UserLogic().create_user(db=db, user=user)
    if status != 201:
        raise HTTPException(status_code=status, detail=response)
    return response
