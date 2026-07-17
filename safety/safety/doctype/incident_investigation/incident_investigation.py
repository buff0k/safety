# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate


class IncidentInvestigation(Document):
    def before_validate(self):
        self.populate_source_details()

    def validate(self):
        self.validate_primary_investigation()
        self.validate_review_readiness()

    def before_save(self):
        if self.workflow_state == "Completed" and not self.actual_completion_date:
            self.actual_completion_date = nowdate()

    def populate_source_details(self):
        if not self.safety_incident:
            return

        source = frappe.get_cached_doc("Incident Report", self.safety_incident)
        self.incident_number = source.incident_number
        self.incident_datetime = source.datetime_incident
        self.site = source.site
        self.location_on_site = source.location_on_site

        if not self.investigation_type:
            self.investigation_type = source.investigation_type

        if not self.incident_summary:
            self.incident_summary = source.description_of_the_event

    def validate_primary_investigation(self):
        if not self.safety_incident or self.investigation_kind != "Primary":
            return

        existing = frappe.db.get_value(
            "Incident Investigation",
            {
                "safety_incident": self.safety_incident,
                "investigation_kind": "Primary",
                "name": ("!=", self.name or ""),
            },
            "name",
        )

        if existing:
            frappe.throw(
                _("Primary investigation {0} already exists for this Incident Report.").format(
                    frappe.bold(existing)
                )
            )

    def validate_review_readiness(self):
        if self.workflow_state not in {"Draft Findings", "Manager Review"}:
            return

        missing = []
        if not self.timeline:
            missing.append(_("Timeline"))
        if not self.causes:
            missing.append(_("Causes and Findings"))
        if not self.recommendations:
            missing.append(_("Recommendations"))
        if not self.final_conclusion:
            missing.append(_("Final Conclusion"))

        if missing:
            frappe.throw(
                _("Complete the following before review: {0}").format(
                    ", ".join(missing)
                )
            )


@frappe.whitelist()
def make_interview(investigation: str):
    source = frappe.get_doc("Incident Investigation", investigation)
    source.check_permission("read")

    target = frappe.new_doc("Incident Investigation Interview")
    target.incident_investigation = source.name
    target.safety_incident = source.safety_incident
    return target.as_dict()


@frappe.whitelist()
def make_lessons_learnt(investigation: str):
    source = frappe.get_doc("Incident Investigation", investigation)
    source.check_permission("read")

    target = frappe.new_doc("Safety Lessons Learnt")
    target.incident_investigation = source.name
    target.safety_incident = source.safety_incident
    target.title = _("Lessons Learnt - {0}").format(source.incident_number or source.name)
    target.incident_summary = source.incident_summary
    target.key_causes = _format_causes(source)
    return target.as_dict()


@frappe.whitelist()
def generate_corrective_actions(investigation: str):
    source = frappe.get_doc("Incident Investigation", investigation)
    source.check_permission("write")

    if source.workflow_state not in {"Approved", "Actions Generated"}:
        frappe.throw(_("The investigation must be Approved before actions are generated."))

    created = []
    skipped = []

    for recommendation in source.recommendations:
        if not recommendation.approved:
            continue

        if recommendation.corrective_action:
            skipped.append(recommendation.corrective_action)
            continue

        if not recommendation.responsible_employee or not recommendation.target_date:
            frappe.throw(
                _(
                    "Approved recommendation row {0} requires a Responsible Employee "
                    "and Target Date."
                ).format(recommendation.idx)
            )

        action = frappe.new_doc("Safety Corrective Action")
        action.incident_investigation = source.name
        action.safety_incident = source.safety_incident
        action.source_recommendation_row = recommendation.name
        action.action = recommendation.recommendation
        action.action_type = recommendation.action_type
        action.priority = recommendation.priority
        action.responsible_employee = recommendation.responsible_employee
        action.target_date = recommendation.target_date
        action.insert(ignore_permissions=True)

        recommendation.db_set("corrective_action", action.name, update_modified=False)
        created.append(action.name)

    return {"created": created, "skipped": skipped}


def _format_causes(source):
    values = []
    for row in source.causes:
        if row.cause_statement:
            values.append(f"{row.cause_type}: {row.cause_statement}")
    return "\n\n".join(values)


@frappe.whitelist()
def get_linked_records(investigation: str):
    if not frappe.has_permission("Incident Investigation", "read", investigation):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    return {
        "interviews": frappe.get_all(
            "Incident Investigation Interview",
            filters={"incident_investigation": investigation},
            fields=[
                "name", "workflow_state", "interviewee_employee",
                "external_interviewee_name", "scheduled_date", "conducted_date",
            ],
            order_by="creation desc",
        ),
        "actions": frappe.get_all(
            "Safety Corrective Action",
            filters={"incident_investigation": investigation},
            fields=[
                "name", "workflow_state", "priority", "responsible_employee",
                "target_date",
            ],
            order_by="creation desc",
        ),
        "lessons": frappe.get_all(
            "Safety Lessons Learnt",
            filters={"incident_investigation": investigation},
            fields=["name", "workflow_state", "title", "publication_date"],
            order_by="creation desc",
        ),
    }
