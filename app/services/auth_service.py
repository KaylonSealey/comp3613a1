from typing import Optional

from app.repositories.user import UserRepository
from app.utilities.security import (
    create_access_token,
    encrypt_password,
    verify_password,
)
from app.schemas.user import RegularUserCreate


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(
            plaintext_password=password,
            encrypted_password=user.password,
        ):
            return None
        access_token = create_access_token(data={"sub": f"{user.id}", "role": user.role})
        return access_token

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        *,
        student_id: str,
        first_name: str,
        last_name: str,
        degree_program_id: int,
    ):
        student_id = student_id.strip()
        first_name = first_name.strip()
        last_name = last_name.strip()
        if not student_id or not first_name or not last_name:
            raise ValueError("Student ID, first name, and last name are required.")

        new_user = RegularUserCreate(
            username=username,
            email=email,
            password=encrypt_password(password),
        )
        return self.user_repo.create_student_account(
            new_user,
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            degree_program_id=degree_program_id,
        )
