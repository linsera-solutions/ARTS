import logging
from sqlalchemy import text
from app.db.session import engine, Base, SessionLocal
from app.models.team import Role
from app.models.enums import RoleStatus
import app.models  # Ensure all models are registered with Base.metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

        # Seed initial approved roles if not already present
        if SessionLocal:
            with SessionLocal() as session:
                for role_data in APPROVED_ROLES:
                    existing = session.query(Role).filter_by(role_name=role_data["role_name"]).first()
                    if not existing:
                        logger.info(f"Seeding approved role: {role_data['role_name']}")
                        role = Role(**role_data)
                        session.add(role)
                session.commit()
                logger.info("Approved team roles seeded successfully.")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False


if __name__ == "__main__":
    init_database()
