from app.utils.nanoid import generate_user_id, generate_event_id, generate_agenda_id, generate_agenda_item_id
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, or_, func, and_
from app.database.db import Base

from app.api.models import EventCreate, EventUpdate, UserCreate, UserUpdate
from app.database.models import Event as DBEvent, User as DBUser, Agenda as DBAgenda, AgendaItem as DBAgendaItem
from app.utils.logger import logger


class UserQuery:
    def get_one(self, db: Session, user_id: str):
        return db.query(DBUser).filter(DBUser.id == user_id).first()

    def get_by_email(self, db: Session, email: str):
        return db.query(DBUser).filter(DBUser.email == email).first()

    def create(self, db: Session, user_data: UserCreate):
        try:
            user = DBUser(
                id=generate_user_id(),
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
        return db.query(DBEvent).options(
            joinedload(DBEvent.agenda).joinedload(DBAgenda.items)
        ).filter(
            and_(DBEvent.id == event_id, DBEvent.owner_id == user_id)
        ).first()

    def get_all(self, db: Session, user_id: str, offset: int = 0, limit: int = 100, status: str = None):
        query = db.query(DBEvent).options(
            joinedload(DBEvent.agenda).joinedload(DBAgenda.items)
        ).filter(DBEvent.owner_id == user_id)
        
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
            logger.info(f"Creating event with user_id: {user_id} (type: {type(user_id)})")
            
            # Handle case where user_id might be a dict (debugging issue)
            if isinstance(user_id, dict):
                logger.warning(f"user_id is dict: {user_id}, extracting user_id value")
                actual_user_id = user_id.get('user_id', str(user_id))
            else:
                actual_user_id = user_id
                
            logger.info(f"Using actual_user_id: {actual_user_id} (type: {type(actual_user_id)})")
            
            event = DBEvent(
                id=generate_event_id(),
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
                status='draft'
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


class AgendaQuery:
    def get_one(self, db: Session, event_id: str, user_id: str):
        """Get agenda for an event with ownership validation"""
        return db.query(DBAgenda).join(DBEvent).filter(
            and_(
                DBAgenda.event_id == event_id,
                DBEvent.owner_id == user_id
            )
        ).first()

    def get_agenda_with_items(self, db: Session, event_id: str, user_id: str):
        """Get agenda with all items ordered by display_order and start_time"""
        agenda = db.query(DBAgenda).join(DBEvent).filter(
            and_(
                DBAgenda.event_id == event_id,
                DBEvent.owner_id == user_id
            )
        ).first()
        
        if agenda:
            # Items are already ordered by the relationship definition
            return agenda
        return None

    def create(self, db: Session, event_id: str, user_id: str, title: str = "Program događaja", description: str = None):
        """Create a new agenda for an event"""
        # First validate that the event exists and user owns it
        event = db.query(DBEvent).filter(
            and_(DBEvent.id == event_id, DBEvent.owner_id == user_id)
        ).first()
        
        if not event:
            return None

        try:
            agenda = DBAgenda(
                id=generate_agenda_id(),
                event_id=event_id,
                title=title,
                description=description
            )
            db.add(agenda)
            db.commit()
            db.refresh(agenda)
            return agenda
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[CREATE AGENDA ERROR] {e}")
            raise

    def update(self, db: Session, event_id: str, user_id: str, title: str = None, description: str = None):
        """Update an existing agenda"""
        agenda = self.get_one(db=db, event_id=event_id, user_id=user_id)
        if not agenda:
            return None

        try:
            if title is not None:
                agenda.title = title
            if description is not None:
                agenda.description = description

            db.commit()
            db.refresh(agenda)
            return agenda
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[UPDATE AGENDA ERROR] {e}")
            raise

    def delete(self, db: Session, event_id: str, user_id: str):
        """Delete an agenda and all its items (cascade)"""
        agenda = self.get_one(db=db, event_id=event_id, user_id=user_id)
        if not agenda:
            return None

        try:
            db.delete(agenda)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[DELETE AGENDA ERROR] {e}")
            raise

    def validate_ownership(self, db: Session, event_id: str, user_id: str):
        """Validate that user owns the event associated with the agenda"""
        event = db.query(DBEvent).filter(
            and_(DBEvent.id == event_id, DBEvent.owner_id == user_id)
        ).first()
        return event is not None


class AgendaItemQuery:
    def get_one(self, db: Session, item_id: str, event_id: str, user_id: str):
        """Get a specific agenda item with ownership validation"""
        return db.query(DBAgendaItem).join(DBAgenda).join(DBEvent).filter(
            and_(
                DBAgendaItem.id == item_id,
                DBAgenda.event_id == event_id,
                DBEvent.owner_id == user_id
            )
        ).first()

    def get_all_for_agenda(self, db: Session, event_id: str, user_id: str):
        """Get all items for an agenda with ownership validation"""
        return db.query(DBAgendaItem).join(DBAgenda).join(DBEvent).filter(
            and_(
                DBAgenda.event_id == event_id,
                DBEvent.owner_id == user_id
            )
        ).order_by(DBAgendaItem.display_order, DBAgendaItem.start_time).all()

    def create(self, db: Session, event_id: str, user_id: str, item_data: dict):
        """Create a new agenda item"""
        # First validate that the agenda exists and user owns the event
        agenda = db.query(DBAgenda).join(DBEvent).filter(
            and_(
                DBAgenda.event_id == event_id,
                DBEvent.owner_id == user_id
            )
        ).first()
        
        if not agenda:
            return None

        try:
            # Auto-assign display_order if not provided
            if 'display_order' not in item_data or item_data['display_order'] is None:
                max_order = db.query(func.max(DBAgendaItem.display_order)).filter(
                    DBAgendaItem.agenda_id == agenda.id
                ).scalar() or 0
                item_data['display_order'] = max_order + 1

            agenda_item = DBAgendaItem(
                id=generate_agenda_item_id(),
                agenda_id=agenda.id,
                **item_data
            )
            db.add(agenda_item)
            db.commit()
            db.refresh(agenda_item)
            return agenda_item
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[CREATE AGENDA ITEM ERROR] {e}")
            raise

    def update(self, db: Session, item_id: str, event_id: str, user_id: str, item_data: dict):
        """Update an existing agenda item"""
        item = self.get_one(db=db, item_id=item_id, event_id=event_id, user_id=user_id)
        if not item:
            return None

        try:
            for key, value in item_data.items():
                if value is not None and hasattr(item, key):
                    setattr(item, key, value)

            db.commit()
            db.refresh(item)
            return item
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[UPDATE AGENDA ITEM ERROR] {e}")
            raise

    def delete(self, db: Session, item_id: str, event_id: str, user_id: str):
        """Delete a specific agenda item"""
        item = self.get_one(db=db, item_id=item_id, event_id=event_id, user_id=user_id)
        if not item:
            return None

        try:
            db.delete(item)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[DELETE AGENDA ITEM ERROR] {e}")
            raise

    def bulk_reorder(self, db: Session, event_id: str, user_id: str, item_orders: list):
        """
        Bulk update display_order for multiple items
        item_orders: list of dicts with 'item_id' and 'display_order' keys
        """
        # First validate that the agenda exists and user owns the event
        agenda = db.query(DBAgenda).join(DBEvent).filter(
            and_(
                DBAgenda.event_id == event_id,
                DBEvent.owner_id == user_id
            )
        ).first()
        
        if not agenda:
            return None

        try:
            # Validate that all items belong to this agenda
            item_ids = [item['item_id'] for item in item_orders]
            existing_items = db.query(DBAgendaItem).filter(
                and_(
                    DBAgendaItem.id.in_(item_ids),
                    DBAgendaItem.agenda_id == agenda.id
                )
            ).all()
            
            if len(existing_items) != len(item_ids):
                logger.error("Some items don't belong to the specified agenda")
                return None

            # Update display_order for each item
            for item_order in item_orders:
                db.query(DBAgendaItem).filter(
                    DBAgendaItem.id == item_order['item_id']
                ).update({
                    'display_order': item_order['display_order']
                })

            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[BULK REORDER ERROR] {e}")
            raise

    def validate_ownership(self, db: Session, item_id: str, event_id: str, user_id: str):
        """Validate that user owns the event associated with the agenda item"""
        item = db.query(DBAgendaItem).join(DBAgenda).join(DBEvent).filter(
            and_(
                DBAgendaItem.id == item_id,
                DBAgenda.event_id == event_id,
                DBEvent.owner_id == user_id
            )
        ).first()
        return item is not None


class DatabaseCleanerQuery:
    @staticmethod
    def recreate_all_tables(db: Session, recreate=False):
        """
        Recreates all tables in the database.

        Parameters:
            - db (Session): The database session.
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

        try:
            # Get the engine from the session
            engine = db.bind
            
            # Drop and recreate all tables
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)

            logger.info("Tables recreated successfully")
            return {"detail": "Tables recreated successfully"}

        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            raise Exception(f"Database error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise Exception(f"Unexpected error: {e}")
