# MyAdvisor — Test Plans (COMP 3613 Assignment 2)

Three levels of testing are planned:

| Level | What is tested | Tool | Location |
|---|---|---|---|
| Unit | One service / utility at a time, with its repository replaced by a `MagicMock` | pytest | `tests/unit/` |
| Integration | Full HTTP request → router → auth → service → repository → database | pytest + FastAPI `TestClient` (fresh in-memory SQLite per test) | `tests/integration/` |
| API | Every REST endpoint against the running app | Postman (test scripts) | `postman/` |
| User Acceptance | The three workflows performed by a user on the web UI, following wireframes W1–W3 | Manual | this document |

---

## 1. User Acceptance Test Plan

**Set-up:** run `python manage.py init` (resets and seeds the database), then `python manage.py run`, and open http://127.0.0.1:5000. Run the cases in order — later cases use the plan built in earlier ones.

| Role | Username | Password |
|---|---|---|
| Student (John Doe, ID 1002450678) | `bob` | `bobpass` |
| Advisor (Demo Advisor) | `advisor` | `advisorpass` |
| Admin | `admin` | `adminpass` |

**Wireframes:** W1 = Degree Audit & Plan Semester Courses, W2 = Submit Course Selection Plan for Approval, W3 = Review and Approve Course Selection Plan.

