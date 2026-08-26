from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings
from typing import Generator

connect_args = {}
if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgresql"):
    connect_args["connect_timeout"] = 3

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args
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
