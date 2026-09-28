import pytest
from app.models.enums import ApplicationStatus, RoleStatus, TeamStatus


def test_team_overview_initial_state(client):
    """
    Tests GET /api/v1/teams/overview returns the 4 approved NASA roles as slots.
    """
    # Clean any prior test members
    overview = client.get("/api/v1/teams/overview").json()["data"]
    for slot in overview["slots"]:
        if slot["is_filled"] and slot["assigned_member"]:
            client.delete(f"/api/v1/teams/members/{slot['assigned_member']['id']}")

    res = client.get("/api/v1/teams/overview")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["team_name"] == "NASA Space Apps Challenge Team"
    assert data["total_slots"] == 4
    assert data["filled_slots_count"] == 0
    assert data["is_team_complete"] is False
    assert len(data["slots"]) == 4

    role_names = [s["role_name"] for s in data["slots"]]
    assert "Team Lead + Product/Game Concept Lead / Research & Presentation" in role_names
    assert "Game/App Developer" in role_names
    assert "UI/UX & Visual Designer" in role_names
    assert "Space/Science Research + Game Logic" in role_names


def test_team_member_assignment_and_validation(client):
    """
    Tests assigning a selected candidate to a role slot and validating business rules:
    - Candidate must be in Selected status
    - Slot must be vacant
    - Candidate cannot occupy multiple slots
    """
    # 1. Ingest candidates
    cand1 = client.post("/api/v1/applications/intake", json={
        "full_name": "Sally Ride",
        "email": "sally.ride@space.org",
        "role_name": "Space/Science Research + Game Logic",
    }).json()["data"]
    app_id1 = cand1["application_id"]

    cand2 = client.post("/api/v1/applications/intake", json={
        "full_name": "Alan Shepard",
        "email": "alan.shepard@space.org",
        "role_name": "Game/App Developer",
    }).json()["data"]
    app_id2 = cand2["application_id"]

    # 2. Fetch team overview to get team_id and role IDs
    overview = client.get("/api/v1/teams/overview").json()["data"]
    team_id = overview["team_id"]
    science_slot = next(s for s in overview["slots"] if "Space/Science" in s["role_name"])
    dev_slot = next(s for s in overview["slots"] if "Game/App" in s["role_name"])

    # 3. Attempt to assign candidate in 'Received' status (Must be rejected: not Selected)
    bad_assign = client.post(f"/api/v1/teams/{team_id}/members", json={
        "application_id": app_id1,
        "role_id": science_slot["role_id"],
    })
    assert bad_assign.status_code == 400
    assert "Selected" in bad_assign.json()["error"]["message"]

    # 4. Advance candidate 1 to Selected through approved workflow
    client.patch(f"/api/v1/applications/{app_id1}/status", json={"new_status": "Under Review"})
    client.patch(f"/api/v1/applications/{app_id1}/status", json={"new_status": "Shortlisted"})
    client.patch(f"/api/v1/applications/{app_id1}/status", json={"new_status": "Selected", "reason": "Approved candidate"})

    # 5. Check that candidate 1 now appears in unassigned_selected_candidates
    overview2 = client.get("/api/v1/teams/overview").json()["data"]
    unassigned_emails = [c["email"] for c in overview2["unassigned_selected_candidates"]]
    assert "sally.ride@space.org" in unassigned_emails

    # 6. Assign Candidate 1 to Space/Science slot
    assign_res = client.post(f"/api/v1/teams/{team_id}/members", json={
        "application_id": app_id1,
        "role_id": science_slot["role_id"],
    })
    assert assign_res.status_code == 201
    member1_id = assign_res.json()["data"]["id"]

    # 7. Verify slot is now filled and candidate 1 is no longer in unassigned list
    overview3 = client.get("/api/v1/teams/overview").json()["data"]
    assert overview3["filled_slots_count"] == 1
    science_slot_updated = next(s for s in overview3["slots"] if s["role_id"] == science_slot["role_id"])
    assert science_slot_updated["is_filled"] is True
    assert science_slot_updated["assigned_member"]["applicant"]["full_name"] == "Sally Ride"
    assert "sally.ride@space.org" not in [c["email"] for c in overview3["unassigned_selected_candidates"]]

    # 8. Attempt duplicate assignment: Candidate 1 cannot be assigned to another slot simultaneously
    dup_assign = client.post(f"/api/v1/teams/{team_id}/members", json={
        "application_id": app_id1,
        "role_id": dev_slot["role_id"],
    })
    assert dup_assign.status_code == 409
    assert "already assigned" in dup_assign.json()["error"]["message"].lower()

    # 9. Advance candidate 2 to Selected
    client.patch(f"/api/v1/applications/{app_id2}/status", json={"new_status": "Under Review"})
    client.patch(f"/api/v1/applications/{app_id2}/status", json={"new_status": "Shortlisted"})
    client.patch(f"/api/v1/applications/{app_id2}/status", json={"new_status": "Selected", "reason": "Approved candidate"})

    # 10. Attempt to assign candidate 2 to already-filled science slot
    slot_full_res = client.post(f"/api/v1/teams/{team_id}/members", json={
        "application_id": app_id2,
        "role_id": science_slot["role_id"],
    })
    assert slot_full_res.status_code == 409
    assert "already filled" in slot_full_res.json()["error"]["message"].lower()

    # 11. Reassign Candidate 1 from Science slot to Dev slot
    reassign_res = client.patch(f"/api/v1/teams/members/{member1_id}/reassign", json={
        "target_role_id": dev_slot["role_id"],
        "reason": "Rebalanced team role assignments based on strong software skills",
    })
    assert reassign_res.status_code == 200

    overview4 = client.get("/api/v1/teams/overview").json()["data"]
    science_slot4 = next(s for s in overview4["slots"] if s["role_id"] == science_slot["role_id"])
    dev_slot4 = next(s for s in overview4["slots"] if s["role_id"] == dev_slot["role_id"])
    assert science_slot4["is_filled"] is False
    assert dev_slot4["is_filled"] is True

    # 12. Remove Candidate 1 from roster
    remove_res = client.delete(f"/api/v1/teams/members/{member1_id}")
    assert remove_res.status_code == 200

    overview5 = client.get("/api/v1/teams/overview").json()["data"]
    dev_slot5 = next(s for s in overview5["slots"] if s["role_id"] == dev_slot["role_id"])
    assert dev_slot5["is_filled"] is False
    assert overview5["filled_slots_count"] == 0