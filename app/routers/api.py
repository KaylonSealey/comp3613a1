"""JSON REST API for MyAdvisor.

Authentication: POST /api/auth/login returns a JWT. Send it on every other
request as ``Authorization: Bearer <token>`` (the browser cookie also works).

Authorization:
- 401 when the token is missing/invalid
- 403 when the user's role is not allowed (student vs advisor vs admin)

Routes stay thin: they resolve the caller's profile, delegate to the existing
services/repositories, and translate service errors to HTTP status codes
(LookupError -> 404, ValueError -> 409).
"""
from fastapi import HTTPException, Query, Response, status

from app.dependencies.auth import AdvisorUserDep, AuthDep, StudentUserDep
from app.dependencies.session import SessionDep
from app.models.plan import Plan
from app.repositories.advisor import AdvisorRepository
from app.repositories.audit import AuditRepository
from app.repositories.course import CourseRepository
from app.repositories.plan import PlanRepository
from app.repositories.student import StudentRepository
from app.repositories.user import UserRepository
from app.schemas.api import (
    AdvisorDecisionRequest,
    AdvisorPlanSummary,
    CourseOut,
    LoginRequest,
    MeResponse,
    PlanCourseOut,
    PlanNotesRequest,
    PlanOut,
    PlanStatusResponse,
    PlanSubmitRequest,
    TokenResponse,
)
from app.schemas.plan import PlanCourseRequest
from app.services.advisor_service import AdvisorService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.course_service import CourseService
from app.services.plan_service import PlanService

from . import api_router

DEFAULT_ACADEMIC_TERM = "2026/27"


# ---------------------------------------------------------------- helpers
def _course_out(course) -> CourseOut:
    return CourseOut(
        id=course.id,
        code=course.code,
        title=course.title,
        faculty=course.faculty,
        credits=course.credits,
    )


def _plan_out(plan: Plan, plan_courses) -> PlanOut:
    return PlanOut(
        id=plan.id,
        student_id=plan.student_id,
        advisor_id=plan.advisor_id,
        academic_term=plan.academic_term,
        status=plan.status,
        notes=plan.notes,
        advisor_notes=plan.advisor_notes,
        submitted_at=plan.submitted_at,
        approved_at=plan.approved_at,
        total_credits=sum(course.credits for _, course in plan_courses),
        courses=[
            PlanCourseOut(
                plan_course_id=plan_course.id,
                placement=plan_course.placement,
                course=_course_out(course),
            )
            for plan_course, course in plan_courses
        ],
    )


def _get_student(user, db):
    student = StudentRepository(db).get_by_user_id(user.id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A student profile is required.",
        )
    return student


def _get_advisor(user, db):
    advisor = AdvisorRepository(db).get_by_user_id(user.id)
    if advisor is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An advisor profile is required.",
        )
    return advisor


