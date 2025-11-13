"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Validate DATABASE_URL
if not settings.DATABASE_URL:
    # Allow imports to work, but operations will fail with clear error message
    engine = None
    SessionLocal = None
else:
    # Create database engine
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=settings.DEBUG,  # Log SQL queries in debug mode
    )
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Get database session."""
    if not SessionLocal:
        raise ValueError(
            "DATABASE_URL is required. Please set it in .env file.\n"
            "Format: postgresql://username:password@host:port/database_name\n"
            "Example: postgresql://postgres:your_password@localhost:5433/chatbot_db\n"
            "See DATABASE_URL_MAU.txt or HUONG_DAN_TAO_DATABASE.md for more details."
        )
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
