from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class DegreeRequirement(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "degree_program_id",
            "course_id",
            name="uq_degree_requirement_program_course",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    degree_program_id: int = Field(foreign_key="degree_program.id")
    course_id: int = Field(foreign_key="course.id")
    requirement_type: str
    credits: int
