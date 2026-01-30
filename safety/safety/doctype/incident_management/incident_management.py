import frappe
from frappe.model.document import Document
from datetime import date
from frappe.utils import get_datetime
from typing import Optional


class IncidentManagement(Document):

    # --------------------------------------------------
    # LIFECYCLE HOOKS
    # --------------------------------------------------
    def before_insert(self):
        if (
            not self.incident_number
            and self.event_category
            and self.datetime_incident
        ):
            self.incident_number = get_next_incident_number(
                event_category=self.event_category,
                datetime_incident=self.datetime_incident
            )

        self.calculate_all()
        self.cleanup_vfl_team()
        self.cleanup_attachments()

    def validate(self):
        self.calculate_all()
        self.cleanup_vfl_team()
        self.cleanup_attachments()

    # --------------------------------------------------
    # CENTRAL CALCULATIONS
    # --------------------------------------------------
    def calculate_all(self):
        self.calculate_child_ages()
        self.calculate_risk_rating()
        self.populate_impact_description()

    # --------------------------------------------------
    # ATTACHMENT ENFORCEMENT
    # --------------------------------------------------
    def cleanup_attachments(self):

        mapping = {
            "storyline": ["attach_one", "attach_five", "attach_six"],
            "investigation_report": ["attach_two", "attach_three", "attach_four"],
            "affected_person_statement": ["attach_seven", "attach_eight", "attach_nine"],
            "incident_notification": ["attach_ten", "attach_eleven", "attach_twelve"],
            "induction_records": ["attach_nine", "attach_ten", "attach_eleven"],
            "training_records": ["attach_twelve", "attach_thirteen", "attach_fourteen"],
            "issue_based_risk_assessment": ["attach_fifteen", "attach_sixteen", "attach_seventeen"],
            "mini_hira": ["attach_eighteen"],
            "applicable_procedure": ["attach_nineteen", "attach_twenty", "attach_twenty_one"],
            "planned_task_observation": ["attach_twenty_two", "attach_twenty_three", "attach_twenty_four"],
            "safety_caucus": ["attach_twenty_five", "attach_twenty_six", "attach_twenty_seven"],
            "investigation_register": ["attach_twenty_eight", "attach_twenty_nine", "attach_thirty"],
            "tmm_records": ["attach_thirty_one", "attach_thirty_two", "attach_thirty_three"],
            "alcohol_and_drug_test": ["attach_thirty_four", "attach_thirty_five", "attach_thirty_six"],
            "action_list": ["attach_thrity_seven", "attach_thirty_eight", "attach_thirty_nine"],
            "evidence_of_actions": ["attach_forty", "attach_forty_one", "attach_forty_two"],
            "medical_certificate_of_fitness": ["attach_forty_three"],
            "license_authorisation": ["attach_forty_four", "attach_forty_five", "attach_forty_six"],
            "other_supporting_documents": ["attach_forty_seven", "attach_forty_eight"]
        }

        for check, attachments in mapping.items():
            if not self.get(check):
                for field in attachments:
                    self.set(field, None)

    # --------------------------------------------------
    # VFL TEAM ENFORCEMENT
    # --------------------------------------------------
    def cleanup_vfl_team(self):
        if self.event_category != "Visible Field Leadership (VFL)":
            self.set("vfl_team_member_details", [])

    # --------------------------------------------------
    # CHILD TABLE AGE CALCULATIONS
    # --------------------------------------------------
    def calculate_child_ages(self):

        today = date.today()

        for row in self.get("injury_details", []):
            row.age_of_injured = self._calculate_age(today, row.injured_id)

        for row in self.get("damage_details", []):
            row.damages_caused_by_age = self._calculate_age(
                today, row.damages_caused_by_id
            )

        for row in self.get("vfl_team_member_details", []):
            row.age_of_team_member = self._calculate_age(
                today, row.team_member_id
            )

    def _calculate_age(self, today, dob):
        if not dob:
            return None

        years = today.year - dob.year
        months = today.month - dob.month

        if today.day < dob.day:
            months -= 1
        if months < 0:
            years -= 1
            months += 12

        return f"{years} years {months} months"

    # --------------------------------------------------
    # RISK MATRIX
    # --------------------------------------------------
    def calculate_risk_rating(self):

        if not self.hazard_consequence or not self.likelyhood:
            self.risk_rating = None
            self.risk_level = None
            return

        consequence = int(self.hazard_consequence)
        likelihood = int(self.likelyhood)

        matrix = {
            1: {1: 1, 2: 3, 3: 4, 4: 7, 5: 11},
            2: {1: 3, 2: 5, 3: 8, 4: None, 5: 16},
            3: {1: 6, 2: 9, 3: 13, 4: 17, 5: 20},
            4: {1: 10, 2: 14, 3: 18, 4: 21, 5: 23},
            5: {1: 15, 2: 19, 3: 22, 4: 24, 5: 25}
        }

        rating = matrix.get(consequence, {}).get(likelihood)

        self.risk_rating = rating

        if rating and 21 <= rating <= 25:
            self.risk_level = "Extreme"
        elif rating and 13 <= rating <= 20:
            self.risk_level = "High"
        elif rating and 6 <= rating <= 12:
            self.risk_level = "Medium"
        elif rating and 1 <= rating <= 5:
            self.risk_level = "Low"
        else:
            self.risk_level = None

    # --------------------------------------------------
    # IMPACT → DESCRIPTION
    # --------------------------------------------------
    def populate_impact_description(self):

        if not self.hazard_consequence:
            self.description = None
            return

        consequence = int(self.hazard_consequence)
        descriptions = []

        if self.harm_to_people:
            descriptions.append({
                1: "First aid case / Exposure to minor health risk",
                2: "Medical treatment case / Exposure to major health risk",
                3: "Lost time injury / Reversible impact on health",
                4: "Single fatality or loss of quality of life / Irreversible impact on health",
                5: "Multiple fatalities / Impact on health ultimately fatal"
            }.get(consequence))

        if self.environmental_impact:
            descriptions.append({
                1: "Minimal environmental harm – L1 incident",
                2: "Material environmental harm – L2 incident remediable short term",
                3: "Serious environmental harm – L2 incident remediable within LOM",
                4: "Major environmental harm – L2 incident remediable post LOM",
                5: "Extreme environmental harm – L3 incident irreversible"
            }.get(consequence))

        if self.business_interruption:
            descriptions.append({
                1: "No disruption to operation / US$20k to US$100k",
                2: "Brief disruption to operation / US$100k to US$1.0M",
                3: "Partial shutdown / US$1.0M to US$10.0M",
                4: "Partial loss of operation / US$10M to US$75.0M",
                5: "Substantial or total loss of operation / >US$75.0M"
            }.get(consequence))

        if self.legal_and_regulatory:
            descriptions.append({
                1: "Low level legal issue",
                2: "Minor legal issue; non compliance and breaches of the law",
                3: "Serious breach of law; investigation/report to authority, prosecution and/or moderate penalty possible",
                4: "Major breach of the law; considerable prosecution and penalties",
                5: "Very considerable penalties & prosecutions. Multiple law suits & jail terms"
            }.get(consequence))

        if self.impact_on_community:
            descriptions.append({
                1: "Slight impact - public awareness may exist but no public concern",
                2: "Limited impact - local public concern",
                3: "Considerable impact - regional public concern",
                4: "National impact - national public concern",
                5: "International impact - international public attention"
            }.get(consequence))

        self.description = "\n".join(filter(None, descriptions))


