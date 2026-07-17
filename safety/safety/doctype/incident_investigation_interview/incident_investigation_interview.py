# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class IncidentInvestigationInterview(Document):
    def validate(self):
        self.validate_interviewee()

    def before_submit(self):
        self.validate_statement_file()

    def validate_interviewee(self):
        if not self.interviewee_employee and not self.external_interviewee_name:
            frappe.throw(
                _(
                    "Please select an Employee or enter the name of the "
                    "external interviewee."
                )
            )

        if self.interviewee_employee and self.external_interviewee_name:
            frappe.throw(
                _(
                    "Use either Employee or External Interviewee Name, "
                    "not both."
                )
            )

    def validate_statement_file(self):
        if not self.statement_file:
            frappe.throw(
                _("A signed interview statement must be attached before submission.")
            )