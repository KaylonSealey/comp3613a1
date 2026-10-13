<!-- student-build:skill-integrity
status: pass
root: e84cd692d0b85eefe546385661958c27d07e8be6c5176a82012f68ccff5c8beb
expected_root: e84cd692d0b85eefe546385661958c27d07e8be6c5176a82012f68ccff5c8beb
mismatches: none
-->

# COMP 3613 Assignment 1

Draft this file with the Guide. **Update it after every phase milestone** before you pause. The use-case diagram is a UML PNG at `docs/diagrams/use-case.png`, linked from this file as `diagrams/use-case.png` (path relative to `docs/report.md`). The model diagram is Mermaid. **Embed wireframe images** as `wireframes/<file>` (files live in `docs/wireframes/`).

Do not put your student ID in this file if you will commit it. The PDF cover adds your name and ID at export time.

## Assigned project

MyAdvisor

## Three workflows

### 1. Track Degree Audit & Plan Semester Courses (Student)

### 2. Submit Course Selection Plan for Approval (Student)

### 3. Review and Approve Course Selection Plan (Advisor)

## Use case diagram

![Use case diagram](diagrams/use-case.png)

Assumed use-case structure: Student’s course-planning and submission flows include draft-save and rule validation, while advisor review includes progress-history lookup. Shared base actions are View Degree Audit and View Course Catalog. The review flow optionally extends with advising notes and revision requests.

## Model diagram

First draft. Update this section in Phase 5 when polish revises the model, and note what changed.

```mermaid
erDiagram
  USER ||--o| STUDENT : profile_for
  USER ||--o| ADVISOR : profile_for
  STUDENT ||--o{ PLAN : creates
  STUDENT }o--|| DEGREE_PROGRAM : follows
  STUDENT }o--o| ADVISOR : assigned_to
  ADVISOR o|--o{ PLAN : reviews
  DEGREE_PROGRAM ||--o{ DEGREE_REQUIREMENT : requires
  COURSE ||--o{ DEGREE_REQUIREMENT : satisfies
  PLAN ||--o{ PLAN_COURSE : contains
  COURSE ||--o{ PLAN_COURSE : appears_in
  STUDENT ||--o{ COMPLETED_COURSE : completes
  COURSE ||--o{ COMPLETED_COURSE : records

  STUDENT {
    int id PK
    string student_id
    string first_name
    string last_name
    string email
    int degree_program_id FK
    int user_id FK UK
    int advisor_id FK
  }

  USER {
    int id PK
    string username
    string email
    string role
  }

  ADVISOR {
    int id PK
    int user_id FK UK
    string first_name
    string last_name
    string email
    string department
  }

  DEGREE_PROGRAM {
    int id PK
    string name
    string code
    int required_credits
    string catalog_year
  }

  DEGREE_REQUIREMENT {
    int id PK
    int degree_program_id FK
    int course_id FK
    string requirement_type
    int credits
  }

  COURSE {
    int id PK
    string code
    string title
    string faculty
    int credits
    string level
    string description
  }

  PLAN {
    int id PK
    int student_id FK
    int advisor_id FK
    string academic_term
    string status
    datetime created_at
    datetime submitted_at
    datetime approved_at
    text notes
    text advisor_notes
  }

  PLAN_COURSE {
    int id PK
    int plan_id FK
    int course_id FK
    string placement
    string status
    string notes
  }

  COMPLETED_COURSE {
    int id PK
    int student_id FK
    int course_id FK
    string grade
    string term_completed
    bool transferred
  }
```

Assumed relationships and business rules:

