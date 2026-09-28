import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.models.enums import UserRole, AccountStatus, TeamStatus
from app.models.user import User
from app.models.team import Team, Role
from app.models.evaluation import EvaluationCriterion
from app.core.security import hash_password, create_access_token
from app.db.init_db import (
    APPROVED_ROLES,
    APPROVED_EVALUATION_CRITERIA,
    DEFAULT_TEAM_NAME,
    DEFAULT_TEAM_DESC,
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASS,
)

# Shared in-memory SQLite engine for all tests
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

TEST_ADMIN_ID = None


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    global TEST_ADMIN_ID
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as session:
        # Seed test admin user (Team Lead)
        admin = User(
            full_name="Team Lead",
            email=DEFAULT_ADMIN_EMAIL,
            user_role=UserRole.ADMINISTRATOR.value,
            account_status=AccountStatus.ACTIVE.value,
            hashed_password=hash_password(DEFAULT_ADMIN_PASS),
        )
        session.add(admin)
        session.flush()
        TEST_ADMIN_ID = admin.id

        # Seed default team
        team = Team(
            team_name=DEFAULT_TEAM_NAME,
            team_description=DEFAULT_TEAM_DESC,
            team_status=TeamStatus.FORMING.value,
        )
        session.add(team)
        session.flush()

        # Seed approved roles linked to team
        for r_data in APPROVED_ROLES:
            role = Role(team_id=team.id, **r_data)
            session.add(role)

        # Seed evaluation criteria (5 qualitative assessment dimensions)
        for crit_data in APPROVED_EVALUATION_CRITERIA:
            crit = EvaluationCriterion(**crit_data)
            session.add(crit)

        session.commit()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_token():
    return create_access_token(
        data={
            "sub": str(TEST_ADMIN_ID),
            "email": DEFAULT_ADMIN_EMAIL,
            "role": UserRole.ADMINISTRATOR.value,
        }
    )


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def client(auth_headers):
    """
    Authenticated TestClient configured with valid Team Lead bearer token.
    """
    c = TestClient(app)
    c.headers.update(auth_headers)
    return c


@pytest.fixture
def unauthenticated_client():
    """
    Unauthenticated TestClient without authorization headers.
    """
    return TestClient(app)