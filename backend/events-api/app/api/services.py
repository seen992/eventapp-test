from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api import models as api_model
from app.database.daos import EventQuery, UserQuery, DatabaseCleanerQuery
from app.utils.logger import logger
from app.utils.config import config_by_name

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
        created = self.event.create(db=db, event_data=event, user_id=user_id)
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


class DatabaseCleaner:
    def __init__(self):
        self.cleaner = DatabaseCleanerQuery()

    def recreate_all_tables(self, user_id: str, recreate=False):
        """
        Recreate all tables in the database.

        Parameters:
            - user_id (str): The ID of the user.
            - recreate (bool): A flag indicating whether to recreate the tables.

        Returns:
            tuple: A tuple containing the status code and a message.

        Raises:
            HTTPException: If an error occurs while recreating the tables.
        """
        try:
            message = self.cleaner.recreate_all_tables(user_id=user_id, recreate=recreate)
            return 200, message
        except ValueError as error:
            logger.warning(f"Warning: {error}")
            raise HTTPException(status_code=400, detail=str(error))
        except Exception as error:
            logger.error(f"Database error: {error}")
            raise HTTPException(status_code=500, detail="Internal server error while recreating tables")
