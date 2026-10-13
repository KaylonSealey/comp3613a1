from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request, status, Form
from app.dependencies import SessionDep
from app.services.auth_service import AuthService
from app.repositories.user import DuplicateAccountError, UserRepository
from app.repositories.degree_program import DegreeProgramRepository
from app.services.degree_program_service import DegreeProgramService
from app.utilities.flash import flash
from . import router, templates

# View route (loads the page)
@router.get("/register", response_class=HTMLResponse)
async def register_view(request: Request, db: SessionDep):
    degree_programs = DegreeProgramService(
        DegreeProgramRepository(db)
    ).list_programs()
    return templates.TemplateResponse(
        request=request, 
        name="register.html",
        context={"degree_programs": degree_programs},
    )

# Action route (performs an action)
@router.post('/register', response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
def signup_user(request:Request, db:SessionDep, 
    username: str = Form(),
    email: str = Form(),
    password: str = Form(),
    student_id: str = Form(),
    first_name: str = Form(),
    last_name: str = Form(),
    degree_program_id: int = Form(),
):
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    try:
        auth_service.register_user(
            username,
            email,
            password,
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            degree_program_id=degree_program_id,
        )
        flash(request, "Registration completed! Sign in now!")
        return RedirectResponse(url=request.url_for("login_view"), status_code=status.HTTP_303_SEE_OTHER)
    except (DuplicateAccountError, ValueError) as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(url=request.url_for("register_view"), status_code=status.HTTP_303_SEE_OTHER)
