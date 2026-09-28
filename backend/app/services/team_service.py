from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session, joinedload
from app.models.team import Team, Role, TeamMember
from app.models.application import Application
from app.models.applicant import Applicant, ApplicantSkill
from app.models.enums import TeamStatus, MembershipStatus, RoleStatus, ApplicationStatus
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamMemberAssignRequest,
    TeamMemberReassignRequest,
    TeamOverviewResponse,
    RosterSlotRead,
    UnassignedCandidateRead,
    TeamMemberRead,
)
from app.services.base import BaseService
from app.core.exceptions import NotFoundException, BadRequestException, ConflictException
from app.db.init_db import DEFAULT_TEAM_NAME, DEFAULT_TEAM_DESC, APPROVED_ROLES


class TeamService(BaseService[Team]):
    def __init__(self):
        super().__init__(Team)

    def get_or_create_default_team(self, db: Session) -> Team:
        """
        Retrieves the primary NASA Space Apps team or initializes it with the 4 approved roles.
        """
        team = db.query(Team).filter(Team.team_name == DEFAULT_TEAM_NAME).first()
        if not team:
            team = Team(
                team_name=DEFAULT_TEAM_NAME,
                team_description=DEFAULT_TEAM_DESC,
                team_status=TeamStatus.FORMING.value,
            )
            db.add(team)
            db.flush()

            for role_data in APPROVED_ROLES:
                existing_role = db.query(Role).filter_by(role_name=role_data["role_name"]).first()
                if not existing_role:
                    role = Role(team_id=team.id, **role_data)
                    db.add(role)
                elif not existing_role.team_id:
                    existing_role.team_id = team.id

            db.commit()
            db.refresh(team)
        return team

    def get_team_overview(self, db: Session, team_id: Optional[UUID] = None) -> TeamOverviewResponse:
        """
        Returns the consolidated 4-position team roster overview for the Team Formation workspace.
        Includes slot states, confirmed candidate details, and unassigned selected candidates.
        """
        team = self.get(db, team_id) if team_id else self.get_or_create_default_team(db)

        # 1. Fetch team roles
        roles = (
            db.query(Role)
            .filter(Role.team_id == team.id)
            .order_by(Role.created_at.asc())
            .all()
        )

        # 2. Fetch active team members with relationships
        active_members = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team.id,
                TeamMember.membership_status == MembershipStatus.ACTIVE.value,
            )
            .options(
                joinedload(TeamMember.applicant),
                joinedload(TeamMember.role),
            )
            .all()
        )
        member_by_role = {m.role_id: m for m in active_members}
        active_applicant_ids = {m.applicant_id for m in active_members}

        # 3. Build 4 roster slots
        slots: List[RosterSlotRead] = []
        filled_count = 0
        for role in roles:
            assigned = member_by_role.get(role.id)
            is_filled = assigned is not None
            if is_filled:
                filled_count += 1
            slots.append(
                RosterSlotRead(
                    role_id=role.id,
                    role_name=role.role_name,
                    role_description=role.role_description,
                    number_of_openings=role.number_of_openings,
                    role_status=RoleStatus.FILLED if is_filled else RoleStatus.OPEN,
                    is_filled=is_filled,
                    assigned_member=assigned,
                )
            )

        # 4. Fetch all Selected applications
        selected_apps = (
            db.query(Application)
            .filter(Application.current_status == ApplicationStatus.SELECTED.value)
            .options(
                joinedload(Application.applicant).joinedload(Applicant.applicant_skills).joinedload(ApplicantSkill.skill),
                joinedload(Application.role),
            )
            .all()
        )

        # 5. Filter for Selected candidates who are not currently assigned to any active slot
        unassigned_candidates: List[UnassignedCandidateRead] = []
        for app in selected_apps:
            if app.applicant_id not in active_applicant_ids:
                skill_names = [
                    s.skill.skill_name for s in (app.applicant.applicant_skills or []) if s.skill
                ]
                unassigned_candidates.append(
                    UnassignedCandidateRead(
                        application_id=app.id,
                        applicant_id=app.applicant_id,
                        full_name=app.applicant.full_name,
                        email=app.applicant.email,
                        location=app.applicant.location,
                        original_applied_role=app.role.role_name if app.role else "General",
                        original_role_id=app.role_id,
                        skills=skill_names,
                        selection_date=app.last_updated_date or app.created_at,
                    )
                )

        return TeamOverviewResponse(
            team_id=team.id,
            team_name=team.team_name,
            team_description=team.team_description,
            team_status=team.team_status,
            total_slots=len(roles),
            filled_slots_count=filled_count,
            is_team_complete=(filled_count == len(roles) and len(roles) > 0),
            slots=slots,
            unassigned_selected_candidates=unassigned_candidates,
        )

    def assign_member(self, db: Session, team_id: UUID, data: TeamMemberAssignRequest) -> TeamMember:
        """
        Assigns a selected candidate application into an active role slot.
        Enforces validation rules:
        - Candidate must be in 'Selected' status (BR-003).
        - Candidate cannot already occupy another active slot on the team.
        - Role slot must not already be filled.
        """
        team = self.get(db, team_id)

        # 1. Validate application
        app = db.query(Application).filter(Application.id == data.application_id).first()
        if not app:
            raise NotFoundException("Application not found.")

        if app.current_status != ApplicationStatus.SELECTED.value:
            raise BadRequestException(
                f"Candidate must be in 'Selected' status to be assigned to a team roster slot "
                f"(current status: '{app.current_status}'). Please finalize the candidate selection first."
            )

        # 2. Validate candidate uniqueness on active roster
        existing_active = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team.id,
                TeamMember.applicant_id == app.applicant_id,
                TeamMember.membership_status == MembershipStatus.ACTIVE.value,
            )
            .first()
        )
        if existing_active:
            raise ConflictException(
                f"Candidate '{app.applicant.full_name}' is already assigned to active role slot "
                f"'{existing_active.role.role_name}'. Use re-assignment to move them to a different role."
            )

        # 3. Validate target role slot availability
        role = db.query(Role).filter(Role.id == data.role_id, Role.team_id == team.id).first()
        if not role:
            raise NotFoundException("Target role slot not found on this team.")

        current_occupant = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team.id,
                TeamMember.role_id == role.id,
                TeamMember.membership_status == MembershipStatus.ACTIVE.value,
            )
            .first()
        )
        if current_occupant:
            raise ConflictException(
                f"Role slot '{role.role_name}' is already filled by '{current_occupant.applicant.full_name}'. "
                f"Remove or reassign the current occupant before assigning a new candidate."
            )

        # 4. Create confirmed team member assignment
        member = TeamMember(
            team_id=team.id,
            applicant_id=app.applicant_id,
            source_application_id=app.id,
            role_id=role.id,
            join_date=date.today(),
            membership_status=MembershipStatus.ACTIVE.value,
        )
        db.add(member)

        # Update role status to Filled
        role.role_status = RoleStatus.FILLED.value

        # Check if team is now completely filled (all roles have active members)
        total_roles = db.query(Role).filter(Role.team_id == team.id).count()
        filled_roles = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team.id,
                TeamMember.membership_status == MembershipStatus.ACTIVE.value,
            )
            .count()
            + 1  # Including the one we are currently adding
        )
        if filled_roles >= total_roles and total_roles > 0:
            team.team_status = TeamStatus.ACTIVE.value

        db.commit()
        db.refresh(member)
        return member

    def reassign_member(self, db: Session, member_id: UUID, data: TeamMemberReassignRequest) -> TeamMember:
        """
        Reassigns an active member to a different vacant role slot.
        """
        member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
        if not member:
            raise NotFoundException("Team member record not found.")

        if member.membership_status != MembershipStatus.ACTIVE.value:
            raise BadRequestException("Only active team members can be reassigned.")

        if member.role_id == data.target_role_id:
            return member

        target_role = db.query(Role).filter(Role.id == data.target_role_id, Role.team_id == member.team_id).first()
        if not target_role:
            raise NotFoundException("Target role slot not found on this team.")

        # Check if target role already has an active occupant
        occupant = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == member.team_id,
                TeamMember.role_id == target_role.id,
                TeamMember.membership_status == MembershipStatus.ACTIVE.value,
            )
            .first()
        )
        if occupant:
            raise ConflictException(
                f"Target role slot '{target_role.role_name}' is already filled by '{occupant.applicant.full_name}'."
            )

        old_role = db.query(Role).filter(Role.id == member.role_id).first()
        if old_role:
            old_role.role_status = RoleStatus.OPEN.value

        member.role_id = target_role.id
        target_role.role_status = RoleStatus.FILLED.value

        db.commit()
        db.refresh(member)
        return member

    def remove_member(self, db: Session, member_id: UUID, reason: Optional[str] = None) -> None:
        """
        Removes a member from the active team roster and returns the role slot to 'Open'.
        """
        member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
        if not member:
            raise NotFoundException("Team member not found.")

        role = db.query(Role).filter(Role.id == member.role_id).first()
        if role:
            role.role_status = RoleStatus.OPEN.value

        team = db.query(Team).filter(Team.id == member.team_id).first()
        if team:
            team.team_status = TeamStatus.FORMING.value

        member.membership_status = MembershipStatus.REMOVED.value
        db.commit()


team_service = TeamService()