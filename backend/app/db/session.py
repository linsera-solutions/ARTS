import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

engine = None
SessionLocal = None

db_uri = settings.sqlalchemy_database_uri
if db_uri:
    try:
        engine = create_engine(
            db_uri,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    except Exception as e:
        logger.error(f"Failed to initialize database engine: {e}")
        engine = None
        SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a SQLAlchemy database session.
    Ensures sessions are cleanly closed after each request.
    """
    if SessionLocal is None:
        raise RuntimeError(
            "Database connection is not configured. Please set DATABASE_URL in environment."
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
