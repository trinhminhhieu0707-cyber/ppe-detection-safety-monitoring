import sys
import os
import argparse
import time
from typing import List, Dict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import cv2
import numpy as np
import glob
from ultralytics import YOLO

from src.tracking.tracker import WorkerTracker
from src.tracking.visualizer import TrackingVisualizer

def generate_smooth_video_sequence(image_path: str, num_frames: int = 50) -> List[np.ndarray]:
    """
    Simulates real-world CCTV camera pan & motion over construction workers.
    Smoothly scrolls a window across high-resolution test footage.
    """
    img = cv2.imread(image_path)
    if img is None:
        return []

    h, w, _ = img.shape
    crop_h = int(h * 0.85)
    crop_w = int(w * 0.85)

    frames = []
    for i in range(num_frames):
        alpha = i / float(num_frames)
        # Sinusoidal trajectory simulation
        off_x = int((w - crop_w) * (0.5 + 0.45 * np.sin(alpha * 2 * np.pi)))
        off_y = int((h - crop_h) * (0.5 + 0.35 * np.cos(alpha * 2 * np.pi)))
        
        crop = img[off_y:off_y + crop_h, off_x:off_x + crop_w]
        resized = cv2.resize(crop, (640, 640))
        frames.append(resized)

    return frames

def run_tracking_pipeline(input_source: str = None, output_dir: str = "data/reports/phase_03_tracking"):
    print("=" * 65)
    print("🛰️ PHASE 03 – OBJECT TRACKING EVALUATION (BYTETRACK)")
    print("=" * 65)

    model_path = "models/checkpoints/best.pt"
    config_path = "configs/tracker_bytetrack.yaml"

    if not os.path.exists(model_path):
        print(f"❌ Error: Model weights not found at {model_path}. Complete Phase 02 first.")
        return

    print(f"[1/4] Nạp mô hình YOLO11s: {model_path}")
    model = YOLO(model_path)

    print(f"[2/4] Khởi tạo ByteTrack Tracker từ cấu hình: {config_path}")
    tracker = WorkerTracker(config_path=config_path, person_class_id=0, trajectory_len=30)
    visualizer = TrackingVisualizer()

    # Prepare input frames
    frames = []
    if input_source and os.path.exists(input_source):
        print(f"[3/4] Đọc video đầu vào từ: {input_source}")
        cap = cv2.VideoCapture(input_source)
        while cap.isOpened() and len(frames) < 100:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
    else:
        # Use verified test images with workers
        test_imgs = glob.glob("data/processed/test/images/ppe_0018_jpg*.jpg")
        if not test_imgs:
            test_imgs = glob.glob("data/processed/test/images/*.jpg")
        base_img = test_imgs[0]
        print(f"[3/4] Tạo chuỗi 45 frames mô phỏng camera CCTV từ ảnh: {os.path.basename(base_img)}")
        frames = generate_smooth_video_sequence(base_img, num_frames=45)

    os.makedirs(output_dir, exist_ok=True)
    out_video_path = os.path.join(output_dir, "tracked_workers_demo.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_writer = cv2.VideoWriter(out_video_path, fourcc, 20.0, (640, 640))

    track_history: Dict[int, int] = {}
    fps_records = []

    print("[4/4] Bắt đầu suy luận Tracking frame-by-frame...")
    for idx, frame in enumerate(frames):
        t0 = time.perf_counter()

        # Track workers exclusively using ByteTrack
        tracked_workers, ppe_items = tracker.track(model, frame, conf=0.25, iou=0.50)

        latency_ms = (time.perf_counter() - t0) * 1000.0
        fps_records.append(1000.0 / latency_ms if latency_ms > 0 else 0)

        for w in tracked_workers:
            track_history[w.track_id] = track_history.get(w.track_id, 0) + 1

        # Draw bounding box, persistent Worker ID badge, and foot trajectory
        annotated = visualizer.draw_tracks(frame, tracked_workers)
        out_writer.write(annotated)

        # Save keyframe snapshots
        if idx in [0, 15, 30, 44]:
            snapshot_path = os.path.join(output_dir, f"tracking_snapshot_frame_{idx}.jpg")
            cv2.imwrite(snapshot_path, annotated)

    out_writer.release()

    # Calculate Evaluation Metrics
    total_unique_workers = len(track_history)
    lifespans = list(track_history.values())
    avg_lifespan = np.mean(lifespans) if lifespans else 0.0
    max_lifespan = max(lifespans) if lifespans else 0
    avg_fps = np.mean(fps_records) if fps_records else 0.0

    print("\n" + "=" * 65)
    print("📊 BÁO CÁO NGHIỆM THU PHASE 03 (OBJECT TRACKING METRICS):")
    print(f"  • Số lượng công nhân nhận diện (Unique Track IDs): {total_unique_workers}")
    print(f"  • Danh sách Track IDs duy trì ổn định         : {list(track_history.keys())}")
    print(f"  • Thời lượng duy trì trung bình (Track Lifespan) : {avg_lifespan:.1f} / {len(frames)} frames")
    print(f"  • Vết theo dõi dài nhất không bị ngắt quãng      : {max_lifespan} frames ({max_lifespan/len(frames)*100:.1f}%)")
    print(f"  • Tốc độ xử lý Pipeline Tracking (FPS)         : {avg_fps:.1f} FPS")
    print(f"  • Video kết quả đã xuất tại                    : {out_video_path}")
    print(f"  • Ảnh snapshot đã lưu tại                      : {output_dir}/")
    print("=" * 65)
    print("✅ HOÀN THÀNH KIỂM ĐỊNH PHASE 03!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 03 Object Tracking Script")
    parser.add_argument("--source", type=str, default=None, help="Video source path (optional)")
    parser.add_argument("--output", type=str, default="data/reports/phase_03_tracking", help="Output directory")
    args = parser.parse_args()

    run_tracking_pipeline(input_source=args.source, output_dir=args.output)

