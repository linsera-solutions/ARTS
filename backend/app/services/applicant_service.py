from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.applicant import Applicant, Experience, PortfolioItem, ApplicantSkill, Skill
from app.schemas.applicant import ApplicantCreate, ApplicantUpdate, EvidenceLinkCreate
from app.models.enums import ApplicantStatus
from app.services.base import BaseService
from app.core.exceptions import NotFoundException, BadRequestException


class ApplicantService(BaseService[Applicant]):
    def __init__(self):
        super().__init__(Applicant)

    def search_applicants(
        self,
        db: Session,
        query: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[ApplicantStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Applicant], int]:
        """
        Search and filter candidates across name, email, location, skills, and experience.
        """
        db_query = db.query(Applicant)

        if status:
            db_query = db_query.filter(Applicant.applicant_status == status.value)

        if location:
            db_query = db_query.filter(Applicant.location.ilike(f"%{location}%"))

        if query:
            search_pattern = f"%{query}%"
            db_query = db_query.filter(
                or_(
                    Applicant.full_name.ilike(search_pattern),
                    Applicant.email.ilike(search_pattern),
                    Applicant.location.ilike(search_pattern),
                    Applicant.experiences.any(Experience.title.ilike(search_pattern)),
                    Applicant.experiences.any(Experience.organization.ilike(search_pattern)),
                    Applicant.applicant_skills.any(
                        ApplicantSkill.skill.has(Skill.skill_name.ilike(search_pattern))
                    ),
                )
            )

        total = db_query.count()
        results = db_query.order_by(Applicant.created_at.desc()).offset(skip).limit(limit).all()
        return results, total

    def create_applicant(self, db: Session, data: ApplicantCreate) -> Applicant:
        applicant = Applicant(
            full_name=data.full_name,
            email=str(data.email).lower().strip(),
            phone_number=data.phone_number,
            location=data.location,
            external_profile_link=data.external_profile_link,
            applicant_status=data.applicant_status.value,
        )
        db.add(applicant)
        db.flush()

        # Add child experiences if provided
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

        # Add portfolio items if provided
        if data.portfolio_items:
            for port_in in data.portfolio_items:
                port = PortfolioItem(
                    applicant_id=applicant.id,
                    title=port_in.title,
                    description=port_in.description,
                    reference_link=port_in.reference_link,
                    attachment_reference=port_in.attachment_reference,
                )
                db.add(port)

        # Add skills if provided
        if data.skills:
            for sk_in in data.skills:
                sk = ApplicantSkill(
                    applicant_id=applicant.id,
                    skill_id=sk_in.skill_id,
                    proficiency_level=sk_in.proficiency_level.value if sk_in.proficiency_level else None,
                    years_of_experience=sk_in.years_of_experience,
                )
                db.add(sk)

        db.commit()
        db.refresh(applicant)
        return applicant

    def update_applicant(self, db: Session, id: UUID, data: ApplicantUpdate) -> Applicant:
        applicant = self.get(db, id)
        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if key == "applicant_status" and value is not None:
                setattr(applicant, key, value.value)
            elif key == "email" and value is not None:
                setattr(applicant, key, str(value).lower().strip())
            else:
                setattr(applicant, key, value)

        db.commit()
        db.refresh(applicant)
        return applicant

    def add_evidence_link(self, db: Session, applicant_id: UUID, data: EvidenceLinkCreate) -> PortfolioItem:
        """
        FR-015, FR-016, FR-018: Add an evidence link with descriptive label to candidate profile.
        """
        applicant = self.get(db, applicant_id)
        portfolio_item = PortfolioItem(
            applicant_id=applicant.id,
            title=data.title,
            reference_link=data.reference_link,
            description=data.description,
        )
        db.add(portfolio_item)
        db.commit()
        db.refresh(portfolio_item)
        return portfolio_item

    def remove_evidence_link(self, db: Session, applicant_id: UUID, evidence_id: UUID) -> None:
        """
        FR-017: Remove an evidence link from a candidate profile.
        """
        item = (
            db.query(PortfolioItem)
            .filter(PortfolioItem.id == evidence_id, PortfolioItem.applicant_id == applicant_id)
            .first()
        )
        if not item:
            raise NotFoundException(f"Evidence item with ID {evidence_id} not found for this candidate.")
        db.delete(item)
        db.commit()

    def archive_applicant(self, db: Session, applicant_id: UUID) -> Applicant:
        """
        FR-010: Archive an applicant record, removing them from active review lists while preserving auditability.
        """
        applicant = self.get(db, applicant_id)
        applicant.applicant_status = ApplicantStatus.ARCHIVED.value
        db.commit()
        db.refresh(applicant)
        return applicant


applicant_service = ApplicantService()