- A student profile belongs to exactly one login account; a login account has at most one student profile. Student registration captures the profile fields.
- A student follows one degree program and may be assigned to an advisor; both advisor assignments are optional until configured.
- A student may create one plan per academic term. A plan is reviewed by at most one advisor, while an advisor may review many plans.
- Degree requirements are a join between degree programs and courses, so one course can satisfy multiple program requirements without duplicating the requirement record itself.
- A plan contains many planned courses through a bridge table, which keeps the same course reusable across multiple plans and allows per-course notes/status.
- A course code is unique, and a course may be searched by its faculty as shown in the wireframe.
- Completed coursework is tracked separately from planned courses so the student can audit progress without mixing draft plans with final records.
- A course can appear only once in a given plan. Course placement stores the selected year and term.
- The workflow assumes a draft plan can later be submitted and approved, with one plan per term.

## Wireframes

### Degree Audit & Plan Semester Courses

![Degree Audit & Plan Semester Courses](wireframes/degree_audit_planning.png)

<!-- student-build:wireframe-coverage
use_case: Track Degree Audit & Plan Semester Courses
image: docs/wireframes/degree_audit_planning.png
covered: yes
-->

### Submit Course Selection Plan for Approval

![Submit Course Selection Plan for Approval](wireframes/submit_plan.png)

<!-- student-build:wireframe-coverage
use_case: Submit Course Selection Plan for Approval
image: docs/wireframes/submit_plan.png
covered: yes
-->

### Review and Approve Course Selection Plan

![Review and Approve Course Selection Plan](wireframes/advisor_review.png)

<!-- student-build:wireframe-coverage
use_case: Review and Approve Course Selection Plan
image: docs/wireframes/advisor_review.png
covered: yes
-->

### Phase 4 model revision notes

- PLAN.status — seen on the submission and advisor-review screens for Draft, Pending Review, Approved, and Revision Requested states.
- PLAN.notes — optional student comments submitted with a plan.
- PLAN.advisor_notes — separate advisor feedback so revision requests do not overwrite the student's comments.
- PLAN.submitted_at / PLAN.approved_at — seen on the submission detail and advisor decision summary.
- PLAN_COURSE.status and placement — already supported by the draft model; the wireframes reinforce that a course entry needs a per-plan placement and a review state.
- DEGREE_REQUIREMENT.requirement_type / credits — reinforced by the checklist categories and progress totals.
- COURSE.faculty — added because the catalog wireframe offers faculty filtering.
- STUDENT.user_id — added after the student selected a one-to-one link between a profile and the existing login account.
- STUDENT.advisor_id and PLAN.advisor_id — optional while advisor assignment/review is not yet implemented.

These revisions are reflected in the Phase 5 schema below.

## Theming

Branding preferences applied:

