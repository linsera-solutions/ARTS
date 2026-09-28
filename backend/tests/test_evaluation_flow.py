import pytest
from app.models.enums import (
    ApplicationStatus,
    EvaluationRecommendation,
    EvaluationStatus,
)


def test_list_evaluation_criteria(client):
    """
    Tests GET /api/v1/evaluations/criteria returns the 5 seeded criteria.
    """
    response = client.get("/api/v1/evaluations/criteria")
    assert response.status_code == 200
    res_data = response.json()["data"]
    assert len(res_data) == 5
    crit_names = [c["criterion_name"] for c in res_data]
    assert "Relevant Skills & Technical Competency" in crit_names
    assert "Project Experience & Demonstrable Work" in crit_names
    assert "Motivation & Role Alignment" in crit_names
    assert "Availability & Commitment" in crit_names
    assert "Communication Clarity" in crit_names


def test_create_qualitative_draft_evaluation(client):
    """
    Tests creating a Draft qualitative evaluation with per-criterion qualitative ratings.
    No mandatory numeric scores — strengths and concerns are reviewer-authored text.
    """
    # 1. Create an application via intake
    intake_payload = {
        "full_name": "Dr. Mae Jemison",
        "email": "mae.jemison@space.org",
        "role_name": "Space/Science Research + Game Logic",
        "motivation_statement": "Deep interest in orbital mechanics and science communication.",
        "availability_info": "Available 25 hours per week.",
        "skills": [{"skill_name": "Physics", "proficiency_level": "Expert"}],
        "evidence_links": [{"title": "Research Paper", "reference_link": "https://arxiv.org/abs/example"}],
    }
    app_res = client.post("/api/v1/applications/intake", json=intake_payload)
    assert app_res.status_code == 201
    application_id = app_res.json()["data"]["application_id"]

    # 2. Get criteria IDs
    crit_res = client.get("/api/v1/evaluations/criteria")
    assert crit_res.status_code == 200
    criteria = crit_res.json()["data"]
    assert len(criteria) >= 3

    # 3. Create Draft Qualitative Evaluation via /upsert (primary review form endpoint)
    eval_payload = {
        "application_id": application_id,
        # reviewer_id omitted: backend falls back to first user (MVP mode)
        "overall_recommendation": EvaluationRecommendation.ADVANCE.value,
        "overall_comments": "Exceptional scientific background with relevant simulation interest.",
        "strengths": "Strong background in astrophysical modeling; clear communication in submitted paper.",
        "concerns": "Verify specific engine/coding preference during discussion.",
        "evaluation_status": EvaluationStatus.DRAFT.value,
        "scores": [
            {
                "criterion_id": criteria[0]["id"],
                "qualitative_rating": "Strong Evidence",
                "score_comment": "Evidence demonstrates domain expertise aligned with game logic.",
            },
            {
                "criterion_id": criteria[2]["id"],
                "qualitative_rating": "Strong Evidence",
                "score_comment": "Motivation statement is specific and well-aligned.",
            },
            {
                "criterion_id": criteria[3]["id"],
                "qualitative_rating": "Some Evidence",
                "score_comment": "Stated 25 hrs/week commitment.",
            },
        ],
    }

    eval_res = client.post("/api/v1/evaluations/upsert", json=eval_payload)
    assert eval_res.status_code == 200
    eval_data = eval_res.json()["data"]
    assert eval_data["evaluation_status"] == EvaluationStatus.DRAFT.value
    assert eval_data["overall_recommendation"] == EvaluationRecommendation.ADVANCE.value
    assert eval_data["strengths"] is not None
    assert eval_data["concerns"] is not None
    assert len(eval_data["scores"]) == 3
    # Verify qualitative_rating is persisted (not a numeric score)
    assert eval_data["scores"][0]["qualitative_rating"] == "Strong Evidence"
    assert eval_data["scores"][0]["score_value"] is None  # No mandatory numeric score
    eval_id = eval_data["id"]

    # 4. Upsert again to update (same reviewer+application: should UPDATE not create new)
    update_payload = {
        "application_id": application_id,
        "evaluation_status": EvaluationStatus.SUBMITTED.value,
        "overall_comments": "Finalized review: Candidate recommended for Discussion / Interview.",
        "strengths": "Exceptional scientist with direct NASA challenge relevance.",
        "concerns": "Coding skill depth to be verified.",
        "scores": eval_payload["scores"],  # keep same scores
    }
    update_res = client.post("/api/v1/evaluations/upsert", json=update_payload)
    assert update_res.status_code == 200
    updated_data = update_res.json()["data"]
    assert updated_data["evaluation_status"] == EvaluationStatus.SUBMITTED.value
    assert updated_data["submission_date"] is not None
    assert updated_data["id"] == eval_id  # Same evaluation updated, not new one created

    # 5. Verify the evaluation is retrievable from the application
    list_res = client.get(f"/api/v1/evaluations?application_id={application_id}")
    assert list_res.status_code == 200
    evals = list_res.json()["data"]
    assert len(evals) == 1
    assert evals[0]["evaluation_status"] == EvaluationStatus.SUBMITTED.value


