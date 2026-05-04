import json

import frappe


@frappe.whitelist()
def create_ticket_from_alarm(payload=None, **kwargs):
    """Create or return the ticket/work order for a unique IoT alarm."""
    data = _coerce_payload(payload, kwargs)

    alarm_id = _required_value(data, "alarm_id")
    device_id = _required_value(data, "device_id")
    alarm_type = _required_value(data, "alarm_type")

    existing_ticket = frappe.db.get_value("FTAP Service Ticket", {"alarm_id": alarm_id}, "name")
    if existing_ticket:
        return _alarm_response(existing_ticket, created=False)

    ticket = frappe.get_doc(
        {
            "doctype": "FTAP Service Ticket",
            "alarm_id": alarm_id,
            "alarm_source": data.get("alarm_source") or "IoT",
            "alarm_type": alarm_type,
            "priority": data.get("priority") or "Medium",
            "site_code": data.get("site_code"),
            "device_id": device_id,
            "reported_at": data.get("reported_at") or frappe.utils.now_datetime(),
            "problem_summary": data.get("problem_summary") or data.get("summary") or alarm_type,
        }
    )
    try:
        ticket.insert()
    except Exception as exc:
        if exc.__class__.__name__ in {"DuplicateEntryError", "UniqueValidationError"}:
            existing_ticket = frappe.db.get_value("FTAP Service Ticket", {"alarm_id": alarm_id}, "name")
            if existing_ticket:
                return _alarm_response(existing_ticket, created=False)
        raise

    return _alarm_response(ticket.name, created=True)


def _coerce_payload(payload, kwargs):
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except ValueError:
            frappe.throw("payload must be valid JSON")
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        frappe.throw("payload must be a JSON object")

    payload.update(kwargs)
    return payload


def _required_value(data, fieldname):
    value = data.get(fieldname)
    if isinstance(value, str):
        value = value.strip()
    if not value:
        frappe.throw(f"{fieldname} is required")
    return value


def _alarm_response(ticket_name, created):
    work_order_name = _ensure_work_order(ticket_name)
    return {
        "ticket": ticket_name,
        "work_order": work_order_name,
        "created": created,
    }


def _ensure_work_order(ticket_name):
    work_order_name = frappe.db.get_value("FTAP Work Order", {"service_ticket": ticket_name}, "name")
    if work_order_name:
        _link_ticket_work_order(ticket_name, work_order_name)
        return work_order_name

    ticket = frappe.get_doc("FTAP Service Ticket", ticket_name)
    work_order = frappe.get_doc(
        {
            "doctype": "FTAP Work Order",
            "service_ticket": ticket.name,
            "priority": ticket.priority,
            "site_code": ticket.site_code,
            "device_id": ticket.device_id,
            "workflow_state": "Open",
        }
    )
    try:
        work_order.insert(ignore_permissions=True)
    except Exception as exc:
        if exc.__class__.__name__ in {"DuplicateEntryError", "UniqueValidationError"}:
            existing_work_order = frappe.db.get_value("FTAP Work Order", {"service_ticket": ticket_name}, "name")
            if existing_work_order:
                _link_ticket_work_order(ticket_name, existing_work_order)
                return existing_work_order
        raise

    _link_ticket_work_order(ticket_name, work_order.name)
    return work_order.name


def _link_ticket_work_order(ticket_name, work_order_name):
    frappe.db.set_value(
        "FTAP Service Ticket",
        ticket_name,
        {
            "assigned_work_order": work_order_name,
            "ticket_status": "Work Order Created",
        },
        update_modified=False,
    )
