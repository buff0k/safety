import frappe
from frappe.model.document import Document


class IncidentReportingForm(Document):
    def before_insert(self):
        self.populate_from_incident()

    def validate(self):
        self.populate_from_incident()

    def populate_from_incident(self):
        if not self.get("select_incident_number"):
            return

        inc = frappe.get_doc("Incident Management", self.select_incident_number)

        # Direct mappings
        self.reporting_name_surname = inc.get("reporting_person_name")
        self.reporting_coy_number = inc.get("reporting_person_coy_number")
        self.responsible_manager_isambane = inc.get("responsible_supervisor_name")
        self.description_of_incident = inc.get("description_of_the_event")

        # Helpful mapping (matches your field intent)
        self.where_did_the_incident_happen = inc.get("location_on_site")

        # datetime_incident -> date_of_incident (your target field is Data)
        dt_val = inc.get("datetime_incident")
        self.date_of_incident = str(dt_val) if dt_val else None

        # Child table mappings: first usable row from injury_details
        injuries = inc.get("injury_details") or []
        first = None
        for row in injuries:
            if row.get("injured_person_name") or row.get("injured_person_coy_number"):
                first = row
                break

        if first:
            self.injured_name_and_surname = first.get("injured_person_name")
            self.injured_person_coy_number = first.get("injured_person_coy_number")
        else:
            self.injured_name_and_surname = None
            self.injured_person_coy_number = None