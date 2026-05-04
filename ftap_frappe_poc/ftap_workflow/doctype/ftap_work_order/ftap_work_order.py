import frappe
from frappe.model.document import Document


class FTAPWorkOrder(Document):
    def validate(self):
        self.photo_evidence_count = get_photo_evidence_count(self.name)
        self._validate_assignment()
        self._validate_field_report()
        self._validate_field_timestamps()

    def on_update(self):
        if not self.service_ticket:
            return

        ticket_status = _ticket_status_for_state(self.workflow_state)
        frappe.db.set_value(
            "FTAP Service Ticket",
            self.service_ticket,
            {
                "ticket_status": ticket_status,
                "assigned_work_order": self.name,
            },
            update_modified=False,
        )

    def _validate_assignment(self):
        if self.workflow_state not in {"Open", "Cancelled"} and not self.assigned_technician:
            frappe.throw("Assigned Technician is required before field work can proceed")

    def _validate_field_report(self):
        if self.workflow_state not in {"Field Report Submitted", "Supervisor Approved", "Manager Approved", "Head Approved"}:
            return

        missing = []
        if not self.arrival_time:
            missing.append("Arrival Time")
        if not self.completion_time:
            missing.append("Completion Time")
        if not self.inspection_checks:
            missing.append("Inspection Checks")
        if not self.field_notes:
            missing.append("Field Notes")
        if not self.technician_recommendation:
            missing.append("Technician Recommendation")
        if not self.photo_evidence_count:
            missing.append("Photo Evidence")

        if missing:
            frappe.throw("Complete the field report before approval: " + ", ".join(missing))

    def _validate_field_timestamps(self):
        if not self.arrival_time or not self.completion_time:
            return

        if frappe.utils.get_datetime(self.completion_time) < frappe.utils.get_datetime(self.arrival_time):
            frappe.throw("Completion Time cannot be earlier than Arrival Time")


def _ticket_status_for_state(workflow_state):
    if not workflow_state or workflow_state == "Open":
        return "Work Order Created"
    if workflow_state == "Head Approved":
        return "Closed"
    if workflow_state == "Cancelled":
        return "Cancelled"
    if workflow_state in {"Field Report Submitted", "Supervisor Approved", "Manager Approved"}:
        return "Pending Approval"
    return "In Progress"


def sync_photo_evidence_count(file_doc, method=None):
    _sync_attached_work_order_photo_count(file_doc)


def sync_photo_evidence_count_on_trash(file_doc, method=None):
    _sync_attached_work_order_photo_count(file_doc, exclude_file=file_doc.name)


def _sync_attached_work_order_photo_count(file_doc, exclude_file=None):
    if file_doc.attached_to_doctype != "FTAP Work Order" or not file_doc.attached_to_name:
        return

    if not frappe.db.exists("FTAP Work Order", file_doc.attached_to_name):
        return

    frappe.db.set_value(
        "FTAP Work Order",
        file_doc.attached_to_name,
        "photo_evidence_count",
        get_photo_evidence_count(file_doc.attached_to_name, exclude_file=exclude_file),
        update_modified=False,
    )


def get_photo_evidence_count(work_order, exclude_file=None):
    if not work_order:
        return 0

    file_names = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "FTAP Work Order",
            "attached_to_name": work_order,
            "is_folder": 0,
        },
        pluck="name",
    )
    if exclude_file:
        file_names = [name for name in file_names if name != exclude_file]
    return len(file_names)
