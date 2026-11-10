"""Integration tests: server-rendered web pages and forms (IT37–IT39)."""
import pytest

from helpers import TERM

pytestmark = pytest.mark.integration


def web_login(client, username, password):
    return client.post("/login", data={"username": username, "password": password},
                       follow_redirects=False)


@pytest.mark.parametrize(
    "username, password, destination",
    [("bob", "bobpass", "/app"), ("advisor", "advisorpass", "/advisor"),
     ("admin", "adminpass", "/admin")],
)
def test_login_redirects_each_role(make_client, username, password, destination):  # IT37
    response = web_login(make_client(), username, password)
    assert response.status_code == 303
    assert response.headers["location"].endswith(destination)


def test_student_cannot_open_advisor_portal(client):  # IT38
    web_login(client, "bob", "bobpass")
    assert client.get("/app").status_code == 200
    assert client.get("/advisor").status_code == 403


def test_full_workflow_through_web_forms(make_client, course_ids):  # IT39
    student, advisor = make_client(), make_client()
    web_login(student, "bob", "bobpass")
    web_login(advisor, "advisor", "advisorpass")

    added = student.post("/app/plans/courses", json={
        "course_id": course_ids["COMP1002"], "academic_term": TERM,
        "placement": "Year 1 - Semester 1", "plan_length": 3,
    })
    assert added.status_code == 200

    submitted = student.post("/app/submit", data={"academic_term": TERM, "notes": "Ready"},
                             follow_redirects=False)
    assert submitted.status_code == 303

    queue_page = advisor.get("/advisor")
    assert queue_page.status_code == 200
    assert "John" in queue_page.text

    plan_id = advisor.get("/api/advisor/plans").json()[0]["plan_id"]
    assert advisor.get(f"/advisor/plans/{plan_id}").status_code == 200
    decision = advisor.post(f"/advisor/plans/{plan_id}/decision",
                            data={"decision": "approve", "notes": ""}, follow_redirects=False)
    assert decision.status_code == 303

    summary = student.get("/app/submit", params={"academic_term": TERM})
    assert summary.status_code == 200
    assert "Approved" in summary.text
