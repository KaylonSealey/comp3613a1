from typing import Annotated
from fastapi import Depends, HTTPException, status, Request
import jwt
from jwt.exceptions import InvalidTokenError
from app.config import get_settings
from app.models.user import User
from app.dependencies.session import SessionDep
from app.repositories.user import UserRepository

async def get_current_user(request:Request, db:SessionDep)->User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Browser pages send the JWT as a cookie; API clients (Postman, mobile)
    # send it as "Authorization: Bearer <token>".
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip() or None
    if token is None:
        token = request.cookies.get("access_token")

    if token is None:
        raise credentials_exception
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[get_settings().jwt_algorithm])
        user_id = payload.get("sub",None)
    except InvalidTokenError as e:
        print("Invalid token error: ", e)
        raise credentials_exception

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception
    return user

async def is_logged_in(request: Request, db:SessionDep):
    try:
        await get_current_user(request, db)
        return True
    except Exception:
        return False

IsUserLoggedIn = Annotated[bool, Depends(is_logged_in)]
AuthDep = Annotated[User, Depends(get_current_user)]

async def is_admin(user: User):
    return user.role == "admin"

async def is_admin_dep(user: AuthDep):
    if not await is_admin(user):
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to access this page",
            )
    return user

AdminDep = Annotated[User, Depends(is_admin_dep)]


# ---------------------------------------------------------------------------
# Role-based authorization for the REST API.
# 401 = not logged in (no/invalid token); 403 = logged in but wrong role.
# ---------------------------------------------------------------------------
STUDENT_ROLE = "regular_user"
ADVISOR_ROLE = "advisor"
ADMIN_ROLE = "admin"


def require_role(*roles: str):
    async def role_checker(user: AuthDep) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return user

    return role_checker


StudentUserDep = Annotated[User, Depends(require_role(STUDENT_ROLE))]
AdvisorUserDep = Annotated[User, Depends(require_role(ADVISOR_ROLE))]
AdminUserDep = Annotated[User, Depends(require_role(ADMIN_ROLE))]
