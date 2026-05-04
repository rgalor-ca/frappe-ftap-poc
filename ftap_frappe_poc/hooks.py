app_name = "ftap_frappe_poc"
app_title = "FTAP Frappe POC"
app_publisher = "FTAP"
app_description = "Ticketing, work order, and workflow management POC"
app_email = "admin@example.com"
app_license = "MIT"

fixtures = [
    {
        "dt": "Role",
        "filters": [
            [
                "name",
                "in",
                [
                    "FTAP Dispatcher",
                    "FTAP Field Technician",
                    "FTAP Supervisor",
                    "FTAP Manager",
                    "FTAP Department Head",
                ],
            ]
        ],
    },
    {
        "dt": "Workflow State",
        "filters": [
            [
                "workflow_state_name",
                "in",
                [
                    "Open",
                    "Dispatched",
                    "In Field",
                    "Field Report Submitted",
                    "Supervisor Approved",
                    "Manager Approved",
                    "Head Approved",
                    "Cancelled",
                ],
            ]
        ],
    },
    {
        "dt": "Workflow Action Master",
        "filters": [
            [
                "workflow_action_name",
                "in",
                [
                    "Dispatch",
                    "Start Work",
                    "Submit Field Report",
                    "Supervisor Approve",
                    "Supervisor Reject",
                    "Manager Approve",
                    "Manager Reject",
                    "Head Approve",
                    "Head Reject",
                    "Cancel",
                ],
            ]
        ],
    },
    {"dt": "Workflow", "filters": [["name", "=", "FTAP Work Order Approval"]]},
]

doc_events = {
    "File": {
        "after_insert": "ftap_frappe_poc.ftap_workflow.doctype.ftap_work_order.ftap_work_order.sync_photo_evidence_count",
        "on_trash": "ftap_frappe_poc.ftap_workflow.doctype.ftap_work_order.ftap_work_order.sync_photo_evidence_count_on_trash",
    }
}
