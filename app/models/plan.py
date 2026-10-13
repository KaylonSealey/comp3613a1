from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Plan(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "academic_term",
            name="uq_plan_student_term",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id")
    advisor_id: Optional[int] = Field(default=None, foreign_key="advisor.id")
    academic_term: str = Field(index=True)
    status: str = Field(default="Draft", index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    advisor_notes: Optional[str] = None
