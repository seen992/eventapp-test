#!/usr/bin/env python3
"""
Simple test script to verify database initialization
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_database_initialization():
    """Test database initialization"""
    try:
        from app.database.db import create_tables, get_db
        
        print("Testing database initialization...")
        
        # Initialize database
        create_tables()
        print("✓ Database initialization successful")
        
        # Test getting a session
        db_gen = get_db()
        db = next(db_gen)
        print("✓ Database session created successfully")
        
        # Test a simple query
        from sqlalchemy import text
        result = db.execute(text("SELECT 1 as test")).fetchone()
        print(f"✓ Database query successful: {result}")
        
        # Close session
        db.close()
        print("✓ Database session closed successfully")
        
        print("\n🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_initialization()
    sys.exit(0 if success else 1)