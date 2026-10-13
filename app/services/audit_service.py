from app.models.student import Student
from app.repositories.audit import AuditRepository


class AuditService:
    def __init__(self, audit_repo: AuditRepository):
        self.audit_repo = audit_repo

    def get_degree_audit(self, student: Student) -> dict:
        requirements = self.audit_repo.list_requirements(student.degree_program_id)
        completed_course_ids = self.audit_repo.list_completed_course_ids(student.id)
        categories: dict[str, dict] = {}

        for requirement, course in requirements:
            category = categories.setdefault(
                requirement.requirement_type,
                {
                    "name": requirement.requirement_type,
                    "required_credits": 0,
                    "completed_credits": 0,
                    "courses": [],
                },
            )
            is_completed = course.id in completed_course_ids
            category["required_credits"] += requirement.credits
            if is_completed:
                category["completed_credits"] += requirement.credits
            category["courses"].append(
                {
                    "course": course,
                    "credits": requirement.credits,
                    "completed": is_completed,
                }
            )

        total_required = sum(item["required_credits"] for item in categories.values())
        total_completed = sum(item["completed_credits"] for item in categories.values())
        return {
            "categories": list(categories.values()),
            "total_required_credits": total_required,
            "total_completed_credits": total_completed,
            "progress_percent": (
                round(total_completed / total_required * 100)
                if total_required
                else 0
            ),
        }
