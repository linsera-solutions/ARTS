import csv
import io
import re
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.team import Role
from app.models.applicant import Applicant, Experience, PortfolioItem, ApplicantSkill, Skill
from app.models.application import Application, ApplicationStatusHistory
from app.models.sync_log import SyncLog
from app.models.enums import ApplicationStatus
from app.schemas.intake import (
    GoogleFormsWebhookPayload,
    GoogleSyncStatusResponse,
    SyncLogRead,
)
from app.schemas.application import IntakeResultItem, IntakeSummaryResponse
from app.core.exceptions import BadRequestException, NotFoundException

logger = logging.getLogger(__name__)

# Standard Approved Target Roles mapping keywords
ROLE_MAPPINGS = {
    "Team Lead + Product/Game Concept Lead / Research & Presentation": [
        "team lead",
        "product lead",
        "game concept",
        "concept lead",
        "presentation",
        "research & presentation",
        "lead",
        "role 1",
    ],
    "Game/App Developer": [
        "game/app developer",
        "game developer",
        "app developer",
        "developer",
        "software engineer",
        "programmer",
        "unity",
        "godot",
        "unreal",
        "frontend/backend developer",
        "role 2",
    ],
    "UI/UX & Visual Designer": [
        "ui/ux & visual designer",
        "ui/ux",
        "visual designer",
        "ui designer",
        "ux designer",
        "designer",
        "graphic designer",
        "2d/3d artist",
        "artist",
        "role 3",
    ],
    "Space/Science Research + Game Logic": [
        "space/science research + game logic",
        "space research",
        "science research",
        "game logic",
        "astrophysics",
        "science",
        "researcher",
        "logic",
        "role 4",
    ],
}


def mask_email(email: str) -> str:
    """Mask email for privacy-safe logging (e.g. j***@example.com)."""
    if not email or "@" not in email:
        return "unknown"
    parts = email.split("@")
    name = parts[0]
    domain = parts[1]
    masked_name = name[0] + "***" if len(name) > 1 else name + "***"
    return f"{masked_name}@{domain}"


