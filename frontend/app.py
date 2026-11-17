import os
import sys

# Ensure project root directory is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import time
import cv2
import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px

from src.detection.detector import PPEDetector
from src.tracking.tracker import WorkerTracker, TrackedPerson
from src.compliance.engine import PPEComplianceEngine
from src.common.types import CLASS_COLORS, ComplianceStatus, Detection, BoundingBox
from src.common.visualizer import PPEVisualizer
from src.database.session import SessionLocal, init_db, DATABASE_URL, engine
from src.database import crud

# Page Configuration
st.set_page_config(
    page_title="PPE Detection & Safety Monitoring",
    page_icon="🦺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark-mode modern dashboard
st.markdown("""
<style>
    .metric-card {
        background-color: #1E222D;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #00D7FF;
        margin-bottom: 10px;
    }
    .metric-title { font-size: 0.85rem; color: #8F9CAE; margin-bottom: 4px; }
    .metric-value { font-size: 1.8rem; font-weight: bold; color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)

# Initialize Database
init_db()

@st.cache_resource
def load_system(model_path: str, conf_thresh: float, iou_thresh: float):
    detector = None
    if os.path.exists(model_path):
        detector = PPEDetector(model_path=model_path, conf_threshold=conf_thresh, iou_threshold=iou_thresh)
    tracker = WorkerTracker(config_path="configs/tracker_bytetrack.yaml")
    compliance_engine = PPEComplianceEngine(config_path="configs/compliance_rules.yaml")
    return detector, tracker, compliance_engine

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🛡️ PPE Safety Control")
st.sidebar.markdown("**Construction Site AI Monitor**")

# Display Active Database
db_backend = "MySQL" if "mysql" in DATABASE_URL.lower() else "SQLite"
st.sidebar.info(f"🗄️ **Database:** `{db_backend}`")

model_option = st.sidebar.selectbox(
    "Select Model Weights",
    [
        "models/checkpoints/best.pt",
        "models/exported/ppe_best_yolo11.onnx",
        "models/pretrained/yolo11s.pt"
    ]
)

conf_thresh = st.sidebar.slider("Confidence Threshold", 0.15, 0.90, 0.35, 0.05)
iou_thresh = st.sidebar.slider("IoU NMS Threshold", 0.20, 0.80, 0.50, 0.05)

st.sidebar.markdown("---")
st.sidebar.subheader("Safety Rules Policy")
require_hardhat = st.sidebar.checkbox("Require Hardhat (Mũ bảo hộ)", value=True)
require_vest = st.sidebar.checkbox("Require Safety Vest (Áo phản quang)", value=True)
require_mask = st.sidebar.checkbox("Require Mask (Khẩu trang)", value=False)

input_source = st.sidebar.radio(
    "Monitoring Video Source",
    [
        "Upload Video File (Tải video từ máy lên)",
        "Demo Construction Video (Video mẫu công trường)",
        "Single Image Test (Kiểm tra từng ảnh)"
    ]
)

# --- HEADER METRIC CARDS ---
db = SessionLocal()
summary = crud.get_system_summary(db)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">TOTAL TRACKED WORKERS</div>
        <div class="metric-value">{summary['total_unique_workers']}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #E74C3C;">
        <div class="metric-title">ACTIVE VIOLATIONS</div>
        <div class="metric-value">{summary['active_open_violations']}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #2ECC71;">
        <div class="metric-title">SITE COMPLIANCE RATE</div>
        <div class="metric-value">{summary['compliance_rate']}%</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #F39C12;">
        <div class="metric-title">TOTAL LOGGED EVENTS</div>
        <div class="metric-value">{summary['total_logged_violations']}</div>
    </div>
    """, unsafe_allow_html=True)

# --- TABS INTERFACE ---
tab1, tab2, tab3 = st.tabs(["🎥 Live Monitoring Stream", "📋 Violation Event Log", "📊 Analytics & Insights"])

# Load detector & tracker
detector, tracker, compliance_engine = load_system(model_option, conf_thresh, iou_thresh)
vis = PPEVisualizer()

with tab1:
    st.subheader("Real-Time CCTV Stream & PPE Compliance Tracking")
    
    if detector is None:
        st.warning(f"⚠️ Weight file `{model_option}` not found. Please upload trained weights to `models/checkpoints/best.pt`.")
    else:
        video_col, status_col = st.columns([3, 1])
        frame_placeholder = video_col.empty()
        worker_status_placeholder = status_col.empty()
        
        # Mode 1: Single Image Test
        if "Single Image Test" in input_source:
            test_dir = os.path.join("data", "processed", "test", "images")
            sample_img_paths = [
                os.path.join(test_dir, f)
                for f in os.listdir(test_dir)
                if f.endswith(('.jpg', '.jpeg', '.png'))
            ] if os.path.exists(test_dir) else []

            if sample_img_paths:
                selected_img = video_col.selectbox("Select Sample Test Image", sample_img_paths)
                img = cv2.imread(selected_img)
                
                # Predict
                detections = detector.predict(img)
                annotated = img.copy()
                annotated = vis.draw_detections(annotated, detections)

                rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(rgb, use_container_width=True)
                
                # Show Detection Breakdown
                worker_status_placeholder.markdown("### Detected Objects")
                counts = {}
                for d in detections:
                    counts[d.class_name] = counts.get(d.class_name, 0) + 1
                for k, v in counts.items():
                    worker_status_placeholder.write(f"- **{k}**: {v}")
            else:
                video_col.info("No test images found in `data/processed/test/images`.")

        # Mode 2: Video Stream (Demo or User Upload)
        else:
            video_path = None

            if "Upload Video File" in input_source:
                uploaded_file = video_col.file_uploader(
                    "📂 Kéo thả hoặc chọn file video từ máy tính của bạn (.mp4, .avi, .mov):",
                    type=["mp4", "avi", "mov"],
                    help="Hệ thống hỗ trợ tải lên video công trường thực tế để phân tích an toàn lao động"
                )
                if uploaded_file is not None:
                    video_path = os.path.join("data", "reports", "uploaded_temp.mp4")
                    os.makedirs(os.path.dirname(video_path), exist_ok=True)
                    with open(video_path, "wb") as f:
                        f.write(uploaded_file.read())
                    video_col.success(f"✅ Đã tải lên video: **{uploaded_file.name}** ({uploaded_file.size / (1024*1024):.1f} MB)")
                else:
                    video_col.info("👆 Hãy chọn hoặc kéo thả 1 file video từ máy tính của bạn vào khung phía trên để bắt đầu!")

            elif "Demo Construction Video" in input_source:
                demo_paths = [
                    "data/demo/raw_construction_demo.mp4",
                    "data/reports/phase_04_compliance/compliance_monitoring_demo.mp4",
                    "data/reports/phase_03_tracking/tracked_workers_demo.mp4"
                ]
                for p in demo_paths:
                    if os.path.exists(p):
                        video_path = p
                        break
                if video_path is None:
                    video_col.warning("Demo video not found. Please run Phase 03/04 or upload a video file.")
                else:
                    video_col.info("🎬 Đang chọn Video mẫu công trường (HD 720p). Bấm nút bên dưới để bắt đầu giám sát AI!")

            if video_path and os.path.exists(video_path):
                if "is_streaming" not in st.session_state:
                    st.session_state.is_streaming = False

                c_btn1, c_btn2 = video_col.columns([1, 1])
                if c_btn1.button("▶️ Start Video Monitoring", use_container_width=True):
                    st.session_state.is_streaming = True
                if c_btn2.button("⏹️ Stop Stream", use_container_width=True):
                    st.session_state.is_streaming = False

                if st.session_state.is_streaming:
                    cap = cv2.VideoCapture(video_path)
                    fps_history = []
                    frame_num = 0
                    
                    while cap.isOpened() and st.session_state.is_streaming:
                        t0 = time.time()
                        ret, frame = cap.read()
                        if not ret:
                            if "Demo Construction Video" in input_source:
                                # Loop demo video continuously
                                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                                ret, frame = cap.read()
                                if not ret:
                                    break
                            else:
                                # Finished uploaded video
                                st.session_state.is_streaming = False
                                break
                        frame_num += 1

                        # Full dual-stream tracking & compliance
                        if hasattr(detector, "model") and detector.model is not None:
                            tracked_workers, ppe_dets = tracker.track(
                                detector.model, frame, conf=conf_thresh, iou=iou_thresh
                            )
                        else:
                            detections = detector.predict(frame)
                            worker_dets = [d for d in detections if d.class_name == "Person"]
                            ppe_dets = [d for d in detections if d.class_name != "Person"]
                            tracked_workers = [
                                TrackedPerson(track_id=i+1, box=w.box, confidence=w.confidence)
                                for i, w in enumerate(worker_dets)
                            ]

                        # Log workers to database
                        for tw in tracked_workers:
                            crud.get_or_create_worker(db, track_id=tw.track_id)

                        # Evaluate compliance
                        worker_states, violation_events = compliance_engine.process_frame(tracked_workers, ppe_dets)
                        for ev in violation_events:
                            crud.log_violation_event(db, ev.event_id, ev.track_id, ev.violations)

                        # Render HUD & Bounding Boxes
                        annotated = vis.draw_tracked_workers(frame, tracked_workers)
                        annotated = vis.draw_detections(annotated, ppe_dets)
                        annotated = vis.draw_hud_summary(annotated, len(tracked_workers), len(violation_events))
                        
                        rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                        frame_placeholder.image(rgb, use_container_width=True)

                        fps_val = 1.0 / max(time.time() - t0, 1e-4)
                        fps_history.append(fps_val)
                        avg_fps = sum(fps_history[-20:]) / len(fps_history[-20:])

                        worker_status_placeholder.markdown(f"""
                        ### Stream Metrics
                        - **Frame:** `{frame_num}`
                        - **Live FPS:** `{avg_fps:.1f}`
                        - **Active Workers:** `{len(tracked_workers)}`
                        - **Active Violations:** `{len(violation_events)}`
                        - **Database Engine:** `{db_backend}`
                        """)
                        time.sleep(0.01)

                    cap.release()

with tab2:
    st.subheader(f"Logged Safety Violations ({db_backend})")
    
    col_filter1, col_filter2 = st.columns([2, 1])
    status_filter = col_filter1.selectbox("Filter Status", ["ALL", "OPEN", "RESOLVED"])
    
    violations = crud.get_all_violations(db, limit=100)
    if status_filter != "ALL":
        violations = [v for v in violations if v.status == status_filter]
        
    if violations:
        data = [
            {
                "Event ID": v.event_id,
                "Worker ID": f"#{v.track_id}",
                "Violations": v.violations,
                "Status": v.status,
                "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(v.timestamp))
            }
            for v in violations
        ]
        df_viols = pd.DataFrame(data)
        st.dataframe(df_viols, use_container_width=True)

        st.markdown("---")
        st.subheader("⚡ Quick Resolve Action")
        open_events = [v.event_id for v in violations if v.status == "OPEN"]
        if open_events:
            selected_evt = st.selectbox("Select Open Event to Resolve", open_events)
            if st.button("Mark as RESOLVED"):
                crud.update_violation_status(db, selected_evt, "RESOLVED")
                st.success(f"Violation `{selected_evt}` successfully marked as RESOLVED!")
                st.rerun()
    else:
        st.success("No violations matching criteria. Site is safe! 🟢")

with tab3:
    st.subheader("Site Safety Analytics & PPE Trends")
    chart_col1, chart_col2 = st.columns(2)
    
    all_viols = crud.get_all_violations(db)
    if all_viols:
        # Violation Distribution Pie Chart
        v_counts = {}
        for v in all_viols:
            for item in v.violations.split(","):
                item = item.strip()
                if item:
                    v_counts[item] = v_counts.get(item, 0) + 1
                    
        df_pie = pd.DataFrame(list(v_counts.items()), columns=["Violation Type", "Count"])
        fig_pie = px.pie(df_pie, names="Violation Type", values="Count", title="Distribution of PPE Violations", hole=0.4)
        chart_col1.plotly_chart(fig_pie, use_container_width=True)
        
        # Worker Compliance Rate Bar Chart
        compliant_workers = max(0, summary['total_unique_workers'] - summary['active_open_violations'])
        df_bar = pd.DataFrame({
            "Category": ["Compliant Workers", "Non-Compliant Workers"],
            "Count": [compliant_workers, summary['active_open_violations']]
        })
        fig_bar = px.bar(df_bar, x="Category", y="Count", color="Category", title="Worker Compliance Overview")
        chart_col2.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Analytics charts will automatically populate once violation data is logged during stream monitoring.")

db.close()
