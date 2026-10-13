from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.audit import AuditRepository
from app.repositories.advisor import AdvisorRepository
from app.repositories.degree_program import DegreeProgramRepository
from app.repositories.plan import PlanRepository
from app.services.audit_service import AuditService
from app.services.advisor_service import AdvisorService
from app.utilities.flash import flash
from . import router, templates


@router.get("/advisor", response_class=HTMLResponse)
async def advisor_home_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    advisor = AdvisorRepository(db).get_by_user_id(user.id)
    if advisor is None:
        raise HTTPException(
            status_code=403,
            detail="An advisor profile is required to access the advisor portal.",
        )

    advisor_repo = AdvisorRepository(db)
    plans = AdvisorService(advisor_repo).get_assigned_plans(advisor.id)

    return templates.TemplateResponse(
        request=request,
        name="advisor_home.html",
        context={
            "user": user,
            "advisor": advisor,
            "plans": plans,
        },
    )


@router.get(
    "/advisor/plans/{plan_id}",
    response_class=HTMLResponse,
    name="advisor_plan_review_view",
)
async def advisor_plan_review_view(
    plan_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    advisor_repo = AdvisorRepository(db)
    advisor = advisor_repo.get_by_user_id(user.id)
    if advisor is None:
        raise HTTPException(
            status_code=403,
            detail="An advisor profile is required to review plans.",
        )

    try:
        plan, student = AdvisorService(advisor_repo).get_assigned_plan(
            advisor.id,
            plan_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if plan.id is None:
        raise HTTPException(status_code=500, detail="The review plan has no database ID.")

    degree_program = DegreeProgramRepository(db).get_by_id(
        student.degree_program_id
    )
    if degree_program is None:
        raise HTTPException(
            status_code=500,
            detail="The student's degree program could not be found.",
        )
    audit = AuditService(AuditRepository(db)).get_degree_audit(student)
    plan_courses = PlanRepository(db).list_courses(plan.id)

    return templates.TemplateResponse(
        request=request,
        name="advisor_review.html",
        context={
            "user": user,
            "advisor": advisor,
            "plan": plan,
            "student": student,
            "degree_program": degree_program,
            "audit": audit,
            "plan_courses": plan_courses,
            "total_plan_credits": sum(course.credits for _, course in plan_courses),
        },
    )


@router.post("/advisor/plans/{plan_id}/decision")
async def submit_advisor_decision(
    plan_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
    decision: str = Form(),
    notes: str = Form(default=""),
):
    advisor_repo = AdvisorRepository(db)
    advisor = advisor_repo.get_by_user_id(user.id)
    if advisor is None:
        raise HTTPException(
            status_code=403,
            detail="An advisor profile is required to submit a decision.",
        )

    try:
        status = AdvisorService(advisor_repo).submit_decision(
            advisor_id=advisor.id,
            plan_id=plan_id,
            decision=decision,
            notes=notes,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    flash(request, f"The plan decision was recorded: {status}.")
    destination = request.url_for(
        "advisor_plan_review_view",
        plan_id=plan_id,
    )
    return RedirectResponse(url=destination, status_code=303)