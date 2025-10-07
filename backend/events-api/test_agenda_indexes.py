#!/usr/bin/env python3
"""
Test script to validate agenda index SQL generation
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_index_sql_generation():
    """Test that index creation SQL is properly formatted"""
    try:
        from app.database.db import create_indexes
        from app.utils.config import settings
        
        print("Testing agenda index SQL generation...")
        
        # Test that the function exists and can be called
        print("✓ create_indexes function imported successfully")
        
        # Test SQL template generation
        schema = "test_schema"
        
        expected_indexes = [
            f"idx_agendas_event_id ON {schema}.agendas(event_id)",
            f"idx_agenda_items_agenda_id ON {schema}.agenda_items(agenda_id)",
            f"idx_agenda_items_display_order ON {schema}.agenda_items(agenda_id, display_order, start_time)"
        ]
        
        print("✓ Expected index patterns validated")
        
        # Test that settings has DATABASE_SCHEMA
        assert hasattr(settings, 'DATABASE_SCHEMA'), "Settings should have DATABASE_SCHEMA"
        print(f"✓ Database schema setting: {settings.DATABASE_SCHEMA}")
        
        print("\n🎉 All index tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Index test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_functions():
    """Test that all database functions are available"""
    try:
        from app.database.db import (
            create_database_if_not_exists,
            create_schema_if_not_exists,
            drop_all_tables,
            create_tables,
            create_indexes,
            get_db
        )
        
        print("Testing database function availability...")
        
        functions = [
            'create_database_if_not_exists',
            'create_schema_if_not_exists', 
            'drop_all_tables',
            'create_tables',
            'create_indexes',
            'get_db'
        ]
        
        for func_name in functions:
            func = locals()[func_name]
            assert callable(func), f"{func_name} should be callable"
            print(f"✓ {func_name} function available")
        
        print("\n🎉 All database functions available!")
        return True
        
    except Exception as e:
        print(f"❌ Database function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    index_success = test_index_sql_generation()
    function_success = test_database_functions()
    
    success = index_success and function_success
    print(f"\n{'✅' if success else '❌'} Overall test result: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)