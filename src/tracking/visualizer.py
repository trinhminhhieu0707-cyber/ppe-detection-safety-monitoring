import cv2
import numpy as np
from typing import List
from src.tracking.tracker import TrackedPerson

class TrackingVisualizer:
    """Specialized visualizer for Multi-Object Tracking IDs and worker trajectories."""

    def __init__(self, trace_color=(255, 180, 0), trace_thickness=2):
        self.trace_color = trace_color
        self.trace_thickness = trace_thickness
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def draw_tracks(self, image: np.ndarray, tracks: List[TrackedPerson]) -> np.ndarray:
        """Draw bounding boxes, persistent IDs, and trajectory paths on frame."""
        annotated = image.copy()
        
        for track in tracks:
            x1, y1, x2, y2 = track.box.to_xyxy()
            color = (235, 120, 0) # High-contrast blue for Person
            
            # 1. Draw worker bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # 2. Draw worker ID badge
            badge_text = f"WORKER #{track.track_id}"
            (tw, th), _ = cv2.getTextSize(badge_text, self.font, 0.5, 1)
            cv2.rectangle(annotated, (x1, max(0, y1 - 22)), (x1 + tw + 8, y1), color, -1)
            cv2.putText(
                annotated,
                badge_text,
                (x1 + 4, y1 - 6),
                self.font,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )
            
            # 3. Draw movement trajectory
            pts = list(track.trajectory)
            if len(pts) >= 2:
                for idx in range(1, len(pts)):
                    alpha = idx / len(pts)
                    thickness = max(1, int(self.trace_thickness * alpha))
                    cv2.line(annotated, pts[idx - 1], pts[idx], self.trace_color, thickness, cv2.LINE_AA)
                    
            # 4. Draw ground anchor point (feet)
            cv2.circle(annotated, track.bottom_center, 4, (0, 255, 255), -1)

        return annotated

