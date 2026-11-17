# PHASE 05 TECHNICAL REPORT: BACKEND REST API & RELATIONAL DATABASE

**Project:** PPE Detection & Construction Site Safety Monitoring System  
**Phase:** 05 – Backend Architecture, Database & REST APIs  
**Status:** ✅ COMPLETED & VERIFIED  
**Date:** 2026-11-10  

---

## 1. Executive Summary

Phase 05 establishes the enterprise backend infrastructure connecting real-time computer vision inference with persistent data storage, site-wide safety analytics, and supervisory incident management.

The backend is built with **FastAPI** (asynchronous, OpenAPI/Swagger native) and **SQLAlchemy ORM** backed by **SQLite** (expandable to PostgreSQL via connection string configuration).

All 7 REST API endpoints and CRUD operations were validated via automated test harnesses (`scripts/run_phase_05_backend.py` and `tests/test_backend.py`), demonstrating 100% test pass rate, correct HTTP status codes (200, 400, 404), and robust schema validation with Pydantic.

---

## 2. Architecture & Data Flow

```
                      +------------------------------------------+
                      |   Phase 04: PPE Compliance Engine        |
                      |   (Worker Track IDs + Violation Events)  |
                      +--------------------+---------------------+
                                           |
                                           v
                             +-----------------------------+
                             |   Database Session & CRUD   |
                             |   (SQLAlchemy ORM)          |
                             +--------------+--------------+
                                            |
                         +------------------+------------------+
                         |                                     |
                         v                                     v
             +-----------------------+             +-----------------------+
             |   SQLite Database     |             |   FastAPI REST APIs   |
             |   (ppe_monitoring.db) |             |   (uvicorn / 8000)    |
             +-----------------------+             +-----------+-----------+
                                                               |
                                       +-----------------------+-----------------------+
                                       |                                               |
                                       v                                               v
                        +------------------------------+                +-------------------------------+
                        |  Phase 06: Streamlit UI      |                |  Enterprise Dashboards /      |
                        |  (Real-time Monitoring HUD)  |                |  External Safety Webhooks     |
                        +------------------------------+                +-------------------------------+
```

---

## 3. Relational Schema Design (`src/database/models.py`)

The relational database architecture is normalized to track workers, violation instances, camera sources, and system audit logs:

| Table Name | Primary Key | Key Columns | Purpose |
| :--- | :--- | :--- | :--- |
| `workers` | `id` (Integer) | `track_id` (Unique), `first_seen`, `last_seen`, `total_violations` | Stores worker entity and cumulative safety score |
| `violations` | `id` (Integer) | `event_id` (Unique), `track_id` (FK), `violation_type`, `status` (`OPEN`/`RESOLVED`), `timestamp` | Granular log of confirmed temporal violation events |
| `cameras` | `id` (Integer) | `camera_id` (Unique), `name`, `source_url`, `location`, `status` (`ACTIVE`/`INACTIVE`) | Manages CCTV / RTSP video streams across site gates |
| `system_logs` | `id` (Integer) | `timestamp`, `level` (`INFO`/`WARN`/`ERROR`), `module`, `message` | Persistent audit trail for debugging and auditing |

---

## 4. API Specification & Verified Endpoints (`src/backend/app.py`)

All endpoints are documented with interactive Swagger UI at `http://localhost:8000/docs`:

| Method | Endpoint | Description | Verification Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Health check & system uptime timestamp | ✅ 200 OK |
| `GET` | `/api/v1/summary` | Real-time safety KPIs (Total workers, violations, compliance %) | ✅ 200 OK |
| `GET` | `/api/v1/violations` | Paginated list of violation events (filter by `status=OPEN/RESOLVED`) | ✅ 200 OK |
| `PATCH` | `/api/v1/violations/{id}/status` | Updates incident status (`RESOLVED`) with input validation | ✅ 200 OK / 400 Bad / 404 Not Found |
| `GET` | `/api/v1/workers` | Lists all detected workers and cumulative violations | ✅ 200 OK |
| `GET` | `/api/v1/cameras` | Lists all active site surveillance cameras | ✅ 200 OK |
| `POST` | `/api/v1/cameras` | Registers a new RTSP camera stream | ✅ 200 OK |

---

## 5. Verification & Test Execution Results

Verification was performed using `scripts/run_phase_05_backend.py` and `pytest tests/test_backend.py -v`:

```
======================================================================
PHASE 05 – BACKEND REST API & DATABASE EVALUATION
======================================================================
[1/4] Khởi tạo SQLite Database & SQLAlchemy Session...
[2/4] Kiểm tra các thao tác CRUD cơ bản trên SQLite...
  • Tổng số công nhân trong DB: 8
  • Tổng số vi phạm đã ghi nhận: 2
  • Số vi phạm đang mở (OPEN) : 2
  • Tỷ lệ tuân thủ an toàn     : 75.0%

[3/4] Kiểm tra toàn diện các REST API Endpoints bằng TestClient...
  ✅ GET   /health                                -> 200 OK
  ✅ GET   /api/v1/summary                        -> 200 OK
  ✅ GET   /api/v1/violations                     -> 200 OK
  ✅ PATCH /api/v1/violations/test-evt-001/status -> 200 OK
  ✅ GET   /api/v1/workers                        -> 200 OK
  ✅ POST  /api/v1/cameras                        -> 200 OK
  ✅ GET   /api/v1/cameras                        -> 200 OK

[4/4] Kiểm tra cơ chế xử lý lỗi (Exception Handling)...
  ✅ PATCH /api/v1/violations/... (Invalid Status) -> 400 Bad Request
  ✅ PATCH /api/v1/violations/... (Not Found)     -> 404 Not Found
======================================================================
✅ HOÀN THÀNH KIỂM ĐỊNH PHASE 05!
```

---

## 6. Phase Acceptance Checklist

- [x] SQLite database schema definitions implemented in `src/database/models.py`.
- [x] Session lifecycle management implemented in `src/database/session.py`.
- [x] High-performance CRUD repository implemented in `src/database/crud.py`.
- [x] Pydantic V2 response & request schemas created in `src/backend/schemas.py`.
- [x] FastAPI application & CORS routing created in `src/backend/app.py`.
- [x] Standalone verification script executed (`scripts/run_phase_05_backend.py`).
- [x] Unit test suite passing (`pytest tests/test_backend.py`).
- [x] Technical report generated (`docs/backend/PHASE_05_BACKEND_REPORT.md`).

---

**Next Milestone:** Proceed to **Phase 06 – Frontend & Streamlit Dashboard** upon user approval.

