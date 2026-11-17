import sys, os
sys.path.insert(0, os.getcwd())
from typing import List

import cv2
import numpy as np
import glob
from ultralytics import YOLO

from src.tracking.tracker import WorkerTracker
from src.tracking.visualizer import TrackingVisualizer

def generate_synthetic_tracking_clip(base_image_path: str, num_frames: int = 40) -> List[np.ndarray]:
    """Generates a continuous synthetic video clip by panning across a high-res image."""
    base_img = cv2.imread(base_image_path)
    if base_img is None:
        return []

    h, w, _ = base_img.shape
    crop_w, crop_h = int(w * 0.85), int(h * 0.85)

    frames = []
    # Pan horizontally and vertically smoothly
    for i in range(num_frames):
        t = i / float(num_frames)
        # Sinusoidal pan offset
        offset_x = int((w - crop_w) * (0.5 + 0.4 * np.sin(t * np.pi)))
        offset_y = int((h - crop_h) * (0.5 + 0.3 * np.cos(t * np.pi)))

        cropped = base_img[offset_y:offset_y + crop_h, offset_x:offset_x + crop_w]
        frame = cv2.resize(cropped, (640, 640))
        frames.append(frame)

    return frames

def evaluate_tracking_performance():
    print("=" * 65)
    print("🛰️ PHASE 03: BYTETRACK OBJECT TRACKING BENCHMARK & EVALUATION")
    print("=" * 65)

    model_path = "models/checkpoints/best.pt"
    if not os.path.exists(model_path):
        print(f"❌ Error: Model weights not found at {model_path}")
        return

    print(f"[1/3] Loading YOLO11s model from {model_path}...")
    model = YOLO(model_path)

    print("[2/3] Initializing WorkerTracker with ByteTrack config...")
    tracker = WorkerTracker(config_path="configs/tracker_bytetrack.yaml")
    visualizer = TrackingVisualizer()

    # Find test image with persons
    sample_images = glob.glob("data/processed/test/images/ppe_0018_jpg*.jpg")
    if not sample_images:
        sample_images = glob.glob("data/processed/test/images/*.jpg")
    
    test_img_path = sample_images[0]
    print(f"  -> Using base image: {os.path.basename(test_img_path)}")

    # Generate synthetic video clip (40 frames simulating CCTV motion)
    frames = generate_synthetic_tracking_clip(test_img_path, num_frames=35)
    print(f"  -> Generated {len(frames)} frames for tracking stability test.")

    out_dir = "data/reports/tracking_evaluation"
    os.makedirs(out_dir, exist_ok=True)

    track_id_lifespans = {}
    total_detections_count = 0

    print("[3/3] Running ByteTrack inference over video sequence...")
    for f_idx, frame in enumerate(frames):
        # Run tracking directly
        tracked_workers, ppe_detections = tracker.track(model, frame, conf=0.25, iou=0.50)
        total_detections_count += len(tracked_workers)

        for w in tracked_workers:
            track_id_lifespans[w.track_id] = track_id_lifespans.get(w.track_id, 0) + 1

        # Draw tracking visualization
        annotated = visualizer.draw_tracks(frame, tracked_workers)
        
        # Save sample keyframes
        if f_idx in [0, 10, 20, 30]:
            cv2.imwrite(f"{out_dir}/track_frame_{f_idx}.jpg", annotated)

    # Compute Tracking Metrics
    unique_ids = list(track_id_lifespans.keys())
    mean_duration = np.mean(list(track_id_lifespans.values())) if unique_ids else 0.0
    longest_track = max(track_id_lifespans.values()) if unique_ids else 0

    print("\n" + "=" * 65)
    print("📈 TRACKING EVALUATION METRICS:")
    print(f"  - Total Unique Worker IDs Assigned: {len(unique_ids)}")
    print(f"  - Active Track IDs Observed       : {unique_ids}")
    print(f"  - Mean Track Duration (Frames)    : {mean_duration:.1f} frames / {len(frames)} frames")
    print(f"  - Longest Continuous Track        : {longest_track} frames")
    print(f"  - Track Continuity Ratio          : {(mean_duration / len(frames))*100:.1f}%")
    print(f"  - Sample Visualizations Saved to  : {out_dir}/")
    print("=" * 65)
    print("✅ PHASE 03 OBJECT TRACKING COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    from typing import List
    evaluate_tracking_performance()

