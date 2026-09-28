from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.team import (
    TeamRead,
    TeamCreate,
    TeamUpdate,
    TeamMemberRead,
    TeamMemberAssignRequest,
    TeamMemberReassignRequest,
    TeamOverviewResponse,
)
from app.schemas.common import ResponseEnvelope
from app.services.team_service import team_service

router = APIRouter()


@router.get(
    "/overview",
    response_model=ResponseEnvelope[TeamOverviewResponse],
    summary="Get 4-Member Team Composition Overview",
    description=(
        "Returns the consolidated team roster state for the Team Formation workspace (SCR-08), "
        "including all 4 position slots with assigned candidate details, filled/open status, "
        "and unassigned selected candidates."
    ),
)
def get_team_overview(
    team_id: Optional[UUID] = Query(None, description="Optional Team ID (defaults to primary NASA team)"),
    db: Session = Depends(get_db),
):
    overview = team_service.get_team_overview(db, team_id=team_id)
    return ResponseEnvelope(data=overview)


@router.get(
    "",
    response_model=ResponseEnvelope[List[TeamRead]],
    summary="List Teams",
)
def list_teams(db: Session = Depends(get_db)):
    teams = team_service.get_multi(db)
    return ResponseEnvelope(data=teams)


@router.get(
    "/{id}",
    response_model=ResponseEnvelope[TeamRead],
    summary="Get Team by ID",
)
def get_team(id: UUID, db: Session = Depends(get_db)):
    team = team_service.get(db, id)
    return ResponseEnvelope(data=team)


@router.post(
    "/{id}/members",
    response_model=ResponseEnvelope[TeamMemberRead],
    status_code=status.HTTP_201_CREATED,
    summary="Assign Candidate to Team Role Slot",
    description=(
        "Assigns a Selected candidate application to an active role slot on the team. "
        "Validates that candidate is in 'Selected' status, not already occupying another slot, "
        "and that the role slot is not already filled."
    ),
)
def assign_team_member(
    id: UUID,
    data: TeamMemberAssignRequest,
    db: Session = Depends(get_db),
):
    member = team_service.assign_member(db, team_id=id, data=data)
    return ResponseEnvelope(data=member, message="Candidate confirmed for team role slot.")


@router.patch(
    "/members/{member_id}/reassign",
    response_model=ResponseEnvelope[TeamMemberRead],
    summary="Reassign Team Member to Different Role Slot",
    description="Moves an active team member from their current slot to another vacant role slot.",
)
def reassign_team_member(
    member_id: UUID,
    data: TeamMemberReassignRequest,
    db: Session = Depends(get_db),
):
    member = team_service.reassign_member(db, member_id=member_id, data=data)
    return ResponseEnvelope(data=member, message="Team member successfully reassigned to new role slot.")


@router.delete(
    "/members/{member_id}",
    response_model=ResponseEnvelope[None],
    summary="Remove Member from Team Role Slot",
    description="Removes a member from the active roster, reverting the role slot to 'Open'.",
)
def remove_team_member(
    member_id: UUID,
    reason: Optional[str] = Query(None, description="Optional removal reason note"),
    db: Session = Depends(get_db),
):
    team_service.remove_member(db, member_id=member_id, reason=reason)
    return ResponseEnvelope(data=None, message="Member removed from role slot; slot is now vacant.")