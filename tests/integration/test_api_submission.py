"""Integration tests: Workflow 2 — Submit Course Selection Plan for Approval (IT23–IT28)."""
import pytest

from helpers import TERM, add_course, get_plan, submit_plan

pytestmark = pytest.mark.integration


def test_save_draft_comments(client, auth):  # IT23
    bob = auth("bob")
    response = client.patch("/api/me/plan", headers=bob,
                            json={"academic_term": TERM, "notes": "  Please check my electives  "})
    assert response.status_code == 200
    assert response.json()["status"] == "Draft"
    assert get_plan(client, bob).json()["notes"] == "Please check my electives"


def test_submit_plan_goes_to_pending_review(client, auth, course_ids):  # IT24
    bob = auth("bob")
    add_course(client, bob, course_ids["COMP1002"])
    response = submit_plan(client, bob, notes="Ready")
    assert response.status_code == 200
    assert response.json()["status"] == "Pending Review"

    plan = get_plan(client, bob).json()
    assert plan["status"] == "Pending Review"
    assert plan["advisor_id"] is not None
    assert plan["submitted_at"] is not None
    assert plan["notes"] == "Ready"


def test_submit_empty_plan_is_409(client, auth):  # IT25
    bob = auth("bob")
    get_plan(client, bob)  # creates the empty draft
    response = submit_plan(client, bob)
    assert response.status_code == 409
    assert "at least one course" in response.json()["detail"]


def test_submit_without_advisor_is_409(client, auth, course_ids):  # IT26
    alice = auth("alice")
    add_course(client, alice, course_ids["COMP1002"])
    response = submit_plan(client, alice)
    assert response.status_code == 409
    assert "advisor must be assigned" in response.json()["detail"]


def test_submitted_plan_is_locked(client, auth, course_ids):  # IT27
    bob = auth("bob")
    plan_course_id = add_course(client, bob, course_ids["COMP1002"]).json()["plan_course_id"]
    assert submit_plan(client, bob).status_code == 200

    assert add_course(client, bob, course_ids["WRIT1001"]).status_code == 409
    assert client.delete(f"/api/me/plan/courses/{plan_course_id}", headers=bob).status_code == 409
    notes = client.patch("/api/me/plan", headers=bob, json={"academic_term": TERM, "notes": "x"})
    assert notes.status_code == 409
    assert submit_plan(client, bob).status_code == 409


def test_submitted_plan_appears_in_advisor_queue(client, auth, submitted_plan_id):  # IT28
    response = client.get("/api/advisor/plans", headers=auth("advisor"))
    assert response.status_code == 200
    queue = response.json()
    assert len(queue) == 1
    assert queue[0]["plan_id"] == submitted_plan_id
    assert queue[0]["student_name"] == "John Doe"
    assert queue[0]["status"] == "Pending Review"
