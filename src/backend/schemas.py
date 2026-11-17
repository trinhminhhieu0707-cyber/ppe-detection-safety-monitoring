from pydantic import BaseModel, Field
from typing import List, Optional

class ViolationEventResponse(BaseModel):
    event_id: str
    track_id: int
    timestamp: float
    violations: List[str]
    status: str
    snapshot_path: Optional[str] = None

    class Config:
        from_attributes = True

class WorkerResponse(BaseModel):
    track_id: int
    first_seen: float
    last_seen: float
    total_frames: int
    is_active: bool

    class Config:
        from_attributes = True

class ViolationStatusUpdate(BaseModel):
    status: str = Field(..., description="Target status: OPEN, ACKNOWLEDGED, RESOLVED")

class CameraCreate(BaseModel):
    camera_id: str
    name: str
    source_url: str
    location: Optional[str] = "Main Site Gate"

class CameraResponse(BaseModel):
    camera_id: str
    name: str
    source_url: str
    location: str
    is_active: bool

    class Config:
        from_attributes = True

class SystemSummaryResponse(BaseModel):
    total_unique_workers: int
    total_logged_violations: int
    active_open_violations: int
    compliance_rate: float

