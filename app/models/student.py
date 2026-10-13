from typing import Optional
from sqlmodel import Field, SQLModel


class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(unique=True, index=True)
    first_name: str
    last_name: str
    email: str
    degree_program_id: int = Field(foreign_key="degree_program.id")
    user_id: int = Field(foreign_key="user.id", unique=True)
    advisor_id: Optional[int] = Field(default=None, foreign_key="advisor.id")