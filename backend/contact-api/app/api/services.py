from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api import models as api_model
from app.database.daos import ContactQuery, DatabaseCleanerQuery
from app.utils.logger import logger
from app.utils.config import config_by_name

config = config_by_name["BasicConfig"]


class ContactLogic:
    def __init__(self):
        self.contact = ContactQuery()

    def get_contact(self, db: Session, contact_id: str):
        """ Retrieve a contact by its ID.

        Parameters:
            - db (Session): The database session.
            - contact_id (str): The ID of the contact to retrieve.
        Returns:
            tuple: A tuple containing the status code and the contact response model.
        Raises:
            HTTPException: If the contact is not found, raises a 404 error.
        """
        result = self.contact.get_one(db=db, contact_id=contact_id)
        if result is None:
            logger.warning(f"Contact not found: {contact_id}")
            raise HTTPException(status_code=404, detail=f"Contact with ID '{contact_id}' not found.")
        return 200, api_model.ContactResponse.model_validate(result, from_attributes=True)

    def get_contacts(self, db: Session, limit: int = 100, offset: int = 0):
        """ Retrieve all contacts with pagination.

        Parameters:
            - db (Session): The database session.
            - limit (int): The maximum number of contacts to return (default is 100).
            - offset (int): The offset for pagination (default is 0).
        Returns:
            tuple: A tuple containing the status code and the contact response model.
        Raises:
            HTTPException: If no contacts are found, raises a 404 error.
        """
        data = self.contact.get_all(db=db, limit=limit, offset=offset)

        if not data or not data.get("contacts"):
            logger.info("No contacts found")
            contacts = []
        else:
            logger.info(f"Found {len(data['contacts'])} contacts")
            contacts = [api_model.ContactResponse.model_validate(c, from_attributes=True) for c in data["contacts"]]
        return 200, api_model.ContactsResponse(
            offset=offset,
            limit=limit,
            count=len(data["contacts"]),
            contacts=contacts,
        )

    def create_contact(self, db: Session, contact: api_model.ContactCreate):
        """ Create a new contact.

        Parameters:
            - db (Session): The database session.
            - contact (ContactCreate): The contact data to create.
        Returns:
            tuple: A tuple containing the status code and the created contact response model.
        Raises:
            "HTTPException": If a contact with the same email or phone already exists, raises a 409 error.
        """
        existing = self.contact.find_by_email_or_phone(
            db=db,
            email=contact.email,
            phone=contact.phone
        )
        if existing:
            raise HTTPException(status_code=409, detail="Contact already exists with the same phone or email.")

        created = self.contact.create(db=db, contact_data=contact)
        return 201, api_model.ContactResponse.model_validate(created, from_attributes=True)

    def update_contact(self, db: Session, contact_id: str, contact: api_model.ContactCreate):
        """ Update an existing contact.

        Parameters:
            - db (Session): The database session.
            - contact_id (str): The ID of the contact to update.
            - contact (ContactCreate): The updated contact data.
        Returns:
            tuple: A tuple containing the status code and the updated contact response model.
        Raises:
            HTTPException: If the contact is not found, raises a 404 error.
        """
        existing = self.contact.get_one(db=db, contact_id=contact_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Contact ID '{contact_id}' not found for update.")

        updated = self.contact.update(db=db, contact_id=contact_id, contact_data=contact)
        return 200, api_model.ContactResponse.model_validate(updated, from_attributes=True)

    def delete_contact(self, db: Session, contact_id: str):
        """ Delete a contact by its ID.

        Parameters:
            - db (Session): The database session.
            - contact_id (str): The ID of the contact to delete.
        Returns:
            tuple: A tuple containing the status code and a success message.
        Raises:
            HTTPException: If the contact is not found, raises a 404 error.
        """
        existing = self.contact.get_one(db=db, contact_id=contact_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Contact ID '{contact_id}' not found for deletion.")

        self.contact.delete(db=db, contact_id=contact_id)
        return 200, {"detail": f"Contact ID '{contact_id}' successfully deleted."}

    def search_contacts(self, db: Session, query: str, offset: int = 0, limit: int = 100):
        """ Search for contacts by a query string.
        Parameters:
            - db (Session): The database session.
            - query (str): The search query string.
            - offset (int): The offset for pagination (default is 0).
            - limit (int): The maximum number of contacts to return (default is 100).
        Returns:
            tuple: A tuple containing the status code and the contacts' response model.
        Raises:
            HTTPException: If no contacts are found, raises a 404 error.
        """
        data = self.contact.search_by_query(
            db=db,
            query=query,
            limit=limit,
            offset=offset
        )

        if not data or not data.get("contacts"):
            logger.info("No contacts found")
            contacts = []
        else:
            logger.info(f"Found {len(data['contacts'])} contacts")
            contacts = [api_model.ContactResponse.model_validate(c, from_attributes=True) for c in data["contacts"]]
        return 200, api_model.ContactsResponse(
            offset=0,
            limit=len(data["contacts"]),
            count=len(data["contacts"]),
            contacts=contacts,
        )


class DatabaseCleaner:
    def __init__(self):
        self.cleaner = DatabaseCleanerQuery()

    def recreate_all_tables(self, tenant_id: str, recreate=False):
        """
        Recreate all tables in the database.

        Parameters:
            - tenant_id (str): The ID of the tenant.
            - recreate (bool): A flag indicating whether to recreate the tables.

        Returns:
            tuple: A tuple containing the status code and a message.

        Raises:
            HTTPException: If an error occurs while recreating the tables.
        """
        try:
            message = self.cleaner.recreate_all_tables(tenant_id=tenant_id, recreate=recreate)
            return 200, message
        except ValueError as error:
            logger.warning(f"Warning: {error}")
            raise HTTPException(status_code=400, detail=str(error))
        except Exception as error:
            logger.error(f"Database error: {error}")
            raise HTTPException(status_code=500, detail="Internal server error while recreating tables")
