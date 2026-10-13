from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep
from app.repositories.audit import AuditRepository
from app.repositories.course import CourseRepository
from app.repositories.plan import PlanRepository
from app.repositories.student import StudentRepository
from app.schemas.plan import PlanCourseRequest
from app.services.audit_service import AuditService
from app.services.course_service import CourseService
from app.services.plan_service import PlanService
from app.utilities.flash import flash
from . import router, templates

DEFAULT_ACADEMIC_TERM = "2026/27"


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    academic_term: str = DEFAULT_ACADEMIC_TERM,
    plan_length: int = 3,
):
    if academic_term not in {"2026/27", "2027/28"}:
        raise HTTPException(status_code=400, detail="Choose a supported academic year.")
    if plan_length not in {1, 2, 3}:
        raise HTTPException(status_code=400, detail="Choose a plan length of one, two, or three years.")

    student = StudentRepository(db).get_by_user_id(user.id)
    if student is None:
        raise HTTPException(
            status_code=403,
            detail="A student profile is required to access the planner.",
        )

    audit = AuditService(AuditRepository(db)).get_degree_audit(student)
    plan, plan_courses = PlanService(PlanRepository(db)).get_plan_courses(
        student.id,
        academic_term,
    )
    course_service = CourseService(CourseRepository(db))
    return templates.TemplateResponse(
        request=request, 
        name="app.html",
        context={
            "user": user,
            "student": student,
            "audit": audit,
            "plan": plan,
            "plan_courses": plan_courses,
            "academic_term": academic_term,
            "planner_years": [f"Year {year}" for year in range(1, plan_length + 1)],
            "planner_terms": ["Semester 1", "Semester 2", "Summer"],
            "faculties": course_service.list_faculties(),
            "plan_length": plan_length,
        }
    )


@router.get("/app/catalog/search")
async def search_course_catalog(
    user: AuthDep,
    db: SessionDep,
    query: str = "",
    faculty: str | None = None,
):
    course_service = CourseService(CourseRepository(db))
    return {"courses": course_service.search_catalog(query, faculty)}


@router.post("/app/plans/courses")
async def add_course_to_plan(
    data: PlanCourseRequest,
    user: AuthDep,
    db: SessionDep,
):
    student = StudentRepository(db).get_by_user_id(user.id)
    if student is None:
        raise HTTPException(
            status_code=403,
            detail="A student profile is required to add courses to a plan.",
        )

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

    return {
        "course": course,
        "placement": plan_course.placement,
    }


@router.delete("/app/plans/courses/{plan_course_id}")
async def remove_course_from_plan(
    plan_course_id: int,
    user: AuthDep,
    db: SessionDep,
    academic_term: str = DEFAULT_ACADEMIC_TERM,
):
    student = StudentRepository(db).get_by_user_id(user.id)
    if student is None:
        raise HTTPException(
            status_code=403,
            detail="A student profile is required to edit a plan.",
        )

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
    return {"removed": True}


@router.get("/app/submit", response_class=HTMLResponse)
async def plan_submission_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    academic_term: str = DEFAULT_ACADEMIC_TERM,
):
    student = StudentRepository(db).get_by_user_id(user.id)
    if student is None:
        raise HTTPException(
            status_code=403,
            detail="A student profile is required to submit a plan.",
        )
    try:
        plan, plan_courses, total_credits = PlanService(
            PlanRepository(db)
        ).get_submission_details(student.id, academic_term)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    courses_by_placement = {}
    for plan_course, course in plan_courses:
        courses_by_placement.setdefault(plan_course.placement, []).append(
            (plan_course, course)
        )

    return templates.TemplateResponse(
        request=request,
        name="submit_plan.html",
        context={
            "user": user,
            "student": student,
            "plan": plan,
            "plan_courses": plan_courses,
            "plan_course_groups": list(courses_by_placement.items()),
            "total_credits": total_credits,
            "academic_term": academic_term,
        },
    )


@router.post("/app/save-draft")
async def save_plan_draft(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    academic_term: str = Form(),
    notes: str = Form(default=""),
):
    student = StudentRepository(db).get_by_user_id(user.id)
    if student is None:
        raise HTTPException(
            status_code=403,
            detail="A student profile is required to save a plan.",
        )
    try:
        PlanService(PlanRepository(db)).save_draft_notes(
            student_id=student.id,
            academic_term=academic_term,
            notes=notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    flash(request, "Your plan comments have been saved.")
    destination = request.url_for("plan_submission_view").include_query_params(
        academic_term=academic_term
    )
    return RedirectResponse(url=destination, status_code=303)


@router.post("/app/submit")
async def submit_plan_for_approval(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    academic_term: str = Form(),
    notes: str = Form(default=""),
):
    student = StudentRepository(db).get_by_user_id(user.id)
    if student is None:
        raise HTTPException(
            status_code=403,
            detail="A student profile is required to submit a plan.",
        )

    try:
        status = PlanService(PlanRepository(db)).submit_plan(
            student_id=student.id,
            academic_term=academic_term,
            notes=notes,
            advisor_id=student.advisor_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    flash(request, f"Your plan is {status.lower()} and awaiting advisor review.")
    destination = request.url_for("plan_submission_view").include_query_params(
        academic_term=academic_term
    )
    return RedirectResponse(url=destination, status_code=303)