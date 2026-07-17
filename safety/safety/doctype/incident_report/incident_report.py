# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

from datetime import date, datetime
from typing import Optional

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime


class IncidentReport(Document):
    def before_insert(self):
        if (
            not self.incident_number
            and self.event_category
            and self.datetime_incident
        ):
            self.incident_number = get_next_incident_number(
                event_category=self.event_category,
                datetime_incident=self.datetime_incident,
            )

        self.calculate_all()
        self.cleanup_attachments()
        self.validate_preliminary_investigation_rows()
        self.validate_investigation_decision()

    def validate(self):
        self.calculate_all()
        self.cleanup_attachments()
        self.validate_preliminary_investigation_rows()
        self.validate_investigation_decision()

    def validate_investigation_decision(self):
        if self.is_the_investigation_required == "Yes" and not self.investigation_type:
            frappe.throw(
                _("Investigation Type is required when an investigation is required.")
            )

        if (
            self.is_the_investigation_required == "No"
            and not self.investigation_not_required_reason
        ):
            frappe.throw(
                _("A reason is required when an investigation is not required.")
            )

        if self.is_the_investigation_required != "Yes":
            self.investigation_type = None

        if self.is_the_investigation_required != "No":
            self.investigation_not_required_reason = None

    def calculate_all(self):
        self.calculate_child_ages()
        self.calculate_risk_rating()
        self.populate_impact_description()

    def calculate_child_ages(self):
        today = date.today()

        for row in self.get("injured_detail", []):
            row.age_of_injured = self._calculate_age(
                today, row.get("injured_id")
            )

        for row in self.get("responsible_for_damages", []):
            row.damages_caused_by_age = self._calculate_age(
                today, row.get("damages_caused_by_id")
            )

    def _calculate_age(self, today, value):
        if not value:
            return None

        dob = self._extract_dob(value, today=today)
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

    def _extract_dob(self, value, today=None):
        if not value:
            return None

        today = today or date.today()

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        value = str(value).strip()

        if len(value) >= 6 and value[:6].isdigit():
            yy = int(value[:2])
            mm = int(value[2:4])
            dd = int(value[4:6])
            current_yy = today.year % 100
            year = 1900 + yy if yy > current_yy else 2000 + yy

            try:
                return date(year, mm, dd)
            except ValueError:
                pass

        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        return None

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
            5: {1: 15, 2: 19, 3: 22, 4: 24, 5: 25},
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

    def populate_impact_description(self):
        if not self.hazard_consequence:
            self.description = None
            return

        consequence = int(self.hazard_consequence)
        selected_impacts = self._get_table_values("type_of_impact")
        descriptions = []

        for impact in selected_impacts:
            key = (impact or "").strip().lower()

            if "harm to people" in key or "safety" in key or "health" in key:
                descriptions.append({
                    1: "First aid case / Exposure to minor health risk",
                    2: "Medical treatment case / Exposure to major health risk",
                    3: "Lost time injury / Reversible impact on health",
                    4: "Single fatality or loss of quality of life / Irreversible impact on health",
                    5: "Multiple fatalities / Impact on health ultimately fatal",
                }.get(consequence))
            elif "environment" in key:
                descriptions.append({
                    1: "Minimal environmental harm - L1 incident",
                    2: "Material environmental harm - L2 incident remediable short term",
                    3: "Serious environmental harm - L2 incident remediable within LOM",
                    4: "Major environmental harm - L2 incident remediable post LOM",
                    5: "Extreme environmental harm - L3 incident irreversible",
                }.get(consequence))
            elif (
                "business interruption" in key
                or "material damage" in key
                or "other losses" in key
            ):
                descriptions.append({
                    1: "No disruption to operation / US$20k to US$100k",
                    2: "Brief disruption to operation / US$100k to US$1.0M",
                    3: "Partial shutdown / US$1.0M to US$10.0M",
                    4: "Partial loss of operation / US$10M to US$75.0M",
                    5: "Substantial or total loss of operation / >US$75.0M",
                }.get(consequence))
            elif "legal" in key or "regulatory" in key:
                descriptions.append({
                    1: "Low level legal issue",
                    2: "Minor legal issue; non compliance and breaches of the law",
                    3: "Serious breach of law; investigation/report to authority, prosecution and/or moderate penalty possible",
                    4: "Major breach of the law; considerable prosecution and penalties",
                    5: "Very considerable penalties & prosecutions. Multiple law suits & jail terms",
                }.get(consequence))
            elif "community" in key or "reputation" in key or "social" in key:
                descriptions.append({
                    1: "Slight impact - public awareness may exist but no public concern",
                    2: "Limited impact - local public concern",
                    3: "Considerable impact - regional public concern",
                    4: "National impact - national public concern",
                    5: "International impact - international public attention",
                }.get(consequence))

        self.description = "\n".join(filter(None, descriptions)) or None

    def _get_table_values(self, table_fieldname):
        values = []
        ignore_fields = {
            "name", "owner", "creation", "modified", "modified_by",
            "parent", "parentfield", "parenttype", "idx", "docstatus", "doctype",
        }

        for row in self.get(table_fieldname, []):
            for key, value in row.as_dict().items():
                if key in ignore_fields:
                    continue
                if (
                    isinstance(value, str)
                    and value.strip()
                    and value.strip() not in {"0", "1"}
                ):
                    values.append(value.strip())
                    break

        return values

    def cleanup_attachments(self):
        selected_field = {
            "5 Why": "five_why",
            "Fishbone": "fishbone",
            "ICAM": "icam",
        }.get(self.specify_type)

        for fieldname in ("five_why", "fishbone", "icam"):
            if fieldname != selected_field:
                self.set(fieldname, None)

    def validate_preliminary_investigation_rows(self):
        for idx, row in enumerate(
            self.get("investigation_type_and_attachments", []), start=1
        ):
            attachment_fields = [
                df.fieldname
                for df in frappe.get_meta(row.doctype).fields
                if df.fieldtype in ("Attach", "Attach Image")
            ]

            if attachment_fields and not any(
                row.get(fieldname) for fieldname in attachment_fields
            ):
                frappe.throw(
                    _(
                        "Please upload at least one attachment in "
                        "Investigation Type and Attachments row {0}."
                    ).format(idx)
                )


