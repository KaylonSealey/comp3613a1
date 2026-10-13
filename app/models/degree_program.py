from typing import Optional

from sqlmodel import Field, SQLModel


class DegreeProgram(SQLModel, table=True):
    __tablename__ = "degree_program"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    code: str = Field(index=True, unique=True)
    required_credits: int
    catalog_year: str
