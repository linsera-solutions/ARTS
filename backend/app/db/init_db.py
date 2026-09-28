import logging
from sqlalchemy import text
from app.db.session import engine, Base, SessionLocal
from app.models.user import User
from app.models.team import Team, Role
from app.models.evaluation import EvaluationCriterion
from app.models.enums import RoleStatus, TeamStatus, UserRole, AccountStatus
from app.core.security import hash_password
import app.models  # Ensure all models are registered with Base.metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_TEAM_NAME = "NASA Space Apps Challenge Team"
DEFAULT_TEAM_DESC = "4-member interdisciplinary project team for the NASA Space Apps Challenge."
DEFAULT_ADMIN_EMAIL = "lead@nasa.org"
DEFAULT_ADMIN_PASS = "NasaSpaceApps2026!"

APPROVED_ROLES = [
    {
        "role_name": "Team Lead + Product/Game Concept Lead / Research & Presentation",
        "role_description": "Lead team vision, narrative concept, product roadmap, research integration, and final presentation.",
        "number_of_openings": 1,
        "role_status": RoleStatus.OPEN.value,
    },
    {
        "role_name": "Game/App Developer",
        "role_description": "Core software engineering, game engine architecture, application development, and interactive feature implementation.",
        "number_of_openings": 1,
        "role_status": RoleStatus.OPEN.value,
    },
    {
        "role_name": "UI/UX & Visual Designer",
        "role_description": "User experience flows, visual assets, wireframing, interface design, and aesthetic presentation.",
        "number_of_openings": 1,
        "role_status": RoleStatus.OPEN.value,
    },
    {
        "role_name": "Space/Science Research + Game Logic",
        "role_description": "Domain science research, accuracy verification, game mechanics logic, and narrative fact alignment.",
        "number_of_openings": 1,
        "role_status": RoleStatus.OPEN.value,
    },
]

APPROVED_EVALUATION_CRITERIA = [
    {
        "criterion_name": "Relevant Skills & Technical Competency",
        "criterion_description": (
            "Does the submitted evidence (portfolio links, claimed skills, project descriptions) "
            "demonstrate skills genuinely relevant to this role? Assess what has been shown, "
            "not what is assumed from credentials or titles alone."
        ),
        "is_active": True,
    },
    {
        "criterion_name": "Project Experience & Demonstrable Work",
        "criterion_description": (
            "Does the applicant submitted work history, portfolio, or GitHub show applied, "
            "hands-on experience relevant to the role? Favour demonstrable output over "
            "self-reported years of experience."
        ),
        "is_active": True,
    },
    {
        "criterion_name": "Motivation & Role Alignment",
        "criterion_description": (
            "Does the applicant stated motivation statement reflect genuine understanding of "
            "and alignment with this role purpose within the NASA Space Apps challenge? "
            "Assess clarity and specificity, not enthusiasm alone."
        ),
        "is_active": True,
    },
    {
        "criterion_name": "Availability & Commitment",
        "criterion_description": (
            "Has the applicant stated adequate and realistic availability for the challenge "
            "duration? Note stated commitments and any ambiguity that would require clarification."
        ),
        "is_active": True,
    },
    {
        "criterion_name": "Communication Clarity",
        "criterion_description": (
            "Is the overall submission coherent, complete, and professional? Does the applicant "
            "communicate clearly about their background and intentions? This reflects "
            "communication ability, not writing perfection."
        ),
        "is_active": True,
    },
]


def init_database() -> bool:
    """
    Initializes database tables, constraints, and baseline seed data.
    """
    if engine is None:
        logger.error("Cannot initialize database: engine is None. Check DATABASE_URL.")
        return False

    try:
        logger.info("Creating database tables and metadata...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")

        if SessionLocal:
            with SessionLocal() as session:
                # Seed default Team Lead recruiter user
                admin = session.query(User).filter_by(email=DEFAULT_ADMIN_EMAIL).first()
                if not admin:
                    logger.info(f"Seeding default Team Lead account: {DEFAULT_ADMIN_EMAIL}")
                    admin = User(
                        full_name="Team Lead",
                        email=DEFAULT_ADMIN_EMAIL,
                        user_role=UserRole.ADMINISTRATOR.value,
                        account_status=AccountStatus.ACTIVE.value,
                        hashed_password=hash_password(DEFAULT_ADMIN_PASS),
                    )
                    session.add(admin)
                elif not admin.hashed_password:
                    admin.hashed_password = hash_password(DEFAULT_ADMIN_PASS)

                # Seed default team
                team = session.query(Team).filter_by(team_name=DEFAULT_TEAM_NAME).first()
                if not team:
                    logger.info(f"Seeding default team: {DEFAULT_TEAM_NAME}")
                    team = Team(
                        team_name=DEFAULT_TEAM_NAME,
                        team_description=DEFAULT_TEAM_DESC,
                        team_status=TeamStatus.FORMING.value,
                    )
                    session.add(team)
                    session.flush()

                # Seed initial approved roles linked to the team
                for role_data in APPROVED_ROLES:
                    existing = session.query(Role).filter_by(role_name=role_data["role_name"]).first()
                    if not existing:
                        logger.info(f"Seeding approved role: {role_data['role_name']}")
                        role = Role(team_id=team.id, **role_data)
                        session.add(role)
                    elif not existing.team_id:
                        existing.team_id = team.id
                session.commit()
                logger.info("Approved team roles seeded successfully.")

                # Seed evaluation criteria if not already present
                for crit_data in APPROVED_EVALUATION_CRITERIA:
                    existing_crit = session.query(EvaluationCriterion).filter_by(
                        criterion_name=crit_data["criterion_name"]
                    ).first()
                    if not existing_crit:
                        logger.info(f"Seeding evaluation criterion: {crit_data['criterion_name']}")
                        crit = EvaluationCriterion(**crit_data)
                        session.add(crit)
                session.commit()
                logger.info("Evaluation criteria seeded successfully.")

        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False


if __name__ == "__main__":
    init_database()