@frappe.whitelist(methods=["POST"])
def get_next_incident_number(
    *,
    event_category: Optional[str] = None,
    datetime_incident: Optional[str] = None,
) -> str:
    if not event_category or not datetime_incident:
        frappe.throw(_("event_category and datetime_incident are required"))

    prefix = {
        "Planned Task Observation (PTO)": "PTO",
        "Visible Field Leadership (VFL)": "VFL",
        "Inspection (INS)": "INS",
        "Audit (AUD)": "AUD",
        "Incident (INC)": "INC",
    }.get(event_category, "GEN")

    year_month = get_datetime(datetime_incident).strftime("%Y-%m")
    last = frappe.db.sql(
        """
        SELECT incident_number
        FROM `tabIncident Report`
        WHERE incident_number REGEXP '/[0-9]{5}$'
        ORDER BY CAST(SUBSTRING_INDEX(incident_number, '/', -1) AS UNSIGNED) DESC
        LIMIT 1
        FOR UPDATE
        """
    )

    next_num = 1
    if last and last[0][0]:
        next_num = int(last[0][0].split("/")[-1]) + 1

    return f"{year_month}/IS/{prefix}/{next_num:05d}"


@frappe.whitelist()
def make_flash_report(incident_report: str):
    source = frappe.get_doc("Incident Report", incident_report)
    source.check_permission("read")

    target = frappe.new_doc("Flash Reports")
    target.incident_number = source.name
    target.action_category = source.event_category
    target.incident_classification = source.incident_type
    target.date_and_time_of_incident = source.datetime_incident
    target.site = source.site
    target.occurence = source.location_on_site
    target.description_of_incident_impact = (
        source.description_of_the_event or source.description
    )
    target.repeat_incident = "Yes" if source.has_happened else "No"

    return target.as_dict()


@frappe.whitelist()
def make_incident_investigation(incident_report: str):
    source = frappe.get_doc("Incident Report", incident_report)
    source.check_permission("read")

    if source.is_the_investigation_required != "Yes":
        frappe.throw(_("This Incident Report does not require an investigation."))

    if not source.investigation_type:
        frappe.throw(_("Investigation Type is required."))

    existing = frappe.db.get_value(
        "Incident Investigation",
        {
            "safety_incident": source.name,
            "investigation_kind": "Primary",
        },
        "name",
    )
    if existing:
        return {"existing": existing}

    target = frappe.new_doc("Incident Investigation")
    target.safety_incident = source.name
    target.investigation_type = source.investigation_type
    target.investigation_kind = "Primary"
    target.incident_number = source.incident_number
    target.incident_datetime = source.datetime_incident
    target.site = source.site
    target.location_on_site = source.location_on_site
    target.incident_summary = source.description_of_the_event

    return target.as_dict()


@frappe.whitelist()
def get_related_safety_records(incident_report: str):
    if not frappe.has_permission("Incident Report", "read", incident_report):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    return {
        "flash_reports": frappe.get_all(
            "Flash Reports",
            filters={"incident_number": incident_report},
            fields=["name", "creation", "modified"],
            order_by="creation desc",
        ),
        "investigations": frappe.get_all(
            "Incident Investigation",
            filters={"safety_incident": incident_report},
            fields=[
                "name",
                "investigation_type",
                "investigation_kind",
                "workflow_state",
                "lead_investigator",
                "target_completion_date",
            ],
            order_by="creation desc",
        ),
    }
