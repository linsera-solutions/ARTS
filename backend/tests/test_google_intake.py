import io
import pytest
from app.models.enums import ApplicationStatus


def test_google_forms_webhook_intake(client):
    """
    Tests POST /api/v1/intake/google-forms/webhook with real-time Google Apps Script format.
    """
    webhook_payload = {
        "timestamp": "2026-09-28T18:30:00Z",
        "email": "sarah.connor@space.org",
        "full_name": "Sarah Connor",
        "role": "Game Developer (Godot/Unity)",
        "phone_number": "+1-555-0199",
        "location": "Los Angeles, CA",
        "linkedin": "https://linkedin.com/in/sarah-connor",
        "github": "https://github.com/sarah-connor",
        "portfolio": "https://sarahconnor.dev",
        "motivation": "Passionate about orbital mechanics gameplay.",
        "availability": "Full-time during hackathon weekend",
        "skills": "Unity, C#, ShaderLab, Git",
        "experience": "5 years building 3D physics engines",
    }

    response = client.post("/api/v1/intake/google-forms/webhook", json=webhook_payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    res_data = res_json["data"]
    assert res_data["status"] == "created"
    assert res_data["email"] == "sarah.connor@space.org"
    assert res_data["role_name"] == "Game/App Developer"
    app_id = res_data["application_id"]

    # Verify candidate detail and evidence links
    detail_res = client.get(f"/api/v1/applications/{app_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()["data"]
    assert detail["current_status"] == ApplicationStatus.RECEIVED.value
    assert len(detail["applicant"]["portfolio_items"]) == 3
    assert len(detail["applicant"]["applicant_skills"]) == 4


def test_google_forms_webhook_deduplication(client):
    """
    Tests idempotent update when same email submits again with updated info.
    """
    update_payload = {
        "email": "sarah.connor@space.org",
        "full_name": "Sarah Connor",
        "role": "Game/App Developer",
        "motivation": "Updated motivation statement: Ready to lead dev track.",
        "availability": "40 hours total",
        "skills": "Unity, C#, Rust",
    }

    response = client.post("/api/v1/intake/google-forms/webhook", json=update_payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    res_data = res_json["data"]
    assert res_data["status"] == "updated"
    assert "Updated" in res_data["reason"]


def test_google_forms_csv_text_intake(client):
    """
    Tests POST /api/v1/intake/google-forms/csv with direct CSV string.
    """
    csv_content = """Timestamp,Email Address,Full Name,Target Role,LinkedIn,GitHub,Portfolio,Motivation Statement,Availability,Skills,Experience
2026-09-28 12:00:00,neil.armstrong@spaceapps.org,Neil Armstrong,Space/Science Research + Game Logic,https://linkedin.com/in/neil,https://github.com/neil,https://neil.aero,Lunar descent trajectories,20 hours,Astrophysics, Orbital Mechanics, Python,Apollo flight data analysis
2026-09-28 12:05:00,buzz.aldrin@spaceapps.org,Buzz Aldrin,UI/UX & Visual Designer,https://linkedin.com/in/buzz,,,Visual telemetry displays,15 hours,Figma, UI Design, Blender,Rendezvous radar displays
"""

    response = client.post(
        "/api/v1/intake/google-forms/csv",
        json={"csv_content": csv_content, "source_name": "Google Sheets Test Export"},
    )
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    res_data = res_json["data"]
    assert res_data["total_received"] == 2
    assert res_data["accepted"] == 2
    assert res_data["rejected"] == 0
    assert len(res_data["results"]) == 2


def test_google_forms_csv_file_upload(client):
    """
    Tests POST /api/v1/intake/google-forms/upload-csv with multipart file upload.
    """
    csv_bytes = b"""Timestamp,Email Address,Your Name,Which role are you applying for?,LinkedIn,Skills
2026-09-28 14:00:00,katherine.johnson@spaceapps.org,Katherine Johnson,Space/Science Research + Game Logic,https://linkedin.com/in/kjohnson,"Mathematics, Trajectory Calculation, Fortran"
"""
    files = {"file": ("google_forms_export.csv", io.BytesIO(csv_bytes), "text/csv")}
    data = {"source_name": "SpaceApps 2026 Live Form"}

    response = client.post("/api/v1/intake/google-forms/upload-csv", files=files, data=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    res_data = res_json["data"]
    assert res_data["total_received"] == 1
    assert res_data["accepted"] == 1
    assert res_data["rejected"] == 0


def test_google_sync_status_and_logs(client):
    """
    Tests GET /api/v1/intake/google-sheets/status and GET /api/v1/intake/logs
    """
    # 1. Check status
    status_res = client.get("/api/v1/intake/google-sheets/status")
    assert status_res.status_code == 200
    status_json = status_res.json()
    assert status_json["success"] is True
    status_data = status_json["data"]
    assert "webhook_enabled" in status_data
    assert status_data["webhook_enabled"] is True
    assert status_data["total_synced"] >= 4

    # 2. Check logs
    logs_res = client.get("/api/v1/intake/logs")
    assert logs_res.status_code == 200
    logs_json = logs_res.json()
    assert logs_json["success"] is True
    logs_data = logs_json["data"]
    assert len(logs_data) >= 2
    assert logs_data[0]["status"] in ["Success", "Partial", "Failed"]