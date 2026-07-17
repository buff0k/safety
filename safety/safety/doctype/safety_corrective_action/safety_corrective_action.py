# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class SafetyCorrectiveAction(Document):
    def before_validate(self):
        self.populate_source_details()

    def validate(self):
        self.validate_completion()
        self.validate_effectiveness_review()

    def before_save(self):
        if self.workflow_state == "Pending Verification" and not self.completed_on:
            self.completed_on = now_datetime()

        if self.workflow_state == "Closed" and not self.verified_on:
            self.verified_on = now_datetime()

    def populate_source_details(self):
        if not self.incident_investigation:
            return

        investigation = frappe.get_cached_doc(
            "Incident Investigation", self.incident_investigation
        )
        self.safety_incident = investigation.safety_incident

        if self.responsible_employee and not self.action_owner:
            self.action_owner = frappe.db.get_value(
                "Employee", self.responsible_employee, "user_id"
            )

        if self.responsible_employee and not self.department:
            self.department = frappe.db.get_value(
                "Employee", self.responsible_employee, "department"
            )

    def validate_completion(self):
        if self.workflow_state in {"Pending Verification", "Closed"}:
            if not self.completion_details:
                frappe.throw(_("Completion Details are required."))
            if not self.completion_evidence:
                frappe.throw(_("Completion Evidence is required."))

        if self.workflow_state == "Closed":
            if not self.verified_by:
                frappe.throw(_("Verified By is required before closing the action."))
            if not self.verification_comments:
                frappe.throw(_("Verification Comments are required before closing the action."))

    def validate_effectiveness_review(self):
        if self.effectiveness_review_required and not self.effectiveness_review_date:
            frappe.throw(_("Effectiveness Review Date is required."))
