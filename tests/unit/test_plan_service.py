"""Unit tests for PlanService (UT01–UT23).

PlanRepository is replaced by a MagicMock, so only the service's own rules are
tested: slot validation, the 16-credit cap, plan locking and submission.
"""
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.models.course import Course
from app.models.plan import Plan
from app.models.plan_course import PlanCourse
from app.services.plan_service import PlanService

pytestmark = pytest.mark.unit


def make_course(course_id=1, credits=3, code="COMP1002"):
    return Course(
        id=course_id,
        code=code,
        title="Data Fundamentals",
        faculty="Computing",
        credits=credits,
        level="Undergraduate",
        description="Demo",
    )


def make_plan(status="Draft", plan_id=10):
    return Plan(id=plan_id, student_id=1, academic_term="2026/27", status=status)


@pytest.fixture
def repo():
    """A mocked PlanRepository with a Draft plan and an empty slot."""
    repo = MagicMock()
    repo.get_or_create_draft.return_value = make_plan()
    repo.get_plan.return_value = make_plan()
    repo.get_course.return_value = make_course()
    repo.credits_in_placement.return_value = 0
    repo.add_course.side_effect = lambda plan_id, course_id, placement: (
        PlanCourse(id=5, plan_id=plan_id, course_id=course_id, placement=placement),
        make_course(course_id),
    )
    repo.list_courses.return_value = [(PlanCourse(id=5, plan_id=10, course_id=1, placement="Year 1 - Semester 1"), make_course())]
    return repo


@pytest.fixture
def service(repo):
    return PlanService(repo)


# ------------------------------------------------------------------ add_course
class TestAddCourse:
    def test_add_course_saves_valid_course(self, service, repo):  # UT01
        plan_course, course = service.add_course(
            student_id=1, course_id=1, academic_term="2026/27",
            placement="Year 1 - Semester 1", plan_length=3,
        )
        repo.add_course.assert_called_once_with(
            plan_id=10, course_id=1, placement="Year 1 - Semester 1"
        )
        assert plan_course.placement == "Year 1 - Semester 1"
        assert course.code == "COMP1002"

    def test_add_course_trims_term_and_placement(self, service, repo):  # UT02
        service.add_course(
            student_id=1, course_id=1, academic_term=" 2026/27 ",
            placement=" Year 2 - Summer ", plan_length=3,
        )
        repo.get_or_create_draft.assert_called_once_with(1, "2026/27")
        repo.add_course.assert_called_once_with(
            plan_id=10, course_id=1, placement="Year 2 - Summer"
        )

    def test_add_course_rejects_unsupported_academic_year(self, service, repo):  # UT03
        with pytest.raises(ValueError, match="supported academic year"):
            service.add_course(1, 1, "2030/31", "Year 1 - Semester 1", 3)
        repo.add_course.assert_not_called()

    @pytest.mark.parametrize("plan_length", [0, 4])
    def test_add_course_rejects_invalid_plan_length(self, service, repo, plan_length):  # UT04
        with pytest.raises(ValueError, match="plan length"):
            service.add_course(1, 1, "2026/27", "Year 1 - Semester 1", plan_length)
        repo.add_course.assert_not_called()

    @pytest.mark.parametrize(
        "placement", ["", "Year 1", "Year 1 - Fall", "Semester 1 - Year 1"]
    )
    def test_add_course_rejects_invalid_placement(self, service, repo, placement):  # UT05
        with pytest.raises(ValueError):
            service.add_course(1, 1, "2026/27", placement, 3)
        repo.add_course.assert_not_called()

    def test_add_course_rejects_year_beyond_plan_length(self, service, repo):  # UT06
        with pytest.raises(ValueError, match="valid year and term"):
            service.add_course(1, 1, "2026/27", "Year 2 - Semester 1", 1)
        repo.add_course.assert_not_called()

    def test_add_course_rejects_unknown_course(self, service, repo):  # UT07
        repo.get_course.return_value = None
        with pytest.raises(LookupError):
            service.add_course(1, 99, "2026/27", "Year 1 - Semester 1", 3)
        repo.add_course.assert_not_called()

    def test_add_course_rejects_more_than_16_credits(self, service, repo):  # UT08
        repo.credits_in_placement.return_value = 15
        with pytest.raises(ValueError, match="16 credits"):
            service.add_course(1, 1, "2026/27", "Year 1 - Semester 1", 3)
        repo.add_course.assert_not_called()

    def test_add_course_allows_exactly_16_credits(self, service, repo):  # UT09
        repo.credits_in_placement.return_value = 13
        service.add_course(1, 1, "2026/27", "Year 1 - Semester 1", 3)
        repo.add_course.assert_called_once()

    @pytest.mark.parametrize("status", ["Pending Review", "Approved"])
    def test_add_course_rejects_locked_plan(self, service, repo, status):  # UT10
        repo.get_or_create_draft.return_value = make_plan(status=status)
        with pytest.raises(ValueError, match="Only draft"):
            service.add_course(1, 1, "2026/27", "Year 1 - Semester 1", 3)
        repo.add_course.assert_not_called()

    def test_add_course_allowed_after_revision_requested(self, service, repo):  # UT11
        repo.get_or_create_draft.return_value = make_plan(status="Revision Requested")
        service.add_course(1, 1, "2026/27", "Year 1 - Semester 1", 3)
        repo.add_course.assert_called_once()


