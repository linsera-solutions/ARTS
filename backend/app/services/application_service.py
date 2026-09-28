from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.application import Application, ApplicationStatusHistory
from app.models.applicant import Applicant, Experience, PortfolioItem, ApplicantSkill, Skill
from app.models.team import Role
from app.models.evaluation import Evaluation
from app.models.interview import Interview
from app.models.note import Note
from app.schemas.application import (
    ApplicationCreate,
    ApplicationStatusUpdate,
    ApplicationIntakeRequest,
    ApplicationBatchIntakeRequest,
    IntakeSummaryResponse,
    IntakeResultItem,
)
from app.models.enums import ApplicationStatus
from app.services.base import BaseService
from app.core.exceptions import NotFoundException, BadRequestException, ConflictException

# Approved Recruitment Workflow Transition Matrix (BR-001, BR-002)
ALLOWED_TRANSITIONS = {
    ApplicationStatus.RECEIVED.value: [
        ApplicationStatus.UNDER_REVIEW.value,
        ApplicationStatus.NOT_SELECTED.value,
        ApplicationStatus.WITHDRAWN.value,
    ],
    ApplicationStatus.UNDER_REVIEW.value: [
        ApplicationStatus.SHORTLISTED.value,
        ApplicationStatus.NOT_SELECTED.value,
        ApplicationStatus.WITHDRAWN.value,
    ],
    ApplicationStatus.SHORTLISTED.value: [
        ApplicationStatus.DISCUSSION_INTERVIEW.value,
        ApplicationStatus.SELECTED.value,
        ApplicationStatus.NOT_SELECTED.value,
        ApplicationStatus.WITHDRAWN.value,
    ],
    ApplicationStatus.DISCUSSION_INTERVIEW.value: [
        ApplicationStatus.SELECTED.value,
        ApplicationStatus.SHORTLISTED.value,
        ApplicationStatus.NOT_SELECTED.value,
        ApplicationStatus.WITHDRAWN.value,
    ],
    ApplicationStatus.SELECTED.value: [
        ApplicationStatus.WITHDRAWN.value,
    ],
    ApplicationStatus.NOT_SELECTED.value: [
        ApplicationStatus.UNDER_REVIEW.value,
        ApplicationStatus.WITHDRAWN.value,
    ],
    ApplicationStatus.WITHDRAWN.value: [],
}


