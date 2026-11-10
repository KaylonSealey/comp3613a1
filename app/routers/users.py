from fastapi import Request
from app.dependencies import SessionDep
from app.dependencies.auth import AdminUserDep
from . import api_router
from app.services.user_service import UserService
from app.repositories.user import UserRepository
from app.schemas import UserResponse


# API endpoint for listing users (admin only)
@api_router.get("/users", response_model=list[UserResponse])
async def list_users(request: Request, db: SessionDep, admin: AdminUserDep):
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    return user_service.get_all_users()