| Test Case | Pre-conditions | Test Steps | Test Criteria | Pass | Fail |
|---|---|---|---|:-:|:-:|
| **1.1 Student login** | Not logged in | ☐ Open the landing page and click Sign in<br>☐ Enter `bob` / `bobpass`<br>☐ Press Login | ☐ The Degree Audit & Course Planner page (W1) opens<br>☐ "Welcome, bob" and "John Doe · 2026/27" are shown<br>☐ Logout appears in the navigation | | |
| **1.2 Invalid login** | Not logged in | ☐ Enter `bob` and a wrong password<br>☐ Press Login | ☐ The user stays on the login page<br>☐ "Incorrect username or password" is displayed | | |
| **1.3 Register a new student** | Not logged in | ☐ Open Register<br>☐ Fill username, email, password, student ID, first and last name, choose *Bachelor of Science in Computer Science*<br>☐ Submit, then log in with the new account | ☐ "Registration completed! Sign in now!" is shown<br>☐ The new student reaches the planner with an empty plan | | |
| **1.4 View degree audit (W1)** | Logged in as `bob` | ☐ Look at the Degree Audit Checklist | ☐ Categories Core, Major, Math, Science, Technical Writing, Free Electives are listed with completed/required credits<br>☐ COMP1001, COMP2001, MATH1001, SCI1001, ELEC1001 are ticked<br>☐ Total progress shows **15/27 credits · 56%** | | |
| **1.5 Search course catalog (W1)** | Logged in as `bob` | ☐ In Search Course Catalog type `data` and search<br>☐ Clear the text, choose faculty *Mathematics* and search | ☐ "1 course(s) found." with COMP1002 Data Fundamentals<br>☐ Faculty filter shows only MATH1001<br>☐ Add to plan stays disabled until a planner slot is selected | | |
| **1.6 Switch plan view (W1)** | Logged in as `bob` | ☐ Change the year-plan view to 1 year, then 2, then 3 | ☐ The planner shows 1, 2 and 3 year rows respectively, each with Semester 1, Semester 2 and Summer | | |
| **1.7 Add course to planner (W1)** | Logged in as `bob`; plan is Draft | ☐ Select the Year 1 – Semester 1 slot<br>☐ Search `COMP1002`<br>☐ Press Add to plan | ☐ COMP1002 appears in Year 1 – Semester 1<br>☐ The slot's total shows 3 credits | | |
| **1.8 Duplicate course blocked** | 1.7 done | ☐ Select Year 1 – Semester 2<br>☐ Add `COMP1002` again | ☐ The course is not added a second time<br>☐ "That course is already in this plan." is displayed | | |
| **1.9 16-credit limit** | Logged in as `bob`; plan is Draft | ☐ Add five more 3-credit courses to Year 2 – Semester 1 (15 credits)<br>☐ Try to add a sixth | ☐ The first five are added<br>☐ The sixth is refused with "A semester cannot exceed 16 credits." | | |
| **1.10 Remove course (W1)** | 1.9 done | ☐ Press Remove on each course in Year 2 – Semester 1 | ☐ The courses disappear from the slot<br>☐ COMP1002 is still in Year 1 – Semester 1 | | |
| **1.11 Save draft comments (W2)** | Plan contains COMP1002 | ☐ Press Proceed to Next Step<br>☐ Type a comment in Comments for Advisor<br>☐ Press Save Draft, then reload the page | ☐ Plan Summary lists COMP1002 with total credits 3<br>☐ "Your plan comments have been saved." is displayed<br>☐ The comment is still there after reloading | | |
| **1.12 Submit plan for approval (W2)** | 1.11 done | ☐ Press Submit for Approval | ☐ "Your plan is pending review and awaiting advisor review." is displayed<br>☐ Status shows Pending Review | | |
| **1.13 Plan locked after submission** | 1.12 done | ☐ Return to the planner<br>☐ Try to add WRIT1001 to any slot | ☐ The course is not added<br>☐ "Only draft or revision-requested plans can be changed." is displayed | | |
| **1.14 Advisor review queue (W3)** | Logged in as `advisor`; 1.12 done | ☐ Log in as the advisor | ☐ Assigned Plan Reviews lists John Doe's 2026/27 plan as Pending Review | | |
| **1.15 Review plan details (W3)** | 1.14 done | ☐ Open John Doe's plan | ☐ Student profile shows John Doe, ID 1002450678, the degree program<br>☐ Proposed plan lists COMP1002 and total credits<br>☐ Degree audit verification shows each category's status | | |
| **1.16 Revision needs notes (W3)** | Review page open | ☐ Choose Request Revisions<br>☐ Leave Advising Notes empty<br>☐ Press Submit Decision | ☐ The form is not submitted<br>☐ The browser asks for the Advising Notes field to be filled | | |
| **1.17 Request revisions (W3)** | Review page open | ☐ Choose Request Revisions<br>☐ Type "Please add WRIT1001 to Year 1 – Semester 1."<br>☐ Press Submit Decision | ☐ "The plan decision was recorded: Revision Requested." is displayed<br>☐ The plan leaves the pending queue | | |
| **1.18 Revise and resubmit** | Logged in as `bob`; 1.17 done | ☐ Open the submit page and read the advisor's note<br>☐ Add WRIT1001 to Year 1 – Semester 1<br>☐ Submit for Approval again | ☐ Status Revision Requested and the advisor's note are shown<br>☐ WRIT1001 is added<br>☐ Status returns to Pending Review | | |
| **1.19 Approve plan (W3)** | Logged in as `advisor`; 1.18 done | ☐ Open the plan<br>☐ Choose Approve Plan, press Submit Decision<br>☐ Log in as `bob` and open the submit page | ☐ "The plan decision was recorded: Approved." is displayed<br>☐ The student sees status Approved | | |
| **1.20 Role restriction** | Logged in as `bob` | ☐ Type `/advisor` in the address bar | ☐ The advisor portal does not open; an "advisor profile is required" message is shown | | |
| **1.21 Logout** | Logged in | ☐ Press Logout<br>☐ Try to open `/app` | ☐ The login page is shown<br>☐ `/app` shows the unauthorized page | | |

---

## 2. Unit Test Plan

Each test isolates **one module**: the service is constructed with a `MagicMock` repository, so no database, HTTP or other service is involved. Run with `python manage.py test unit`.

### `tests/unit/test_plan_service.py` — `PlanService`

