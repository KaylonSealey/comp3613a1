"""Request/response bodies for the JSON REST API (/api/...)."""
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class LoginRequest(SQLModel):
    username: str
    password: str


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class MeResponse(SQLModel):
    id: int
    username: str
    email: str
    role: str


class CourseOut(SQLModel):
    id: int
    code: str
    title: str
    faculty: str
    credits: int


class PlanCourseOut(SQLModel):
    plan_course_id: int
    placement: str
    course: CourseOut


class PlanOut(SQLModel):
    id: int
    student_id: int
    advisor_id: Optional[int] = None
    academic_term: str
    status: str
    notes: Optional[str] = None
    advisor_notes: Optional[str] = None
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    total_credits: int
    courses: list[PlanCourseOut]


class PlanNotesRequest(SQLModel):
    academic_term: str
    notes: str = ""


class PlanSubmitRequest(SQLModel):
    academic_term: str
    notes: str = ""


class AdvisorDecisionRequest(SQLModel):
    decision: str  # "approve" | "request_revisions"
    notes: str = ""


class PlanStatusResponse(SQLModel):
    plan_id: Optional[int] = None
    academic_term: Optional[str] = None
    status: str
    message: str


class AdvisorPlanSummary(SQLModel):
    plan_id: int
    academic_term: str
    status: str
    submitted_at: Optional[datetime] = None
    student_id: str
    student_name: str
