import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.models.enums import ApplicationStatus, RoleStatus, UserRole, AccountStatus, ApplicantStatus
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
        # Seed approved roles
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


def test_google_forms_single_intake_and_duplicate_handling():
    """
    Tests FR-001, FR-005, FR-007: Intake processing, profile creation,
    evidence links, skills, and idempotent update on re-submission.
    """
    intake_payload = {
        "full_name": "Commander Alex Vance",
        "email": "alex.vance@space.org",
        "phone_number": "+1-555-4321",
        "location": "Pasadena, CA",
        "external_profile_link": "https://github.com/alexvance",
        "role_name": "Game/App Developer",
        "motivation_statement": "Experienced with Godot and Unity space simulations.",
        "availability_info": "Available 20 hours per week during challenge.",
        "skills": [
            {"skill_name": "Godot", "proficiency_level": "Expert", "years_of_experience": 4.5},
            {"skill_name": "C#", "proficiency_level": "Advanced", "years_of_experience": 5.0},
        ],
        "evidence_links": [
            {
                "title": "Orbital Simulator Demo",
                "reference_link": "https://github.com/alexvance/orbit-sim",
                "description": "Custom physics engine for orbital mechanics",
            }
        ],
        "experiences": [
            {
                "title": "Lead Simulation Engineer",
                "organization": "AeroTech Labs",
                "start_date": "2023-01-01",
                "description": "Developed real-time spacecraft trajectory visualization.",
            }
        ],
    }

    # 1. Initial Intake Submission (FR-001)
    res = client.post("/api/v1/applications/intake", json=intake_payload)
    assert res.status_code == 201
    intake_res = res.json()["data"]
    assert intake_res["status"] == "created"
    app_id = intake_res["application_id"]
    applicant_id = intake_res["applicant_id"]

    # 2. Check Consolidated Detail (FR-011)
    detail_res = client.get(f"/api/v1/applications/{app_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()["data"]
    assert detail_data["current_status"] == ApplicationStatus.RECEIVED.value
    assert len(detail_data["applicant"]["portfolio_items"]) == 1
    assert len(detail_data["applicant"]["applicant_skills"]) == 2
    assert len(detail_data["status_history"]) == 1

    # 3. Re-Submission / Update Handling without Duplication (FR-005)
    updated_payload = dict(intake_payload)
    updated_payload["motivation_statement"] = "Updated motivation statement with more detail."
    res_update = client.post("/api/v1/applications/intake", json=updated_payload)
    assert res_update.status_code == 201
    update_data = res_update.json()["data"]
    assert update_data["status"] == "updated"
    assert update_data["applicant_id"] == applicant_id
    assert update_data["application_id"] == app_id


def test_google_forms_batch_intake():
    """
    Tests FR-002, FR-003, FR-004: Batch import with accepted/rejected summary.
    """
    batch_payload = {
        "submissions": [
            {
                "full_name": "Elena Rostova",
                "email": "elena@spaceapps.org",
                "role_name": "UI/UX & Visual Designer",
                "motivation_statement": "Figma design system lead.",
                "evidence_links": [{"title": "Design Portfolio", "reference_link": "https://figma.com/@elena"}],
            },
            {
                "full_name": "Dr. Marcus Bell",
                "email": "marcus@astronomy.edu",
                "role_name": "Space/Science Research + Game Logic",
                "motivation_statement": "Astrophysics PhD with simulation background.",
            },
            {
                "full_name": "Invalid Candidate",
                "email": "invalid@nowhere.com",
                "role_name": "Non-Existent Role That Fails Validation",
            },
        ]
    }

    res = client.post("/api/v1/applications/intake/batch", json=batch_payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_received"] == 3
    assert data["accepted"] == 2
    assert data["rejected"] == 1
    assert len(data["errors"]) == 1


def test_search_and_filter_applications():
    """
    Tests multi-criteria search, role filter, status filter, and pagination.
    """
    # 1. Search by name query
    res = client.get("/api/v1/applications?query=Elena")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 1
    assert "Elena" in data["items"][0]["applicant"]["full_name"]

    # 2. Filter by status
    res_status = client.get("/api/v1/applications?status=Received")
    assert res_status.status_code == 200
    assert all(a["current_status"] == "Received" for a in res_status.json()["data"]["items"])


def test_evidence_link_management():
    """
    Tests FR-015, FR-016, FR-017: Adding and removing evidence links on candidate profile.
    """
    # 1. List applicants to get an ID
    res = client.get("/api/v1/applicants?query=Elena")
    applicant_id = res.json()["data"]["items"][0]["id"]

    # 2. Add new evidence link (FR-015, FR-016)
    evidence_payload = {
        "title": "NASA Web Design Case Study",
        "reference_link": "https://behance.net/gallery/nasa-case-study",
        "description": "Visual identity concept for lunar rover interface",
    }
    add_res = client.post(f"/api/v1/applicants/{applicant_id}/evidence", json=evidence_payload)
    assert add_res.status_code == 201
    evidence_id = add_res.json()["data"]["id"]

    # 3. Remove evidence link (FR-017)
    del_res = client.delete(f"/api/v1/applicants/{applicant_id}/evidence/{evidence_id}")
    assert del_res.status_code == 200


def test_applicant_archive():
    """
    Tests FR-010: Archiving an applicant record.
    """
    res = client.get("/api/v1/applicants?query=Marcus")
    applicant_id = res.json()["data"]["items"][0]["id"]

    arch_res = client.patch(f"/api/v1/applicants/{applicant_id}/archive")
    assert arch_res.status_code == 200
    assert arch_res.json()["data"]["applicant_status"] == ApplicantStatus.ARCHIVED.value


def test_business_rules_status_transitions():
    """
    Tests BR-001, BR-002: Status validation rules and immutable audit history.
    """
    # 1. Get an application in Received status
    res = client.get("/api/v1/applications?status=Received")
    app_id = res.json()["data"]["items"][0]["id"]

    # 2. Attempt invalid jump from Received directly to Selected (Blocked by BR-002)
    invalid_res = client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"new_status": "Selected", "reason": "Direct jump should fail"},
    )
    assert invalid_res.status_code == 400
    assert "BR-002" in invalid_res.json()["error"]["message"]

    # 3. Valid transition to Under Review
    res1 = client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"new_status": "Under Review", "reason": "Passed initial screening"},
    )
    assert res1.status_code == 200

    # 4. Valid transition to Shortlisted
    res2 = client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"new_status": "Shortlisted", "reason": "Shortlisted by panel lead"},
    )
    assert res2.status_code == 200

    # 5. Valid transition to Selected from Shortlisted (Allowed by BR-002)
    res3 = client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"new_status": "Selected", "reason": "Final human selection confirmed"},
    )
    assert res3.status_code == 200
    assert res3.json()["data"]["current_status"] == "Selected"
    assert len(res3.json()["data"]["status_history"]) >= 4