class ApplicationService(BaseService[Application]):
    def __init__(self):
        super().__init__(Application)

    def search_applications(
        self,
        db: Session,
        query: Optional[str] = None,
        role_id: Optional[UUID] = None,
        status: Optional[ApplicationStatus] = None,
        location: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Application], int]:
        """
        Multi-criteria search and filtering for applicant review.
        """
        db_query = db.query(Application).join(Applicant).join(Role)

        if role_id:
            db_query = db_query.filter(Application.role_id == role_id)

        if status:
            db_query = db_query.filter(Application.current_status == status.value)

        if location:
            db_query = db_query.filter(Applicant.location.ilike(f"%{location}%"))

        if query:
            search_pattern = f"%{query}%"
            db_query = db_query.filter(
                or_(
                    Applicant.full_name.ilike(search_pattern),
                    Applicant.email.ilike(search_pattern),
                    Applicant.location.ilike(search_pattern),
                    Role.role_name.ilike(search_pattern),
                    Application.motivation_statement.ilike(search_pattern),
                )
            )

        total = db_query.count()
        results = (
            db_query.order_by(Application.submission_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return results, total

    def get_detailed_application(self, db: Session, application_id: UUID) -> dict:
        """
        FR-011: Consolidated profile combining applicant record data, skills,
        experience, availability, evidence links, evaluations, interviews, notes, and status.
        """
        app = self.get(db, application_id)
        evaluations = db.query(Evaluation).filter(Evaluation.application_id == app.id).all()
        interviews = db.query(Interview).filter(Interview.application_id == app.id).all()
        notes = (
            db.query(Note)
            .filter(Note.related_entity_type == "Application", Note.related_entity_id == app.id)
            .order_by(Note.created_at.desc())
            .all()
        )

        return {
            "id": app.id,
            "applicant_id": app.applicant_id,
            "role_id": app.role_id,
            "current_status": app.current_status,
            "motivation_statement": app.motivation_statement,
            "availability_info": app.availability_info,
            "submission_date": app.submission_date,
            "last_updated_date": app.last_updated_date,
            "created_at": app.created_at,
            "updated_at": app.updated_at,
            "role": app.role,
            "applicant": app.applicant,
            "status_history": app.status_history,
            "evaluations": evaluations,
            "interviews": interviews,
            "notes": notes,
        }

    def process_intake(self, db: Session, data: ApplicationIntakeRequest) -> IntakeResultItem:
        """
        Process single intake submission from Google Forms (FR-001, FR-005, FR-007).
        Matches existing applicant by email idempotently without creating duplicates.
        """
        email_clean = str(data.email).lower().strip()

        # 1. Resolve Target Role
        role = None
        if data.role_id:
            role = db.query(Role).filter(Role.id == data.role_id).first()
        elif data.role_name:
            role = db.query(Role).filter(Role.role_name.ilike(data.role_name.strip())).first()

        if not role:
            raise BadRequestException(f"Target role '{data.role_name or data.role_id}' not found.")

        # 2. Match or Create Applicant (FR-005: match by email without duplicate)
        applicant = db.query(Applicant).filter(Applicant.email == email_clean).first()

        if not applicant:
            applicant = Applicant(
                full_name=data.full_name.strip(),
                email=email_clean,
                phone_number=data.phone_number,
                location=data.location,
                external_profile_link=data.external_profile_link,
            )
            db.add(applicant)
            db.flush()
        else:
            # Update contact info if changed
            applicant.full_name = data.full_name.strip()
            if data.phone_number:
                applicant.phone_number = data.phone_number
            if data.location:
                applicant.location = data.location
            if data.external_profile_link:
                applicant.external_profile_link = data.external_profile_link

        # 3. Add Evidence Links (Portfolio Items) (FR-015, FR-016, FR-018)
        if data.evidence_links:
            for ev in data.evidence_links:
                if ev.reference_link or ev.attachment_reference:
                    existing_item = (
                        db.query(PortfolioItem)
                        .filter(
                            PortfolioItem.applicant_id == applicant.id,
                            PortfolioItem.reference_link == ev.reference_link,
                        )
                        .first()
                    )
                    if not existing_item:
                        item = PortfolioItem(
                            applicant_id=applicant.id,
                            title=ev.title,
                            reference_link=ev.reference_link,
                            attachment_reference=ev.attachment_reference,
                            description=ev.description,
                        )
                        db.add(item)

        # 4. Add Skills Claimed
        if data.skills:
            for sk in data.skills:
                skill_record = (
                    db.query(Skill).filter(Skill.skill_name.ilike(sk.skill_name.strip())).first()
                )
                if not skill_record:
                    skill_record = Skill(skill_name=sk.skill_name.strip())
                    db.add(skill_record)
                    db.flush()

                existing_sk = (
                    db.query(ApplicantSkill)
                    .filter(
                        ApplicantSkill.applicant_id == applicant.id,
                        ApplicantSkill.skill_id == skill_record.id,
                    )
                    .first()
                )
                if not existing_sk:
                    app_skill = ApplicantSkill(
                        applicant_id=applicant.id,
                        skill_id=skill_record.id,
                        proficiency_level=sk.proficiency_level.value if sk.proficiency_level else None,
                        years_of_experience=sk.years_of_experience,
                    )
                    db.add(app_skill)

        # 5. Add Experiences if provided
        if data.experiences:
            for exp_in in data.experiences:
                exp = Experience(
                    applicant_id=applicant.id,
                    title=exp_in.title,
                    organization=exp_in.organization,
                    start_date=exp_in.start_date,
                    end_date=exp_in.end_date,
                    description=exp_in.description,
                )
                db.add(exp)

        # 6. Check if application for this role already exists
        existing_app = (
            db.query(Application)
            .filter(
                Application.applicant_id == applicant.id,
                Application.role_id == role.id,
            )
            .first()
        )

        if existing_app:
            if data.motivation_statement:
                existing_app.motivation_statement = data.motivation_statement
            if data.availability_info:
                existing_app.availability_info = data.availability_info

            db.commit()
            return IntakeResultItem(
                email=email_clean,
                full_name=applicant.full_name,
                application_id=existing_app.id,
                applicant_id=applicant.id,
                role_name=role.role_name,
                status="updated",
                reason="Updated existing application and profile for candidate.",
            )

        # Create new application
        application = Application(
            applicant_id=applicant.id,
            role_id=role.id,
            motivation_statement=data.motivation_statement,
            availability_info=data.availability_info,
            current_status=ApplicationStatus.RECEIVED.value,
        )
        db.add(application)
        db.flush()

        # Audit History Record (FR-013, E-16)
        history = ApplicationStatusHistory(
            application_id=application.id,
            previous_status=None,
            new_status=ApplicationStatus.RECEIVED.value,
            reason="Application intake received via Google Forms",
        )
        db.add(history)

        db.commit()
        db.refresh(application)

        return IntakeResultItem(
            email=email_clean,
            full_name=applicant.full_name,
            application_id=application.id,
            applicant_id=applicant.id,
            role_name=role.role_name,
            status="created",
            reason="Successfully created new application and candidate profile.",
        )

    def process_batch_intake(self, db: Session, batch_data: ApplicationBatchIntakeRequest) -> IntakeSummaryResponse:
        """
        Process batch intake of Google Forms submissions (FR-002, FR-003, FR-004).
        """
        accepted = 0
        updated = 0
        rejected = 0
        results: List[IntakeResultItem] = []
        errors: List[str] = []

        for sub in batch_data.submissions:
            try:
                res = self.process_intake(db, sub)
                results.append(res)
                if res.status == "created":
                    accepted += 1
                elif res.status == "updated":
                    updated += 1
            except Exception as e:
                rejected += 1
                err_msg = f"Failed to process {sub.email}: {str(e)}"
                errors.append(err_msg)
                results.append(
                    IntakeResultItem(
                        email=str(sub.email),
                        full_name=sub.full_name,
                        status="rejected",
                        reason=str(e),
                    )
                )

        return IntakeSummaryResponse(
            total_received=len(batch_data.submissions),
            accepted=accepted,
            updated=updated,
            rejected=rejected,
            results=results,
            errors=errors,
        )

    def get_allowed_transitions(self, db: Session, id: UUID) -> dict:
        """
        Return the permitted status transitions for an application based on its current lifecycle state.
        """
        application = self.get(db, id)
        allowed = ALLOWED_TRANSITIONS.get(application.current_status, [])
        return {
            "application_id": application.id,
            "current_status": application.current_status,
            "allowed_transitions": allowed,
        }

    def update_status(self, db: Session, id: UUID, data: ApplicationStatusUpdate) -> Application:
        """
        BR-001, BR-002: Transition application status with audit trail and strict validation.
        """
        application = self.get(db, id)
        previous_status = application.current_status
        new_status = data.new_status.value

        if previous_status == new_status:
            return application

        # Enforce approved workflow transition rules
        allowed_next = ALLOWED_TRANSITIONS.get(previous_status, [])
        if new_status not in allowed_next:
            raise BadRequestException(
                f"Invalid status transition (BR-002): An application cannot move from "
                f"'{previous_status}' to '{new_status}'. Allowed transitions: "
                f"{', '.join(allowed_next) if allowed_next else 'None (terminal status)'}."
            )

        # Update status
        application.current_status = new_status

        # Append audit history (E-16)
        history = ApplicationStatusHistory(
            application_id=application.id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by_id=data.changed_by_id,
            reason=data.reason,
        )
        db.add(history)

        db.commit()
        db.refresh(application)
        return application


application_service = ApplicationService()