| ID | Unit Test | Input | Expected Output |
|---|---|---|---|
| UT01 | `test_add_course_saves_valid_course` | course 1, "2026/27", "Year 1 - Semester 1", plan length 3; Draft plan, 0 credits in slot | `repo.add_course(plan_id, 1, "Year 1 - Semester 1")` called |
| UT02 | `test_add_course_trims_term_and_placement` | " 2026/27 ", " Year 2 - Summer " | saved with "Year 2 - Summer" |
| UT03 | `test_add_course_rejects_unsupported_academic_year` | "2030/31" | `ValueError` "supported academic year"; nothing saved |
| UT04 | `test_add_course_rejects_invalid_plan_length` | plan length 0 and 4 | `ValueError` "plan length" |
| UT05 | `test_add_course_rejects_invalid_placement` | "", "Year 1", "Year 1 - Fall", "Semester 1 - Year 1" | `ValueError`; nothing saved |
| UT06 | `test_add_course_rejects_year_beyond_plan_length` | "Year 2 - Semester 1" with plan length 1 | `ValueError` "valid year and term" |
| UT07 | `test_add_course_rejects_unknown_course` | `repo.get_course` returns None | `LookupError` |
| UT08 | `test_add_course_rejects_more_than_16_credits` | 15 credits in slot + 3-credit course | `ValueError` "16 credits"; nothing saved |
| UT09 | `test_add_course_allows_exactly_16_credits` | 13 credits in slot + 3-credit course | course saved |
| UT10 | `test_add_course_rejects_locked_plan` | plan status "Pending Review" and "Approved" | `ValueError` "Only draft" |
| UT11 | `test_add_course_allowed_after_revision_requested` | plan status "Revision Requested" | course saved |
| UT12 | `test_remove_course_from_draft` | Draft plan, plan course 5 | returns True; `repo.remove_course(plan_id, 5)` called |
| UT13 | `test_remove_course_without_plan_returns_false` | `repo.get_plan` returns None | returns False |
| UT14 | `test_remove_course_rejects_locked_plan` | plan status "Approved" | `ValueError`; nothing removed |
| UT15 | `test_save_draft_notes_trims_text` | "  Check my electives  " | `repo.save_notes(plan, "Check my electives")` |
| UT16 | `test_save_draft_notes_blank_saved_as_none` | "   " | `repo.save_notes(plan, None)` |
| UT17 | `test_save_draft_notes_rejects_locked_plan` | plan status "Pending Review" | `ValueError` |
| UT18 | `test_submit_plan_marks_pending_review` | notes " Ready ", advisor 3, plan with 1 course | `mark_submitted` called with advisor 3, notes "Ready", a `submitted_at`; returns "Pending Review" |
| UT19 | `test_submit_plan_without_plan_raises_lookup_error` | `repo.get_plan` returns None | `LookupError` |
| UT20 | `test_submit_plan_requires_assigned_advisor` | advisor None | `ValueError` "advisor must be assigned" |
| UT21 | `test_submit_plan_rejects_empty_plan` | plan with no courses | `ValueError` "at least one course" |
| UT22 | `test_submit_plan_rejects_already_submitted_plan` | status "Pending Review" and "Approved" | `ValueError` "Only draft" |
| UT23 | `test_submission_details_total_credits` | courses of 3 and 4 credits | total credits 7 |

### `tests/unit/test_advisor_service.py` — `AdvisorService`

| ID | Unit Test | Input | Expected Output |
|---|---|---|---|
| UT24 | `test_approve_sets_status_approved` | decision "approve", Pending Review plan | `save_decision(status="Approved")`; returns "Approved" |
| UT25 | `test_request_revisions_saves_notes` | "request_revisions", " Add WRIT1001 " | status "Revision Requested", notes "Add WRIT1001" |
| UT26 | `test_request_revisions_requires_notes` | "request_revisions" with "" and "   " | `ValueError` "notes are required"; nothing saved |
| UT27 | `test_unknown_decision_is_rejected` | decision "reject" | `ValueError`; nothing saved |
| UT28 | `test_only_pending_plans_can_be_decided` | status "Draft", "Approved", "Revision Requested" | `ValueError` "pending review" |
| UT29 | `test_unassigned_plan_raises_lookup_error` | `repo.get_assigned_plan` returns None | `LookupError` "not assigned" |
| UT30 | `test_get_assigned_plans_returns_repo_result` | advisor 2 | repository list returned unchanged |

### `tests/unit/test_audit_and_catalog.py` — `AuditService`, `CourseService`

