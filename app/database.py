from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import get_settings

settings = get_settings()

# Writer engine (primary) - handles all writes
engine = create_engine(
    settings.db_url,
    pool_pre_ping=True,    # Check connection health before using
    pool_size=10,          # Number of connections to keep open
    max_overflow=20,       # Extra connections if needed
    pool_recycle=3600,     # Recycle connections after 1 hour
    echo=settings.debug,   # Show SQL queries when debugging
    connect_args={
        "options": f"-csearch_path={settings.database_schema},public"
    }
)

# Set schema for each writer connection
@event.listens_for(engine, "connect")
def set_writer_search_path(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute(f"SET search_path TO {settings.database_schema}, public")
    cursor.close()

# Reader engine (replicas) - handles reads only
read_engine = None
if settings.db_read_url:
    read_engine = create_engine(
        settings.db_read_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        echo=settings.debug,
        connect_args={
            "options": f"-csearch_path={settings.database_schema},public"
        }
    )

    # Set schema for read replica connections
    @event.listens_for(read_engine, "connect")
    def set_read_search_path(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute(f"SET search_path TO {settings.database_schema}, public")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ReadSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=read_engine) if read_engine else SessionLocal

Base = declarative_base()
# Set schema for all tables
Base.metadata.schema = settings.database_schema


def get_db() -> Session:
    """
    Get write database session (primary instance).
    Use for INSERT, UPDATE, DELETE operations.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_read_db() -> Session:
    """
    Get read database session (replica instances).
    Use for SELECT queries to reduce load on primary.
    """
    db = ReadSessionLocal()
    try:
        yield db
    finally:
        db.close()


