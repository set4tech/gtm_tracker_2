import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

# Create base class for models
Base = declarative_base()

# Lazy initialization of engine and session
_engine = None
_SessionLocal = None

def get_database_url():
    """Get database URL from environment variables"""
    # Try DATABASE_URL first, then fall back to Neon-provided variables
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("POSTGRES_URL_NO_SSL")

    # For Vercel Postgres/Neon, ensure the connection string is properly formatted
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url

def get_engine():
    """Get or create database engine (lazy initialization)"""
    global _engine
    if _engine is None:
        db_url = get_database_url()
        if not db_url:
            raise ValueError("No database URL configured")
        _engine = create_engine(
            db_url,
            poolclass=NullPool,
            echo=False
        )
    return _engine

def get_session_local():
    """Get or create session factory (lazy initialization)"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

def get_db():
    """
    Dependency function to get database session.
    Use this in FastAPI endpoints with Depends(get_db)
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database - create all tables.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
