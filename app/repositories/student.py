from sqlmodel import Session, select

from app.models.student import Student


class StudentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> Student | None:
        statement = select(Student).where(Student.user_id == user_id)
        return self.db.exec(statement).one_or_none()
