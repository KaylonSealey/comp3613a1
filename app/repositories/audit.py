from sqlmodel import Session, select

from app.models.completed_course import CompletedCourse
from app.models.course import Course
from app.models.degree_requirement import DegreeRequirement


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_requirements(self, degree_program_id: int) -> list[tuple[DegreeRequirement, Course]]:
        statement = (
            select(DegreeRequirement, Course)
            .join(Course, Course.id == DegreeRequirement.course_id)
            .where(DegreeRequirement.degree_program_id == degree_program_id)
            .order_by(DegreeRequirement.requirement_type, Course.code)
        )
        return self.db.exec(statement).all()

    def list_completed_course_ids(self, student_id: int) -> set[int]:
        statement = select(CompletedCourse.course_id).where(
            CompletedCourse.student_id == student_id
        )
        return set(self.db.exec(statement).all())
