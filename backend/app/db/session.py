from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings
from typing import Generator

# Create the SQLAlchemy database engine
# - For Neon PostgreSQL, we use standard connection pools
# - we pass pool_pre_ping=True to automatically reconnect if the serverless DB goes cold
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)

# Create a sessionmaker factory to instantiate database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for SQLAlchemy models to inherit from
Base = declarative_base()

# FastAPI dependency function to yield a database session
# - Opens a session for the request
# - Automatically closes the session after the request finishes
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
