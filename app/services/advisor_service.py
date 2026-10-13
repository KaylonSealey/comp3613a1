from datetime import datetime

from app.models.plan import Plan
from app.models.student import Student
from app.repositories.advisor import AdvisorRepository


class AdvisorService:
    def __init__(self, advisor_repo: AdvisorRepository):
        self.advisor_repo = advisor_repo

    def get_assigned_plans(self, advisor_id: int) -> list[tuple[Plan, Student]]:
        return self.advisor_repo.list_assigned_plans(advisor_id)

    def get_assigned_plan(
        self,
        advisor_id: int,
        plan_id: int,
    ) -> tuple[Plan, Student]:
        result = self.advisor_repo.get_assigned_plan(advisor_id, plan_id)
        if result is None:
            raise LookupError("That plan is not assigned to this advisor.")
        return result

    def submit_decision(
        self,
        advisor_id: int,
        plan_id: int,
        decision: str,
        notes: str,
    ) -> str:
        plan, _ = self.get_assigned_plan(advisor_id, plan_id)
        if plan.status != "Pending Review":
            raise ValueError("Only plans pending review can receive an advisor decision.")

        cleaned_notes = notes.strip()
        if decision == "approve":
            status = "Approved"
        elif decision == "request_revisions":
            if not cleaned_notes:
                raise ValueError("Advising notes are required when requesting revisions.")
            status = "Revision Requested"
        else:
            raise ValueError("Choose Approve Plan or Request Revisions.")

        updated_plan = self.advisor_repo.save_decision(
            plan=plan,
            status=status,
            advisor_notes=cleaned_notes or None,
            decided_at=datetime.now(),
        )
        return updated_plan.status
