from sqlalchemy import or_
from sqlmodel import Session, select

from app.models.course import Course


class CourseRepository:
    def __init__(self, db: Session):
        self.db = db

    def search_catalog(self, query: str, faculty: str | None = None) -> list[Course]:
        normalized_query = (query or "").strip()
        statement = select(Course)

        if normalized_query:
            search_term = f"%{normalized_query.lower()}%"
            statement = statement.where(
                or_(
                    Course.code.ilike(search_term),
                    Course.title.ilike(search_term),
                    Course.faculty.ilike(search_term),
                    Course.description.ilike(search_term),
                )
            )
        if faculty:
            statement = statement.where(Course.faculty.ilike(faculty.strip()))

        return self.db.exec(statement.order_by(Course.code)).all()

    def list_faculties(self) -> list[str]:
        statement = select(Course.faculty).distinct().order_by(Course.faculty)
        return self.db.exec(statement).all()
