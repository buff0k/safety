import frappe
from frappe.model.document import Document
from datetime import datetime


class ActionManagement(Document):

    def before_insert(self):
        self.populate_from_incident()
        self.set_action_number()
        self.set_month_from_date()
        self.enforce_overdue_status()

    def validate(self):
        self.populate_from_incident()
        self.set_month_from_date()
        self.enforce_overdue_status()

    def enforce_overdue_status(self):
        if not self.target_date:
            return

        today = datetime.today().date()

        # 🔒 Ensure target_date is a date object
        if isinstance(self.target_date, str):
            target_date = datetime.strptime(self.target_date, "%Y-%m-%d").date()
        else:
            target_date = self.target_date

        COMPLETE_STATUS = (
            "Complete: Action have been closed and Non-Conformance rectified"
        )

        if today > target_date and self.status != COMPLETE_STATUS:
            self.status = "Overdue"


    def populate_from_incident(self):
        if not self.reactive_actions_taken or not self.incident_number:
            return

        inc = frappe.get_doc("Incident Management", self.incident_number)

        if inc.datetime_incident:
            self.date = inc.datetime_incident.date()

        self.site = inc.site
        self.non_conformance = inc.event_category
        self.select_area = inc.location_on_site

        self.engineering = 0
        self.drill_and_blast = 0
        self.mining = 0
        self.safety = 0
        self.other_department = None

        department_map = {
            "Engineering": "engineering",
            "Drill and Blast": "drill_and_blast",
            "Mining": "mining",
            "Safety": "safety"
        }

        if inc.departmentx in department_map:
            setattr(self, department_map[inc.departmentx], 1)
        else:
            self.other_department = inc.departmentx

    def set_month_from_date(self):
        if self.date:
            if isinstance(self.date, str):
                date_obj = datetime.strptime(self.date, "%Y-%m-%d")
            else:
                date_obj = self.date
            self.month = date_obj.strftime("%B")

    def set_action_number(self):
        if self.action_number:
            return

        if self.reactive_actions_taken:
            self.action_number = get_next_action_number(
                incident_number=self.incident_number
            )

        elif self.proactive_actions_taken:
            if not self.action_category:
                frappe.throw("Action Category is required for proactive actions.")

            self.action_number = get_next_action_number(
                action_category=self.action_category
            )
        else:
            frappe.throw("Please select either Reactive or Proactive Actions Taken.")


@frappe.whitelist()
def get_next_action_number(incident_number=None, action_category=None):
    if incident_number:
        result = frappe.db.sql(
            """
            SELECT MAX(action_number)
            FROM `tabAction Management`
            WHERE incident_number = %s
            FOR UPDATE
            """,
            incident_number,
        )

    elif action_category:
        result = frappe.db.sql(
            """
            SELECT MAX(action_number)
            FROM `tabAction Management`
            WHERE action_category = %s
            FOR UPDATE
            """,
            action_category,
        )

    else:
        return 1

    max_num = result[0][0] if result and result[0][0] is not None else 0
    return int(max_num) + 1
