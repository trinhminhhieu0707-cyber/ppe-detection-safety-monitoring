import time
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import DBWorker, DBViolationEvent, DBSystemLog, DBCameraStream

def get_all_workers(db: Session, limit: int = 100, active_only: bool = False) -> List[DBWorker]:
    """Returns tracked workers."""
    query = db.query(DBWorker)
    if active_only:
        query = query.filter(DBWorker.is_active == True)
    return query.order_by(DBWorker.last_seen.desc()).limit(limit).all()

def add_camera(
    db: Session,
    camera_id: str,
    name: str,
    source_url: str,
    location: str = "Main Construction Gate"
) -> DBCameraStream:
    """Registers a new camera or video stream source."""
    cam = db.query(DBCameraStream).filter(DBCameraStream.camera_id == camera_id).first()
    if cam:
        cam.name = name
        cam.source_url = source_url
        cam.location = location
        cam.is_active = True
    else:
        cam = DBCameraStream(
            camera_id=camera_id,
            name=name,
            source_url=source_url,
            location=location,
            is_active=True
        )
        db.add(cam)
    db.commit()
    db.refresh(cam)
    return cam

def get_cameras(db: Session) -> List[DBCameraStream]:
    """Returns registered cameras."""
    return db.query(DBCameraStream).all()

def get_or_create_worker(db: Session, track_id: int) -> DBWorker:
    """Retrieves an existing worker by track_id or creates a new record."""
    worker = db.query(DBWorker).filter(DBWorker.track_id == track_id).first()
    if not worker:
        worker = DBWorker(track_id=track_id, first_seen=time.time(), last_seen=time.time())
        db.add(worker)
        db.commit()
        db.refresh(worker)
    else:
        worker.last_seen = time.time()
        worker.total_frames += 1
        worker.is_active = True
        db.commit()
    return worker

def log_violation_event(
    db: Session,
    event_id: str,
    track_id: int,
    violations: List[str],
    snapshot_path: Optional[str] = None
) -> DBViolationEvent:
    """Logs a new violation event into database if not already present."""
    existing = db.query(DBViolationEvent).filter(DBViolationEvent.event_id == event_id).first()
    if existing:
        return existing

    event = DBViolationEvent(
        event_id=event_id,
        track_id=track_id,
        timestamp=time.time(),
        violations=",".join(violations),
        status="OPEN",
        snapshot_path=snapshot_path
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def get_active_violations(db: Session) -> List[DBViolationEvent]:
    """Returns all currently open violations."""
    return db.query(DBViolationEvent).filter(DBViolationEvent.status == "OPEN").order_by(DBViolationEvent.timestamp.desc()).all()

def get_all_violations(db: Session, limit: int = 100) -> List[DBViolationEvent]:
    """Returns historical violation events."""
    return db.query(DBViolationEvent).order_by(DBViolationEvent.timestamp.desc()).limit(limit).all()

def update_violation_status(db: Session, event_id: str, status: str) -> Optional[DBViolationEvent]:
    """Updates the status of a violation (e.g. ACKNOWLEDGED, RESOLVED)."""
    event = db.query(DBViolationEvent).filter(DBViolationEvent.event_id == event_id).first()
    if event:
        event.status = status
        db.commit()
        db.refresh(event)
    return event

def get_system_summary(db: Session) -> Dict:
    """Aggregates high-level safety statistics for dashboard."""
    total_workers = db.query(func.count(DBWorker.id)).scalar() or 0
    total_violations = db.query(func.count(DBViolationEvent.id)).scalar() or 0
    open_violations = db.query(func.count(DBViolationEvent.id)).filter(DBViolationEvent.status == "OPEN").scalar() or 0

    return {
        "total_unique_workers": total_workers,
        "total_logged_violations": total_violations,
        "active_open_violations": open_violations,
        "compliance_rate": round(
            max(0.0, 100.0 - (open_violations / total_workers * 100.0)) if total_workers > 0 else 100.0,
            1
        )
    }

