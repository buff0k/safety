import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class TheSmartStartHira(Document):
    def autoname(self):
        site = self.site or "NO-SITE"
        working_area = self.working_area or "NO-WORKING-AREA"

        if self.date:
            hira_date = getdate(self.date).strftime("%Y-%m-%d")
        else:
            hira_date = frappe.utils.nowdate()

        site = self._clean_name_part(site)
        working_area = self._clean_name_part(working_area)

        self.name = f"{site}-{hira_date}-{working_area}"

    def _clean_name_part(self, value):
        value = str(value).strip().upper()
        value = value.replace("/", "-")
        value = value.replace("\\", "-")
        value = value.replace(" ", "-")

        while "--" in value:
            value = value.replace("--", "-")

        return value[:80].strip("-")