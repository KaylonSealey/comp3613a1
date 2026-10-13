from sqlmodel import Session, select, func
from app.models.user import UserBase, User
from app.models.student import Student
from typing import Optional, Tuple
from app.utilities.pagination import Pagination
from app.schemas.user import UserUpdate
import logging
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class DuplicateAccountError(Exception):
    pass


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_data: UserBase) -> Optional[User]:
        try:
            user_db = User.model_validate(user_data)
            self.db.add(user_db)
            self.db.commit()
            self.db.refresh(user_db)
            return user_db
        except Exception as e:
            logger.error(f"An error occurred while saving user: {e}")
            self.db.rollback()
            raise

    def create_student_account(
        self,
        user_data: UserBase,
        *,
        student_id: str,
        first_name: str,
        last_name: str,
        degree_program_id: int,
    ) -> User:
        from app.models.degree_program import DegreeProgram

        if self.db.get(DegreeProgram, degree_program_id) is None:
            raise ValueError("The selected degree program does not exist.")

        try:
            user_db = User.model_validate(user_data)
            self.db.add(user_db)
            self.db.flush()
            student = Student(
                user_id=user_db.id,
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                email=user_db.email,
                degree_program_id=degree_program_id,
            )
            self.db.add(student)
            self.db.commit()
            self.db.refresh(user_db)
            return user_db
        except IntegrityError as exc:
            self.db.rollback()
            logger.info("Student registration conflicted with an existing record.")
            raise DuplicateAccountError(
                "Username, email, or student ID already exists."
            ) from exc
        except Exception as exc:
            self.db.rollback()
            logger.error("An error occurred while creating student account: %s", exc)
            raise

    def search_users(self, query: str, page:int=1, limit:int=10) -> Tuple[list[User], Pagination]:
        offset = (page - 1) * limit
        db_qry = select(User)
        if query:
            db_qry = db_qry.where(
                User.username.ilike(f"%{query}%") | User.email.ilike(f"%{query}%")
            )
        count_qry = select(func.count()).select_from(db_qry.subquery())
        count_todos = self.db.exec(count_qry).one()

        users = self.db.exec(db_qry.offset(offset).limit(limit)).all()
        pagination = Pagination(total_count=count_todos, current_page=page, limit=limit)

        return users, pagination

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.exec(select(User).where(User.username == username)).one_or_none()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_all_users(self) -> list[User]:
        return self.db.exec(select(User)).all()

    def update_user(self, user_id:int, user_data: UserUpdate)->User:
        user = self.db.get(User, user_id)
        if not user:
            raise Exception("Invalid user id given")
        if user_data.username:
            user.username = user_data.username
        if user_data.email:
            user.email = user_data.email
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            logger.error(f"An error occurred while updating user: {e}")
            self.db.rollback()
            raise

    def delete_user(self, user_id: int):
        user = self.db.get(User, user_id)
        if not user:
            raise Exception("User doesn't exist")
        try:
            self.db.delete(user)
            self.db.commit()
        except Exception as e:
            logger.error(f"An error occurred while deleting user: {e}")
            self.db.rollback()
            raise