def test_draft_evaluation_cannot_be_deleted_if_submitted(client):
    """
    Tests that submitted evaluations are protected from deletion (audit integrity).
    """
    # Get the submitted evaluation from previous test
    crit_res = client.get("/api/v1/evaluations/criteria")
    criteria = crit_res.json()["data"]

    intake_payload = {
        "full_name": "Chris Hadfield",
        "email": "chris.hadfield@space.org",
        "role_name": "Team Lead + Product/Game Concept Lead / Research & Presentation",
        "motivation_statement": "Experienced team leader and science communicator.",
    }
    app_res = client.post("/api/v1/applications/intake", json=intake_payload)
    application_id = app_res.json()["data"]["application_id"]

    # Create and submit
    eval_res = client.post("/api/v1/evaluations/upsert", json={
        "application_id": application_id,
        "evaluation_status": EvaluationStatus.SUBMITTED.value,
        "overall_comments": "Strong candidate.",
        "scores": [],
    })
    eval_id = eval_res.json()["data"]["id"]

    # Attempt to delete submitted evaluation — should be blocked
    del_res = client.delete(f"/api/v1/evaluations/{eval_id}")
    assert del_res.status_code == 400
    assert "submitted" in del_res.json()["error"]["message"].lower()


def test_reviewer_notes_crud(client):
    """
    Tests adding, listing, updating, and deleting reviewer notes on an application.
    Notes are informal reviewer annotations — separate from formal Evaluation records.
    """
    # 1. Get an application
    app_res = client.get("/api/v1/applications?query=Mae")
    app_item = app_res.json()["data"]["items"][0]
    app_id = app_item["id"]
    author_id = app_item["applicant_id"]

    # 2. Add a note
    note_payload = {
        "author_id": author_id,
        "related_entity_type": "Application",
        "related_entity_id": app_id,
        "note_text": "Candidate demonstrates clear domain leadership potential.",
        "visibility": "Internal",
    }
    note_res = client.post("/api/v1/notes", json=note_payload)
    assert note_res.status_code == 201
    note_id = note_res.json()["data"]["id"]
    assert note_res.json()["data"]["note_text"] == "Candidate demonstrates clear domain leadership potential."

    # 3. Update the note
    update_res = client.patch(f"/api/v1/notes/{note_id}", json={"note_text": "Updated: Verified strong orbital mechanics background."})
    assert update_res.status_code == 200
    assert update_res.json()["data"]["note_text"] == "Updated: Verified strong orbital mechanics background."

    # 4. List notes by entity
    list_res = client.get(f"/api/v1/notes?entity_type=Application&entity_id={app_id}")
    assert list_res.status_code == 200
    notes_list = list_res.json()["data"]
    assert any(n["id"] == note_id for n in notes_list)

    # 5. Delete the note
    del_res = client.delete(f"/api/v1/notes/{note_id}")
    assert del_res.status_code == 200