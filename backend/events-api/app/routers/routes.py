
# Removed inspect import
# Removed UUID import since we're using NanoID strings now
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Generator, Annotated

from fastapi import APIRouter, Depends, Query, HTTPException, Request

from app.api import models
from app.database.db import get_db, create_tables
from app.api.services import EventLogic, UserLogic, DatabaseCleaner, AgendaLogic
from app.api.security import get_user_id, get_user_db, get_current_user
from app.database.db import get_db
from app.utils.logger import logger

api = APIRouter()


# Removed user-specific database session dependency
def get_user_id():
    return "4rOq4dpioFJq"# {"user_id": str(uuid4())}

@api.get("/health-check")
def health_check():
    """Health check endpoint with database iJ,Ónitialization fallback"""
    try:
        # Try to get a database session to ensure everything is working
        
        
        # Ensure tables are created
        create_tables()
        
        # Test database connection
        db = next(get_db())
        
        db.execute(text("SELECT 1"))
        db.close()
        
        return {"HEALTH": "OK", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"HEALTH": "OK", "database": "error", "error": str(e)}


@api.delete("/recreate-tables")
def drop_tables(
    recreate: bool = False,
):
    """Recreate all database tables and enum types"""
    if not recreate:
        raise HTTPException(status_code=400, detail="Set recreate=true to proceed")
    
    try:
        
        create_tables(force_recreate=True)
        return {"detail": "Tables recreated successfully"}
    except Exception as e:
        logger.error(f"Failed to recreate tables: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to recreate tables: {str(e)}")


@api.get("/events", response_model=models.EventsResponse)
def get_events(
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    status, response = EventLogic().create_event(db, event, user_id)
    if status != 201:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.get("/events/{event_id}", response_model=models.EventResponse)
def get_event(
    event_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    status, response = EventLogic().get_event(db=db, event_id=event_id, user_id=user_id)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.put("/events/{event_id}", response_model=models.EventResponse, status_code=200)
def update_event(
    event_id: str,
    event: models.EventUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    status, response = EventLogic().update_event(db=db, event_id=event_id, event=event, user_id=user_id)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.delete("/events/{event_id}", status_code=200)
def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    status, response = EventLogic().delete_event(db=db, event_id=event_id, user_id=user_id)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


# Agenda endpoints
@api.get("/events/{event_id}/agenda", response_model=models.AgendaResponse)
def get_agenda(
    event_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Get agenda for an event with all items ordered by display_order and start_time"""
    status, response = AgendaLogic().get_agenda(db=db, event_id=event_id, user_id=user_id)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.post("/events/{event_id}/agenda", response_model=models.AgendaResponse, status_code=201)
def create_agenda(
    event_id: str,
    agenda: models.AgendaCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Create a new agenda for an event"""
    status, response = AgendaLogic().create_agenda(db=db, event_id=event_id, user_id=user_id, agenda_data=agenda)
    if status != 201:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.put("/events/{event_id}/agenda", response_model=models.AgendaResponse, status_code=200)
def update_agenda(
    event_id: str,
    agenda: models.AgendaUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Update an existing agenda for an event"""
    status, response = AgendaLogic().update_agenda(db=db, event_id=event_id, user_id=user_id, agenda_data=agenda)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.delete("/events/{event_id}/agenda", status_code=204)
def delete_agenda(
    event_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Delete an agenda and all its items (cascade delete)"""
    status, response = AgendaLogic().delete_agenda(db=db, event_id=event_id, user_id=user_id)
    if status != 204:
        raise HTTPException(status_code=status, detail=response)
    return None


# Agenda Item endpoints
@api.post("/events/{event_id}/agenda/items", response_model=models.AgendaItemResponse, status_code=201)
def create_agenda_item(
    event_id: str,
    item: models.AgendaItemCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Create a new agenda item for an event's agenda"""
    status, response = AgendaLogic().create_agenda_item(db=db, event_id=event_id, user_id=user_id, item_data=item)
    if status != 201:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.put("/events/{event_id}/agenda/items/{item_id}", response_model=models.AgendaItemResponse, status_code=200)
def update_agenda_item(
    event_id: str,
    item_id: str,
    item: models.AgendaItemUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Update an existing agenda item"""
    status, response = AgendaLogic().update_agenda_item(db=db, event_id=event_id, item_id=item_id, user_id=user_id, item_data=item)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.delete("/events/{event_id}/agenda/items/{item_id}", status_code=204)
def delete_agenda_item(
    event_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Delete a specific agenda item"""
    status, response = AgendaLogic().delete_agenda_item(db=db, event_id=event_id, item_id=item_id, user_id=user_id)
    if status != 204:
        raise HTTPException(status_code=status, detail=response)
    return None


@api.put("/events/{event_id}/agenda/reorder", status_code=200)
def reorder_agenda_items(
    event_id: str,
    reorder_data: models.AgendaReorderRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Reorder agenda items by updating their display_order values"""
    status, response = AgendaLogic().reorder_agenda_items(db=db, event_id=event_id, user_id=user_id, reorder_data=reorder_data)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


# User endpoints
@api.get("/users/profile", response_model=models.UserResponse)
def get_user_profile(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    status, response = UserLogic().get_user(db=db, user_id=user_id)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.put("/users/profile", response_model=models.UserResponse, status_code=200)
def update_user_profile(
    user: models.UserUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    status, response = UserLogic().update_user(db=db, user_id=user_id, user=user)
    if status != 200:
        raise HTTPException(status_code=status, detail=response)
    return response


@api.post("/users", response_model=models.UserResponse, status_code=201)
def create_user(
    user: models.UserCreate,
    db: Session = Depends(get_db),
):
    status, response = UserLogic().create_user(db=db, user=user)
    if status != 201:
        raise HTTPException(status_code=status, detail=response)
    return response
