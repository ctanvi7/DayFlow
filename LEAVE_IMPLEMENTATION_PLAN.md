# Dayflow Leave Module Implementation Plan

## Scope and ownership

This document describes only Member 3's Leave / Time-Off backend, Admin
Employee Directory UI, Admin Leave Approval UI, and (if absent) Employee Leave
UI. It intentionally does not define application setup, authentication,
authorization infrastructure, employee APIs, shared styling, seed data, or
test fixtures owned by other members.

## Planned files

Files to create after the shared foundation is available:

- `app/models/leave.py`
- `app/services/leave_service.py`
- `app/routes/leave_routes.py`
- `app/static/js/leave.js`
- `app/static/js/admin_directory.js`
- `tests/test_leave.py`

The precise HTML/template file will be selected after the team agrees on the
frontend shell and routing pattern. No placeholder source files are needed now.

## Leave model

`LeaveRequest` will contain these fields:

| Field | Purpose |
| --- | --- |
| `id` | Primary key |
| `employee_id` | Foreign key to `employees.id` |
| `leave_type` | One of `PAID`, `SICK`, `UNPAID` |
| `start_date` | First requested leave date |
| `end_date` | Last requested leave date |
| `days_requested` | Server-calculated inclusive day count |
| `remarks` | Employee explanation/request notes |
| `attachment_path` | Optional future attachment path |
| `status` | One of `PENDING`, `APPROVED`, `REJECTED`; default `PENDING` |
| `review_comment` | Optional Admin/HR decision comment, maximum 500 characters |
| `reviewed_by_user_id` | Foreign key to the reviewing `users.id` |
| `reviewed_at` | Server timestamp of the decision |
| `created_at` | Server timestamp |
| `updated_at` | Server timestamp |

Indexes/constraints to agree with Member 4: indexes on `employee_id`, `status`,
and date fields. Overlap prevention requires a service-layer query and should
not rely on a simple database uniqueness constraint.

## API contract

### `GET /api/leaves/me`

- Authenticated employee receives only their own leave requests.
- Response contains no unrelated employee or user data.

### `POST /api/leaves`

- Authenticated employee submits `leave_type`, `start_date`, `end_date`, and
  `remarks`.
- The server calculates `days_requested` and always stores `PENDING`.
- Client-supplied `status`, reviewer fields, and `days_requested` are ignored.
- Returns `201` on success, `400` for invalid input, and `409` for overlap.

### `GET /api/leaves`

- Restricted to `ADMIN` and `HR`.
- Returns all requests and supports agreed query parameters such as `search`,
  `status`, `employee_id`, `leave_type`, `start_date`, and `end_date`.

### `PATCH /api/leaves/<id>/decision`

- Restricted to `ADMIN` and `HR`.
- Accepts one decision (`APPROVED` or `REJECTED`) and an optional
  `review_comment` of at most 500 characters.
- Records reviewer identity and server review time.
- Returns `404` when the request does not exist and `409` if it was already
  reviewed, so decisions cannot silently replace an existing state.

All routes will use the project's shared JSON response helper. If none exists,
the team should first agree on the required `success`, `data`, `message`, and
`errors` response shape.

## Validation and business rules

1. `leave_type` must be `PAID`, `SICK`, or `UNPAID`.
2. Both dates are required and parsed server-side.
3. `start_date` cannot be after `end_date`.
4. `days_requested` is an inclusive count calculated server-side.
5. A request overlapping a `PENDING` or `APPROVED` request for the same
   employee is rejected with `409`.
6. New requests always begin as `PENDING`.
7. Only `ADMIN` or `HR` can list all requests or record a decision.
8. Employees can view and submit only for their own employee record.
9. A decision can only transition `PENDING` to `APPROVED` or `REJECTED` once.
10. `review_comment` cannot exceed 500 characters.

## Leave service responsibilities

`leave_service.py` will own business logic rather than placing it in routes:

- validate and normalize leave inputs;
- calculate requested days;
- find conflicting requests;
- create an atomic pending request;
- retrieve a caller's own requests;
- filter Admin/HR request listings;
- validate and record a one-time approval/rejection; and
- serialize safe leave data for the relevant role.

## Admin Employee Directory UI

The directory UI will consume Member 1's existing employee API; it will not
create an employee model or API. It will provide:

- search;
- a responsive employee-card grid;
- name, job title, department, current status, and image/initials;
- a click-through action using the existing employee profile route/function;
- loading, empty, and error states.

The exact API path, employee-card response fields, profile navigation route,
and status representation must be agreed with Member 1 and Member 2.

## Admin Leave Approval UI

The Admin Time Off screen will provide:

- search and status filtering;
- employee, leave type, start date, end date, days, and status columns;
- a details view;
- review-comment input plus Approve/Reject actions for pending requests;
- in-place refresh of the affected request when practical;
- success/error feedback; and
- visually distinct pending, approved, and rejected statuses along with
  loading and empty states.

## Employee Leave UI

If not already provided, `leave.js` will provide:

- a list sourced from `GET /api/leaves/me`;
- a New Leave Request form;
- Paid/Sick/Unpaid selection, start/end dates, and remarks;
- submission to `POST /api/leaves`; and
- visible pending/approved/rejected status and error feedback.

File uploads are excluded unless the shared foundation already implements safe
upload handling.

## Required shared-foundation exports

### Member 1: authentication, users, employees, and API conventions

The leave module needs the following concrete, importable contracts:

- `db`: the configured Flask-SQLAlchemy instance (recommended location:
  `app.extensions.db` or the team's equivalent);
- authenticated current-user/session access that exposes at least `id` and
  `role` (for example `current_user` or `get_current_user()`);
- a reusable route guard/decorator for authenticated callers and a role guard
  for `ADMIN`/`HR`;
- `User` model with `id` for `reviewed_by_user_id`;
- `Employee` model with `id` and its relationship/mapping to a user ID, so the
  API can derive an employee's own record safely;
- the existing employee-directory endpoint, response shape, profile route, and
  approved fields for card display; and
- shared JSON response helpers/error conventions.

### Member 2: attendance/status contract

- The normalized current-status field or endpoint used by employee directory
  cards, including its allowed values and display intent.
- No attendance implementation is required by the leave module.

### Member 4: database, UI, and testing coordination

- Migration workflow and the migration that creates/accepts the
  `leave_requests` table.
- Database conventions (timestamps, enum approach, foreign-key naming, and
  transaction/rollback practice).
- Shared CSS class/tokens and the template/navigation shell into which Member 3
  will mount the directory and leave screens.
- Test application/client fixtures, database isolation strategy, and seed data
  conventions.

## Tests to implement once fixtures exist

1. Valid employee leave submission creates a pending request with a
   server-calculated day count.
2. Invalid date range is rejected.
3. Overlapping pending/approved leave is rejected.
4. Employee cannot approve a leave request.
5. Admin/HR can approve a pending request and reviewer fields are recorded.
6. Admin/HR can reject a pending request.
7. Invalid leave type is rejected.
8. An employee can retrieve only their own requests.
9. A repeated decision on a reviewed request returns a conflict.
10. An overlong review comment is rejected.

## Integration checklist before implementation

- [ ] Member 1 publishes the imports/contracts above.
- [ ] Member 2 publishes the employee-card status contract.
- [ ] Member 4 confirms database migration and test-fixture conventions.
- [ ] The team agrees on API response shape and frontend mounting point.
- [ ] Member 3 pulls/rebases the updated shared foundation before coding.
