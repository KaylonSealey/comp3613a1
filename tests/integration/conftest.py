"""Integration-test fixtures.

Every test gets a brand-new in-memory SQLite database seeded with known data,
and the app's ``get_session`` dependency is overridden to use it. Requests go
through the real FastAPI app (routing, auth, services, repositories, DB).

Seed data
- Degree program BSC-CS; 7 required courses, 3 credits each (21 credits)
- bob    : student John Doe (1002450678), advisor = advisor, completed COMP1001 + MATH1001
- alice  : student Alice Smith (1002450679), NO advisor
- advisor: advisor Demo Advisor (assigned to bob)
- advisor2: advisor with no students
- admin  : admin
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  (registers every table)
from app.database import get_session
from app.main import app as fastapi_app
from app.models import (
    Advisor,
    CompletedCourse,
    Course,
    DegreeProgram,
    DegreeRequirement,
    Student,
    User,
)
from app.utilities.security import encrypt_password

PASSWORDS = {
    "bob": "bobpass",
    "alice": "alicepass",
    "advisor": "advisorpass",
    "advisor2": "advisor2pass",
    "admin": "adminpass",
}
ROLES = {
    "bob": "regular_user",
    "alice": "regular_user",
    "advisor": "advisor",
    "advisor2": "advisor",
    "admin": "admin",
}
COURSES = [
    ("COMP1001", "Introduction to Programming", "Computing", "Core"),
    ("COMP1002", "Data Fundamentals", "Computing", "Core"),
    ("COMP2001", "Algorithms", "Computing", "Major"),
    ("COMP2002", "Software Design", "Computing", "Major"),
    ("MATH1001", "Calculus I", "Mathematics", "Math"),
    ("SCI1001", "Science Foundations", "Science", "Science"),
    ("WRIT1001", "Technical Writing", "General Education", "Technical Writing"),
]
from helpers import TERM, add_course, submit_plan  # noqa: E402


@pytest.fixture(scope="session")
def password_hashes():
    # Hash once per run: argon2 is deliberately slow.
    return {name: encrypt_password(pw) for name, pw in PASSWORDS.items()}


def _seed(session: Session, password_hashes) -> dict:
    program = DegreeProgram(
        name="Bachelor of Science in Computer Science",
        code="BSC-CS", required_credits=120, catalog_year=TERM,
    )
    session.add(program)
    session.flush()

    users = {}
    for name in PASSWORDS:
        user = User(username=name, email=f"{name}@example.com",
                    password=password_hashes[name], role=ROLES[name])
        session.add(user)
        session.flush()
        users[name] = user

    advisor = Advisor(user_id=users["advisor"].id, first_name="Demo", last_name="Advisor",
                      email="advisor@example.com", department="Computing")
    advisor2 = Advisor(user_id=users["advisor2"].id, first_name="Second", last_name="Advisor",
                       email="advisor2@example.com", department="Computing")
    session.add_all([advisor, advisor2])
    session.flush()

    bob = Student(user_id=users["bob"].id, student_id="1002450678", first_name="John",
                  last_name="Doe", email="bob@example.com",
                  degree_program_id=program.id, advisor_id=advisor.id)
    alice = Student(user_id=users["alice"].id, student_id="1002450679", first_name="Alice",
                    last_name="Smith", email="alice@example.com",
                    degree_program_id=program.id, advisor_id=None)
    session.add_all([bob, alice])
    session.flush()

    course_ids = {}
    for code, title, faculty, requirement_type in COURSES:
        course = Course(code=code, title=title, faculty=faculty, credits=3,
                        level="Undergraduate", description=f"Demo catalog entry for {title}.")
        session.add(course)
        session.flush()
        course_ids[code] = course.id
        session.add(DegreeRequirement(degree_program_id=program.id, course_id=course.id,
                                      requirement_type=requirement_type, credits=3))

    for code in ("COMP1001", "MATH1001"):
        session.add(CompletedCourse(student_id=bob.id, course_id=course_ids[code],
                                    grade="A", term_completed="2025/26"))
    session.commit()
    return course_ids


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def course_ids(engine, password_hashes):
    with Session(engine) as session:
        return _seed(session, password_hashes)


@pytest.fixture
def make_client(engine, course_ids):
    """Factory: each call returns a separate client (separate cookie jar)."""

    def override_get_session():
        with Session(engine) as session:
            yield session

    fastapi_app.dependency_overrides[get_session] = override_get_session
    clients = []

    def _make():
        client = TestClient(fastapi_app)
        clients.append(client)
        return client

    yield _make
    for client in clients:
        client.close()
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client(make_client):
    return make_client()


@pytest.fixture
def auth(client):
    """auth("bob") -> {"Authorization": "Bearer <token>"} via the real login endpoint."""

    def _auth(username: str) -> dict:
        response = client.post(
            "/api/auth/login",
            json={"username": username, "password": PASSWORDS[username]},
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _auth


@pytest.fixture
def submitted_plan_id(client, auth, course_ids):
    """bob adds COMP1002 and submits; returns the plan id."""
    bob = auth("bob")
    assert add_course(client, bob, course_ids["COMP1002"]).status_code == 201
    response = submit_plan(client, bob)
    assert response.status_code == 200, response.text
    return response.json()["plan_id"]
