import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.models import Base
from src.database.session import get_db
from src.backend.app import app
from src.database import crud

# In-memory SQLite with StaticPool so all connections share the same memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"

def test_crud_and_endpoints(client):
    db = TestingSessionLocal()
    crud.get_or_create_worker(db, track_id=201)
    crud.log_violation_event(
        db,
        event_id="test-pytest-001",
        track_id=201,
        violations=["NO-Hardhat"]
    )
    db.close()

    # Test summary
    res_summary = client.get("/api/v1/summary")
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["total_unique_workers"] >= 1
    assert summary["total_logged_violations"] >= 1

    # Test list violations
    res_violations = client.get("/api/v1/violations")
    assert res_violations.status_code == 200
    violations = res_violations.json()
    assert len(violations) >= 1
    assert violations[0]["event_id"] == "test-pytest-001"

    # Test status update
    res_patch = client.patch(
        "/api/v1/violations/test-pytest-001/status",
        json={"status": "RESOLVED"}
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "RESOLVED"

    # Test 400 Bad Request
    res_bad = client.patch(
        "/api/v1/violations/test-pytest-001/status",
        json={"status": "INVALID_STATUS"}
    )
    assert res_bad.status_code == 400

    # Test 404 Not Found
    res_not_found = client.patch(
        "/api/v1/violations/non-existent-id/status",
        json={"status": "RESOLVED"}
    )
    assert res_not_found.status_code == 404

    # Test camera registration and listing
    res_cam = client.post(
        "/api/v1/cameras",
        json={"camera_id": "test_cam_1", "name": "Test Cam", "source_url": "rtsp://0.0.0.0"}
    )
    assert res_cam.status_code == 200

    res_list_cam = client.get("/api/v1/cameras")
    assert res_list_cam.status_code == 200
    assert len(res_list_cam.json()) >= 1
