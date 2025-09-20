from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session
from typing import Annotated
import re
from uuid import UUID

from app.database.db import get_db
from app.database.daos import UserQuery


def get_user_id(
    authorization: Annotated[str, Header(..., alias="Authorization")],
) -> str:
    """
    Fake auth system - extracts user_id from Authorization header.
    In real implementation, this would validate JWT token from AWS Cognito.
    
    Expected format: "Bearer user_uuid" or "user_uuid"
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required"
        )
    
    # Remove "Bearer " prefix if present
    token = authorization.replace("Bearer ", "").strip()
    
    # Validate token format (UUID format)
    try:
        UUID(token)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token format. Must be a valid UUID."
        )
    
    return token


def get_user_db(
    authorization: Annotated[str, Header(..., alias="Authorization")],
) -> str:
    """
    Get user_id from authorization header for database session.
    """
    user_id = get_user_id(authorization)
    return user_id


def get_current_user(
    authorization: Annotated[str, Header(..., alias="Authorization")],
    db: Session = Depends(get_db)
) -> str:
    """
    Get current user and validate that user exists in database.
    """
    user_id = get_user_id(authorization)
    
    # Validate that user exists in database
    user_query = UserQuery()
    user = user_query.get_one(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found. Please register first."
        )
    
    return user_id