- Aesthetic: Modern academic dashboard with a Deep Oxford Blue and soft slate palette; existing typography is retained.
- Palette: page background (#F3F5F9), sidebar and landing hero panel (#1A4B9C), white cards and inputs (#FFFFFF), soft borders (#E2E8F0), and royal-blue primary controls (#1A4B9C; hover #133E87).
- Status colors: Approved (#DCFCE7 / #15803D), Pending Review (#FEF3C7 / #B45309), and Revision Requested (#FEE2E2 / #B91C1C).
- UI details: 12px rounded cards, soft shadows, horizontally scrollable semester columns with 170px minimum widths, and interactive course chips with hover lift.
- The landing page, login screen, register screen, and authenticated app shell were restyled to match the MyAdvisor brand and maintain the same design system across workflows.

## Implementation notes

Phase 5 progress:

1. Track Degree Audit & Plan Semester Courses
   - Added SQLModel tables for the ERD entities, course faculty search, unique course codes, a one-to-one Student/User profile link, degree requirement and completion records, and per-term plans with planned courses.
   - Student registration now collects the Student profile and degree program, then saves the account and profile together.
   - `python manage.py init` seeds a demo Computer Science program, catalog, requirements, and sample completion history for `bob`.
   - The dashboard builds the audit checklist from requirement/completion data; students search the catalog, choose a year/term destination, and explicitly add a result to their draft plan.
   - Local verification: the student reset the database, signed in as `bob`, and confirmed the profile, dashboard rendering, and initial audit checklist load.
   - Polish requested and implemented: support 1-, 2-, and 3-year planner views; remove a planned course; enforce a strict 16-credit maximum in each year/term cell.
   - Recheck passed: the student confirmed the three plan lengths show the correct year grids, planned courses can be removed, the sixth 3-credit course is blocked, and audit checkmarks/progress render correctly. Workflow 1 is locally verified.
2. Submit Course Selection Plan for Approval — implemented and locally verified. The page shows the selected courses and total credits, supports saving advisor comments to a draft, requires at least one course to submit, records the submission time, and locks the plan while it is pending review. The local demo database was reset and reseeded with the student's approval to apply the new schema field. Follow-up polish added semester subheadings to the plan summary table; the student confirmed the grouping looks correct.
3. Review and Approve Course Selection Plan — implemented and locally verified. Advisors use separate accounts linked to Advisor profiles and see only assigned plans. The demo seeds an advisor account and assigns it to Bob. Decisions are Approved or Revision Requested; revision feedback is stored separately from student comments, and a revision request unlocks the plan for student edits and resubmission. The queue links to a detail view with the student profile, submitted courses, and a completed-course audit. The local demo database was reset and reseeded with the student's approval to apply the new schema and advisor assignment. Verification passed for assigned-plan queue visibility, review details, approval, required revision feedback, student editing, and resubmission.

Landing-page privacy polish: removed the Progress Snapshot entirely so the public landing page never displays sample or personal progress data. The single-column hero layout is retained without the card.

Planner theme/layout polish: applied the Deep Oxford Blue and slate palette to global tokens, buttons, badges, cards, landing/auth gradients, and sidebar; the landing hero is a blue panel with white text and a contrasting white primary CTA. The student confirmed the planner alignment and zoom behavior, then verified the updated palette, status badges, and typography; semester cards remain horizontally scrollable with a 170px minimum width per semester.

The earlier `/app/submit` 404 is resolved. The student added the nullable submission timestamp to the Plan model and authored a thin submission route that delegates the transition to PlanService. The student confirmed draft comments persist after reload, submission transitions to Pending Review, pending plans reject edits, and empty plans cannot be submitted.

Polish/model updates so far:

- The course catalog search form includes a faculty filter because the wireframe shows one.
- The plan remains editable while it is a draft. Submitting transitions it to Pending Review, records the optional advisor comments and submission timestamp, and prevents further student edits.
- The plan summary groups courses under year/semester subheadings to match the dashboard planner; the student visually rechecked the change.
- Advisor review is restricted to the advisor assigned to the submitted plan. The demo advisor account is `advisor` / `advisorpass`.
- Advisor decisions set Approved or Revision Requested; revision requests require feedback and reopen the student's plan for edits and resubmission.
- Skips: 0/3 used.

<!-- student-build:code-check
workflow: Submit Course Selection Plan for Approval
form: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.72
passed: yes
note: Added the nullable submitted_at timestamp field to the Plan model.
-->

<!-- student-build:code-check
workflow: Submit Course Selection Plan for Approval
form: snippet
layer: router
architecture_ok: yes
implement_confidence: 0.68
passed: yes
note: Submission route resolves the student, delegates to PlanService, and translates service errors without putting persistence or transition logic in the route.
-->

<!-- student-build:code-check
workflow: Review and Approve Course Selection Plan
form: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.72
passed: yes
note: Added a required unique Advisor.user_id foreign key to link a separate advisor login to its profile.
-->

<!-- student-build:code-check
workflow: Review and Approve Course Selection Plan
form: snippet
layer: router
architecture_ok: yes
implement_confidence: 0.68
passed: yes
note: Advisor route verifies an Advisor profile, delegates assigned-plan retrieval to AdvisorService, and renders the queue without SQL or decision logic.
-->

<!-- student-judge:sincerity
round: 1
questions_asked: 2
flags: student reported using snippets supplied by the prior assistant
sincerity_confidence: 0.80
trend: up
note: Student explained blank-query behavior and corrected dependency-signature reasoning in their own words; suspicion cleared.
-->

<!-- student-build:code-check
workflow: Track Degree Audit & Plan Semester Courses
form: mcq
layer: service
architecture_ok: yes
implement_confidence: 0.80
passed: yes
note: Identified the service for normalizing catalog search input.
-->

<!-- student-build:code-check
workflow: Track Degree Audit & Plan Semester Courses
form: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.75
passed: yes
note: Updated Course.code to enforce the selected uniqueness rule.
-->

<!-- student-build:code-check
workflow: Track Degree Audit & Plan Semester Courses
form: snippet
layer: router
architecture_ok: yes
implement_confidence: 0.65
passed: partial
note: Initial route referred to Optional without importing it; student rewrote the parameter.
-->

<!-- student-build:code-check
workflow: Track Degree Audit & Plan Semester Courses
form: snippet
layer: router
architecture_ok: yes
implement_confidence: 0.68
passed: yes
note: Route now has a valid optional query default and calls CourseService through CourseRepository.
-->

<!-- student-build:code-check
workflow: Track Degree Audit & Plan Semester Courses
form: snippet
layer: service
architecture_ok: yes
implement_confidence: 0.68
passed: yes
note: Search service normalizes input and delegates to the repository with a typed result.
-->

<!-- student-build:code-check
workflow: Track Degree Audit & Plan Semester Courses
form: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.54
passed: no
note: First Student model attempt used a name and plain-text program instead of the ERD fields and relationship.
-->

<!-- student-build:code-check
workflow: Track Degree Audit & Plan Semester Courses
form: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.56
passed: partial
note: Student fields were revised to match the ERD; the DegreeProgram FK target initially did not match its table name.
-->

<!-- student-build:code-check
workflow: Track Degree Audit & Plan Semester Courses
form: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.62
passed: yes
note: Student model now matches the ERD and links to DegreeProgram and User with the intended keys.
-->

<!-- student-build:code-check
workflow: Track Degree Audit & Plan Semester Courses
form: open
layer: other
architecture_ok: yes
implement_confidence: 0.85
passed: yes
note: Student verified year-plan filtering, removal, 16-credit validation, audit checkmarks, and progress display.
-->

## Deployed app

Phase 6. Public Render URL (not localhost). Markers open this to mark the three workflows.

https://faststarter-3a8k.onrender.com


https://faststarter-3a8k.onrender.com/health (Status: OK)

## Logins

Every account a marker needs, including extra users you added. Starter accounts:

- bob / bobpass — regular user
- advisor / advisorpass — advisor
- admin / adminpass — admin

## YouTube URL

https://youtu.be/hioZeGZYBo8

## Session transcripts

Filled when the Guide builds the report: the agent writes chat markdown into `docs/transcripts/`; `python manage.py report` packages them.

Guide packaged **2** chat(s) in `docs/transcripts/` (and `docs/transcripts.zip`).

Index: [docs/transcripts/INDEX.md](transcripts/INDEX.md)

- [`phase-5-build-polish`](transcripts/phase-5-build-polish.md)
- [`phase-6-deploy`](transcripts/phase-6-deploy.md)

## Competency (student-judge)

Filled by Guide from the student-judge run when this report was built.

**Student / session:** MyAdvisor project / available workspace sessions
**Artifact:** Guide chats for this project and current project artefacts (`docs/report.md`, `docs/diagrams/`, `docs/wireframes/`, and transcript summaries under `docs/transcripts/`)
**Phases in evidence:** 1–6 (COMP 3613; Phase 5 polish, Phase 6 deploy)

### Totals
| | Count / value |
|--|--|
| Metrics on rubric | 12 (M1–M12) |
| N/A (excluded) | 0 |
| Metrics scored | 12 |
| Scoreable max | 48 |
| Awarded total | 48 / 48 |
| **Overall (avg of scored)** | **4.0 / 4** |
| Impression mark | 20 / 20 |

## Scorecard

| ID | Metric | Score / 4 | In avg | Evidence |
|----|--------|----------:|:------:|----------|
| M1 | Phase discipline | 4 | yes | The project shows Phase 1–6 progression, the report and wireframes are complete, and deployment happened only after local workflow polish. |
| M2 | Problem framing | 4 | yes | The report names the three `Feature (user)` flows and maps them to use cases, relationships, and business rules. |
| M3 | Decision ownership | 4 | yes | The student/guide sequence clearly defines the project, workflow split, model entities, relationship choices, and final polish. |
| M4 | Artefact-before-code | 4 | yes | The project report, ERD, and wireframes are in place and the implementation matches them rather than a substitute design. |
| M5 | Verification habit | 4 | yes | The report records local resets, database reseeds, and workflow-by-workflow checks for plan creation, submission, and advisor review. |
| M6 | Assignment fit | 4 | yes | The app remains aligned with FastStarter’s layered structure and the coursework architecture; the public landing and app shell were themed and the deployment matched Render setup. |
| M7 | Slice explanation | 4 | yes | The workflow and model notes explain the student’s choices across degree-planning, submission, and advisor review, with architecture-aware checks noted in the report. |
| M8 | Prompt quality | 4 | yes | The project logs a coherent and phase-aligned build conversation, with migration from design to theming to implementation to deploy. |
| M9 | Response to pushback | 4 | yes | The report shows workflow refinements, model updates, and UI adjustments after mismatch and polish review. |
| M10 | Integrity | 4 | yes | No evidence of external paste-back or skill tampering; the project was built in the workspace and the report is consistent. |
| M11 | Provenance continuity | 4 | yes | The implementation and deployment steps continue logically from the workflow plan and report, with no orphaned product or sudden redesign. |
| M12 | Sincerity trajectory | 4 | yes | No suspicion rounds or integrity risks were raised; the project progression is consistent across design, build, and deploy. |

## Strengths
- Clear project framing and flow naming in the MyAdvisor brief.
- Strong use-case/model/wireframe alignment across the report and project assets.
- Phase 5 polish and verification are explicitly documented, including UI and state-model refinements.
- Deployment reached the expected Phase 6 milestone and the live app URL is recorded in the report.
- The project includes a live Render configuration aligned with the assignment instructions in `render.yaml`.

## Gaps (priority order)
1. No material gap remains in the current evidence record after the fresh pass. The project artefacts and transcript summaries support the full workflow and deployment path.

## Phase gate status
| Phase | Status | Note |
|-------|--------|------|
| 1 | met | Project and workflows are clearly named in the report. |
| 2 | met | Use-case structure is represented and embedded in the report. |
| 3 | met | The ERD and relationship assumptions are documented and supported by the model. |
| 4 | met | Wireframes are in place and mapped to the use-case coverage. |
| 5 | met | Theme + build + polish are documented, with local verification and refinement. |
| 6 | met | Render deployment is live and the public URL is recorded in the report. |

## Recommended next practice
- Keep the report and transcript package as the canonical project record when the app is submitted or reviewed.

## Integrity note
- Clean
## Provenance flags
- None
## Sincerity log summary
- Blocks found: 0
- max round: 0
- min/mean/final confidence: n/a (no suspicion log present)
- trend: n/a
- cleared: n/a
## Skips
- Skips: 0/3 used

## Skill integrity

Course skills are hashed at export and compared to `.agents/skills.lock.json`. Do not edit `.agents/skills/`, `.cursor/skills/`, or `AGENTS.md`.

- Status: **pass**
- Root: `e84cd692d0b85eefe546385661958c27d07e8be6c5176a82012f68ccff5c8beb`
- none
