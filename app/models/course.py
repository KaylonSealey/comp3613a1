from typing import Optional

from sqlmodel import Field, SQLModel


class Course(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    title: str = Field(index=True)
    faculty: str = Field(index=True)
    credits: int
    level: str
    description: str