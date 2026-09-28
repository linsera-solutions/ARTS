import pytest
from app.models.enums import ApplicationStatus, InterviewStatus


def test_recruitment_workflow_complete_progression(client):
    """
    Tests the complete progression of a candidate through the approved recruitment workflow:
    Received -> Under Review -> Shortlisted -> Discussion / Interview -> Selected
    """
    # 1. Intake application (Starts in 'Received')
    intake_payload = {
        "full_name": "Peggy Whitson",
        "email": "peggy.whitson@space.org",
        "role_name": "Game/App Developer",
        "motivation_statement": "Extensive experience with space systems simulation and game architecture.",
    }
    app_res = client.post("/api/v1/applications/intake", json=intake_payload)
    assert app_res.status_code == 201
    app_id = app_res.json()["data"]["application_id"]

    # 2. Check allowed transitions from 'Received'
    trans_res = client.get(f"/api/v1/applications/{app_id}/allowed-transitions")
    assert trans_res.status_code == 200
    allowed = trans_res.json()["data"]["allowed_transitions"]
    assert "Under Review" in allowed
    assert "Not Selected" in allowed
    assert "Withdrawn" in allowed
    assert "Selected" not in allowed
    assert "Shortlisted" not in allowed
    assert "Discussion / Interview" not in allowed

    # 3. Transition: Received -> Under Review
    step1 = client.patch(f"/api/v1/applications/{app_id}/status", json={
        "new_status": "Under Review",
        "reason": "Initial screening passed; reviewing code repository and portfolio.",
    })
    assert step1.status_code == 200
    assert step1.json()["data"]["current_status"] == "Under Review"

    # 4. Check allowed transitions from 'Under Review'
    trans_res2 = client.get(f"/api/v1/applications/{app_id}/allowed-transitions")
    allowed2 = trans_res2.json()["data"]["allowed_transitions"]
    assert "Shortlisted" in allowed2
    assert "Not Selected" in allowed2
    assert "Withdrawn" in allowed2
    assert "Selected" not in allowed2  # Direct jump to Selected from Under Review must be blocked

    # 5. Transition: Under Review -> Shortlisted
    step2 = client.patch(f"/api/v1/applications/{app_id}/status", json={
        "new_status": "Shortlisted",
        "reason": "Strong evidence in Godot and simulation architecture.",
    })
    assert step2.status_code == 200
    assert step2.json()["data"]["current_status"] == "Shortlisted"

    # 6. Verify application appears in Shortlist query
    shortlist_res = client.get("/api/v1/applications?status=Shortlisted")
    assert shortlist_res.status_code == 200
    shortlisted_ids = [a["id"] for a in shortlist_res.json()["data"]["items"]]
    assert app_id in shortlisted_ids

    # 7. Transition: Shortlisted -> Discussion / Interview
    step3 = client.patch(f"/api/v1/applications/{app_id}/status", json={
        "new_status": "Discussion / Interview",
        "reason": "Invited for 30-min technical and role alignment discussion.",
    })
    assert step3.status_code == 200
    assert step3.json()["data"]["current_status"] == "Discussion / Interview"

    # 8. Schedule and conduct interview
    interview_res = client.post("/api/v1/interviews", json={
        "application_id": app_id,
        "scheduled_at": "2026-10-01T14:00:00Z",
        "format": "Video Call",
        "status": "Scheduled",
        "outcome_summary": "Scheduled technical discussion.",
    })
    assert interview_res.status_code == 201
    interview_id = interview_res.json()["data"]["id"]

    # 9. Update interview with completed outcome
    update_interview_res = client.patch(f"/api/v1/interviews/{interview_id}", json={
        "status": "Completed",
        "outcome_summary": "Candidate demonstrated excellent communication and clear technical command.",
    })
    assert update_interview_res.status_code == 200
    assert update_interview_res.json()["data"]["status"] == "Completed"

    # 10. Transition: Discussion / Interview -> Selected
    step4 = client.patch(f"/api/v1/applications/{app_id}/status", json={
        "new_status": "Selected",
        "reason": "Unanimous team consensus to offer Game/App Developer roster slot.",
    })
    assert step4.status_code == 200
    assert step4.json()["data"]["current_status"] == "Selected"

    # 11. Verify complete status audit history is preserved in detail view
    detail_res = client.get(f"/api/v1/applications/{app_id}")
    assert detail_res.status_code == 200
    history = detail_res.json()["data"]["status_history"]
    assert len(history) == 5  # Initial intake + 4 transitions
    statuses_traversed = [h["new_status"] for h in history]
    assert statuses_traversed == ["Received", "Under Review", "Shortlisted", "Discussion / Interview", "Selected"]
    assert all(h["changed_at"] is not None for h in history)
    assert all(h["reason"] is not None for h in history)


def test_invalid_status_transitions_rejected(client):
    """
    Tests that illegal jumps across the workflow are strictly blocked with 400 Bad Request.
    """
    intake_payload = {
        "full_name": "Scott Kelly",
        "email": "scott.kelly@space.org",
        "role_name": "UI/UX & Visual Designer",
    }
    app_res = client.post("/api/v1/applications/intake", json=intake_payload)
    app_id = app_res.json()["data"]["application_id"]

    # Invalid: Received -> Selected
    res1 = client.patch(f"/api/v1/applications/{app_id}/status", json={"new_status": "Selected"})
    assert res1.status_code == 400

    # Invalid: Received -> Discussion / Interview
    res2 = client.patch(f"/api/v1/applications/{app_id}/status", json={"new_status": "Discussion / Interview"})
    assert res2.status_code == 400

    # Move to Under Review
    client.patch(f"/api/v1/applications/{app_id}/status", json={"new_status": "Under Review"})

    # Invalid: Under Review -> Selected (Direct selection without shortlist/interview is blocked)
    res3 = client.patch(f"/api/v1/applications/{app_id}/status", json={"new_status": "Selected"})
    assert res3.status_code == 400

    # Move to Withdrawn (Terminal)
    client.patch(f"/api/v1/applications/{app_id}/status", json={"new_status": "Withdrawn", "reason": "Candidate withdrew"})

    # Invalid: Withdrawn -> Under Review (Terminal status)
    res4 = client.patch(f"/api/v1/applications/{app_id}/status", json={"new_status": "Under Review"})
    assert res4.status_code == 400


def test_interviews_list_all_and_filtered(client):
    """
    Tests GET /api/v1/interviews listing across all candidates and filtering by status.
    """
    list_all = client.get("/api/v1/interviews")
    assert list_all.status_code == 200
    assert isinstance(list_all.json()["data"], list)

    list_completed = client.get("/api/v1/interviews?status=Completed")
    assert list_completed.status_code == 200
    assert all(i["status"] == "Completed" for i in list_completed.json()["data"])