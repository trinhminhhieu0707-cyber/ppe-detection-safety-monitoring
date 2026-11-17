import time
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class DBWorker(Base):
    """Database record for tracked workers."""
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, unique=True, index=True, nullable=False)
    first_seen = Column(Float, default=time.time)
    last_seen = Column(Float, default=time.time)
    total_frames = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

class DBViolationEvent(Base):
    """Database record for individual PPE safety violation events."""
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(36), unique=True, index=True, nullable=False)
    track_id = Column(Integer, index=True, nullable=False)
    timestamp = Column(Float, default=time.time, index=True)
    violations = Column(String(255), nullable=False)  # Comma-separated violation names
    status = Column(String(20), default="OPEN")       # OPEN, ACKNOWLEDGED, RESOLVED
    snapshot_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class DBCameraStream(Base):
    """Database record for camera/video sources."""
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    source_url = Column(String(255), nullable=False)
    location = Column(String(100), default="Gate 01 - Construction Site")
    is_active = Column(Boolean, default=True)

class DBSystemLog(Base):
    """Audit log for system monitoring events and alerts."""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), default="INFO")
    message = Column(Text, nullable=False)
    timestamp = Column(Float, default=time.time)

