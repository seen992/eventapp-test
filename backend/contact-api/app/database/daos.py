from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, or_, func
from app.database.db import tenant_sessions_postgres, initialized_tenants, Base, DATABASE_URL_TEMPLATE

from app.api.models import ContactCreate
from app.database.models import Contact as DBContact
from app.utils.logger import logger


class ContactQuery:
    def get_one(self, db: Session, contact_id: str):
        return db.query(DBContact).filter(DBContact.contact_id == contact_id).first()

    def find_by_email_or_phone(self, db: Session, email: str = None, phone: str = None):
        query = db.query(DBContact)
        if email:
            query = query.filter(DBContact.email == email)
        if phone:
            query = query.filter(DBContact.phone == phone)
        return query.first()

    def get_all(self, db: Session, offset: int = 0, limit: int = 100):
        contacts = db.query(DBContact).offset(offset).limit(limit).all()
        return {"contacts": contacts}

    def create(self, db: Session, contact_data: ContactCreate):
        try:
            contact = DBContact(
                contact_id=str(uuid4()),
                first_name=contact_data.first_name,
                last_name=contact_data.last_name,
                full_name=f"{contact_data.first_name} {contact_data.last_name}",
                contact_type=contact_data.contact_type,
                owner=contact_data.owner,
                created_by=contact_data.created_by,
                email=contact_data.email,
                phone=contact_data.phone,
                attributes=contact_data.attributes,
                list_of_profile_ids=[],
            )
            db.add(contact)
            db.commit()
            db.refresh(contact)
            return contact
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[CREATE ERROR] {e}")
            raise

    def update(self, db: Session, contact_id: str, contact_data: ContactCreate):
        contact = self.get_one(db=db, contact_id=contact_id)
        if not contact:
            return None

        try:
            contact.first_name = contact_data.first_name
            contact.last_name = contact_data.last_name
            contact.full_name = f"{contact_data.first_name} {contact_data.last_name}"
            contact.contact_type = contact_data.contact_type
            contact.owner = contact_data.owner
            contact.created_by = contact_data.created_by
            contact.email = contact_data.email
            contact.phone = contact_data.phone
            contact.attributes = contact_data.attributes
            contact.list_of_profile_ids = []

            db.commit()
            db.refresh(contact)
            return contact
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[UPDATE ERROR] {e}")
            raise

    def delete(self, db: Session, contact_id: str):
        contact = self.get_one(db=db, contact_id=contact_id)
        if not contact:
            return None

        try:
            db.delete(contact)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[DELETE ERROR] {e}")
            raise

    def search_by_query(self, db: Session, query: str, offset: int = 0, limit: int = 100):
        """ Searches for contacts based on a query string.
        Parameters:
            - db (Session): The database session.
            - query (str): The search query string.
            - offset (int): The offset for pagination.
            - limit (int): The maximum number of results to return.
        Returns:
            list: A list of contacts that match the search criteria.
        Raises:
            - ValueError: If the query is empty.
        """
        like_query = f"%{query.lower()}%"
        search_contacts = db.query(DBContact).filter(
            or_(
                func.lower(DBContact.first_name).like(like_query),
                func.lower(DBContact.last_name).like(like_query),
                func.lower(DBContact.full_name).like(like_query),
                func.lower(DBContact.email).like(like_query),
                func.lower(DBContact.phone).like(like_query),
            )
        ).offset(offset).limit(limit).all()
        return {"contacts": search_contacts}


class DatabaseCleanerQuery:
    @staticmethod
    def recreate_all_tables(tenant_id: str, recreate=False):
        """
        Recreates all tables for the tenant database.

        Parameters:
            - tenant_id (str): The ID of the tenant database.
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

        tenant_db_name = tenant_id + "db"
        try:
            # Close and remove existing session
            if tenant_db_name in tenant_sessions_postgres:
                session = tenant_sessions_postgres[tenant_db_name]()
                session.close()
                del tenant_sessions_postgres[tenant_db_name]

            # Create engine
            database_url = DATABASE_URL_TEMPLATE.format(tenant_db_name)
            engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=1800, echo=False)

            # Drop and recreate all tables
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)

            # Reinitialize tracking
            initialized_tenants.add(tenant_db_name)

            logger.info(f"Tables recreated for tenant: {tenant_id}")
            return {"detail": f"Tables recreated for tenant: {tenant_id}"}

        except SQLAlchemyError as e:
            logger.error(f"Database error for tenant {tenant_id}: {e}")
            raise Exception(f"Database error for tenant {tenant_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error for tenant {tenant_id}: {e}")
            raise Exception(f"Unexpected error for tenant {tenant_id}: {e}")
