import cv2
import numpy as np
from typing import List
from src.common.types import Detection, CLASS_COLORS, DEFAULT_COLOR

class PPEVisualizer:
    """Professional OpenCV visualizer for PPE Bounding Boxes and Compliance Badges."""

    def __init__(self, line_thickness: int = 2, font_scale: float = 0.5):
        self.line_thickness = line_thickness
        self.font_scale = font_scale
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def draw_detections(self, image: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """Draw bounding boxes and labels on image copy."""
        annotated = image.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det.box.to_xyxy()
            color = CLASS_COLORS.get(det.class_name, DEFAULT_COLOR)
            
            # Draw primary bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, self.line_thickness)
            
            # Format label
            label = f"{det.class_name} {det.confidence:.2f}"
            if det.track_id is not None:
                label = f"ID:{det.track_id} {label}"
                
            # Compute text size for banner background
            (txt_w, txt_h), baseline = cv2.getTextSize(label, self.font, self.font_scale, 1)
            banner_y1 = max(0, y1 - txt_h - 6)
            banner_y2 = y1
            banner_x2 = min(annotated.shape[1], x1 + txt_w + 8)
            
            # Draw semi-transparent label banner
            cv2.rectangle(annotated, (x1, banner_y1), (banner_x2, banner_y2), color, -1)
            cv2.putText(
                annotated,
                label,
                (x1 + 4, y1 - 4),
                self.font,
                self.font_scale,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )
            
        return annotated

    def draw_hud_summary(self, image: np.ndarray, total_workers: int, violations: int) -> np.ndarray:
        """Draw Heads-Up Display (HUD) banner on top-left of the stream."""
        annotated = image.copy()
        hud_w = 260
        hud_h = 70
        
        # Semi-transparent dark overlay
        sub_img = annotated[10:10+hud_h, 10:10+hud_w]
        dark_rect = np.zeros(sub_img.shape, dtype=np.uint8)
        res = cv2.addWeighted(sub_img, 0.4, dark_rect, 0.6, 1.0)
        annotated[10:10+hud_h, 10:10+hud_w] = res
        
        # Border
        cv2.rectangle(annotated, (10, 10), (10+hud_w, 10+hud_h), (80, 80, 80), 1)
        
        # Text
        cv2.putText(annotated, "PPE MONITORING SYSTEM", (20, 30), self.font, 0.5, (0, 215, 255), 1, cv2.LINE_AA)
        worker_text = f"Workers: {total_workers}"
        violation_color = (41, 41, 231) if violations > 0 else (46, 204, 113)
        violation_text = f"Violations: {violations}"
        
        cv2.putText(annotated, worker_text, (20, 52), self.font, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(annotated, violation_text, (20 + 110, 52), self.font, 0.45, violation_color, 1, cv2.LINE_AA)
        
        return annotated

    def draw_tracked_workers(self, image: np.ndarray, tracks) -> np.ndarray:
        """Draw bounding boxes, persistent IDs, and trajectory paths for tracked workers."""
        annotated = image.copy()
        for track in tracks:
            x1, y1, x2, y2 = track.box.to_xyxy()
            color = (235, 120, 0)
            
            # 1. Draw worker bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, self.line_thickness)
            
            # 2. Draw worker ID badge
            badge_text = f"WORKER #{track.track_id}"
            (tw, th), _ = cv2.getTextSize(badge_text, self.font, self.font_scale, 1)
            cv2.rectangle(annotated, (x1, max(0, y1 - 22)), (x1 + tw + 8, y1), color, -1)
            cv2.putText(
                annotated,
                badge_text,
                (x1 + 4, y1 - 6),
                self.font,
                self.font_scale,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )
            
            # 3. Draw trajectory trail if available
            if hasattr(track, 'trajectory'):
                pts = list(track.trajectory)
                if len(pts) >= 2:
                    for idx in range(1, len(pts)):
                        cv2.line(annotated, pts[idx - 1], pts[idx], (255, 180, 0), 2, cv2.LINE_AA)
                        
            # 4. Draw ground anchor point (feet)
            if hasattr(track, 'bottom_center'):
                cv2.circle(annotated, track.bottom_center, 4, (0, 255, 255), -1)

        return annotated