# ------------------------------------------------------------------ remove_course
class TestRemoveCourse:
    def test_remove_course_from_draft(self, service, repo):  # UT12
        repo.remove_course.return_value = True
        assert service.remove_course(1, "2026/27", 5) is True
        repo.remove_course.assert_called_once_with(10, 5)

    def test_remove_course_without_plan_returns_false(self, service, repo):  # UT13
        repo.get_plan.return_value = None
        assert service.remove_course(1, "2026/27", 5) is False
        repo.remove_course.assert_not_called()

    def test_remove_course_rejects_locked_plan(self, service, repo):  # UT14
        repo.get_plan.return_value = make_plan(status="Approved")
        with pytest.raises(ValueError):
            service.remove_course(1, "2026/27", 5)
        repo.remove_course.assert_not_called()


# ------------------------------------------------------------------ save_draft_notes
class TestSaveDraftNotes:
    def test_save_draft_notes_trims_text(self, service, repo):  # UT15
        plan = make_plan()
        repo.get_or_create_draft.return_value = plan
        repo.save_notes.return_value = plan
        service.save_draft_notes(1, "2026/27", "  Check my electives  ")
        repo.save_notes.assert_called_once_with(plan, "Check my electives")

    def test_save_draft_notes_blank_saved_as_none(self, service, repo):  # UT16
        plan = make_plan()
        repo.get_or_create_draft.return_value = plan
        repo.save_notes.return_value = plan
        service.save_draft_notes(1, "2026/27", "   ")
        repo.save_notes.assert_called_once_with(plan, None)

    def test_save_draft_notes_rejects_locked_plan(self, service, repo):  # UT17
        repo.get_or_create_draft.return_value = make_plan(status="Pending Review")
        with pytest.raises(ValueError):
            service.save_draft_notes(1, "2026/27", "Too late")
        repo.save_notes.assert_not_called()


# ------------------------------------------------------------------ submit_plan
class TestSubmitPlan:
    def test_submit_plan_marks_pending_review(self, service, repo):  # UT18
        plan = make_plan()
        repo.get_plan.return_value = plan
        repo.mark_submitted.return_value = make_plan(status="Pending Review")

        status = service.submit_plan(1, "2026/27", " Ready ", advisor_id=3)

        assert status == "Pending Review"
        kwargs = repo.mark_submitted.call_args.kwargs
        assert kwargs["plan"] is plan
        assert kwargs["advisor_id"] == 3
        assert kwargs["notes"] == "Ready"
        assert isinstance(kwargs["submitted_at"], datetime)

    def test_submit_plan_without_plan_raises_lookup_error(self, service, repo):  # UT19
        repo.get_plan.return_value = None
        with pytest.raises(LookupError):
            service.submit_plan(1, "2026/27", "", advisor_id=3)
        repo.mark_submitted.assert_not_called()

    def test_submit_plan_requires_assigned_advisor(self, service, repo):  # UT20
        with pytest.raises(ValueError, match="advisor must be assigned"):
            service.submit_plan(1, "2026/27", "", advisor_id=None)
        repo.mark_submitted.assert_not_called()

    def test_submit_plan_rejects_empty_plan(self, service, repo):  # UT21
        repo.list_courses.return_value = []
        with pytest.raises(ValueError, match="at least one course"):
            service.submit_plan(1, "2026/27", "", advisor_id=3)
        repo.mark_submitted.assert_not_called()

    @pytest.mark.parametrize("status", ["Pending Review", "Approved"])
    def test_submit_plan_rejects_already_submitted_plan(self, service, repo, status):  # UT22
        repo.get_plan.return_value = make_plan(status=status)
        with pytest.raises(ValueError, match="Only draft"):
            service.submit_plan(1, "2026/27", "", advisor_id=3)
        repo.mark_submitted.assert_not_called()


# ------------------------------------------------------------------ get_submission_details
def test_submission_details_total_credits(service, repo):  # UT23
    repo.list_courses.return_value = [
        (PlanCourse(id=1, plan_id=10, course_id=1, placement="Year 1 - Semester 1"), make_course(1, 3)),
        (PlanCourse(id=2, plan_id=10, course_id=2, placement="Year 1 - Semester 1"), make_course(2, 4, "COMP2001")),
    ]
    plan, courses, total = service.get_submission_details(1, "2026/27")
    assert total == 7
    assert len(courses) == 2
