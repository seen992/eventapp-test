from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, or_, func, and_
from app.database.db import user_sessions_postgres, initialized_users, Base, DATABASE_URL_TEMPLATE

from app.api.models import EventCreate, EventUpdate, UserCreate, UserUpdate
from app.database.models import Event as DBEvent, User as DBUser
from app.utils.logger import logger


class UserQuery:
    def get_one(self, db: Session, user_id: str):
        return db.query(DBUser).filter(DBUser.id == user_id).first()

    def get_by_email(self, db: Session, email: str):
        return db.query(DBUser).filter(DBUser.email == email).first()

    def create(self, db: Session, user_data: UserCreate):
        try:
            user = DBUser(
                id=str(uuid4()),
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                phone=user_data.phone
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[CREATE USER ERROR] {e}")
            raise

    def update(self, db: Session, user_id: str, user_data: UserUpdate):
        user = self.get_one(db=db, user_id=user_id)
        if not user:
            return None

        try:
            if user_data.first_name is not None:
                user.first_name = user_data.first_name
            if user_data.last_name is not None:
                user.last_name = user_data.last_name
            if user_data.phone is not None:
                user.phone = user_data.phone

            db.commit()
            db.refresh(user)
            return user
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[UPDATE USER ERROR] {e}")
            raise


class EventQuery:
    def get_one(self, db: Session, event_id: str, user_id: str):
        return db.query(DBEvent).filter(
            and_(DBEvent.id == event_id, DBEvent.owner_id == user_id)
        ).first()

    def get_all(self, db: Session, user_id: str, offset: int = 0, limit: int = 100, status: str = None):
        query = db.query(DBEvent).filter(DBEvent.owner_id == user_id)
        
        if status:
            query = query.filter(DBEvent.status == status)
            
        events = query.offset(offset).limit(limit).all()
        total = query.count()
        has_more = (offset + limit) < total
        
        return {
            "events": events,
            "total": total,
            "has_more": has_more
        }

    def create(self, db: Session, event_data: EventCreate, user_id: str):
        try:
            event = DBEvent(
                id=str(uuid4()),
                name=event_data.name,
                plan=event_data.plan,
                location=event_data.location,
                restaurant_name=event_data.restaurant_name,
                date=event_data.date,
                time=event_data.time,
                event_type=event_data.event_type,
                expected_guests=event_data.expected_guests,
                description=event_data.description,
                owner_id=user_id,
                status="draft"
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            return event
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[CREATE ERROR] {e}")
            raise

    def update(self, db: Session, event_id: str, event_data: EventUpdate, user_id: str):
        event = self.get_one(db=db, event_id=event_id, user_id=user_id)
        if not event:
            return None

        try:
            if event_data.name is not None:
                event.name = event_data.name
            if event_data.location is not None:
                event.location = event_data.location
            if event_data.restaurant_name is not None:
                event.restaurant_name = event_data.restaurant_name
            if event_data.date is not None:
                event.date = event_data.date
            if event_data.time is not None:
                event.time = event_data.time
            if event_data.event_type is not None:
                event.event_type = event_data.event_type
            if event_data.expected_guests is not None:
                event.expected_guests = event_data.expected_guests
            if event_data.description is not None:
                event.description = event_data.description

            db.commit()
            db.refresh(event)
            return event
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[UPDATE ERROR] {e}")
            raise

    def delete(self, db: Session, event_id: str, user_id: str):
        event = self.get_one(db=db, event_id=event_id, user_id=user_id)
        if not event:
            return None

        try:
            db.delete(event)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[DELETE ERROR] {e}")
            raise


class DatabaseCleanerQuery:
    @staticmethod
    def recreate_all_tables(user_id: str, recreate=False):
        """
        Recreates all tables for the user database.

        Parameters:
            - user_id (str): The ID of the user database.
            - recreate (bool): A flag indicating whether to recreate the tables.

        Returns:
            - dict: A dictionary containing the result of the operation.

        Raises:
            - ValueError: If the tables are not recreated.
            - SQLAlchemyError: If there is a database error.
            - Exception: If there is an unexpected error
        """
        if not recreate:
            raise ValueError("Tables are not recreated. Set `recreate=True` to proceed")

        user_db_name = user_id + "db"
        try:
            # Close and remove existing session
            if user_db_name in user_sessions_postgres:
                session = user_sessions_postgres[user_db_name]()
                session.close()
                del user_sessions_postgres[user_db_name]

            # Create engine
            database_url = DATABASE_URL_TEMPLATE.format(user_db_name)
            engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=1800, echo=False)

            # Drop and recreate all tables
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)

            # Reinitialize tracking
            initialized_users.add(user_db_name)

            logger.info(f"Tables recreated for user: {user_id}")
            return {"detail": f"Tables recreated for user: {user_id}"}

        except SQLAlchemyError as e:
            logger.error(f"Database error for user {user_id}: {e}")
            raise Exception(f"Database error for user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error for user {user_id}: {e}")
            raise Exception(f"Unexpected error for user {user_id}: {e}")
