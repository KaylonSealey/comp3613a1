from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class PlanCourse(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "course_id",
            name="uq_plan_course",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(foreign_key="plan.id")
    course_id: int = Field(foreign_key="course.id")
    placement: str
    status: str = Field(default="Planned")
    notes: Optional[str] = None