# ======================================================
# INCIDENT NUMBER GENERATOR (v16 COMPATIBLE)
# ======================================================
@frappe.whitelist(methods=["POST"])
def get_next_incident_number(
    *,
    event_category: Optional[str] = None,
    datetime_incident: Optional[str] = None
) -> str:
    """
    Generate a globally sequential Incident Number.

    Format:
        YYYY-MM/IS/<PREFIX>/<SEQUENCE>

    Sequence:
        Global, never resets
    """

    if not event_category or not datetime_incident:
        frappe.throw("event_category and datetime_incident are required")

    category_map = {
        "Planned Task Observation (PTO)": "PTO",
        "Visible Field Leadership (VFL)": "VFL",
        "Inspection (INS)": "INS",
        "Audit (AUD)": "AUD",
        "Incident (INC)": "INC"
    }

    prefix = category_map.get(event_category, "GEN")

    dt = get_datetime(datetime_incident)
    year_month = dt.strftime("%Y-%m")

    last = frappe.db.sql(
        """
        SELECT incident_number
        FROM `tabIncident Management`
        WHERE incident_number REGEXP '/[0-9]{5}$'
        ORDER BY CAST(SUBSTRING_INDEX(incident_number, '/', -1) AS UNSIGNED) DESC
        LIMIT 1
        FOR UPDATE
        """,
        as_dict=False
    )

    next_num = 1
    if last and last[0][0]:
        next_num = int(last[0][0].split("/")[-1]) + 1

    return f"{year_month}/IS/{prefix}/{next_num:05d}"
