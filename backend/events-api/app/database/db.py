import urllib3
import warnings
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.schema import CreateSchema
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.utils.config import config_by_name
from app.utils.logger import logger

warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)

config = config_by_name["BasicConfig"]
Base = declarative_base()

DATABASE_URL_TEMPLATE = "postgresql://{}:{}@{}:{}/{{}}".format(
    config.db_user,
    config.db_password,
    config.db_host,
    config.db_port,
)

# Cache for user-specific session makers and initialization status
user_sessions_postgres = {}
# Tracks users for which schema and tables are set up. We need to create database and tables for each user
initialized_users = set()


def get_db(user_id: str) -> Generator[Session, None, None]:
    user_db_name = user_id + "db"

    if user_db_name not in user_sessions_postgres:
        # Connect to the 'postgres' system database to check for database existence
        server_url = DATABASE_URL_TEMPLATE.format("postgres")
        server_engine = create_engine(server_url, echo=False, future=True)

        with server_engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")

            # Check if the database already exists
            db_exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": user_db_name}
            ).scalar()

            if not db_exists:
                # If a database does not exist, attempt to create it
                try:
                    conn.execute(text(f"CREATE DATABASE {user_db_name}"))
                    logger.info(f"Database '{user_db_name}' created successfully.")
                except Exception as e:
                    logger.error(f"Failed to create database '{user_db_name}'. Error: {e}")
            else:
                logger.info(f"Database '{user_db_name}' already exists. Skipping creation.")

        # Connect to the user's database after ensuring its existence
        database_url = DATABASE_URL_TEMPLATE.format(user_db_name)
        engine = create_engine(database_url,
                               pool_size=20,
                               max_overflow=30,
                               pool_timeout=30,
                               pool_pre_ping=True,
                               pool_recycle=1800,
                               echo=False)
        session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        user_sessions_postgres[user_db_name] = session

        # Initialize schema and tables for this user if not already done
        if user_db_name not in initialized_users:
            with engine.connect() as conn:
                conn.execution_options(isolation_level="AUTOCOMMIT")
                conn.execute(CreateSchema(config.db_schema, if_not_exists=True))
                conn.commit()

            # Create all tables for the user
            Base.metadata.create_all(bind=engine)
            initialized_users.add(user_db_name)

    # Return a session bound to the user's engine
    db = user_sessions_postgres[user_db_name]()
    try:
        yield db
    finally:
        db.close()
