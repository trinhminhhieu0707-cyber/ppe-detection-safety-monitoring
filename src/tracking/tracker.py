import os
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Deque
from collections import deque
import numpy as np

from src.common.types import Detection, BoundingBox

@dataclass
class TrackedPerson:
    """Represents an actively tracked construction worker across consecutive frames."""
    track_id: int
    box: BoundingBox
    confidence: float
    trajectory: Deque[Tuple[int, int]] = field(default_factory=lambda: deque(maxlen=30))
    frames_since_update: int = 0
    total_frames_tracked: int = 1

    @property
    def bottom_center(self) -> Tuple[int, int]:
        """Ground contact point (feet) for accurate trajectory and spatial tracking."""
        return (int((self.box.x1 + self.box.x2) / 2.0), int(self.box.y2))


class WorkerTracker:
    """Production Multi-Object Tracking Engine based on ByteTrack for construction workers."""

    def __init__(
        self,
        config_path: str = "configs/tracker_bytetrack.yaml",
        person_class_id: int = 0,
        trajectory_len: int = 30
    ):
        self.config_path = config_path
        self.person_class_id = person_class_id
        self.trajectory_len = trajectory_len
        self.active_tracks: Dict[int, TrackedPerson] = {}
        
        # Verify tracker config
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Tracker configuration file not found at: {config_path}")

    def track(
        self,
        model,
        frame: np.ndarray,
        conf: float = 0.25,
        iou: float = 0.50
    ) -> Tuple[List[TrackedPerson], List[Detection]]:
        """
        Runs dual-stream architecture:
        1. Full-spectrum detection for all PPE classes.
        2. High-precision ByteTrack tracking exclusively on Person (Class 0).
        """
        # 1. Full detection for all objects
        pred_results = model.predict(source=frame, conf=conf, iou=iou, verbose=False)
        all_boxes = pred_results[0].boxes if pred_results and len(pred_results) > 0 else []

        # 2. Track workers exclusively using ByteTrack
        track_results = model.track(
            source=frame,
            persist=True,
            classes=[self.person_class_id],
            conf=conf,
            iou=iou,
            tracker=self.config_path,
            verbose=False
        )

        tracked_workers: List[TrackedPerson] = []
        current_frame_ids = set()

        if track_results and len(track_results) > 0 and track_results[0].boxes is not None:
            t_boxes = track_results[0].boxes
            for i in range(len(t_boxes)):
                xyxy = t_boxes.xyxy[i].cpu().numpy()
                conf_val = float(t_boxes.conf[i].cpu().numpy())
                track_id = int(t_boxes.id[i].cpu().numpy()) if t_boxes.id is not None else (i + 1)
                current_frame_ids.add(track_id)

                box = BoundingBox(float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3]))

                if track_id in self.active_tracks:
                    track = self.active_tracks[track_id]
                    track.box = box
                    track.confidence = conf_val
                    track.frames_since_update = 0
                    track.total_frames_tracked += 1
                    track.trajectory.append(track.bottom_center)
                else:
                    track = TrackedPerson(
                        track_id=track_id,
                        box=box,
                        confidence=conf_val,
                        trajectory=deque(maxlen=self.trajectory_len)
                    )
                    track.trajectory.append(track.bottom_center)
                    self.active_tracks[track_id] = track

                tracked_workers.append(self.active_tracks[track_id])

        # 3. Separate non-person PPE detections
        other_detections: List[Detection] = []
        if all_boxes is not None and len(all_boxes) > 0:
            names = pred_results[0].names
            for i in range(len(all_boxes)):
                cls_id = int(all_boxes.cls[i].cpu().numpy())
                if cls_id != self.person_class_id:
                    xyxy = all_boxes.xyxy[i].cpu().numpy()
                    c_val = float(all_boxes.conf[i].cpu().numpy())
                    other_detections.append(Detection(
                        box=BoundingBox(float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])),
                        confidence=c_val,
                        class_id=cls_id,
                        class_name=names.get(cls_id, f"Class_{cls_id}")
                    ))

        # Cleanup lost worker tracks
        stale_ids = [tid for tid in self.active_tracks if tid not in current_frame_ids]
        for tid in stale_ids:
            self.active_tracks[tid].frames_since_update += 1
            if self.active_tracks[tid].frames_since_update > 45:
                del self.active_tracks[tid]

        return tracked_workers, other_detections

    def update_from_ultralytics(
        self,
        yolo_track_results
    ) -> Tuple[List[TrackedPerson], List[Detection]]:
        """
        Parses results from YOLO's native ByteTrack integration (model.track).
        Extracts tracked workers with persistent IDs and separates non-person PPE detections.
        """
        tracked_workers: List[TrackedPerson] = []
        other_detections: List[Detection] = []
        
        if not yolo_track_results or len(yolo_track_results) == 0:
            return tracked_workers, other_detections
            
        boxes = yolo_track_results[0].boxes
        if boxes is None or len(boxes) == 0:
            return tracked_workers, other_detections

        names = yolo_track_results[0].names
        current_frame_ids = set()

        for i in range(len(boxes)):
            xyxy = boxes.xyxy[i].cpu().numpy()
            conf = float(boxes.conf[i].cpu().numpy())
            cls_id = int(boxes.cls[i].cpu().numpy())
            cls_name = names.get(cls_id, f"Class_{cls_id}")
            
            box = BoundingBox(
                x1=float(xyxy[0]),
                y1=float(xyxy[1]),
                x2=float(xyxy[2]),
                y2=float(xyxy[3])
            )
            
            track_id = int(boxes.id[i].cpu().numpy()) if boxes.id is not None else None
            
            # If target is Person with a valid track ID
            if cls_id == self.person_class_id and track_id is not None:
                current_frame_ids.add(track_id)
                if track_id in self.active_tracks:
                    # Update existing track
                    track = self.active_tracks[track_id]
                    track.box = box
                    track.confidence = conf
                    track.frames_since_update = 0
                    track.total_frames_tracked += 1
                    track.trajectory.append(track.bottom_center)
                else:
                    # Initialize new track
                    track = TrackedPerson(
                        track_id=track_id,
                        box=box,
                        confidence=conf,
                        trajectory=deque(maxlen=self.trajectory_len)
                    )
                    track.trajectory.append(track.bottom_center)
                    self.active_tracks[track_id] = track
                    
                tracked_workers.append(self.active_tracks[track_id])
            else:
                # Other PPE items or untracked objects
                other_detections.append(Detection(
                    box=box,
                    confidence=conf,
                    class_id=cls_id,
                    class_name=cls_name,
                    track_id=track_id
                ))

        # Cleanup lost tracks
        stale_ids = [tid for tid in self.active_tracks if tid not in current_frame_ids]
        for tid in stale_ids:
            self.active_tracks[tid].frames_since_update += 1
            if self.active_tracks[tid].frames_since_update > 45: # Buffer limit
                del self.active_tracks[tid]

        return tracked_workers, other_detections

    def get_track_count(self) -> int:
        """Returns the count of currently active worker tracks."""
        return len(self.active_tracks)

    def reset(self) -> None:
        """Resets all active tracks (e.g., when switching video stream)."""
        self.active_tracks.clear()

