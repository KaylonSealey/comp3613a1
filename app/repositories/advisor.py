from datetime import datetime

from sqlmodel import Session, select

from app.models.advisor import Advisor
from app.models.plan import Plan
from app.models.student import Student


class AdvisorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> Advisor | None:
        statement = select(Advisor).where(Advisor.user_id == user_id)
        return self.db.exec(statement).one_or_none()

    def list_assigned_plans(self, advisor_id: int) -> list[tuple[Plan, Student]]:
        statement = (
            select(Plan, Student)
            .join(Student, Student.id == Plan.student_id)
            .where(
                Plan.advisor_id == advisor_id,
                Plan.status == "Pending Review",
            )
            .order_by(Plan.submitted_at, Plan.id)
        )
        return self.db.exec(statement).all()

    def get_assigned_plan(
        self,
        advisor_id: int,
        plan_id: int,
    ) -> tuple[Plan, Student] | None:
        statement = (
            select(Plan, Student)
            .join(Student, Student.id == Plan.student_id)
            .where(Plan.id == plan_id, Plan.advisor_id == advisor_id)
        )
        return self.db.exec(statement).one_or_none()

    def save_decision(
        self,
        plan: Plan,
        status: str,
        advisor_notes: str | None,
        decided_at: datetime,
    ) -> Plan:
        plan.status = status
        plan.advisor_notes = advisor_notes
        plan.approved_at = decided_at if status == "Approved" else None
        self.db.add(plan)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(plan)
        return plan
