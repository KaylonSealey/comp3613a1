"""Unit tests for AdvisorService (UT24–UT30), with AdvisorRepository mocked."""
from unittest.mock import MagicMock

import pytest

from app.models.plan import Plan
from app.models.student import Student
from app.services.advisor_service import AdvisorService

pytestmark = pytest.mark.unit


def make_plan(status="Pending Review"):
    return Plan(id=7, student_id=1, advisor_id=2, academic_term="2026/27", status=status)


def make_student():
    return Student(
        id=1, student_id="1002450678", first_name="John", last_name="Doe",
        email="bob@example.com", degree_program_id=1, user_id=1, advisor_id=2,
    )


def _save_decision(plan, status, advisor_notes, decided_at):
    plan.status = status
    plan.advisor_notes = advisor_notes
    return plan


@pytest.fixture
def repo():
    repo = MagicMock()
    repo.get_assigned_plan.return_value = (make_plan(), make_student())
    repo.save_decision.side_effect = _save_decision
    return repo


@pytest.fixture
def service(repo):
    return AdvisorService(repo)


def test_approve_sets_status_approved(service, repo):  # UT24
    status = service.submit_decision(advisor_id=2, plan_id=7, decision="approve", notes="")
    assert status == "Approved"
    assert repo.save_decision.call_args.kwargs["status"] == "Approved"


def test_request_revisions_saves_notes(service, repo):  # UT25
    status = service.submit_decision(2, 7, "request_revisions", " Add WRIT1001 ")
    assert status == "Revision Requested"
    assert repo.save_decision.call_args.kwargs["advisor_notes"] == "Add WRIT1001"


@pytest.mark.parametrize("notes", ["", "   "])
def test_request_revisions_requires_notes(service, repo, notes):  # UT26
    with pytest.raises(ValueError, match="notes are required"):
        service.submit_decision(2, 7, "request_revisions", notes)
    repo.save_decision.assert_not_called()


def test_unknown_decision_is_rejected(service, repo):  # UT27
    with pytest.raises(ValueError):
        service.submit_decision(2, 7, "reject", "No")
    repo.save_decision.assert_not_called()


@pytest.mark.parametrize("status", ["Draft", "Approved", "Revision Requested"])
def test_only_pending_plans_can_be_decided(service, repo, status):  # UT28
    repo.get_assigned_plan.return_value = (make_plan(status=status), make_student())
    with pytest.raises(ValueError, match="pending review"):
        service.submit_decision(2, 7, "approve", "")
    repo.save_decision.assert_not_called()


def test_unassigned_plan_raises_lookup_error(service, repo):  # UT29
    repo.get_assigned_plan.return_value = None
    with pytest.raises(LookupError, match="not assigned"):
        service.get_assigned_plan(advisor_id=2, plan_id=99)


def test_get_assigned_plans_returns_repo_result(service, repo):  # UT30
    queue = [(make_plan(), make_student())]
    repo.list_assigned_plans.return_value = queue
    assert service.get_assigned_plans(2) is queue
    repo.list_assigned_plans.assert_called_once_with(2)
