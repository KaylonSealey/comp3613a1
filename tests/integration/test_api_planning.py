"""Integration tests: Workflow 1 — Track Degree Audit & Plan Semester Courses (IT11–IT22)."""
import pytest

from helpers import add_course, get_plan

pytestmark = pytest.mark.integration


def test_audit_shows_completed_credits(client, auth):  # IT11
    response = client.get("/api/me/audit", headers=auth("bob"))
    assert response.status_code == 200
    audit = response.json()
    assert audit["total_completed_credits"] == 6
    assert audit["total_required_credits"] == 21
    assert audit["progress_percent"] == 29
    core = next(c for c in audit["categories"] if c["name"] == "Core")
    completed = {course["code"]: course["completed"] for course in core["courses"]}
    assert completed == {"COMP1001": True, "COMP1002": False}


def test_catalog_search_by_text(client, auth):  # IT12
    response = client.get("/api/courses", headers=auth("bob"), params={"query": "algo"})
    assert response.status_code == 200
    assert [c["code"] for c in response.json()] == ["COMP2001"]


def test_catalog_filter_by_faculty(client, auth):  # IT13
    response = client.get("/api/courses", headers=auth("bob"), params={"faculty": "Mathematics"})
    assert response.status_code == 200
    assert [c["code"] for c in response.json()] == ["MATH1001"]


def test_catalog_requires_login(client):  # IT14
    assert client.get("/api/courses").status_code == 401


def test_get_plan_returns_empty_draft(client, auth):  # IT15
    response = get_plan(client, auth("bob"))
    assert response.status_code == 200
    plan = response.json()
    assert plan["status"] == "Draft"
    assert plan["total_credits"] == 0
    assert plan["courses"] == []


def test_add_course_appears_in_plan(client, auth, course_ids):  # IT16
    bob = auth("bob")
    response = add_course(client, bob, course_ids["COMP1002"])
    assert response.status_code == 201
    assert response.json()["course"]["code"] == "COMP1002"

    plan = get_plan(client, bob).json()
    assert plan["total_credits"] == 3
    assert [(c["course"]["code"], c["placement"]) for c in plan["courses"]] == [
        ("COMP1002", "Year 1 - Semester 1")
    ]


def test_duplicate_course_is_409(client, auth, course_ids):  # IT17
    bob = auth("bob")
    assert add_course(client, bob, course_ids["COMP1002"]).status_code == 201
    response = add_course(client, bob, course_ids["COMP1002"], "Year 1 - Semester 2")
    assert response.status_code == 409
    assert response.json()["detail"] == "That course is already in this plan."


def test_unknown_course_is_404(client, auth):  # IT18
    assert add_course(client, auth("bob"), 999).status_code == 404


def test_invalid_placement_is_409(client, auth, course_ids):  # IT19
    response = add_course(client, auth("bob"), course_ids["COMP1002"], "Year 9 - Semester 1")
    assert response.status_code == 409


def test_sixteen_credit_limit_is_409(client, auth, course_ids):  # IT20
    bob = auth("bob")
    for code in ["COMP1001", "COMP1002", "COMP2001", "COMP2002", "MATH1001"]:
        assert add_course(client, bob, course_ids[code], "Year 2 - Semester 1").status_code == 201
    sixth = add_course(client, bob, course_ids["SCI1001"], "Year 2 - Semester 1")
    assert sixth.status_code == 409
    assert "16 credits" in sixth.json()["detail"]
    assert get_plan(client, bob).json()["total_credits"] == 15


def test_remove_course_then_404(client, auth, course_ids):  # IT21
    bob = auth("bob")
    plan_course_id = add_course(client, bob, course_ids["COMP1002"]).json()["plan_course_id"]
    url = f"/api/me/plan/courses/{plan_course_id}"
    assert client.delete(url, headers=bob).status_code == 204
    assert get_plan(client, bob).json()["courses"] == []
    assert client.delete(url, headers=bob).status_code == 404


def test_students_have_separate_plans(client, auth, course_ids):  # IT22
    assert add_course(client, auth("bob"), course_ids["COMP1002"]).status_code == 201
    alice_plan = get_plan(client, auth("alice")).json()
    assert alice_plan["courses"] == []
