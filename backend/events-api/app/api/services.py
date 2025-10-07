from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api import models as api_model
from app.database.daos import EventQuery, UserQuery, DatabaseCleanerQuery, AgendaQuery, AgendaItemQuery
from app.utils.logger import logger
from app.utils.config import config_by_name, settings
from sqlalchemy import text

config = config_by_name["BasicConfig"]


class UserLogic:
    def __init__(self):
        self.user = UserQuery()

    def get_user(self, db: Session, user_id: str):
        """ Retrieve a user by its ID.

        Parameters:
            - db (Session): The database session.
            - user_id (str): The ID of the user to retrieve.
        Returns:
            tuple: A tuple containing the status code and the user response model.
        Raises:
            HTTPException: If the user is not found, raises a 404 error.
        """
        result = self.user.get_one(db=db, user_id=user_id)
        if result is None:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found.")
        return 200, api_model.UserResponse(user=api_model.User.model_validate(result, from_attributes=True))

    def create_user(self, db: Session, user: api_model.UserCreate):
        """ Create a new user.

        Parameters:
            - db (Session): The database session.
            - user (UserCreate): The user data to create.
        Returns:
            tuple: A tuple containing the status code and the created user response model.
        Raises:
            HTTPException: If a user with the same email already exists, raises a 409 error.
        """
        existing = self.user.get_by_email(db=db, email=user.email)
        if existing:
            raise HTTPException(status_code=409, detail="User already exists with the same email.")

        created = self.user.create(db=db, user_data=user)
        return 201, api_model.UserResponse(user=api_model.User.model_validate(created, from_attributes=True))

    def update_user(self, db: Session, user_id: str, user: api_model.UserUpdate):
        """ Update an existing user.

        Parameters:
            - db (Session): The database session.
            - user_id (str): The ID of the user to update.
            - user (UserUpdate): The updated user data.
        Returns:
            tuple: A tuple containing the status code and the updated user response model.
        Raises:
            HTTPException: If the user is not found, raises a 404 error.
        """
        existing = self.user.get_one(db=db, user_id=user_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"User ID '{user_id}' not found for update.")

        updated = self.user.update(db=db, user_id=user_id, user_data=user)
        return 200, api_model.UserResponse(user=api_model.User.model_validate(updated, from_attributes=True))


