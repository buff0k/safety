# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate


class SafetyLessonsLearnt(Document):
    def before_validate(self):
        self.populate_source_details()

    def validate(self):
        self.validate_publication()

    def before_save(self):
        if self.workflow_state == "Published" and not self.publication_date:
            self.publication_date = nowdate()

    def populate_source_details(self):
        if not self.incident_investigation:
            return

        investigation = frappe.get_cached_doc(
            "Incident Investigation", self.incident_investigation
        )
        self.safety_incident = investigation.safety_incident

        if not self.incident_summary:
            self.incident_summary = investigation.incident_summary

    def validate_publication(self):
        if self.workflow_state != "Published":
            return

        missing = []
        if not self.target_audience:
            missing.append(_("Target Audience"))
        if not self.communication_channel:
            missing.append(_("Communication Channel"))
        if not self.communication_owner:
            missing.append(_("Communication Owner"))

        if missing:
            frappe.throw(
                _("Complete the following before publication: {0}").format(
                    ", ".join(missing)
                )
            )
