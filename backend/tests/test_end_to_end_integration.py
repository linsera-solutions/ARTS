import pytest
from app.models.enums import ApplicationStatus, RoleStatus, TeamStatus


def test_complete_end_to_end_arts_workflow(client):
    """
    End-to-End Integration Verification:
    Google Forms Intake -> Review & Evaluation -> Shortlist -> Discussion -> Selection -> Team Formation Roster
    """
    # =========================================================================
    # STEP 1: Candidate Application Intake (Google Forms Simulation)
    # =========================================================================
    intake_1 = {
        "full_name": "Astraea Vance",
        "email": "astraea.vance@galaxy.org",
        "role_name": "Team Lead + Product/Game Concept Lead / Research & Presentation",
        "motivation_statement": "Experienced mission concept director with background in interactive astrophysics narrative.",
        "availability_info": "Available 30 hrs/week throughout the challenge period.",
        "skills": [
            {"skill_name": "Mission Architecture", "proficiency_level": "Expert"},
            {"skill_name": "Scientific Writing", "proficiency_level": "Advanced"},
        ],
        "evidence_links": [
            {"title": "Mars Habitat Concept Pitch", "reference_link": "https://behance.net/mars-concept"},
            {"title": "Astrophysics Simulation Demo", "reference_link": "https://github.com/astraea/sim"},
        ],
        "experiences": [
            {
                "title": "Lead Concept Designer",
                "organization": "Orbital Dynamics Lab",
                "start_date": "2023-01-15",
                "description": "Directed 6-person hackathon team",
            }
        ],
    }
    res_intake = client.post("/api/v1/applications/intake", json=intake_1)
    assert res_intake.status_code == 201
    app_id = res_intake.json()["data"]["application_id"]
    applicant_id = res_intake.json()["data"]["applicant_id"]

    # Ingest 3 other candidates for the other 3 roles to demonstrate complete team formation
    dev_app_id = client.post("/api/v1/applications/intake", json={
        "full_name": "Kaelen Voss",
        "email": "kaelen.voss@galaxy.org",
        "role_name": "Game/App Developer",
        "motivation_statement": "Godot & Unity game engine architect with shaders and procedural generation experience.",
    }).json()["data"]["application_id"]

    ui_app_id = client.post("/api/v1/applications/intake", json={
        "full_name": "Lyra Thorne",
        "email": "lyra.thorne@galaxy.org",
        "role_name": "UI/UX & Visual Designer",
        "motivation_statement": "UI designer specialized in HUD interfaces and sci-fi aesthetic workflows.",
    }).json()["data"]["application_id"]

    science_app_id = client.post("/api/v1/applications/intake", json={
        "full_name": "Dr. Orion Cruz",
        "email": "orion.cruz@galaxy.org",
        "role_name": "Space/Science Research + Game Logic",
        "motivation_statement": "Planetary scientist passionate about orbital mechanic fidelity in games.",
    }).json()["data"]["application_id"]

    # =========================================================================
    # STEP 2: Screen 1 - Dashboard & Screen 2 - Applications List
    # =========================================================================
    apps_list = client.get("/api/v1/applications?query=Astraea")
    assert apps_list.status_code == 200
    assert apps_list.json()["data"]["total"] >= 1
    assert apps_list.json()["data"]["items"][0]["current_status"] == "Received"

    # =========================================================================
    # STEP 3: Screen 3 - Candidate Detail & Status Transition
    # =========================================================================
    detail = client.get(f"/api/v1/applications/{app_id}")
    assert detail.status_code == 200
    detail_data = detail.json()["data"]
    assert detail_data["applicant"]["full_name"] == "Astraea Vance"
    assert len(detail_data["applicant"]["portfolio_items"]) == 2
    assert len(detail_data["applicant"]["applicant_skills"]) == 2

    # Verify allowed transitions from Received
    allowed_from_received = client.get(f"/api/v1/applications/{app_id}/allowed-transitions").json()["data"]["allowed_transitions"]
    assert "Under Review" in allowed_from_received
    assert "Selected" not in allowed_from_received

    # Move to Under Review
    client.patch(f"/api/v1/applications/{app_id}/status", json={
        "new_status": "Under Review",
        "reason": "Initial submission review initiated",
    })

    # =========================================================================
    # STEP 4: Screen 4 - Review & Qualitative Evaluation
    # =========================================================================
    criteria = client.get("/api/v1/evaluations/criteria").json()["data"]
    assert len(criteria) == 5

    eval_payload = {
        "application_id": app_id,
        "overall_recommendation": "Advance",
        "overall_comments": "Exceptional leadership profile with demonstrable mission design evidence.",
        "strengths": "Proven track record in team leadership and astrophysics visualization.",
        "concerns": "Confirm time commitment during synchronized challenge sprints.",
        "evaluation_status": "Submitted",
        "scores": [
            {
                "criterion_id": criteria[0]["id"],
                "qualitative_rating": "Strong Evidence",
                "score_comment": "Portfolio pitch deck demonstrates clear concept design skills.",
            },
            {
                "criterion_id": criteria[1]["id"],
                "qualitative_rating": "Strong Evidence",
                "score_comment": "GitHub repository exhibits working simulation prototype.",
            },
        ],
    }
    eval_res = client.post("/api/v1/evaluations/upsert", json=eval_payload)
    assert eval_res.status_code == 200
    assert eval_res.json()["data"]["evaluation_status"] == "Submitted"

    # Add informal reviewer note
    note_res = client.post("/api/v1/notes", json={
        "author_id": applicant_id,
        "related_entity_type": "Application",
        "related_entity_id": app_id,
        "note_text": "Team Lead alignment verified. Excellent communication clarity.",
        "visibility": "Internal",
    })
    assert note_res.status_code == 201

    # =========================================================================
    # STEP 5: Screen 5 - Shortlist Workspace
    # =========================================================================
    # Transition: Under Review -> Shortlisted
    client.patch(f"/api/v1/applications/{app_id}/status", json={
        "new_status": "Shortlisted",
        "reason": "Vetted and approved for shortlist by recruiter",
    })

    # Verify candidate appears in shortlist query
    shortlist_res = client.get("/api/v1/applications?status=Shortlisted")
    assert shortlist_res.status_code == 200
    shortlisted_ids = [a["id"] for a in shortlist_res.json()["data"]["items"]]
    assert app_id in shortlisted_ids

    # =========================================================================
    # STEP 6: Screen 6 - Candidate Discussion / Interview Workspace
    # =========================================================================
    # Transition: Shortlisted -> Discussion / Interview
    client.patch(f"/api/v1/applications/{app_id}/status", json={
        "new_status": "Discussion / Interview",
        "reason": "Scheduled for video call discussion",
    })

    # Schedule interview
    interview_res = client.post("/api/v1/interviews", json={
        "application_id": app_id,
        "scheduled_at": "2026-10-02T16:00:00Z",
        "format": "Video Call",
        "status": "Scheduled",
        "outcome_summary": "Discuss challenge roadmap and sprint cadence",
    })
    assert interview_res.status_code == 201
    interview_id = interview_res.json()["data"]["id"]

    # Record interview outcome & confirm Selected status
    client.patch(f"/api/v1/interviews/{interview_id}", json={
        "status": "Completed",
        "outcome_summary": "Unanimous consensus: Excellent vision, communication, and clear readiness to lead.",
    })
    client.patch(f"/api/v1/applications/{app_id}/status", json={
        "new_status": "Selected",
        "reason": "Confirmed selected candidate for Team Lead position",
    })

    # Advance the other 3 candidates to Selected status
    for other_id in [dev_app_id, ui_app_id, science_app_id]:
        client.patch(f"/api/v1/applications/{other_id}/status", json={"new_status": "Under Review"})
        client.patch(f"/api/v1/applications/{other_id}/status", json={"new_status": "Shortlisted"})
        client.patch(f"/api/v1/applications/{other_id}/status", json={"new_status": "Selected", "reason": "Candidate vetted and selected"})

    # =========================================================================
    # STEP 7: Screen 7 - Team Formation & 4-Member Roster Assembly
    # =========================================================================
    team_overview = client.get("/api/v1/teams/overview").json()["data"]
    team_id = team_overview["team_id"]
    slots = team_overview["slots"]
    assert len(slots) == 4

    slot_lead = next(s for s in slots if "Team Lead" in s["role_name"])
    slot_dev = next(s for s in slots if "Game/App" in s["role_name"])
    slot_ui = next(s for s in slots if "UI/UX" in s["role_name"])
    slot_science = next(s for s in slots if "Space/Science" in s["role_name"])

    # 1. Assign Astraea to Team Lead Slot
    assign_lead = client.post(f"/api/v1/teams/{team_id}/members", json={
        "application_id": app_id,
        "role_id": slot_lead["role_id"],
    })
    assert assign_lead.status_code == 201

    # 2. Assign Kaelen to Dev Slot
    assign_dev = client.post(f"/api/v1/teams/{team_id}/members", json={
        "application_id": dev_app_id,
        "role_id": slot_dev["role_id"],
    })
    assert assign_dev.status_code == 201

    # 3. Assign Lyra to UI/UX Slot
    assign_ui = client.post(f"/api/v1/teams/{team_id}/members", json={
        "application_id": ui_app_id,
        "role_id": slot_ui["role_id"],
    })
    assert assign_ui.status_code == 201

    # 4. Assign Orion to Science Slot
    assign_science = client.post(f"/api/v1/teams/{team_id}/members", json={
        "application_id": science_app_id,
        "role_id": slot_science["role_id"],
    })
    assert assign_science.status_code == 201

    # =========================================================================
    # STEP 8: Verify Complete 4-Person Roster State
    # =========================================================================
    final_overview = client.get("/api/v1/teams/overview").json()["data"]
    assert final_overview["total_slots"] == 4
    assert final_overview["filled_slots_count"] == 4
    assert final_overview["is_team_complete"] is True
    assert final_overview["team_status"] == TeamStatus.ACTIVE.value
    assert all(s["is_filled"] is True for s in final_overview["slots"])