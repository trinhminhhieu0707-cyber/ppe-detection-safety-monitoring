import os
import sys
import cv2
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def generate_pan_frames(img: np.ndarray, num_frames: int = 50, out_w: int = 1280, out_h: int = 720):
    """Generates smooth CCTV pan & slight zoom frames from a high-resolution image."""
    h, w, _ = img.shape
    # Ensure aspect ratio compatible crop window (85% of image)
    target_aspect = out_w / out_h
    if w / h > target_aspect:
        crop_h = int(h * 0.85)
        crop_w = int(crop_h * target_aspect)
    else:
        crop_w = int(w * 0.85)
        crop_h = int(crop_w / target_aspect)

    crop_w = min(crop_w, w)
    crop_h = min(crop_h, h)

    frames = []
    max_x = max(0, w - crop_w)
    max_y = max(0, h - crop_h)

    for i in range(num_frames):
        t = i / max(1, num_frames - 1)
        # Smooth ease-in-out horizontal & subtle vertical pan
        smooth_t = 0.5 - 0.5 * np.cos(t * np.pi)
        off_x = int(max_x * smooth_t)
        off_y = int(max_y * (0.5 + 0.3 * np.sin(t * np.pi)))

        crop = img[off_y:off_y + crop_h, off_x:off_x + crop_w]
        resized = cv2.resize(crop, (out_w, out_h), interpolation=cv2.INTER_AREA)
        frames.append(resized)

    return frames

def create_raw_demo_video(output_path: str = "data/demo/raw_construction_demo.mp4"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    test_img_dir = os.path.join(PROJECT_ROOT, "data", "processed", "test", "images")

    # Selected high-res clean test scenes (Compliant, Non-Compliant, Mixed)
    scene_files = [
        "ppe_1073_jpg.rf.92536fa1d42874966bc7622b6f87290a.jpg",      # Compliant workers
        "ka_01181_png_jpg.rf.9c3964077521e121d1bc9b552af45413.jpg",  # Non-compliant (No-Hardhat, No-Vest)
        "NX_img_177_jpg.rf.96ecd1df106d0d0386ff1f8f03877833.jpg"     # Mixed scene
    ]

    all_scene_frames = []
    for fname in scene_files:
        fpath = os.path.join(test_img_dir, fname)
        if os.path.exists(fpath):
            # Support Unicode Windows paths reliably with np.fromfile + imdecode
            img = cv2.imdecode(np.fromfile(fpath, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                print(f"  • Generating smooth pan sequence from: {fname} ({img.shape[1]}x{img.shape[0]})")
                frames = generate_pan_frames(img, num_frames=45, out_w=1280, out_h=720)
                all_scene_frames.append(frames)
        else:
            print(f"  ⚠️ Scene file not found: {fpath}")

    if not all_scene_frames:
        print("❌ No source images found to generate demo video.")
        return

    # Stitch scenes with smooth 8-frame crossfade transitions
    final_frames = []
    fade_len = 8
    for s_idx, frames in enumerate(all_scene_frames):
        if s_idx == 0:
            final_frames.extend(frames)
        else:
            prev_tail = final_frames[-fade_len:]
            curr_head = frames[:fade_len]
            final_frames = final_frames[:-fade_len]
            for f_i in range(fade_len):
                alpha = (f_i + 1) / (fade_len + 1)
                blended = cv2.addWeighted(prev_tail[f_i], 1.0 - alpha, curr_head[f_i], alpha, 0)
                final_frames.append(blended)
            final_frames.extend(frames[fade_len:])

    # Save as MP4
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 15.0
    out = cv2.VideoWriter(output_path, fourcc, fps, (1280, 720))
    for frame in final_frames:
        out.write(frame)
    out.release()

    print(f"\n✅ Đã tạo thành công Raw Demo Video sạch (chưa vẽ khung): {output_path}")
    print(f"   • Độ phân giải : 1280x720 (HD)")
    print(f"   • Tổng số frame: {len(final_frames)} frames ({len(final_frames)/fps:.1f} giây @ {fps} FPS)")

if __name__ == "__main__":
    create_raw_demo_video()