| ID | Unit Test | Input | Expected Output |
|---|---|---|---|
| UT31 | `test_audit_groups_requirements_by_category` | 2 Core + 1 Math requirement | categories ["Core", "Math"]; Core requires 6 credits |
| UT32 | `test_audit_counts_completed_credits_and_percent` | 9 required credits, 2 of 3 courses completed | 6 completed, 67 % |
| UT33 | `test_audit_with_no_requirements_is_zero` | no requirements | 0 %, no categories |
| UT34 | `test_search_trims_query` | " comp ", faculty "Computing" | `repo.search_catalog("comp", "Computing")` |
| UT35 | `test_search_with_no_query_uses_empty_string` | None | `repo.search_catalog("", None)` |

### `tests/unit/test_auth_and_security.py` — `security` utilities, `AuthService`

| ID | Unit Test | Input | Expected Output |
|---|---|---|---|
| UT36 | `test_password_is_hashed_and_verified` | "mypassword" | hash ≠ password; verify True for correct, False for wrong |
| UT37 | `test_access_token_contains_user_id_and_role` | {"sub": "4", "role": "advisor"} | decoded sub "4", role "advisor", `exp` present |
| UT38 | `test_expired_token_is_rejected` | token that expired 5 s ago | `ExpiredSignatureError` |
| UT39 | `test_authenticate_valid_credentials_returns_token` | bob / correct password (mocked user) | token whose sub is bob's id |
| UT40 | `test_authenticate_wrong_password_returns_none` | bob / wrong password | None |
| UT41 | `test_authenticate_unknown_user_returns_none` | "ghost" | None |
| UT42 | `test_register_hashes_password_and_trims_names` | " 816 ", " Amy ", " Ng ", "secret1" | repository receives hashed password, "816", "Amy", "Ng" |
| UT43 | `test_register_requires_student_details` | blank student ID / first / last name | `ValueError` "required"; nothing saved |

---

## 3. Integration Test Plan

Each test sends real HTTP requests through the FastAPI app with `TestClient`. The database session is overridden with a **fresh in-memory SQLite database** for every test, seeded with:

- Degree program BSC-CS; courses COMP1001, COMP1002, COMP2001, COMP2002, MATH1001, SCI1001, WRIT1001 (3 credits each, all required)
- `bob` — student John Doe, assigned to `advisor`, completed COMP1001 and MATH1001 (6/21 credits, 29 %)
- `alice` — student with **no** advisor
- `advisor`, `advisor2` (no students), `admin`

Run with `python manage.py test integration`.

### `tests/integration/test_api_auth.py` — authentication & authorization

| ID | Test | Components | Description / Expected |
|---|---|---|---|
| IT01 | `test_login_returns_bearer_token` | `POST /api/auth/login`, `AuthService` | 200, `access_token`, `token_type` "bearer", role "regular_user" |
| IT02 | `test_login_wrong_password_is_401` | `POST /api/auth/login` | 401 JSON "Incorrect username or password" |
| IT03 | `test_login_missing_password_is_422` | request validation | 422 |
| IT04 | `test_me_returns_current_user` | `GET /api/auth/me`, `get_current_user` | 200, username "bob", no password field |
| IT05 | `test_no_token_returns_json_401` | 401 handler in `main.py` | 401 with JSON body (not the HTML page) |
| IT06 | `test_invalid_token_is_401` | `get_current_user` | 401 |
| IT07 | `test_web_login_cookie_works_for_api` | `POST /login` → cookie → `GET /api/auth/me` | 200 |
| IT08 | `test_student_cannot_use_advisor_endpoints` | `require_role("advisor")` | bob → `GET /api/advisor/plans` 403 |
| IT09 | `test_advisor_cannot_use_student_endpoints` | `require_role("regular_user")` | advisor → `GET /api/me/plan` 403 |
| IT10 | `test_user_list_is_admin_only` | `GET /api/users`, `require_role("admin")` | student 403; admin 200 with every user and no passwords |

### `tests/integration/test_api_planning.py` — Workflow 1: Track Degree Audit & Plan Semester Courses

