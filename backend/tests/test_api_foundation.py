import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.models.enums import ApplicationStatus, RoleStatus, UserRole, AccountStatus
from app.models.user import User
from app.models.team import Role
from app.db.init_db import APPROVED_ROLES

# In-memory SQLite for testing
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


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as session:
        # Seed test admin user
        admin = User(
            full_name="Team Lead",
            email="lead@nasa.org",
            user_role=UserRole.ADMINISTRATOR.value,
            account_status=AccountStatus.ACTIVE.value,
        )
        session.add(admin)
        # Seed roles
        for r_data in APPROVED_ROLES:
            role = Role(**r_data)
            session.add(role)
        session.commit()
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to ARTS" in response.json()["message"]


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data


def test_list_roles():
    response = client.get("/api/v1/roles")
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert len(res["data"]) >= 4


def test_applicant_and_application_workflow():
    # 1. Create applicant with experience & portfolio
    applicant_payload = {
        "full_name": "Dr. Sarah Astronaut",
        "email": "sarah.astronaut@example.com",
        "phone_number": "+1-555-0199",
        "location": "Houston, TX",
        "external_profile_link": "https://linkedin.com/in/sarah-astronaut",
        "experiences": [
            {
                "title": "Robotics Researcher",
                "organization": "Space Lab",
                "start_date": "2024-01-01",
                "description": "Rover mobility logic",
            }
        ],
        "portfolio_items": [
            {
                "title": "Rover Sim",
                "reference_link": "https://github.com/sarah/rover-sim",
            }
        ],
    }
    app_res = client.post("/api/v1/applicants", json=applicant_payload)
    assert app_res.status_code == 201
    applicant_data = app_res.json()["data"]
    applicant_id = applicant_data["id"]

    # 2. Get a role ID
    roles_res = client.get("/api/v1/roles")
    role_id = roles_res.json()["data"][0]["id"]

    # 3. Create application
    application_payload = {
        "applicant_id": applicant_id,
        "role_id": role_id,
        "motivation_statement": "Passionate about NASA Space Apps Challenge.",
        "availability_info": "Full weekend availability.",
    }
    app_post_res = client.post("/api/v1/applications", json=application_payload)
    assert app_post_res.status_code == 201
    application_data = app_post_res.json()["data"]
    application_id = application_data["id"]
    assert application_data["current_status"] == ApplicationStatus.RECEIVED.value

    # 4. Update status to Shortlisted
    status_update_payload = {
        "new_status": ApplicationStatus.SHORTLISTED.value,
        "reason": "Strong robotics background aligns with role.",
    }
    status_res = client.patch(f"/api/v1/applications/{application_id}/status", json=status_update_payload)
    assert status_res.status_code == 200
    updated_app = status_res.json()["data"]
    assert updated_app["current_status"] == ApplicationStatus.SHORTLISTED.value
    assert len(updated_app["status_history"]) == 2

    # 5. Add Note
    with TestingSessionLocal() as session:
        user = session.query(User).first()
        user_id = str(user.id)

    note_payload = {
        "author_id": user_id,
        "related_entity_type": "Application",
        "related_entity_id": application_id,
        "note_text": "Reviewed portfolio link, looks outstanding.",
    }
    note_res = client.post("/api/v1/notes", json=note_payload)
    assert note_res.status_code == 201

    # 6. Schedule Interview
    interview_payload = {
        "application_id": application_id,
        "scheduled_at": "2026-10-02T15:00:00Z",
        "format": "Video Call",
        "participant_user_ids": [user_id],
    }
    interview_res = client.post("/api/v1/interviews", json=interview_payload)
    assert interview_res.status_code == 201


def test_validation_error_format():
    # Attempting to create an applicant with invalid email
    invalid_payload = {
        "full_name": "Test User",
        "email": "not-a-valid-email",
    }
    res = client.post("/api/v1/applicants", json=invalid_payload)
    assert res.status_code == 422
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) > 0
    assert "email" in data["error"]["details"][0]["field"]


def test_not_found_error_format():
    res = client.get("/api/v1/roles/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
