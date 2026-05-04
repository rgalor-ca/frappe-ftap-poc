# Frontier Tower Associates Philippines Inc. (FTAP) Frappe Framework Proof of Concept (POC)

Minimal Frappe Framework custom application for replacing the current JIRA work-order path with native Frappe Framework tickets, work orders, field technician reports, attachments, and approval workflow.

## Proof of Concept (POC) Scope

This app models the immediate flow:

1. Internet of Things alarm creates an `FTAP Service Ticket`.
2. The ticket automatically opens one linked `FTAP Work Order`.
3. Dispatcher assigns the field technician.
4. Technician records arrival/completion, checklist rows, field notes, and uploads photos using Frappe Framework file attachments.
5. Supervisor reviews the field report.
6. Manager approves.
7. Department head gives final approval and closes the work order.

The implementation uses Frappe Framework standard DocTypes, role permissions, workflow records, comments, version history, assignments, and file attachments instead of JIRA.

## Free Frappe Cloud Proof of Concept (POC)

The free public-bench proof of concept (POC) is deployed directly on `https://erpnext-ftap-poc.frappe.cloud` using Frappe Framework metadata and REST APIs. It includes custom ticket/work-order records, roles, workflow, sample data, reports, a Kanban board, dashboard cards, and photo attachments.

Start with [docs/ftap-frappe-poc.md](docs/ftap-frappe-poc.md). It is the single merged source of truth for the full implementation handoff: from-scratch setup, free Frappe Cloud constraints, REST integration, architecture visuals, workflow visuals, validation coverage, edge cases, pilot gaps, production path, security notes, and continuation plan.

## Main Records

### Frontier Tower Associates Philippines Inc. (FTAP) Service Ticket

The alarm-facing record. One row should exist per alarm ID.

Key fields:

- `alarm_id`
- `alarm_source`
- `alarm_type`
- `priority`
- `site_code`
- `device_id`
- `reported_at`
- `problem_summary`
- `ticket_status`
- `assigned_work_order`

### Frontier Tower Associates Philippines Inc. (FTAP) Work Order

The field execution and approval record.

Key fields:

- `service_ticket`
- `assigned_technician`
- `supervisor`
- `manager`
- `department_head`
- `dispatch_time`
- `arrival_time`
- `completion_time`
- `inspection_checks`
- `field_notes`
- `technician_recommendation`
- approval notes

### Frontier Tower Associates Philippines Inc. (FTAP) Inspection Check

Child table under `FTAP Work Order` for the technician checklist.

## Workflow

`FTAP Work Order Approval`:

| State | Main owner | Next action |
| --- | --- | --- |
| Open | Dispatcher | Dispatch |
| Dispatched | Field Technician | Start Work |
| In Field | Field Technician | Submit Field Report |
| Field Report Submitted | Supervisor | Supervisor Approve / Supervisor Reject |
| Supervisor Approved | Manager | Manager Approve / Manager Reject |
| Manager Approved | Department Head | Head Approve / Head Reject |
| Head Approved | Closed | final submitted state |

Reject actions return the record to `In Field` so the technician can correct the field report.

The custom app blocks approval progression until the work order has an assigned technician, arrival/completion timestamps, checklist rows, field notes, technician recommendation, and photo evidence.

## Alarm API

Use a Frappe Framework API key/secret for an integration user with the `FTAP Dispatcher` role.

On the current free Frappe Cloud public-bench proof of concept (POC), use Frappe Framework standard REST resources because custom app Python methods are not installed there:

```bash
curl -X POST "https://erpnext-ftap-poc.frappe.cloud/api/resource/FTAP%20Service%20Ticket" \
  -H "Authorization: token API_KEY:API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "alarm_id": "ALARM-EXAMPLE-001",
    "alarm_source": "IoT",
    "device_id": "TOWER-001-RRU-02",
    "alarm_type": "Power Failure",
    "priority": "High",
    "site_code": "SITE-001",
    "reported_at": "<reported timestamp>",
    "problem_summary": "IoT alarm detected power loss at tower site."
  }'
```

Then create the linked work order and update the ticket with `assigned_work_order`. See [docs/ftap-frappe-poc.md](docs/ftap-frappe-poc.md) for the full free REST sequence.

When this repo is installed as a custom app on a local or private bench, use the idempotent app endpoint:

```bash
curl -X POST "https://YOUR-SITE/api/method/ftap_frappe_poc.ftap_workflow.api.create_ticket_from_alarm" \
  -H "Authorization: token API_KEY:API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "alarm_id": "ALARM-EXAMPLE-001",
    "device_id": "TOWER-001-RRU-02",
    "alarm_type": "Power Failure",
    "priority": "High",
    "site_code": "SITE-001",
    "problem_summary": "IoT alarm detected power loss at tower site."
  }'
```

Custom endpoint response:

```json
{
  "ticket": "SERVICE_TICKET_NAME",
  "work_order": "WORK_ORDER_NAME",
  "created": true
}
```

The custom endpoint is idempotent by `alarm_id`; repeated requests return the existing ticket and work order, and a partial retry repairs a missing ticket-to-work-order link. On the free REST path, the integration layer must enforce the same idempotency by querying `alarm_id` before creating a new ticket.

## Photo Uploads

Use the Frappe Framework built-in file upload endpoint and attach the file to `FTAP Work Order`.

```bash
curl -X POST "https://erpnext-ftap-poc.frappe.cloud/api/method/upload_file" \
  -H "Authorization: token API_KEY:API_SECRET" \
  -F "file=@field-photo.jpg" \
  -F "doctype=FTAP Work Order" \
  -F "docname=WORK_ORDER_NAME" \
  -F "is_private=1"
```

## Deploy To Frappe Cloud

This machine does not currently have `bench` installed, so deployment should happen from a Linux/WSL/Frappe Cloud bench environment.

Typical local bench commands:

```bash
bench get-app https://github.com/YOUR_ORG/ftap_frappe_poc
bench --site erpnext-ftap-poc.frappe.cloud install-app ftap_frappe_poc
bench --site erpnext-ftap-poc.frappe.cloud migrate
```

For Frappe Cloud, push this folder as a Git repository or copy it into the target custom-app repository, then add it to the bench group and install it on the POC site.

## Setup Checklist

1. Install the app.
2. Confirm the roles exist:
   - `FTAP Dispatcher`
   - `FTAP Field Technician`
   - `FTAP Supervisor`
   - `FTAP Manager`
   - `FTAP Department Head`
3. Create users and assign the appropriate FTAP role.
4. Create one API integration user with `FTAP Dispatcher`.
5. Send one test alarm through the API.
6. Assign the generated work order to a technician.
7. Walk the workflow through final head approval.