class EventLogic:
    def __init__(self):
        self.event = EventQuery()

    def get_event(self, db: Session, event_id: str, user_id: str):
        """ Retrieve an event by its ID.

        Parameters:
            - db (Session): The database session.
            - event_id (str): The ID of the event to retrieve.
            - user_id (str): The ID of the user who owns the event.
        Returns:
            tuple: A tuple containing the status code and the event response model.
        Raises:
            HTTPException: If the event is not found, raises a 404 error.
        """
        result = self.event.get_one(db=db, event_id=event_id, user_id=user_id)
        if result is None:
            logger.warning(f"Event not found: {event_id} for user: {user_id}")
            raise HTTPException(status_code=404, detail=f"Event with ID '{event_id}' not found.")
        return 200, api_model.EventResponse(event=api_model.Event.model_validate(result, from_attributes=True))

    def get_events(self, db: Session, user_id: str, limit: int = 20, offset: int = 0, status: str = None):
        """ Retrieve all events for a user with pagination.

        Parameters:
            - db (Session): The database session.
            - user_id (str): The ID of the user.
            - limit (int): The maximum number of events to return (default is 20).
            - offset (int): The offset for pagination (default is 0).
            - status (str): Optional status filter.
        Returns:
            tuple: A tuple containing the status code and the events response model.
        """
        data = self.event.get_all(db=db, user_id=user_id, limit=limit, offset=offset, status=status)

        if not data or not data.get("events"):
            logger.info(f"No events found for user: {user_id}")
            events = []
        else:
            logger.info(f"Found {len(data['events'])} events for user: {user_id}")
            events = [api_model.Event.model_validate(e, from_attributes=True) for e in data["events"]]
        
        return 200, api_model.EventsResponse(
            events=events,
            total=data.get("total", 0),
            has_more=data.get("has_more", False)
        )

    def create_event(self, db: Session, event: api_model.EventCreate, user_id: str):
        """ Create a new event.

        Parameters:
            - db (Session): The database session.
            - event (EventCreate): The event data to create.
            - user_id (str): The ID of the user creating the event.
        Returns:
            tuple: A tuple containing the status code and the created event response model.
        """
        # Check if user exists first
        user_query = UserQuery()
        existing_user = user_query.get_one(db=db, user_id=user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found. Please create user first.")
        
        created = self.event.create(db, event, user_id)
        return 201, api_model.EventResponse(event=api_model.Event.model_validate(created, from_attributes=True))

    def update_event(self, db: Session, event_id: str, event: api_model.EventUpdate, user_id: str):
        """ Update an existing event.

        Parameters:
            - db (Session): The database session.
            - event_id (str): The ID of the event to update.
            - event (EventUpdate): The updated event data.
            - user_id (str): The ID of the user who owns the event.
        Returns:
            tuple: A tuple containing the status code and the updated event response model.
        Raises:
            HTTPException: If the event is not found, raises a 404 error.
        """
        existing = self.event.get_one(db=db, event_id=event_id, user_id=user_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Event ID '{event_id}' not found for update.")

        updated = self.event.update(db=db, event_id=event_id, event_data=event, user_id=user_id)
        return 200, api_model.EventResponse(event=api_model.Event.model_validate(updated, from_attributes=True))

    def delete_event(self, db: Session, event_id: str, user_id: str):
        """ Delete an event by its ID.

        Parameters:
            - db (Session): The database session.
            - event_id (str): The ID of the event to delete.
            - user_id (str): The ID of the user who owns the event.
        Returns:
            tuple: A tuple containing the status code and a success message.
        Raises:
            HTTPException: If the event is not found, raises a 404 error.
        """
        existing = self.event.get_one(db=db, event_id=event_id, user_id=user_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Event ID '{event_id}' not found for deletion.")

        self.event.delete(db=db, event_id=event_id, user_id=user_id)
        return 200, {"detail": f"Event ID '{event_id}' successfully deleted."}


class AgendaLogic:
    def __init__(self):
        self.agenda = AgendaQuery()
        self.agenda_item = AgendaItemQuery()

    def get_agenda(self, db: Session, event_id: str, user_id: str):
        """
        Retrieve an agenda with all items for an event.

        Parameters:
            - db (Session): The database session.
            - event_id (str): The ID of the event.
            - user_id (str): The ID of the user who owns the event.
        Returns:
            tuple: A tuple containing the status code and the agenda response model.
        Raises:
            HTTPException: If the agenda is not found, raises a 404 error.
            HTTPException: If the user doesn't own the event, raises a 403 error.
        """
        # Validate event ownership first
        if not self.agenda.validate_ownership(db=db, event_id=event_id, user_id=user_id):
            logger.warning(f"User {user_id} doesn't own event {event_id}")
            raise HTTPException(status_code=403, detail="You don't have permission to access this event.")

        result = self.agenda.get_agenda_with_items(db=db, event_id=event_id, user_id=user_id)
        if result is None:
            logger.warning(f"Agenda not found for event: {event_id}")
            raise HTTPException(status_code=404, detail=f"Agenda not found for event '{event_id}'.")
        
        return 200, api_model.AgendaResponse(agenda=api_model.Agenda.model_validate(result, from_attributes=True))

    def create_agenda(self, db: Session, event_id: str, user_id: str, agenda_data: api_model.AgendaCreate):
        """
        Create a new agenda for an event.

        Parameters:
            - db (Session): The database session.
            - event_id (str): The ID of the event.
            - user_id (str): The ID of the user who owns the event.
            - agenda_data (AgendaCreate): The agenda data to create.
        Returns:
            tuple: A tuple containing the status code and the created agenda response model.
        Raises:
            HTTPException: If the event is not found or user doesn't own it, raises a 404 error.
            HTTPException: If an agenda already exists for the event, raises a 409 error.
        """
        # Validate event ownership
        if not self.agenda.validate_ownership(db=db, event_id=event_id, user_id=user_id):
            logger.warning(f"Event not found or user {user_id} doesn't own event {event_id}")
            raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found or you don't have permission to access it.")

        # Check if agenda already exists
        existing = self.agenda.get_one(db=db, event_id=event_id, user_id=user_id)
        if existing:
            raise HTTPException(status_code=409, detail="Agenda already exists for this event.")

        # Set default title if not provided
        title = agenda_data.title if agenda_data.title else "Program događaja"
        
        created = self.agenda.create(
            db=db, 
            event_id=event_id, 
            user_id=user_id, 
            title=title, 
            description=agenda_data.description
        )
        
        if created is None:
            raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
        
        return 201, api_model.AgendaResponse(agenda=api_model.Agenda.model_validate(created, from_attributes=True))

    def update_agenda(self, db: Session, event_id: str, user_id: str, agenda_data: api_model.AgendaUpdate):
        """
        Update an existing agenda.

        Parameters:
            - db (Session): The database session.
            - event_id (str): The ID of the event.
            - user_id (str): The ID of the user who owns the event.
            - agenda_data (AgendaUpdate): The updated agenda data.
        Returns:
            tuple: A tuple containing the status code and the updated agenda response model.
        Raises:
            HTTPException: If the agenda is not found, raises a 404 error.
            HTTPException: If the user doesn't own the event, raises a 403 error.
        """
        # Validate event ownership
        if not self.agenda.validate_ownership(db=db, event_id=event_id, user_id=user_id):
            logger.warning(f"User {user_id} doesn't own event {event_id}")
            raise HTTPException(status_code=403, detail="You don't have permission to access this event.")

        updated = self.agenda.update(
            db=db, 
            event_id=event_id, 
            user_id=user_id, 
            title=agenda_data.title, 
            description=agenda_data.description
        )
        
        if updated is None:
            raise HTTPException(status_code=404, detail=f"Agenda not found for event '{event_id}'.")
        
        return 200, api_model.AgendaResponse(agenda=api_model.Agenda.model_validate(updated, from_attributes=True))

    def delete_agenda(self, db: Session, event_id: str, user_id: str):
        """
        Delete an agenda and all its items.

        Parameters:
            - db (Session): The database session.
            - event_id (str): The ID of the event.
            - user_id (str): The ID of the user who owns the event.
        Returns:
            tuple: A tuple containing the status code and a success message.
        Raises:
            HTTPException: If the agenda is not found, raises a 404 error.
            HTTPException: If the user doesn't own the event, raises a 403 error.
        """
        # Validate event ownership
        if not self.agenda.validate_ownership(db=db, event_id=event_id, user_id=user_id):
            logger.warning(f"User {user_id} doesn't own event {event_id}")
            raise HTTPException(status_code=403, detail="You don't have permission to access this event.")

        result = self.agenda.delete(db=db, event_id=event_id, user_id=user_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"Agenda not found for event '{event_id}'.")
        
        return 204, {"detail": f"Agenda for event '{event_id}' successfully deleted."}

    def create_agenda_item(self, db: Session, event_id: str, user_id: str, item_data: api_model.AgendaItemCreate):
        """
        Create a new agenda item.

        Parameters:
            - db (Session): The database session.
            - event_id (str): The ID of the event.
            - user_id (str): The ID of the user who owns the event.
            - item_data (AgendaItemCreate): The agenda item data to create.
        Returns:
            tuple: A tuple containing the status code and the created agenda item response model.
        Raises:
            HTTPException: If the agenda is not found, raises a 404 error.
            HTTPException: If the user doesn't own the event, raises a 403 error.
            HTTPException: If end_time is before start_time, raises a 422 error.
        """
        # Validate event ownership
        if not self.agenda.validate_ownership(db=db, event_id=event_id, user_id=user_id):
            logger.warning(f"User {user_id} doesn't own event {event_id}")
            raise HTTPException(status_code=403, detail="You don't have permission to access this event.")

        # Validate time range if end_time is provided
        if item_data.end_time and item_data.end_time <= item_data.start_time:
            raise HTTPException(status_code=422, detail="End time must be after start time.")

        # Convert Pydantic model to dict for DAO
        item_dict = {
            "title": item_data.title,
            "description": item_data.description,
            "start_time": item_data.start_time,
            "end_time": item_data.end_time,
            "location": item_data.location,
            "type": item_data.type.value,  # Convert enum to string
            "display_order": item_data.display_order,
            "is_important": item_data.is_important
        }

        created = self.agenda_item.create(db=db, event_id=event_id, user_id=user_id, item_data=item_dict)
        
        if created is None:
            raise HTTPException(status_code=404, detail=f"Agenda not found for event '{event_id}'.")
        
        return 201, api_model.AgendaItemResponse(agenda_item=api_model.AgendaItem.model_validate(created, from_attributes=True))

    def update_agenda_item(self, db: Session, event_id: str, item_id: str, user_id: str, item_data: api_model.AgendaItemUpdate):
        """
        Update an existing agenda item.

        Parameters:
            - db (Session): The database session.
            - event_id (str): The ID of the event.
            - item_id (str): The ID of the agenda item.
            - user_id (str): The ID of the user who owns the event.
            - item_data (AgendaItemUpdate): The updated agenda item data.
        Returns:
            tuple: A tuple containing the status code and the updated agenda item response model.
        Raises:
            HTTPException: If the agenda item is not found, raises a 404 error.
            HTTPException: If the user doesn't own the event, raises a 403 error.
            HTTPException: If end_time is before start_time, raises a 422 error.
        """
        # Validate event ownership
        if not self.agenda.validate_ownership(db=db, event_id=event_id, user_id=user_id):
            logger.warning(f"User {user_id} doesn't own event {event_id}")
            raise HTTPException(status_code=403, detail="You don't have permission to access this event.")

        # Validate time range if both times are provided
        if (item_data.start_time and item_data.end_time and 
            item_data.end_time <= item_data.start_time):
            raise HTTPException(status_code=422, detail="End time must be after start time.")

        # Convert Pydantic model to dict for DAO, excluding None values
        item_dict = {}
        if item_data.title is not None:
            item_dict["title"] = item_data.title
        if item_data.description is not None:
            item_dict["description"] = item_data.description
        if item_data.start_time is not None:
            item_dict["start_time"] = item_data.start_time
        if item_data.end_time is not None:
            item_dict["end_time"] = item_data.end_time
        if item_data.location is not None:
            item_dict["location"] = item_data.location
        if item_data.type is not None:
            item_dict["type"] = item_data.type.value
        if item_data.display_order is not None:
            item_dict["display_order"] = item_data.display_order
        if item_data.is_important is not None:
            item_dict["is_important"] = item_data.is_important

        updated = self.agenda_item.update(
            db=db, 
            item_id=item_id, 
            event_id=event_id, 
            user_id=user_id, 
            item_data=item_dict
        )
        
        if updated is None:
            raise HTTPException(status_code=404, detail=f"Agenda item '{item_id}' not found.")
        
        return 200, api_model.AgendaItemResponse(agenda_item=api_model.AgendaItem.model_validate(updated, from_attributes=True))

    def delete_agenda_item(self, db: Session, event_id: str, item_id: str, user_id: str):
        """
        Delete a specific agenda item.

        Parameters:
            - db (Session): The database session.
            - event_id (str): The ID of the event.
            - item_id (str): The ID of the agenda item.
            - user_id (str): The ID of the user who owns the event.
        Returns:
            tuple: A tuple containing the status code and a success message.
        Raises:
            HTTPException: If the agenda item is not found, raises a 404 error.
            HTTPException: If the user doesn't own the event, raises a 403 error.
        """
        # Validate event ownership
        if not self.agenda.validate_ownership(db=db, event_id=event_id, user_id=user_id):
            logger.warning(f"User {user_id} doesn't own event {event_id}")
            raise HTTPException(status_code=403, detail="You don't have permission to access this event.")

        result = self.agenda_item.delete(db=db, item_id=item_id, event_id=event_id, user_id=user_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"Agenda item '{item_id}' not found.")
        
        return 204, {"detail": f"Agenda item '{item_id}' successfully deleted."}

    def reorder_agenda_items(self, db: Session, event_id: str, user_id: str, reorder_data: api_model.AgendaReorderRequest):
        """
        Reorder agenda items by updating their display_order values.

        Parameters:
            - db (Session): The database session.
            - event_id (str): The ID of the event.
            - user_id (str): The ID of the user who owns the event.
            - reorder_data (AgendaReorderRequest): The reorder data with item IDs and new orders.
        Returns:
            tuple: A tuple containing the status code and a success message.
        Raises:
            HTTPException: If the agenda is not found, raises a 404 error.
            HTTPException: If the user doesn't own the event, raises a 403 error.
            HTTPException: If some items don't belong to the agenda, raises a 400 error.
        """
        # Validate event ownership
        if not self.agenda.validate_ownership(db=db, event_id=event_id, user_id=user_id):
            logger.warning(f"User {user_id} doesn't own event {event_id}")
            raise HTTPException(status_code=403, detail="You don't have permission to access this event.")

        # Convert Pydantic models to dict format expected by DAO
        item_orders = [
            {"item_id": item.item_id, "display_order": item.display_order}
            for item in reorder_data.items
        ]

        result = self.agenda_item.bulk_reorder(
            db=db, 
            event_id=event_id, 
            user_id=user_id, 
            item_orders=item_orders
        )
        
        if result is None:
            raise HTTPException(status_code=400, detail="Some agenda items don't belong to the specified agenda or agenda not found.")
        
        return 200, {"detail": "Agenda items successfully reordered."}


class DatabaseCleaner:
    def __init__(self):
        self.cleaner = DatabaseCleanerQuery()

    def recreate_all_tables(self, db: Session, recreate=False):
        """
        Recreate all tables in the database.

        Parameters:
            - db (Session): The database session.
            - recreate (bool): A flag indicating whether to recreate the tables.

        Returns:
            tuple: A tuple containing the status code and a message.

        Raises:
            HTTPException: If an error occurs while recreating the tables.
        """
        try:
            message = self.cleaner.recreate_all_tables(db=db, recreate=recreate)
            return 200, message
        except ValueError as error:
            logger.warning(f"Warning: {error}")
            raise HTTPException(status_code=400, detail=str(error))
        except Exception as error:
            logger.error(f"Database error: {error}")
            raise HTTPException(status_code=500, detail="Internal server error while recreating tables")
