import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "ppe_monitoring.db"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
DEFAULT_SQLITE_URL = f"sqlite:///{DB_PATH}"

# Allows seamless switching between SQLite and MySQL (or PostgreSQL) via DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} # SQLite specific for multi-threaded FastAPI
    )
else:
    # MySQL / MariaDB / PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Creates database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency helper for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

