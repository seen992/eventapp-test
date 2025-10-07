from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.utils.config import settings
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log database configuration for debugging
logger.info(f"Database configuration:")
logger.info(f"  POSTGRES_DB_USER: {settings.POSTGRES_DB_USER}")
logger.info(f"  POSTGRES_DB_HOST: {settings.POSTGRES_DB_HOST}")
logger.info(f"  POSTGRES_DB_PORT: {settings.POSTGRES_DB_PORT}")
logger.info(f"  POSTGRES_DB_NAME: {settings.POSTGRES_DB_NAME}")
logger.info(f"  DATABASE_SCHEMA: {settings.DATABASE_SCHEMA}")
logger.info(f"  Constructed DATABASE_URL: {settings.DATABASE_URL}")

# Create database engine
engine = create_engine(settings.DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class with schema support
Base = declarative_base()

# Set schema globally for all tables
Base.metadata.schema = settings.DATABASE_SCHEMA

def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    try:
        # Try to connect to the target database first
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info(f"Database '{settings.POSTGRES_DB_NAME}' exists and is accessible")
            return
    except Exception as e:
        logger.info(f"Database '{settings.POSTGRES_DB_NAME}' doesn't exist or isn't accessible: {e}")
        
        # Connect to postgres system database to create our database
        postgres_url = f"postgresql://{settings.POSTGRES_DB_USER}:{settings.POSTGRES_DB_PASSWORD}@{settings.POSTGRES_DB_HOST}:{settings.POSTGRES_DB_PORT}/postgres"
        postgres_engine = create_engine(postgres_url)
        
        try:
            with postgres_engine.connect() as connection:
                connection.execution_options(isolation_level="AUTOCOMMIT")
                
                # Check if database exists
                result = connection.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :name"),
                    {"name": settings.POSTGRES_DB_NAME}
                )
                
                if not result.fetchone():
                    # Create the database
                    connection.execute(text(f'CREATE DATABASE "{settings.POSTGRES_DB_NAME}"'))
                    logger.info(f"Created database: {settings.POSTGRES_DB_NAME}")
                else:
                    logger.info(f"Database already exists: {settings.POSTGRES_DB_NAME}")
                    
        except Exception as create_error:
            logger.error(f"Error creating database: {create_error}")
            raise
        finally:
            postgres_engine.dispose()

def create_schema_if_not_exists():
    """Create database schema if it doesn't exist"""
    try:
        with engine.connect() as connection:
            # Check if schema exists
            result = connection.execute(
                text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"),
                {"schema": settings.DATABASE_SCHEMA}
            )
            if not result.fetchone():
                # Create schema
                connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.DATABASE_SCHEMA}"'))
                connection.commit()
                logger.info(f"Created database schema: {settings.DATABASE_SCHEMA}")
            else:
                logger.info(f"Database schema already exists: {settings.DATABASE_SCHEMA}")
    except Exception as e:
        logger.error(f"Error creating schema: {e}")
        raise

def drop_all_tables():
    """Drop all tables and enum types"""
    try:
        # Import models here to avoid circular imports
        from app.database.models import User, Event, Agenda, AgendaItem
        
        # Schema is already set globally on Base.metadata
        
        # Drop enum types first with CASCADE to remove dependencies
        with engine.connect() as connection:
            connection.execute(text(f"DROP TYPE IF EXISTS {settings.DATABASE_SCHEMA}.eventplan CASCADE"))
            connection.execute(text(f"DROP TYPE IF EXISTS {settings.DATABASE_SCHEMA}.eventtype CASCADE"))
            connection.execute(text(f"DROP TYPE IF EXISTS {settings.DATABASE_SCHEMA}.eventstatus CASCADE"))
            connection.execute(text(f"DROP TYPE IF EXISTS {settings.DATABASE_SCHEMA}.agendaitemtype CASCADE"))
            connection.commit()
            logger.info(f"Dropped enum types in schema: {settings.DATABASE_SCHEMA}")
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
            
        logger.info(f"Dropped all tables in schema: {settings.DATABASE_SCHEMA}")
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        # Don't raise - this is expected if tables don't exist

def create_indexes():
    """Create performance indexes for agenda tables"""
    try:
        with engine.connect() as connection:
            # Index for agendas by event_id
            connection.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_agendas_event_id 
                ON {settings.DATABASE_SCHEMA}.agendas(event_id)
            """))
            
            # Index for agenda_items by agenda_id
            connection.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_agenda_items_agenda_id 
                ON {settings.DATABASE_SCHEMA}.agenda_items(agenda_id)
            """))
            
            # Composite index for agenda_items ordering
            connection.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_agenda_items_display_order 
                ON {settings.DATABASE_SCHEMA}.agenda_items(agenda_id, display_order, start_time)
            """))
            
            connection.commit()
            logger.info(f"Created performance indexes in schema: {settings.DATABASE_SCHEMA}")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise

def create_tables(force_recreate=False):
    """Create all tables in the specified schema"""
    try:
        # Import models here to avoid circular imports
        from app.database.models import User, Event, Agenda, AgendaItem
        logger.info("Database models imported successfully")
        
        # Schema is already set globally on Base.metadata
        
        # Create database first
        create_database_if_not_exists()
        
        # Create schema first
        create_schema_if_not_exists()
        
        # Always drop tables when switching from UUID to NanoID
        drop_all_tables()
        
        # Create all tables (will skip if they already exist)
        Base.metadata.create_all(bind=engine)
        logger.info(f"Created all tables in schema: {settings.DATABASE_SCHEMA}")
        
        # Create performance indexes
        create_indexes()
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
