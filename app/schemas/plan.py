from sqlmodel import SQLModel


class PlanCourseRequest(SQLModel):
    course_id: int
    academic_term: str
    placement: str
    plan_length: int
