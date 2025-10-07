#!/usr/bin/env python3
"""
Script to check what's in the database
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def check_database():
    """Check database contents"""
    try:
        from app.database.db import engine, settings
        from sqlalchemy import text
        
        print("Database Configuration:")
        print(f"  Host: {settings.POSTGRES_DB_HOST}")
        print(f"  Port: {settings.POSTGRES_DB_PORT}")
        print(f"  User: {settings.POSTGRES_DB_USER}")
        print(f"  Database: {settings.POSTGRES_DB_NAME}")
        print(f"  Schema: {settings.DATABASE_SCHEMA}")
        print(f"  URL: {settings.DATABASE_URL}")
        print()
        
        with engine.connect() as conn:
            # Check if database exists and is accessible
            result = conn.execute(text("SELECT current_database(), current_schema()"))
            db_info = result.fetchone()
            print(f"Connected to database: {db_info[0]}")
            print(f"Current schema: {db_info[1]}")
            print()
            
            # Check available schemas
            result = conn.execute(text("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name"))
            schemas = [row[0] for row in result.fetchall()]
            print(f"Available schemas: {schemas}")
            print()
            
            # Check tables in our schema
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema
                ORDER BY table_name
            """), {"schema": settings.DATABASE_SCHEMA})
            tables = [row[0] for row in result.fetchall()]
            print(f"Tables in '{settings.DATABASE_SCHEMA}' schema: {tables}")
            print()
            
            # Check users table if it exists
            if 'users' in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {settings.DATABASE_SCHEMA}.users"))
                user_count = result.scalar()
                print(f"Users count: {user_count}")
                
                if user_count > 0:
                    result = conn.execute(text(f"SELECT id, email FROM {settings.DATABASE_SCHEMA}.users LIMIT 5"))
                    users = result.fetchall()
                    print("Sample users:")
                    for user in users:
                        print(f"  ID: {user[0]}, Email: {user[1]}")
                print()
            
            # Check events table if it exists
            if 'events' in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {settings.DATABASE_SCHEMA}.events"))
                event_count = result.scalar()
                print(f"Events count: {event_count}")
                
                if event_count > 0:
                    result = conn.execute(text(f"SELECT id, name, owner_id FROM {settings.DATABASE_SCHEMA}.events LIMIT 5"))
                    events = result.fetchall()
                    print("Sample events:")
                    for event in events:
                        print(f"  ID: {event[0]}, Name: {event[1]}, Owner: {event[2]}")
                print()
            
            # Check enum types
            result = conn.execute(text("""
                SELECT t.typname, e.enumlabel 
                FROM pg_type t 
                JOIN pg_enum e ON t.oid = e.enumtypid 
                JOIN pg_namespace n ON t.typnamespace = n.oid
                WHERE n.nspname = :schema
                ORDER BY t.typname, e.enumsortorder
            """), {"schema": settings.DATABASE_SCHEMA})
            enums = result.fetchall()
            if enums:
                print("Enum types:")
                current_type = None
                for enum_type, enum_value in enums:
                    if enum_type != current_type:
                        if current_type is not None:
                            print()
                        print(f"  {enum_type}:")
                        current_type = enum_type
                    print(f"    - {enum_value}")
                print()
        
        print("✓ Database check completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)