| ID | Test | Components | Description / Expected |
|---|---|---|---|
| IT11 | `test_audit_shows_completed_credits` | `GET /api/me/audit`, `AuditService`, `AuditRepository` | 6 / 21 credits, 29 %; COMP1001 completed |
| IT12 | `test_catalog_search_by_text` | `GET /api/courses?query=algo`, `CourseService`, `CourseRepository` | only COMP2001 |
| IT13 | `test_catalog_filter_by_faculty` | `GET /api/courses?faculty=Mathematics` | only MATH1001 |
| IT14 | `test_catalog_requires_login` | `GET /api/courses` without token | 401 |
| IT15 | `test_get_plan_returns_empty_draft` | `GET /api/me/plan`, `PlanService.get_plan_courses` | 200, status Draft, 0 credits, no courses |
| IT16 | `test_add_course_appears_in_plan` | `POST /api/me/plan/courses`, `PlanService.add_course`, `PlanRepository` | 201; then `GET /api/me/plan` lists COMP1002 in Year 1 - Semester 1 |
| IT17 | `test_duplicate_course_is_409` | `PlanRepository.add_course` | same course in another slot → 409 |
| IT18 | `test_unknown_course_is_404` | `PlanService.add_course` | course id 999 → 404 |
| IT19 | `test_invalid_placement_is_409` | `PlanService.add_course` | "Year 9 - Semester 1" → 409 |
| IT20 | `test_sixteen_credit_limit_is_409` | `PlanService.add_course`, `credits_in_placement` | 5 courses in one slot ok, 6th → 409 |
| IT21 | `test_remove_course_then_404` | `DELETE /api/me/plan/courses/{id}` | 204, then 404 on second delete |
| IT22 | `test_students_have_separate_plans` | `GET /api/me/plan` as bob and alice | alice's plan does not contain bob's course |

### `tests/integration/test_api_submission.py` — Workflow 2: Submit Course Selection Plan for Approval

| ID | Test | Components | Description / Expected |
|---|---|---|---|
| IT23 | `test_save_draft_comments` | `PATCH /api/me/plan`, `save_draft_notes` | 200 status Draft; plan notes saved |
| IT24 | `test_submit_plan_goes_to_pending_review` | `POST /api/me/plan/submission`, `submit_plan`, `mark_submitted` | 200 "Pending Review"; plan has advisor and `submitted_at` |
| IT25 | `test_submit_empty_plan_is_409` | `submit_plan` | 409 |
| IT26 | `test_submit_without_advisor_is_409` | alice submits | 409 "advisor must be assigned" |
| IT27 | `test_submitted_plan_is_locked` | add / remove / notes / resubmit after submit | all 409 |
| IT28 | `test_submitted_plan_appears_in_advisor_queue` | `GET /api/advisor/plans` | queue lists John Doe's plan |

### `tests/integration/test_api_advisor_review.py` — Workflow 3: Review and Approve Course Selection Plan

| ID | Test | Components | Description / Expected |
|---|---|---|---|
| IT29 | `test_queue_empty_when_nothing_submitted` | `GET /api/advisor/plans` | 200, [] |
| IT30 | `test_review_detail_has_plan_student_and_audit` | `GET /api/advisor/plans/{id}`, `AdvisorService`, `AuditService` | plan courses, student ID, audit totals |
| IT31 | `test_other_advisor_cannot_see_plan` | advisor2 → `GET /api/advisor/plans/{id}` | 404 |
| IT32 | `test_approve_plan` | `POST /api/advisor/plans/{id}/decision`, `save_decision` | 200 "Approved"; student's plan shows Approved and leaves queue |
| IT33 | `test_request_revisions_requires_notes` | `submit_decision` | 409 |
| IT34 | `test_revision_cycle` | decision → add course → resubmit → approve | final status Approved, student notes kept, advisor notes saved |
| IT35 | `test_cannot_decide_twice` | second decision on approved plan | 409 |
| IT36 | `test_unknown_decision_is_409` | decision "reject" | 409 |

### `tests/integration/test_web_pages.py` — server-rendered pages

| ID | Test | Components | Description / Expected |
|---|---|---|---|
| IT37 | `test_login_redirects_each_role` | `POST /login` | bob → /app, advisor → /advisor, admin → /admin |
| IT38 | `test_student_cannot_open_advisor_portal` | `GET /advisor` | 403 |
| IT39 | `test_full_workflow_through_web_forms` | `POST /app/plans/courses`, `POST /app/submit`, `POST /advisor/plans/{id}/decision` | plan ends Approved |
