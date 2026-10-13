from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class CompletedCourse(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "course_id",
            name="uq_completed_course_student_course",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id")
    course_id: int = Field(foreign_key="course.id")
    grade: str
    term_completed: str
    transferred: bool = False
