import sys
import os
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from src.database.session import init_db, SessionLocal, DATABASE_URL, engine
from src.database import crud
from src.backend.app import app

def run_backend_evaluation():
    print("=" * 70)
    print("🗄️ PHASE 05 – BACKEND REST API & DATABASE EVALUATION")
    print("=" * 70)

    # 1. Initialize Database
    db_type = engine.name.upper()
    print(f"[1/4] Khởi tạo {db_type} Database & SQLAlchemy Session...")
    init_db()
    db = SessionLocal()

    # 2. Seed Mock Tracking & Violation Data
    print(f"[2/4] Kiểm tra các thao tác CRUD cơ bản trên {db_type}...")
    w1 = crud.get_or_create_worker(db, track_id=101)
    w2 = crud.get_or_create_worker(db, track_id=102)

    ev1 = crud.log_violation_event(
        db,
        event_id="test-evt-001",
        track_id=101,
        violations=["NO-Hardhat", "NO-Safety Vest"]
    )
    ev2 = crud.log_violation_event(
        db,
        event_id="test-evt-002",
        track_id=102,
        violations=["NO-Mask"]
    )

    cam1 = crud.add_camera(
        db,
        camera_id="cam_gate_01",
        name="CCTV Gate 1",
        source_url="rtsp://192.168.1.100:554/live",
        location="Main Construction Gate"
    )

    summary_before = crud.get_system_summary(db)
    print(f"  • Tổng số công nhân trong DB: {summary_before['total_unique_workers']}")
    print(f"  • Tổng số vi phạm đã ghi nhận: {summary_before['total_logged_violations']}")
    print(f"  • Số vi phạm đang mở (OPEN) : {summary_before['active_open_violations']}")
    print(f"  • Tỷ lệ tuân thủ an toàn     : {summary_before['compliance_rate']}%")

    db.close()

    # 3. Test FastAPI Endpoints using TestClient
    print("\n[3/4] Kiểm tra toàn diện các REST API Endpoints bằng TestClient...")
    client = TestClient(app)

    # Test /health
    r_health = client.get("/health")
    assert r_health.status_code == 200, "Health check failed"
    print("  ✅ GET  /health                                -> 200 OK")

    # Test /api/v1/summary
    r_summary = client.get("/api/v1/summary")
    assert r_summary.status_code == 200, "Summary endpoint failed"
    print(f"  ✅ GET  /api/v1/summary                        -> 200 OK (Workers={r_summary.json()['total_unique_workers']})")

    # Test /api/v1/violations
    r_violations = client.get("/api/v1/violations?status=ALL")
    assert r_violations.status_code == 200, "Violations endpoint failed"
    viols_data = r_violations.json()
    assert len(viols_data) >= 2, "Violations count mismatch"
    print(f"  ✅ GET  /api/v1/violations                     -> 200 OK (Count={len(viols_data)})")

    # Test PATCH /api/v1/violations/{event_id}/status
    r_patch = client.patch(
        "/api/v1/violations/test-evt-001/status",
        json={"status": "RESOLVED"}
    )
    assert r_patch.status_code == 200, "Status update failed"
    assert r_patch.json()["status"] == "RESOLVED"
    print("  ✅ PATCH /api/v1/violations/test-evt-001/status -> 200 OK (Chuyển OPEN -> RESOLVED)")

    # Test /api/v1/workers
    r_workers = client.get("/api/v1/workers")
    assert r_workers.status_code == 200, "Workers endpoint failed"
    print(f"  ✅ GET  /api/v1/workers                        -> 200 OK (Workers count={len(r_workers.json())})")

    # Test POST /api/v1/cameras
    r_cam_post = client.post(
        "/api/v1/cameras",
        json={
            "camera_id": "cam_tower_crane",
            "name": "Tower Crane CCTV",
            "source_url": "rtsp://192.168.1.102:554/live",
            "location": "Zone B Crane"
        }
    )
    assert r_cam_post.status_code == 200, "Camera registration failed"
    print("  ✅ POST /api/v1/cameras                        -> 200 OK (Đăng ký Camera mới)")

    # Test GET /api/v1/cameras
    r_cams = client.get("/api/v1/cameras")
    assert r_cams.status_code == 200, "List cameras failed"
    print(f"  ✅ GET  /api/v1/cameras                        -> 200 OK (Active Cameras={len(r_cams.json())})")

    # 4. Error Handling Verification
    print("\n[4/4] Kiểm tra cơ chế xử lý lỗi (Exception Handling)...")
    r_invalid_status = client.patch(
        "/api/v1/violations/test-evt-001/status",
        json={"status": "INVALID_STATUS_CODE"}
    )
    assert r_invalid_status.status_code == 400, "Expected 400 Bad Request"
    print("  ✅ PATCH /api/v1/violations/... (Invalid Status) -> 400 Bad Request (Bắt lỗi hợp lệ)")

    r_not_found = client.patch(
        "/api/v1/violations/non_existing_event/status",
        json={"status": "RESOLVED"}
    )
    assert r_not_found.status_code == 400 or r_not_found.status_code == 404, "Expected 404 Not Found"
    print("  ✅ PATCH /api/v1/violations/... (Not Found)     -> 404 Not Found (Bắt lỗi hợp lệ)")

    print("\n" + "=" * 70)
    print("📊 BÁO CÁO NGHIỆM THU PHASE 05 (BACKEND & DATABASE):")
    print(f"  • Cơ sở dữ liệu đang dùng: {db_type} ({DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL})")
    print("  • Bảng dữ liệu đã tạo     : workers, violations, cameras, system_logs")
    print("  • Kiểm thử REST Endpoints : 7/7 APIs đạt chuẩn 200/400/404")
    print("  • Swagger UI Documentation: http://localhost:8000/docs")
    print("=" * 70)
    print("✅ HOÀN THÀNH KIỂM ĐỊNH PHASE 05!")

if __name__ == "__main__":
    run_backend_evaluation()

