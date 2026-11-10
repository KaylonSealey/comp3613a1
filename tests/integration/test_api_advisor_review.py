"""Integration tests: Workflow 3 — Review and Approve Course Selection Plan (IT29–IT36)."""
import pytest

from helpers import add_course, get_plan, submit_plan

pytestmark = pytest.mark.integration


def decide(client, headers, plan_id, decision, notes=""):
    return client.post(f"/api/advisor/plans/{plan_id}/decision", headers=headers,
                       json={"decision": decision, "notes": notes})


def test_queue_empty_when_nothing_submitted(client, auth):  # IT29
    response = client.get("/api/advisor/plans", headers=auth("advisor"))
    assert response.status_code == 200
    assert response.json() == []


def test_review_detail_has_plan_student_and_audit(client, auth, submitted_plan_id):  # IT30
    response = client.get(f"/api/advisor/plans/{submitted_plan_id}", headers=auth("advisor"))
    assert response.status_code == 200
    body = response.json()
    assert [c["course"]["code"] for c in body["plan"]["courses"]] == ["COMP1002"]
    assert body["plan"]["status"] == "Pending Review"
    assert body["student"]["student_id"] == "1002450678"
    assert body["student"]["name"] == "John Doe"
    assert body["audit"]["total_completed_credits"] == 6


def test_other_advisor_cannot_see_plan(client, auth, submitted_plan_id):  # IT31
    advisor2 = auth("advisor2")
    assert client.get(f"/api/advisor/plans/{submitted_plan_id}", headers=advisor2).status_code == 404
    assert decide(client, advisor2, submitted_plan_id, "approve").status_code == 404


def test_approve_plan(client, auth, submitted_plan_id):  # IT32
    advisor = auth("advisor")
    response = decide(client, advisor, submitted_plan_id, "approve")
    assert response.status_code == 200
    assert response.json()["status"] == "Approved"

    plan = get_plan(client, auth("bob")).json()
    assert plan["status"] == "Approved"
    assert plan["approved_at"] is not None
    assert client.get("/api/advisor/plans", headers=advisor).json() == []


def test_request_revisions_requires_notes(client, auth, submitted_plan_id):  # IT33
    response = decide(client, auth("advisor"), submitted_plan_id, "request_revisions", "   ")
    assert response.status_code == 409
    assert "notes are required" in response.json()["detail"]


def test_revision_cycle(client, auth, course_ids, submitted_plan_id):  # IT34
    advisor, bob = auth("advisor"), auth("bob")

    revision = decide(client, advisor, submitted_plan_id, "request_revisions", "Please add WRIT1001.")
    assert revision.json()["status"] == "Revision Requested"
    plan = get_plan(client, bob).json()
    assert plan["status"] == "Revision Requested"
    assert plan["advisor_notes"] == "Please add WRIT1001."

    assert add_course(client, bob, course_ids["WRIT1001"]).status_code == 201
    assert submit_plan(client, bob, notes="Added WRIT1001").json()["status"] == "Pending Review"

    assert decide(client, advisor, submitted_plan_id, "approve").json()["status"] == "Approved"
    plan = get_plan(client, bob).json()
    assert plan["status"] == "Approved"
    assert plan["notes"] == "Added WRIT1001"
    assert {c["course"]["code"] for c in plan["courses"]} == {"COMP1002", "WRIT1001"}


def test_cannot_decide_twice(client, auth, submitted_plan_id):  # IT35
    advisor = auth("advisor")
    assert decide(client, advisor, submitted_plan_id, "approve").status_code == 200
    assert decide(client, advisor, submitted_plan_id, "approve").status_code == 409


def test_unknown_decision_is_409(client, auth, submitted_plan_id):  # IT36
    response = decide(client, auth("advisor"), submitted_plan_id, "reject", "No")
    assert response.status_code == 409
