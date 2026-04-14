import frappe
from frappe.model.document import Document


class IncidentReportingForm(Document):
    def before_insert(self):
        self.populate_from_incident()

    def validate(self):
        self.populate_from_incident()

    def _na(self, value):
        if value is None:
            return "N/A"
        if isinstance(value, str) and not value.strip():
            return "N/A"
        return value

    def _get_first_usable_row(self, rows, fields):
        rows = rows or []
        for row in rows:
            for fieldname in fields:
                value = row.get(fieldname)
                if value is not None and str(value).strip():
                    return row
        return None

    def populate_from_incident(self):
        if not self.get("select_incident_number"):
            return

        inc = frappe.get_doc("Incident Report", self.select_incident_number)

        # Direct mappings
        self.reporting_name_surname = self._na(inc.get("reporting_person_name"))
        self.reporting_coy_number = self._na(inc.get("reporting_person_coy_number"))
        self.responsible_manager_isambane = self._na(inc.get("responsible_supervisor_name"))
        self.description_of_incident = self._na(inc.get("description_of_the_event"))
        self.where_did_the_incident_happen = self._na(inc.get("location_on_site"))

        # datetime_incident -> date_of_incident
        dt_val = inc.get("datetime_incident")
        self.date_of_incident = self._na(str(dt_val) if dt_val else None)

        # Child table mappings: injured_detail (with fallback to injury_details)
        injured_rows = inc.get("injured_detail") or inc.get("injury_details") or []
        first_injured = self._get_first_usable_row(
            injured_rows,
            ["injured_person_name", "injured_person_coy_number"]
        )

        if first_injured:
            self.injured_name_and_surname = self._na(first_injured.get("injured_person_name"))
            self.injured_person_coy_number = self._na(first_injured.get("injured_person_coy_number"))
        else:
            self.injured_name_and_surname = "N/A"
            self.injured_person_coy_number = "N/A"

        # Child table mappings: responsible_for_damages
        damage_rows = inc.get("responsible_for_damages") or []
        first_damage = self._get_first_usable_row(
            damage_rows,
            ["damages_by_full_name", "damages_caused_by"]
        )

        if first_damage:
            self.involved_name_surname = self._na(first_damage.get("damages_by_full_name"))
            self.involved_person_coy_number = self._na(first_damage.get("damages_caused_by"))
        else:
            self.involved_name_surname = "N/A"
            self.involved_person_coy_number = "N/A"