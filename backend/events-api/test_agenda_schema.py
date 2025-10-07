#!/usr/bin/env python3
"""
Test script to validate agenda table schema and SQL generation
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_agenda_schema():
    """Test agenda table schema without database connection"""
    try:
        from sqlalchemy import create_engine, MetaData
        from sqlalchemy.schema import CreateTable, CreateIndex
        from app.database.models import Agenda, AgendaItem, AgendaItemType
        
        print("Testing agenda schema generation...")
        
        # Create a mock engine for SQL generation (no actual connection)
        engine = create_engine("postgresql://user:pass@localhost/test", echo=False)
        
        # Test that models are properly defined
        print("✓ Agenda and AgendaItem models imported successfully")
        
        # Test enum values
        expected_types = {'ceremony', 'reception', 'entertainment', 'speech', 'meal', 'break', 'photo_session', 'other'}
        actual_types = {item.value for item in AgendaItemType}
        assert actual_types == expected_types, f"Enum mismatch: expected {expected_types}, got {actual_types}"
        print("✓ AgendaItemType enum has correct values")
        
        # Test table structure
        agenda_table = Agenda.__table__
        agenda_item_table = AgendaItem.__table__
        
        # Check agenda table columns
        agenda_columns = {col.name for col in agenda_table.columns}
        expected_agenda_cols = {'id', 'event_id', 'title', 'description', 'created_at', 'updated_at'}
        assert agenda_columns == expected_agenda_cols, f"Agenda columns mismatch: expected {expected_agenda_cols}, got {agenda_columns}"
        print("✓ Agenda table has correct columns")
        
        # Check agenda_item table columns
        item_columns = {col.name for col in agenda_item_table.columns}
        expected_item_cols = {'id', 'agenda_id', 'title', 'description', 'start_time', 'end_time', 'location', 'type', 'display_order', 'is_important', 'created_at', 'updated_at'}
        assert item_columns == expected_item_cols, f"AgendaItem columns mismatch: expected {expected_item_cols}, got {item_columns}"
        print("✓ AgendaItem table has correct columns")
        
        # Test foreign key relationships
        agenda_fks = [fk.column.table.name for fk in agenda_table.foreign_keys]
        assert 'events' in agenda_fks, f"Agenda should have FK to events table, got: {agenda_fks}"
        print("✓ Agenda has foreign key to events table")
        
        item_fks = [fk.column.table.name for fk in agenda_item_table.foreign_keys]
        assert 'agendas' in item_fks, f"AgendaItem should have FK to agendas table, got: {item_fks}"
        print("✓ AgendaItem has foreign key to agendas table")
        
        # Generate CREATE TABLE SQL to verify structure
        agenda_sql = str(CreateTable(agenda_table).compile(engine))
        item_sql = str(CreateTable(agenda_item_table).compile(engine))
        
        print("✓ SQL generation successful")
        print(f"  Agenda table SQL length: {len(agenda_sql)} chars")
        print(f"  AgendaItem table SQL length: {len(item_sql)} chars")
        
        # Test that cascade delete is configured
        agenda_relationship = None
        for rel in Agenda.__mapper__.relationships:
            if rel.key == 'items':
                agenda_relationship = rel
                break
        
        assert agenda_relationship is not None, "Agenda should have 'items' relationship"
        assert 'delete-orphan' in str(agenda_relationship.cascade), "Items relationship should have delete-orphan cascade"
        print("✓ Cascade delete configured correctly")
        
        print("\n🎉 All agenda schema tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_nanoid_generators():
    """Test that NanoID generators are available"""
    try:
        from app.utils.nanoid import generate_agenda_id, generate_agenda_item_id
        
        # Test ID generation
        agenda_id = generate_agenda_id()
        item_id = generate_agenda_item_id()
        
        assert len(agenda_id) == 12, f"Agenda ID should be 12 chars, got {len(agenda_id)}"
        assert len(item_id) == 12, f"Item ID should be 12 chars, got {len(item_id)}"
        assert agenda_id != item_id, "IDs should be unique"
        
        print("✓ NanoID generators working correctly")
        print(f"  Sample agenda ID: {agenda_id}")
        print(f"  Sample item ID: {item_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ NanoID test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    schema_success = test_agenda_schema()
    nanoid_success = test_nanoid_generators()
    
    success = schema_success and nanoid_success
    print(f"\n{'✅' if success else '❌'} Overall test result: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)