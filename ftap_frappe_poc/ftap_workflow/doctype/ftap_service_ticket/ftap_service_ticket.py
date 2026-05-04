import frappe
from frappe.model.document import Document


class FTAPServiceTicket(Document):
    def after_insert(self):
        if frappe.db.exists("FTAP Work Order", {"service_ticket": self.name}):
            return

        work_order = frappe.get_doc(
            {
                "doctype": "FTAP Work Order",
                "service_ticket": self.name,
                "priority": self.priority,
                "site_code": self.site_code,
                "device_id": self.device_id,
                "workflow_state": "Open",
            }
        )
        work_order.insert(ignore_permissions=True)

        self.db_set("assigned_work_order", work_order.name, update_modified=False)
        self.db_set("ticket_status", "Work Order Created", update_modified=False)