# ---------------------------------------------------------------- auth
@api_router.post("/auth/login", response_model=TokenResponse)
async def api_login(data: LoginRequest, db: SessionDep):
    user_repo = UserRepository(db)
    token = AuthService(user_repo).authenticate_user(data.username, data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    user = user_repo.get_by_username(data.username)
    return TokenResponse(access_token=token, role=user.role)


@api_router.get("/auth/me", response_model=MeResponse)
async def api_me(user: AuthDep):
    return MeResponse(id=user.id, username=user.username, email=user.email, role=user.role)


# ---------------------------------------------------------------- catalog (any logged-in user)
@api_router.get("/courses", response_model=list[CourseOut])
async def api_search_courses(
    user: AuthDep,
    db: SessionDep,
    query: str = "",
    faculty: str | None = None,
):
    courses = CourseService(CourseRepository(db)).search_catalog(query, faculty)
    return [_course_out(course) for course in courses]


# ---------------------------------------------------------------- student: degree audit
@api_router.get("/me/audit")
async def api_my_audit(user: StudentUserDep, db: SessionDep):
    student = _get_student(user, db)
    audit = AuditService(AuditRepository(db)).get_degree_audit(student)
    return {
        "total_required_credits": audit["total_required_credits"],
        "total_completed_credits": audit["total_completed_credits"],
        "progress_percent": audit["progress_percent"],
        "categories": [
            {
                "name": category["name"],
                "required_credits": category["required_credits"],
                "completed_credits": category["completed_credits"],
                "courses": [
                    {
                        "code": item["course"].code,
                        "title": item["course"].title,
                        "credits": item["credits"],
                        "completed": item["completed"],
                    }
                    for item in category["courses"]
                ],
            }
            for category in audit["categories"]
        ],
    }


# ---------------------------------------------------------------- student: my plan
@api_router.get("/me/plan", response_model=PlanOut)
async def api_get_my_plan(
    user: StudentUserDep,
    db: SessionDep,
    academic_term: str = Query(DEFAULT_ACADEMIC_TERM),
):
    student = _get_student(user, db)
    try:
        plan, plan_courses = PlanService(PlanRepository(db)).get_plan_courses(
            student.id, academic_term
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _plan_out(plan, plan_courses)


@api_router.post(
    "/me/plan/courses",
    response_model=PlanCourseOut,
    status_code=status.HTTP_201_CREATED,
)
async def api_add_course(data: PlanCourseRequest, user: StudentUserDep, db: SessionDep):
    student = _get_student(user, db)
    try:
        plan_course, course = PlanService(PlanRepository(db)).add_course(
            student_id=student.id,
            course_id=data.course_id,
            academic_term=data.academic_term,
            placement=data.placement,
            plan_length=data.plan_length,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return PlanCourseOut(
        plan_course_id=plan_course.id,
        placement=plan_course.placement,
        course=_course_out(course),
    )


@api_router.delete(
    "/me/plan/courses/{plan_course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def api_remove_course(
    plan_course_id: int,
    user: StudentUserDep,
    db: SessionDep,
    academic_term: str = Query(DEFAULT_ACADEMIC_TERM),
):
    student = _get_student(user, db)
    try:
        removed = PlanService(PlanRepository(db)).remove_course(
            student_id=student.id,
            academic_term=academic_term,
            plan_course_id=plan_course_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not removed:
        raise HTTPException(status_code=404, detail="That course is not in this plan.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api_router.patch("/me/plan", response_model=PlanStatusResponse)
async def api_save_draft(data: PlanNotesRequest, user: StudentUserDep, db: SessionDep):
    student = _get_student(user, db)
    try:
        plan_status = PlanService(PlanRepository(db)).save_draft_notes(
            student_id=student.id,
            academic_term=data.academic_term,
            notes=data.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return PlanStatusResponse(
        academic_term=data.academic_term,
        status=plan_status,
        message="Your plan comments have been saved.",
    )


@api_router.post("/me/plan/submission", response_model=PlanStatusResponse)
async def api_submit_plan(data: PlanSubmitRequest, user: StudentUserDep, db: SessionDep):
    student = _get_student(user, db)
    plan_repo = PlanRepository(db)
    try:
        plan_status = PlanService(plan_repo).submit_plan(
            student_id=student.id,
            academic_term=data.academic_term,
            notes=data.notes,
            advisor_id=student.advisor_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    plan = plan_repo.get_plan(student.id, data.academic_term)
    return PlanStatusResponse(
        plan_id=plan.id if plan else None,
        academic_term=data.academic_term,
        status=plan_status,
        message="Your plan was submitted and is awaiting advisor review.",
    )


# ---------------------------------------------------------------- advisor
@api_router.get("/advisor/plans", response_model=list[AdvisorPlanSummary])
async def api_advisor_queue(user: AdvisorUserDep, db: SessionDep):
    advisor = _get_advisor(user, db)
    plans = AdvisorService(AdvisorRepository(db)).get_assigned_plans(advisor.id)
    return [
        AdvisorPlanSummary(
            plan_id=plan.id,
            academic_term=plan.academic_term,
            status=plan.status,
            submitted_at=plan.submitted_at,
            student_id=student.student_id,
            student_name=f"{student.first_name} {student.last_name}",
        )
        for plan, student in plans
    ]


@api_router.get("/advisor/plans/{plan_id}")
async def api_advisor_plan_detail(plan_id: int, user: AdvisorUserDep, db: SessionDep):
    advisor = _get_advisor(user, db)
    try:
        plan, student = AdvisorService(AdvisorRepository(db)).get_assigned_plan(
            advisor.id, plan_id
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    plan_courses = PlanRepository(db).list_courses(plan.id)
    audit = AuditService(AuditRepository(db)).get_degree_audit(student)
    return {
        "plan": _plan_out(plan, plan_courses),
        "student": {
            "student_id": student.student_id,
            "name": f"{student.first_name} {student.last_name}",
            "email": student.email,
        },
        "audit": {
            "total_required_credits": audit["total_required_credits"],
            "total_completed_credits": audit["total_completed_credits"],
            "progress_percent": audit["progress_percent"],
        },
    }


@api_router.post("/advisor/plans/{plan_id}/decision", response_model=PlanStatusResponse)
async def api_advisor_decision(
    plan_id: int,
    data: AdvisorDecisionRequest,
    user: AdvisorUserDep,
    db: SessionDep,
):
    advisor = _get_advisor(user, db)
    try:
        plan_status = AdvisorService(AdvisorRepository(db)).submit_decision(
            advisor_id=advisor.id,
            plan_id=plan_id,
            decision=data.decision,
            notes=data.notes,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return PlanStatusResponse(
        plan_id=plan_id,
        status=plan_status,
        message=f"The plan decision was recorded: {plan_status}.",
    )
