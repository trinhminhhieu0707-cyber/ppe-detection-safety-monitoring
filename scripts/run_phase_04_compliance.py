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
from src.compliance.engine import PPEComplianceEngine, ComplianceStatus
from src.common.visualizer import PPEVisualizer

def generate_test_video_sequence(image_path: str, num_frames: int = 30) -> List[np.ndarray]:
    """
    Simulates real-world stationary CCTV camera stream with realistic
    environmental lighting fluctuation and subtle micro-jitter vibrations.
    """
    img = cv2.imread(image_path)
    if img is None:
        return []
    h, w, _ = img.shape

    frames = []
    for i in range(num_frames):
        # Subtle CCTV jitter (+- 3 pixels)
        dx = int(3 * np.sin(i * 0.4))
        dy = int(2 * np.cos(i * 0.4))
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        jittered = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)
        
        # Subtle illumination fluctuation
        gain = 1.0 + 0.02 * np.sin(i * 0.2)
        frame_aug = cv2.convertScaleAbs(jittered, alpha=gain, beta=0)
        frames.append(frame_aug)
    return frames

def run_compliance_evaluation(input_source: str = None, output_dir: str = "data/reports/phase_04_compliance"):
    print("=" * 70)
    print("🛡️ PHASE 04 – PPE COMPLIANCE ENGINE EVALUATION")
    print("=" * 70)

    model_path = "models/checkpoints/best.pt"
    rules_path = "configs/compliance_rules.yaml"

    if not os.path.exists(model_path):
        print(f"❌ Error: Model weights not found at {model_path}. Complete Phase 02 first.")
        return

    print(f"[1/4] Nạp mô hình YOLO11s: {model_path}")
    model = YOLO(model_path)

    print(f"[2/4] Khởi tạo Tracker (ByteTrack) và Compliance Engine (Quy tắc: {rules_path})...")
    tracker = WorkerTracker(config_path="configs/tracker_bytetrack.yaml")
    compliance_engine = PPEComplianceEngine(config_path=rules_path)
    visualizer = PPEVisualizer()

    # Load input frames
    frames = []
    if input_source and os.path.exists(input_source):
        # Check if input is a video file or an image
        if input_source.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            print(f"[3/4] Đọc video từ: {input_source}")
            cap = cv2.VideoCapture(input_source)
            while cap.isOpened() and len(frames) < 100:
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
            cap.release()
        else:
            print(f"[3/4] Đọc ảnh đầu vào: {os.path.basename(input_source)} -> Tạo chuỗi 35 frames kiểm thử đa khung hình.")
            frames = generate_test_video_sequence(input_source, num_frames=35)
    else:
        test_imgs = glob.glob("data/processed/test/images/youtube-126*.jpg")
        if not test_imgs:
            test_imgs = glob.glob("data/processed/test/images/*.jpg")
        base_img = test_imgs[0]
        print(f"[3/4] Tạo chuỗi 35 frames kiểm thử từ ảnh: {os.path.basename(base_img)}")
        frames = generate_test_video_sequence(base_img, num_frames=35)

    os.makedirs(output_dir, exist_ok=True)
    out_video_path = os.path.join(output_dir, "compliance_monitoring_demo.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_h, out_w = frames[0].shape[:2]
    out_writer = cv2.VideoWriter(out_video_path, fourcc, 20.0, (out_w, out_h))

    all_emitted_events = []
    status_summary: Dict[int, str] = {}
    violations_by_type: Dict[str, int] = {}
    transient_glitches_filtered = 0

    print("[4/4] Bắt đầu phân tích liên kết giải phẫu và lọc rung vi phạm đa khung hình...")
    for idx, frame in enumerate(frames):
        # Step 1: Detect and Track
        tracked_workers, ppe_detections = tracker.track(model, frame, conf=0.20, iou=0.50)

        # Step 2: Compliance Logic (Spatial Partitioning + Temporal Voting)
        worker_states, new_events = compliance_engine.process_frame(tracked_workers, ppe_detections)

        for event in new_events:
            all_emitted_events.append(event)
            print(f"  🚨 Frame {idx+1:02d}: PHÁT HIỆN VI PHẠM - Worker #{event.track_id} -> {event.violations}")
            for v in event.violations:
                violations_by_type[v] = violations_by_type.get(v, 0) + 1

        # Step 3: Draw compliance badges on frame
        annotated = frame.copy()
        for state in worker_states:
            status_summary[state.track_id] = state.status.value
            x1, y1, x2, y2 = state.box.to_xyxy()
            
            # Green if Compliant, Red if Non-Compliant
            badge_color = (46, 204, 113) if state.status == ComplianceStatus.COMPLIANT else (41, 41, 231)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), badge_color, 2)
            
            status_text = f"WORKER #{state.track_id}: {state.status.value}"
            if state.active_violations:
                status_text += f" ({', '.join(state.active_violations)})"

            (tw, th), _ = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(annotated, (x1, max(0, y1 - 20)), (x1 + tw + 6, y1), badge_color, -1)
            cv2.putText(annotated, status_text, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        # Draw HUD summary banner
        annotated = visualizer.draw_hud_summary(annotated, total_workers=len(tracked_workers), violations=len(all_emitted_events))
        out_writer.write(annotated)

        # Save sample keyframes
        if idx in [0, 15, 30, 44]:
            snapshot_path = os.path.join(output_dir, f"compliance_frame_{idx}.jpg")
            cv2.imwrite(snapshot_path, annotated)

    out_writer.release()

    # Metrics Summary
    compliant_workers = sum(1 for s in status_summary.values() if s == "COMPLIANT")
    non_compliant_workers = sum(1 for s in status_summary.values() if s == "NON_COMPLIANT")

    print("\n" + "=" * 70)
    print("📊 BÁO CÁO NGHIỆM THU PHASE 04 (PPE COMPLIANCE METRICS):")
    print(f"  • Tổng số công nhân được kiểm tra trạng thái : {len(status_summary)}")
    print(f"  • Số công nhân Tuân thủ đầy đủ (COMPLIANT)   : {compliant_workers}")
    print(f"  • Số công nhân Vi phạm (NON-COMPLIANT)       : {non_compliant_workers}")
    print(f"  • Chi tiết các sự kiện vi phạm được ghi nhận: {violations_by_type}")
    print(f"  • Tổng số sự kiện vi phạm chính thức (Events): {len(all_emitted_events)}")
    print(f"  • Video bằng chứng kiểm định đã lưu tại      : {out_video_path}")
    print(f"  • Ảnh chụp keyframes đã lưu tại              : {output_dir}/")
    print("=" * 70)
    print("✅ HOÀN THÀNH KIỂM ĐỊNH PHASE 04!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 04 PPE Compliance Engine Script")
    parser.add_argument("--source", type=str, default=None, help="Video source path (optional)")
    parser.add_argument("--output", type=str, default="data/reports/phase_04_compliance", help="Output directory")
    args = parser.parse_args()

    run_compliance_evaluation(input_source=args.source, output_dir=args.output)
