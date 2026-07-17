# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class IncidentInvestigationInterview(Document):
    def before_validate(self):
        self.populate_source_details()
        self.populate_interviewee_details()

    def validate(self):
        self.validate_interviewee()
        self.validate_dates()

    def populate_source_details(self):
        if not self.incident_investigation:
            return

        investigation = frappe.get_cached_doc(
            "Incident Investigation", self.incident_investigation
        )
        self.safety_incident = investigation.safety_incident

    def populate_interviewee_details(self):
        if not self.interviewee_employee:
            return

        employee = frappe.db.get_value(
            "Employee",
            self.interviewee_employee,
            ["employee_name", "designation"],
            as_dict=True,
        ) or {}

        self.interviewee_designation = employee.get("designation")

    def validate_interviewee(self):
        if self.external_interviewee:
            if not self.external_interviewee_name:
                frappe.throw(_("External Interviewee Name is required."))
            return

        if not self.interviewee_employee:
            frappe.throw(_("Select an Employee or mark the interviewee as external."))

    def validate_dates(self):
        if (
            self.scheduled_date
            and self.conducted_date
            and self.conducted_date < self.scheduled_date
        ):
            frappe.throw(_("Conducted Date cannot be before Scheduled Date."))
