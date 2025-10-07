#!/usr/bin/env python3
"""
Test script to check for circular imports
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test imports to check for circular dependencies"""
    try:
        print("Testing imports...")
        
        # Test db imports
        from app.database.db import Base, initialize_database
        print("✓ Successfully imported Base and initialize_database")
        
        # Test model imports
        from app.database.models import User, Event
        print("✓ Successfully imported models")
        
        print("✓ No circular import detected")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)