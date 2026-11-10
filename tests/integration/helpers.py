"""Small request helpers shared by the integration tests."""
TERM = "2026/27"


def add_course(client, headers, course_id, placement="Year 1 - Semester 1"):
    return client.post(
        "/api/me/plan/courses",
        headers=headers,
        json={"course_id": course_id, "academic_term": TERM,
              "placement": placement, "plan_length": 3},
    )


def submit_plan(client, headers, notes="Ready for review"):
    return client.post(
        "/api/me/plan/submission",
        headers=headers,
        json={"academic_term": TERM, "notes": notes},
    )


def get_plan(client, headers):
    return client.get("/api/me/plan", headers=headers, params={"academic_term": TERM})
