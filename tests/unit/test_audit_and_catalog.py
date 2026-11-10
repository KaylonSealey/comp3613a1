"""Unit tests for AuditService and CourseService (UT31–UT35), repositories mocked."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.audit_service import AuditService
from app.services.course_service import CourseService

pytestmark = pytest.mark.unit

STUDENT = SimpleNamespace(id=1, degree_program_id=1)


def requirement(course_id, category, credits=3):
    req = SimpleNamespace(requirement_type=category, credits=credits)
    course = SimpleNamespace(id=course_id, code=f"C{course_id}", title=f"Course {course_id}")
    return req, course


# ------------------------------------------------------------------ AuditService
def test_audit_groups_requirements_by_category():  # UT31
    repo = MagicMock()
    repo.list_requirements.return_value = [
        requirement(1, "Core"), requirement(2, "Core"), requirement(3, "Math"),
    ]
    repo.list_completed_course_ids.return_value = set()

    audit = AuditService(repo).get_degree_audit(STUDENT)

    assert [c["name"] for c in audit["categories"]] == ["Core", "Math"]
    assert audit["categories"][0]["required_credits"] == 6
    assert len(audit["categories"][0]["courses"]) == 2


def test_audit_counts_completed_credits_and_percent():  # UT32
    repo = MagicMock()
    repo.list_requirements.return_value = [
        requirement(1, "Core"), requirement(2, "Core"), requirement(3, "Math"),
    ]
    repo.list_completed_course_ids.return_value = {1, 3}

    audit = AuditService(repo).get_degree_audit(STUDENT)

    assert audit["total_required_credits"] == 9
    assert audit["total_completed_credits"] == 6
    assert audit["progress_percent"] == 67
    core_courses = audit["categories"][0]["courses"]
    assert [item["completed"] for item in core_courses] == [True, False]


def test_audit_with_no_requirements_is_zero():  # UT33
    repo = MagicMock()
    repo.list_requirements.return_value = []
    repo.list_completed_course_ids.return_value = set()

    audit = AuditService(repo).get_degree_audit(STUDENT)

    assert audit["progress_percent"] == 0
    assert audit["categories"] == []


# ------------------------------------------------------------------ CourseService
def test_search_trims_query():  # UT34
    repo = MagicMock()
    repo.search_catalog.return_value = []
    CourseService(repo).search_catalog(" comp ", "Computing")
    repo.search_catalog.assert_called_once_with("comp", "Computing")


def test_search_with_no_query_uses_empty_string():  # UT35
    repo = MagicMock()
    repo.search_catalog.return_value = []
    CourseService(repo).search_catalog(None)
    repo.search_catalog.assert_called_once_with("", None)
