import os
import sys

# Ensure project root directory is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import time
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.database.session import init_db, get_db
from src.database import crud
from src.backend.schemas import (
    ViolationEventResponse,
    WorkerResponse,
    ViolationStatusUpdate,
    SystemSummaryResponse,
    CameraCreate,
    CameraResponse
)

# Initialize database tables on app startup
init_db()

app = FastAPI(
    title="PPE Safety Monitoring REST API",
    description="Enterprise API for Construction Site PPE Compliance & Worker Tracking",
    version="1.0.0"
)

# Enable CORS for Streamlit / Web UI clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "HEALTHY", "timestamp": time.time(), "system": "PPE Detection Backend"}

@app.get("/api/v1/summary", response_model=SystemSummaryResponse, tags=["Analytics"])
def get_summary(db: Session = Depends(get_db)):
    """Returns aggregated site safety and compliance KPIs."""
    return crud.get_system_summary(db)

@app.get("/api/v1/violations", response_model=List[ViolationEventResponse], tags=["Violations"])
def list_violations(
    status: str = Query("ALL", description="Filter by status: ALL, OPEN, RESOLVED"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Lists recorded PPE safety violation events."""
    if status == "OPEN":
        events = crud.get_active_violations(db)
    else:
        events = crud.get_all_violations(db, limit=limit)

    return [
        ViolationEventResponse(
            event_id=e.event_id,
            track_id=e.track_id,
            timestamp=e.timestamp,
            violations=e.violations.split(",") if e.violations else [],
            status=e.status,
            snapshot_path=e.snapshot_path
        )
        for e in events
    ]

@app.patch("/api/v1/violations/{event_id}/status", response_model=ViolationEventResponse, tags=["Violations"])
def update_violation_status(
    event_id: str,
    update_data: ViolationStatusUpdate,
    db: Session = Depends(get_db)
):
    """Updates status of a specific violation (e.g. ACKNOWLEDGED, RESOLVED)."""
    valid_statuses = {"OPEN", "ACKNOWLEDGED", "RESOLVED"}
    if update_data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    updated = crud.update_violation_status(db, event_id, update_data.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Violation event not found")

    return ViolationEventResponse(
        event_id=updated.event_id,
        track_id=updated.track_id,
        timestamp=updated.timestamp,
        violations=updated.violations.split(",") if updated.violations else [],
        status=updated.status,
        snapshot_path=updated.snapshot_path
    )

@app.get("/api/v1/workers", response_model=List[WorkerResponse], tags=["Workers"])
def list_workers(
    active_only: bool = Query(False, description="Filter only currently active workers"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Lists tracked construction workers with their persistent track IDs."""
    workers = crud.get_all_workers(db, limit=limit, active_only=active_only)
    return [
        WorkerResponse(
            track_id=w.track_id,
            first_seen=w.first_seen,
            last_seen=w.last_seen,
            total_frames=w.total_frames,
            is_active=w.is_active
        )
        for w in workers
    ]

@app.post("/api/v1/cameras", response_model=CameraResponse, tags=["Cameras"])
def register_camera(
    cam_data: CameraCreate,
    db: Session = Depends(get_db)
):
    """Registers or updates a CCTV / RTSP camera stream."""
    return crud.add_camera(
        db,
        camera_id=cam_data.camera_id,
        name=cam_data.name,
        source_url=cam_data.source_url,
        location=cam_data.location or "Site Area"
    )

@app.get("/api/v1/cameras", response_model=List[CameraResponse], tags=["Cameras"])
def list_cameras(db: Session = Depends(get_db)):
    """Lists all registered cameras and RTSP streams."""
    return crud.get_cameras(db)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.backend.app:app", host="0.0.0.0", port=8000, reload=True)

