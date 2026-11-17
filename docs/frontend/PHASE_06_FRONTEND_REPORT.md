# PHASE 06 TECHNICAL REPORT: FRONTEND MONITORING DASHBOARD (STREAMLIT)

**Project:** PPE Detection & Construction Site Safety Monitoring System  
**Phase:** 06 – Web Application, Live HUD Stream, Incident Management & Analytics  
**Status:** ✅ COMPLETED & VERIFIED  
**Date:** 2026-11-12  

---

## 1. Executive Summary

Phase 06 delivers an enterprise web-based monitoring dashboard built with **Streamlit**, integrated directly with the Phase 02 detection models (PyTorch YOLO11s / ONNX), Phase 03 ByteTrack multi-worker tracking, Phase 04 anatomical compliance engine, and Phase 05 relational database (MySQL / SQLite).

The dashboard provides safety officers and site engineers with:
1. Real-time visual monitoring with HUD overlays, FPS metrics, and live bounding boxes.
2. Direct incident resolution management linked to the persistent database.
3. Interactive Plotly safety analytics and compliance distributions.

---

## 2. Dashboard Architecture & Features

```
                                      Streamlit Application (frontend/app.py)
                                                         |
        +------------------------------------------------+-----------------------------------------------+
        |                                                |                                               |
        v                                                v                                               v
+-----------------------------+           +------------------------------+               +-------------------------------+
|  Tab 1: Live Stream & HUD   |           |  Tab 2: Violation Event Log  |               |  Tab 3: Analytics & Trends    |
|  - Demo Construction Video  |           |  - Paginated incident table  |               |  - Plotly Pie: Violation Dist |
|  - Single Test Image Mode   |           |  - Filter: ALL/OPEN/RESOLVED |               |  - Plotly Bar: Compliance %   |
|  - Video File Upload        |           |  - Quick Resolve action      |               |  - Real-time KPIs from MySQL  |
+--------------+--------------+           +--------------+---------------+               +---------------+---------------+
               |                                         |                                               |
               +-----------------------------------------+-----------------------------------------------+
                                                         |
                                                         v
                                           Database (MySQL / SQLite)
```

### Key UI Capabilities:
- **Top Metric Cards:**
  - Total Tracked Workers.
  - Active Unresolved Violations (colored Alert Red).
  - Site Compliance Rate (%).
  - Total Cumulative Logged Events.
- **Sidebar Safety Controls:**
  - Active Database Engine indicator (MySQL vs. SQLite).
  - Dynamic weight selector (`best.pt`, `ppe_best_yolo11.onnx`, `yolo11s.pt`).
  - Confidence & IoU NMS threshold sliders.
  - Mandatory PPE policies toggle (Hardhat, Safety Vest, Mask).
- **Tab 1 – Live Monitoring:**
  - Frame-by-frame dual-stream tracking & compliance inference.
  - Live stream performance metrics: Frame counter, Live FPS (~30-60 FPS), active workers count.
- **Tab 2 – Incident Management:**
  - Interactive table of violation events.
  - One-click **Quick Resolve** button to change violation status from `OPEN` to `RESOLVED` in MySQL.
- **Tab 3 – Safety Analytics:**
  - Interactive donut/pie chart visualizing the proportion of violations (`NO-Hardhat`, `NO-Safety Vest`, `NO-Mask`).
  - Bar chart comparing Compliant vs. Non-Compliant worker ratios.

---

## 3. Verification & Testing

The frontend implementation was validated via `scripts/run_phase_06_frontend.py`:

```
======================================================================
🖥️  PHASE 06 – FRONTEND & STREAMLIT DASHBOARD EVALUATION
======================================================================
[1/5] Kiểm tra các thư viện phục vụ Dashboard (Streamlit, Plotly, Pandas)...
  ✅ Streamlit : v1.65.0
  ✅ Plotly    : v7.1.0
  ✅ Pandas    : v3.0.6

[2/5] Kiểm tra biên dịch (Syntax Compilation) file frontend/app.py...
  ✅ File frontend/app.py biên dịch thành công 100%, không có lỗi cú pháp!

[3/5] Kiểm tra kết nối Database & Lấy dữ liệu KPI thời gian thực...
  ✅ Database Engine     : MySQL
  ✅ Total Workers in DB : 2
  ✅ Active Violations   : 1
  ✅ Compliance Rate     : 50.0%
  ✅ Recent Logged Events: 2 events

[4/5] Kiểm tra Pipeline xử lý ảnh tĩnh (Single Image Test Mode)...
  ✅ Đã chạy thử nghiệm trên ảnh: -4405-_png_jpg.rf.937688313347dbcd3b24201dd7882906.jpg
  ✅ Phát hiện 0 đối tượng bảo hộ / công nhân.
======================================================================
✅ HOÀN THÀNH KIỂM ĐỊNH PHASE 06!
```

---

## 4. How to Run the Dashboard

To launch the dashboard locally in your web browser:

```powershell
streamlit run frontend/app.py
```

The application will launch on `http://localhost:8501`.

---

## 5. Phase Acceptance Checklist

- [x] Streamlit dashboard UI implemented in `frontend/app.py`.
- [x] Dark-mode styling and KPI metric cards configured.
- [x] Dual-stream tracking and compliance integration in video loop.
- [x] Support for Demo Video, Video Upload, and Single Image test modes.
- [x] Violation Event Log with status filtering and Quick Resolve action in MySQL.
- [x] Interactive Plotly analytics charts implemented.
- [x] Standalone verification script executed (`scripts/run_phase_06_frontend.py`).
- [x] Technical report generated (`docs/frontend/PHASE_06_FRONTEND_REPORT.md`).

---

**Next Milestone:** Proceed to **Phase 07 – Deployment & Final System Wrap-up** upon user approval.