class GoogleSyncService:
    @staticmethod
    def match_role(db: Session, raw_role: Optional[str]) -> Optional[Role]:
        """
        Matches a free-text or selected Google Form role value to one of the 4 approved roles.
        """
        if not raw_role:
            return None

        clean_text = raw_role.strip().lower()

        # 1. Exact or partial match on database role_name
        all_roles = db.query(Role).all()
        for r in all_roles:
            if r.role_name.lower() in clean_text or clean_text in r.role_name.lower():
                return r

        # 2. Keyword dictionary matching
        for standard_role_name, keywords in ROLE_MAPPINGS.items():
            for kw in keywords:
                if kw in clean_text:
                    matched = db.query(Role).filter(Role.role_name == standard_role_name).first()
                    if matched:
                        return matched

        return all_roles[0] if all_roles else None

    @staticmethod
    def parse_timestamp(raw_time: Optional[str]) -> datetime:
        """Parses Google Forms date/time formats into UTC datetime."""
        if not raw_time:
            return datetime.now(timezone.utc)

        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%m/%d/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]

        cleaned = raw_time.strip()
        for fmt in formats:
            try:
                dt = datetime.strptime(cleaned, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

        return datetime.now(timezone.utc)

    @staticmethod
    def parse_skills_string(skills_str: Optional[str]) -> List[str]:
        """Splits free-text skills by comma, semicolon, newline, or bullets."""
        if not skills_str:
            return []
        tokens = re.split(r"[,;\n•\r]+", skills_str)
        return [t.strip() for t in tokens if t.strip()]

    def process_normalized_row(
        self,
        db: Session,
        row_data: Dict[str, Any],
        source: str = "Google Forms",
    ) -> IntakeResultItem:
        """
        Core mapping and deduplication processor for a single Google Forms response row.
        """
        raw_email = row_data.get("email") or ""
        email_clean = raw_email.strip().lower()
        full_name = (row_data.get("full_name") or "Anonymous Applicant").strip()

        if not email_clean or "@" not in email_clean:
            raise BadRequestException("Missing or invalid email address in Google Forms response.")

        # 1. Resolve Target Role
        role = self.match_role(db, row_data.get("role"))
        if not role:
            role = db.query(Role).first()
            if not role:
                raise NotFoundException("No approved target roles configured in database.")

        # 2. Match or Create Candidate (FR-005: match by email without duplicate profile)
        applicant = db.query(Applicant).filter(Applicant.email == email_clean).first()
        is_update = applicant is not None

        if not applicant:
            applicant = Applicant(
                full_name=full_name,
                email=email_clean,
                phone_number=row_data.get("phone_number"),
                location=row_data.get("location"),
                external_profile_link=row_data.get("linkedin") or row_data.get("portfolio"),
            )
            db.add(applicant)
            db.flush()
            logger.info(f"Created new candidate profile for {mask_email(email_clean)} from {source}")
        else:
            applicant.full_name = full_name
            if row_data.get("phone_number"):
                applicant.phone_number = row_data.get("phone_number")
            if row_data.get("location"):
                applicant.location = row_data.get("location")
            if row_data.get("linkedin") or row_data.get("portfolio"):
                applicant.external_profile_link = row_data.get("linkedin") or row_data.get("portfolio")
            logger.info(f"Updated existing candidate profile for {mask_email(email_clean)} from {source}")

        # 3. Add Evidence Links (LinkedIn, GitHub, Portfolio URLs) (FR-015, FR-016, FR-018)
        evidence_entries = []
        if row_data.get("linkedin"):
            evidence_entries.append(("LinkedIn Profile", row_data["linkedin"].strip()))
        if row_data.get("github"):
            evidence_entries.append(("GitHub Repository / Profile", row_data["github"].strip()))
        if row_data.get("portfolio"):
            evidence_entries.append(("Portfolio / Work Sample", row_data["portfolio"].strip()))

        for label, url in evidence_entries:
            if url:
                existing_item = (
                    db.query(PortfolioItem)
                    .filter(
                        PortfolioItem.applicant_id == applicant.id,
                        PortfolioItem.reference_link == url,
                    )
                    .first()
                )
                if not existing_item:
                    item = PortfolioItem(
                        applicant_id=applicant.id,
                        title=label,
                        reference_link=url,
                    )
                    db.add(item)

        # 4. Add Claimed Skills
        skills_list = self.parse_skills_string(row_data.get("skills"))
        for sk_name in skills_list:
            skill_rec = db.query(Skill).filter(Skill.skill_name.ilike(sk_name)).first()
            if not skill_rec:
                skill_rec = Skill(skill_name=sk_name)
                db.add(skill_rec)
                db.flush()

            existing_sk = (
                db.query(ApplicantSkill)
                .filter(
                    ApplicantSkill.applicant_id == applicant.id,
                    ApplicantSkill.skill_id == skill_rec.id,
                )
                .first()
            )
            if not existing_sk:
                app_skill = ApplicantSkill(
                    applicant_id=applicant.id,
                    skill_id=skill_rec.id,
                )
                db.add(app_skill)

        # 5. Add Experience summary if provided
        if row_data.get("experience"):
            exp_text = row_data["experience"].strip()
            existing_exp = (
                db.query(Experience)
                .filter(
                    Experience.applicant_id == applicant.id,
                    Experience.description == exp_text,
                )
                .first()
            )
            if not existing_exp:
                exp = Experience(
                    applicant_id=applicant.id,
                    title=f"Experience ({role.role_name})",
                    description=exp_text,
                    start_date=datetime.now(timezone.utc).date(),
                )
                db.add(exp)

        # 6. Check existing application for this role (De-duplication & Idempotency)
        submission_time = self.parse_timestamp(row_data.get("timestamp"))

        existing_app = (
            db.query(Application)
            .filter(
                Application.applicant_id == applicant.id,
                Application.role_id == role.id,
            )
            .first()
        )

        if existing_app:
            if row_data.get("motivation"):
                existing_app.motivation_statement = row_data["motivation"].strip()
            if row_data.get("availability"):
                existing_app.availability_info = row_data["availability"].strip()
            existing_app.last_updated_date = datetime.now(timezone.utc)
            db.commit()

            return IntakeResultItem(
                email=email_clean,
                full_name=applicant.full_name,
                application_id=existing_app.id,
                applicant_id=applicant.id,
                role_name=role.role_name,
                status="updated",
                reason="Updated existing application and candidate details.",
            )

        # 7. Create New Application in 'Received' Status
        new_app = Application(
            applicant_id=applicant.id,
            role_id=role.id,
            motivation_statement=row_data.get("motivation"),
            availability_info=row_data.get("availability"),
            current_status=ApplicationStatus.RECEIVED.value,
            submission_date=submission_time,
            last_updated_date=submission_time,
        )
        db.add(new_app)
        db.flush()

        # Audit History Record (E-16)
        history = ApplicationStatusHistory(
            application_id=new_app.id,
            previous_status=None,
            new_status=ApplicationStatus.RECEIVED.value,
            reason=f"Ingested from {source}",
            changed_at=submission_time,
        )
        db.add(history)

        db.commit()
        db.refresh(new_app)

        return IntakeResultItem(
            email=email_clean,
            full_name=applicant.full_name,
            application_id=new_app.id,
            applicant_id=applicant.id,
            role_name=role.role_name,
            status="created",
            reason="Successfully ingested new application.",
        )

    def process_webhook_payload(
        self,
        db: Session,
        payload: GoogleFormsWebhookPayload,
    ) -> IntakeResultItem:
        """
        Processes real-time webhook payload sent from Google Apps Script.
        """
        # Validate Webhook Secret if configured
        if settings.GOOGLE_WEBHOOK_SECRET:
            if payload.secret_token != settings.GOOGLE_WEBHOOK_SECRET:
                raise BadRequestException("Invalid webhook secret token.")

        # Extract normalized row dictionary
        row_dict = {
            "timestamp": payload.timestamp,
            "email": payload.email,
            "full_name": payload.full_name,
            "role": payload.role,
            "phone_number": payload.phone_number,
            "location": payload.location,
            "linkedin": payload.linkedin,
            "github": payload.github,
            "portfolio": payload.portfolio,
            "motivation": payload.motivation,
            "availability": payload.availability,
            "skills": payload.skills,
            "experience": payload.experience,
        }

        # Fallback to raw_responses dictionary if standard fields were not populated
        if payload.raw_responses:
            for key, val in payload.raw_responses.items():
                k_lower = key.lower()
                if "email" in k_lower and not row_dict["email"]:
                    row_dict["email"] = str(val)
                elif ("name" in k_lower or "full name" in k_lower) and not row_dict["full_name"]:
                    row_dict["full_name"] = str(val)
                elif "role" in k_lower and not row_dict["role"]:
                    row_dict["role"] = str(val)
                elif "phone" in k_lower and not row_dict["phone_number"]:
                    row_dict["phone_number"] = str(val)
                elif "location" in k_lower and not row_dict["location"]:
                    row_dict["location"] = str(val)
                elif "linkedin" in k_lower and not row_dict["linkedin"]:
                    row_dict["linkedin"] = str(val)
                elif "github" in k_lower and not row_dict["github"]:
                    row_dict["github"] = str(val)
                elif "portfolio" in k_lower and not row_dict["portfolio"]:
                    row_dict["portfolio"] = str(val)
                elif "motivation" in k_lower and not row_dict["motivation"]:
                    row_dict["motivation"] = str(val)
                elif "availability" in k_lower and not row_dict["availability"]:
                    row_dict["availability"] = str(val)
                elif "skill" in k_lower and not row_dict["skills"]:
                    row_dict["skills"] = str(val)
                elif "experience" in k_lower and not row_dict["experience"]:
                    row_dict["experience"] = str(val)

        return self.process_normalized_row(db, row_dict, source="Google Forms Webhook")

    def process_csv_content(
        self,
        db: Session,
        csv_text: str,
        source_name: str = "Google Forms CSV Upload",
    ) -> IntakeSummaryResponse:
        """
        Parses CSV export from Google Sheets/Forms, maps headers automatically,
        and records a SyncLog audit entry.
        """
        reader = csv.DictReader(io.StringIO(csv_text))
        if not reader.fieldnames:
            raise BadRequestException("CSV file contains no headers or data.")

        # Header mapper
        field_map: Dict[str, str] = {}
        for h in reader.fieldnames:
            h_low = h.strip().lower()
            if any(k in h_low for k in ["timestamp", "submission time", "time"]):
                field_map[h] = "timestamp"
            elif any(k in h_low for k in ["email", "email address", "username"]):
                field_map[h] = "email"
            elif any(k in h_low for k in ["full name", "your name", "name"]):
                field_map[h] = "full_name"
            elif any(k in h_low for k in ["which role", "target role", "role", "position"]):
                field_map[h] = "role"
            elif any(k in h_low for k in ["phone", "contact number", "mobile"]):
                field_map[h] = "phone_number"
            elif any(k in h_low for k in ["location", "city", "country", "timezone"]):
                field_map[h] = "location"
            elif any(k in h_low for k in ["linkedin"]):
                field_map[h] = "linkedin"
            elif any(k in h_low for k in ["github"]):
                field_map[h] = "github"
            elif any(k in h_low for k in ["portfolio", "work sample", "website"]):
                field_map[h] = "portfolio"
            elif any(k in h_low for k in ["motivation", "why do you want", "statement"]):
                field_map[h] = "motivation"
            elif any(k in h_low for k in ["availability", "hours"]):
                field_map[h] = "availability"
            elif any(k in h_low for k in ["skill", "competencies"]):
                field_map[h] = "skills"
            elif any(k in h_low for k in ["experience", "background", "projects"]):
                field_map[h] = "experience"

        total_rows = 0
        accepted = 0
        updated = 0
        rejected = 0
        results: List[IntakeResultItem] = []
        errors: List[str] = []

        for row in reader:
            total_rows += 1
            row_dict: Dict[str, Any] = {}
            for original_header, mapped_field in field_map.items():
                row_dict[mapped_field] = row.get(original_header)

            try:
                res = self.process_normalized_row(db, row_dict, source=source_name)
                results.append(res)
                if res.status == "created":
                    accepted += 1
                elif res.status == "updated":
                    updated += 1
            except Exception as e:
                rejected += 1
                email_val = row_dict.get("email") or f"Row {total_rows}"
                err_msg = f"Failed to ingest row {total_rows} ({mask_email(str(email_val))}): {str(e)}"
                errors.append(err_msg)
                results.append(
                    IntakeResultItem(
                        email=str(email_val),
                        full_name=row_dict.get("full_name") or "Unknown",
                        status="rejected",
                        reason=str(e),
                    )
                )

        # Record SyncLog (ARTS-TRA-010 Section 11 & 14)
        sync_status = "Success" if rejected == 0 else ("Partial" if accepted + updated > 0 else "Failed")
        sync_log = SyncLog(
            source=source_name,
            status=sync_status,
            total_rows=total_rows,
            created_count=accepted,
            updated_count=updated,
            rejected_count=rejected,
            error_summary="; ".join(errors[:5]) if errors else None,
            details={"errors_count": len(errors)},
        )
        db.add(sync_log)
        db.commit()

        return IntakeSummaryResponse(
            total_received=total_rows,
            accepted=accepted,
            updated=updated,
            rejected=rejected,
            results=results,
            errors=errors,
        )

    def get_sync_status(self, db: Session) -> GoogleSyncStatusResponse:
        """Returns the readiness and historical summary of Google intake sync."""
        last_log = db.query(SyncLog).order_by(SyncLog.synced_at.desc()).first()
        total_synced = db.query(Application).count()

        is_configured = bool(
            settings.GOOGLE_SHEETS_SPREADSHEET_ID
            and (settings.GOOGLE_SERVICE_ACCOUNT_FILE or settings.GOOGLE_SERVICE_ACCOUNT_JSON)
        )

        return GoogleSyncStatusResponse(
            configured=is_configured,
            spreadsheet_id_configured=bool(settings.GOOGLE_SHEETS_SPREADSHEET_ID),
            service_account_configured=bool(settings.GOOGLE_SERVICE_ACCOUNT_FILE or settings.GOOGLE_SERVICE_ACCOUNT_JSON),
            webhook_enabled=True,
            last_sync=last_log.synced_at if last_log else None,
            last_sync_status=last_log.status if last_log else "Never Synced",
            total_synced=total_synced,
        )


google_sync_service = GoogleSyncService()
