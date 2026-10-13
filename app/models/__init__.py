"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.user import User
from app.models.course import Course
from app.models.degree_program import DegreeProgram
from app.models.student import Student
from app.models.advisor import Advisor
from app.models.degree_requirement import DegreeRequirement
from app.models.completed_course import CompletedCourse
from app.models.plan import Plan
from app.models.plan_course import PlanCourse

__all__ = [
    "User",
    "Course",
    "DegreeProgram",
    "Student",
    "Advisor",
    "DegreeRequirement",
    "CompletedCourse",
    "Plan",
    "PlanCourse",
]
