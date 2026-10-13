from datetime import datetime

from app.models.course import Course
from app.models.plan import Plan
from app.models.plan_course import PlanCourse
from app.repositories.plan import PlanRepository


class PlanService:
    VALID_ACADEMIC_TERMS = {"2026/27", "2027/28"}
    VALID_TERMS = {"Semester 1", "Semester 2", "Summer"}
    MAX_CREDITS_PER_TERM = 16
    STUDENT_EDITABLE_STATUSES = {"Draft", "Revision Requested"}

    def __init__(self, plan_repo: PlanRepository):
        self.plan_repo = plan_repo

    def get_plan_courses(
        self,
        student_id: int,
        academic_term: str,
    ) -> tuple[Plan, list[tuple[PlanCourse, Course]]]:
        if academic_term not in self.VALID_ACADEMIC_TERMS:
            raise ValueError("Choose a supported academic year.")
        plan = self.plan_repo.get_or_create_draft(student_id, academic_term)
        if plan.id is None:
            raise RuntimeError("The draft plan was not persisted.")
        return plan, self.plan_repo.list_courses(plan.id)

    def get_submission_details(
        self,
        student_id: int,
        academic_term: str,
    ) -> tuple[Plan, list[tuple[PlanCourse, Course]], int]:
        if academic_term not in self.VALID_ACADEMIC_TERMS:
            raise ValueError("Choose a supported academic year.")
        plan = self.plan_repo.get_or_create_draft(student_id, academic_term)
        if plan.id is None:
            raise RuntimeError("The plan was not persisted.")
        courses = self.plan_repo.list_courses(plan.id)
        total_credits = sum(course.credits for _, course in courses)
        return plan, courses, total_credits

    def save_draft_notes(
        self,
        student_id: int,
        academic_term: str,
        notes: str,
    ) -> str:
        if academic_term not in self.VALID_ACADEMIC_TERMS:
            raise ValueError("Choose a supported academic year.")
        plan = self.plan_repo.get_or_create_draft(student_id, academic_term)
        if plan.status not in self.STUDENT_EDITABLE_STATUSES:
            raise ValueError("Only draft or revision-requested plans can be changed.")
        cleaned_notes = notes.strip()
        saved_plan = self.plan_repo.save_notes(plan, cleaned_notes or None)
        return saved_plan.status

    def submit_plan(
        self,
        student_id: int,
        academic_term: str,
        notes: str,
        advisor_id: int | None,
    ) -> str:
        if academic_term not in self.VALID_ACADEMIC_TERMS:
            raise ValueError("Choose a supported academic year.")
        plan = self.plan_repo.get_plan(student_id, academic_term)
        if plan is None:
            raise LookupError("There is no plan to submit for this academic year.")
        if plan.status not in self.STUDENT_EDITABLE_STATUSES:
            raise ValueError("Only draft or revision-requested plans can be submitted.")
        if advisor_id is None:
            raise ValueError("An advisor must be assigned before submitting this plan.")
        if plan.id is None:
            raise RuntimeError("The plan was not persisted.")
        if not self.plan_repo.list_courses(plan.id):
            raise ValueError("Add at least one course before submitting your plan.")
        cleaned_notes = notes.strip()
        submitted_plan = self.plan_repo.mark_submitted(
            plan=plan,
            advisor_id=advisor_id,
            notes=cleaned_notes or None,
            submitted_at=datetime.now(),
        )
        return submitted_plan.status

    def add_course(
        self,
        student_id: int,
        course_id: int,
        academic_term: str,
        placement: str,
        plan_length: int,
    ) -> tuple[PlanCourse, Course]:
        normalized_term = academic_term.strip()
        normalized_placement = placement.strip()
        if not normalized_term or not normalized_placement:
            raise ValueError("Choose an academic term and planner destination.")
        if normalized_term not in self.VALID_ACADEMIC_TERMS:
            raise ValueError("Choose a supported academic year.")
        if plan_length not in {1, 2, 3}:
            raise ValueError("Choose a plan length of one, two, or three years.")
        placement_parts = normalized_placement.split(" - ", maxsplit=1)
        if (
            len(placement_parts) != 2
            or placement_parts[0] not in {
                f"Year {year}" for year in range(1, plan_length + 1)
            }
            or placement_parts[1] not in self.VALID_TERMS
        ):
            raise ValueError("Choose a valid year and term destination.")

        plan = self.plan_repo.get_or_create_draft(student_id, normalized_term)
        if plan.id is None:
            raise RuntimeError("The draft plan was not persisted.")
        if plan.status not in self.STUDENT_EDITABLE_STATUSES:
            raise ValueError("Only draft or revision-requested plans can be changed.")
        course = self.plan_repo.get_course(course_id)
        if course is None:
            raise LookupError("The selected course does not exist.")
        credits_in_term = self.plan_repo.credits_in_placement(
            plan.id,
            normalized_placement,
        )
        if credits_in_term + course.credits > self.MAX_CREDITS_PER_TERM:
            raise ValueError(
                f"A semester cannot exceed {self.MAX_CREDITS_PER_TERM} credits."
            )
        return self.plan_repo.add_course(
            plan_id=plan.id,
            course_id=course_id,
            placement=normalized_placement,
        )

    def remove_course(
        self,
        student_id: int,
        academic_term: str,
        plan_course_id: int,
    ) -> bool:
        if academic_term not in self.VALID_ACADEMIC_TERMS:
            raise ValueError("Choose a supported academic year.")
        plan = self.plan_repo.get_plan(student_id, academic_term)
        if plan is None:
            return False
        if plan.id is None:
            raise RuntimeError("The draft plan was not persisted.")
        if plan.status not in self.STUDENT_EDITABLE_STATUSES:
            raise ValueError("Only draft or revision-requested plans can be changed.")
        return self.plan_repo.remove_course(plan.id, plan_course_id)
