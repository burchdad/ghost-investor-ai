"""Database connection and session management."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from .config import settings

# Database setup with environment-aware configuration
if settings.environment == "production":
    # Production: Use QueuePool for connection pooling with larger limits
    engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=20,  # Larger pool for production
        max_overflow=40,  # Allow overflow connections
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=False,  # Disable query logging for performance
    )
else:
    # Development: Use NullPool for simpler connection handling
    engine = create_engine(
        settings.database_url,
        poolclass=NullPool if settings.environment == "testing" else QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=settings.debug,  # Log queries in development
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Connection pool event listeners
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Configure connection on creation."""
    if settings.environment == "production":
        # Set connection timeout for production
        if hasattr(dbapi_conn, 'connection'):
            dbapi_conn.connection.set_client_encoding('UTF8')


def get_db() -> Session:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
