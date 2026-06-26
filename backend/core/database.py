from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.core.config import DATABASE_URL

# Create PostgreSQL engine with automatic SQLite fallback
try:
    # Use a short timeout for the connection test if possible, or just attempt connection
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )
    # Test the connection to ensure PostgreSQL is actually up and running
    with engine.connect() as conn:
        pass
    print("Database: Connected to PostgreSQL successfully.")
except Exception as e:
    import os
    from backend.core.config import BASE_DIR
    sqlite_path = os.path.join(BASE_DIR, "chronoiks_ai.db")
    print(f"Database Warning: PostgreSQL connection failed ({e}). Falling back to local SQLite at {sqlite_path}.")
    sqlite_url = f"sqlite:///{sqlite_path}"
    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False}
    )

# Create local session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for DB models
Base = declarative_base()

def get_db():
    """Dependency injector for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
