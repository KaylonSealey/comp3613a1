from datetime import datetime

from sqlmodel import Session, func, select

from app.models.course import Course
from app.models.plan import Plan
from app.models.plan_course import PlanCourse


class PlanRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_plan(self, student_id: int, academic_term: str) -> Plan | None:
        statement = select(Plan).where(
            Plan.student_id == student_id,
            Plan.academic_term == academic_term,
        )
        return self.db.exec(statement).one_or_none()

    def save_notes(self, plan: Plan, notes: str | None) -> Plan:
        plan.notes = notes
        self.db.add(plan)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(plan)
        return plan

    def mark_submitted(
        self,
        plan: Plan,
        advisor_id: int,
        notes: str | None,
        submitted_at: datetime,
    ) -> Plan:
        plan.advisor_id = advisor_id
        plan.notes = notes
        plan.status = "Pending Review"
        plan.submitted_at = submitted_at
        plan.approved_at = None
        self.db.add(plan)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(plan)
        return plan

    def get_or_create_draft(self, student_id: int, academic_term: str) -> Plan:
        plan = self.get_plan(student_id, academic_term)
        if plan is not None:
            return plan

        plan = Plan(student_id=student_id, academic_term=academic_term)
        self.db.add(plan)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(plan)
        return plan

    def list_courses(self, plan_id: int) -> list[tuple[PlanCourse, Course]]:
        statement = (
            select(PlanCourse, Course)
            .join(Course, Course.id == PlanCourse.course_id)
            .where(PlanCourse.plan_id == plan_id)
            .order_by(PlanCourse.placement, Course.code)
        )
        return self.db.exec(statement).all()

    def get_course(self, course_id: int) -> Course | None:
        return self.db.get(Course, course_id)

    def credits_in_placement(self, plan_id: int, placement: str) -> int:
        statement = (
            select(func.coalesce(func.sum(Course.credits), 0))
            .join(PlanCourse, PlanCourse.course_id == Course.id)
            .where(
                PlanCourse.plan_id == plan_id,
                PlanCourse.placement == placement,
            )
        )
        return self.db.exec(statement).one()

    def add_course(
        self,
        plan_id: int,
        course_id: int,
        placement: str,
    ) -> tuple[PlanCourse, Course]:
        course = self.db.get(Course, course_id)
        if course is None:
            raise LookupError("The selected course does not exist.")

        duplicate = self.db.exec(
            select(PlanCourse).where(
                PlanCourse.plan_id == plan_id,
                PlanCourse.course_id == course_id,
            )
        ).one_or_none()
        if duplicate is not None:
            raise ValueError("That course is already in this plan.")

        item = PlanCourse(
            plan_id=plan_id,
            course_id=course_id,
            placement=placement,
        )
        self.db.add(item)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(item)
        return item, course

    def remove_course(self, plan_id: int, plan_course_id: int) -> bool:
        item = self.db.exec(
            select(PlanCourse).where(
                PlanCourse.id == plan_course_id,
                PlanCourse.plan_id == plan_id,
            )
        ).one_or_none()
        if item is None:
            return False

        self.db.delete(item)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return True
