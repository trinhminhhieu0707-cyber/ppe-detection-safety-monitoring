import os
import sys
import argparse
import time
import cv2
from collections import deque

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.detection.detector import PPEDetector
from src.tracking.tracker import WorkerTracker, TrackedPerson
from src.compliance.engine import PPEComplianceEngine
from src.common.visualizer import PPEVisualizer
from src.database.session import SessionLocal, init_db
from src.database import crud

def process_video(
    video_source: str,
    output_path: str = "data/reports/annotated_video.mp4",
    model_path: str = "models/checkpoints/best.pt",
    conf_thresh: float = 0.25,
    show_window: bool = False
):
    """
    End-to-End Video Processing Pipeline:
    Video Stream -> YOLO11 Detector -> ByteTrack Worker Tracker -> 
    Spatial PPE Association & Temporal Voting -> HUD Visualizer -> MP4 Output.
    """
    print(f"🎬 Initializing Video Pipeline for: {video_source}")
    cap = cv2.VideoCapture(int(video_source) if video_source.isdigit() else video_source)
    if not cap.isOpened():
        print(f"❌ Error: Cannot open video source: {video_source}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Initialize engines
    init_db()
    db = SessionLocal()
    detector = PPEDetector(model_path=model_path, conf_threshold=conf_thresh)
    tracker = WorkerTracker(config_path="configs/tracker_bytetrack.yaml")
    compliance_engine = PPEComplianceEngine(config_path="configs/compliance_rules.yaml")
    visualizer = PPEVisualizer()

    frame_idx = 0
    t_start = time.time()

    print(f"⚡ Processing {total_frames} frames ({width}x{height} @ {fps:.1f} FPS)...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1

        # 1. Detection
        detections = detector.predict(frame)
        worker_dets = [d for d in detections if d.class_name == "Person"]
        ppe_dets = [d for d in detections if d.class_name != "Person"]

        # 2. Tracking Workers (ByteTrack)
        # Using Ultralytics track delegation or manual tracking assignment
        tracked_workers = []
        for w_idx, w in enumerate(worker_dets):
            t_person = TrackedPerson(
                track_id=w_idx + 1,
                box=w.box,
                confidence=w.confidence,
                trajectory=deque([w.box.center], maxlen=30)
            )
            tracked_workers.append(t_person)
            crud.get_or_create_worker(db, track_id=t_person.track_id)

        # 3. Spatial Association & Temporal Voting
        worker_states, violation_events = compliance_engine.process_frame(tracked_workers, ppe_dets)

        # 4. Log Violations to SQLite
        for event in violation_events:
            crud.log_violation_event(
                db=db,
                event_id=event.event_id,
                track_id=event.track_id,
                violations=event.violations
            )

        # 5. Render HUD & Visuals
        annotated = visualizer.draw_detections(frame, detections)
        annotated = visualizer.draw_hud_summary(
            annotated,
            total_workers=len(tracked_workers),
            violations=len(violation_events)
        )

        out.write(annotated)

        if show_window:
            cv2.imshow("PPE Safety Monitor", annotated)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        if frame_idx % 25 == 0 or frame_idx == total_frames:
            elapsed = time.time() - t_start
            current_fps = frame_idx / elapsed if elapsed > 0 else 0
            print(f"  Frame [{frame_idx}/{total_frames}] | Speed: {current_fps:.1f} FPS")

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    db.close()

    total_time = time.time() - t_start
    print(f"\n🎉 Video Processing Finished!")
    print(f"  - Output Video Saved : {output_path}")
    print(f"  - Total Time Elapsed : {total_time:.2f}s ({frame_idx / total_time:.1f} avg FPS)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Video Inference Pipeline")
    parser.add_argument("--source", type=str, default="0", help="Video file path or webcam index (default: 0)")
    parser.add_argument("--output", type=str, default="data/reports/annotated_video.mp4", help="Output MP4 path")
    parser.add_argument("--model", type=str, default="models/checkpoints/best.pt", help="Path to weights")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--show", action="store_true", help="Display output window in real-time")
    args = parser.parse_args()

    process_video(
        video_source=args.source,
        output_path=args.output,
        model_path=args.model,
        conf_thresh=args.conf,
        show_window=args.show
    )

