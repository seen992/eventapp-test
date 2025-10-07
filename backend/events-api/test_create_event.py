#!/usr/bin/env python3
"""
Test script for creating events with real user UUID
"""
import sys
import os
import json
from uuid import uuid4

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_create_event():
    """Test creating an event with database operations"""
    try:
        from app.database.db import create_tables, get_db
        from app.database.daos import UserQuery, EventQuery
        from app.api.models import UserCreate, EventCreate
        from datetime import date, time
        
        print("Testing event creation...")
        
        # Initialize database
        create_tables()
        print("✓ Database initialized")
        
        # Get database session
        db = next(get_db())
        
        # Create a test user first
        user_query = UserQuery()
        user_data = UserCreate(
            email=f"test_{uuid4()}@example.com",
            first_name="Test",
            last_name="User",
            phone="+381123456789"
        )
        
        created_user = user_query.create(db, user_data)
        print(f"✓ Created user: {created_user.id}")
        
        # Create an event for this user
        event_query = EventQuery()
        event_data = EventCreate(
            name="Test Wedding",
            plan="freemium",  # Use string instead of enum
            location="Belgrade, Serbia",
            restaurant_name="Test Restaurant",
            date=date(2024, 6, 15),
            time=time(18, 0),
            event_type="wedding",  # Use string instead of enum
            expected_guests=100,
            description="Test wedding event"
        )
        
        print(f"Creating event with user_id: {created_user.id} (type: {type(created_user.id)})")
        created_event = event_query.create(db, event_data, str(created_user.id))
        print(f"✓ Created event: {created_event.id}")
        print(f"✓ Event owner_id: {created_event.owner_id}")
        print(f"✓ Event plan: {created_event.plan}")
        print(f"✓ Event type: {created_event.event_type}")
        
        # Close session
        db.close()
        print("✓ Database session closed")
        
        print("\n🎉 Event creation test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Event creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_create_event()
    sys.exit(0 if success else 1)