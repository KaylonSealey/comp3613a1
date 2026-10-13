from typing import Optional

from sqlmodel import Field, SQLModel


class Advisor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    first_name: str
    last_name: str
    email: str = Field(index=True, unique=True)
    department: str
