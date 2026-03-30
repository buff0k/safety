# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


NA_VALUE = "N/A"


class LessonsLearnt(Document):
    def validate(self):
        populate_lessons_learnt_from_incident_doc(self)


@frappe.whitelist()
def populate_lessons_learnt_from_incident(lessons_learnt_name):
    doc = frappe.get_doc("Lessons Learnt", lessons_learnt_name)
    populate_lessons_learnt_from_incident_doc(doc)
    doc.save(ignore_permissions=True)
    return {
        "name": doc.name,
        "incident_number": doc.incident_number,
    }


def populate_lessons_learnt_from_incident_doc(doc):
    if not doc.incident_number:
        clear_auto_mapped_fields(doc)
        return

    incident = frappe.get_doc("Incident Report", doc.incident_number)

    injured_row = get_first_injured_row(incident)
    damage_row = get_first_damage_row(incident)

    # Nature of Injury -> nature_of_the_injury child table -> nature_of_injury
    doc.nature_of_injury = with_na(
        join_child_link_values(
            getattr(incident, "nature_of_the_injury", []),
            "nature_of_injury"
        )
    )

    # Nature of Damage -> type_of_damage child table -> specify_type_of_damage
    doc.nature_of_damage = with_na(
        join_child_link_values(
            getattr(incident, "type_of_damage", []),
            "specify_type_of_damage"
        )
    )

    # Nature of Environmental Impact -> any value in type_of_impact field
    doc.nature_of_environmental_impact = with_na(
        join_child_link_values(
            getattr(incident, "type_of_impact", []),
            "describe_type_of_impact"
        )
    )

    # Name of Injured Person -> Responsible Person child table -> injured_person_name
    doc.name_of_injured_person = with_na(
        safe_strip(getattr(injured_row, "injured_person_name", None))
    )

    # Name of Affected Person -> Person Responsible for Damages child table -> damages_by_full_name
    doc.name_of_affected_person = with_na(
        safe_strip(getattr(damage_row, "damages_by_full_name", None))
    )

    # Position of Employee
    # Prefer injury row position first, then damage row position.
    doc.position_of_employee = with_na(
        safe_strip(getattr(injured_row, "position_of_injured", None))
        or safe_strip(getattr(damage_row, "damages_caused_by_position", None))
    )

    # Years in Current Position
    # Prefer damage row years first, then injury row years.
    doc.years_in_current_position = with_na(
        safe_strip(getattr(damage_row, "damages_caused_by_years_in_current_position", None))
        or safe_strip(getattr(injured_row, "years_in_current_position", None))
    )

    # Potential Severity Classification -> select_severity child table -> classify
    doc.potential_severity_classification = with_na(
        join_child_link_values(
            getattr(incident, "select_severity", []),
            "classify"
        )
    )

    # Repeat Incident -> checkboxes in Incident Report
    doc.repeat_incident = with_na(get_repeat_incident_value(incident))

    # Life Saving Rule -> life_save_rule child table -> specify_life_saving_rule
    doc.life_saving_rule = with_na(
        join_child_link_values(
            getattr(incident, "life_save_rule", []),
            "specify_life_saving_rule"
        )
    )

    # These fields must remain blank when empty, per your rule:
    # immediate_causes
    # basic_causes
    # system_and_control_failures
    # comments
    # disclaimer

    # Not mapped yet from your instructions, so left unchanged:
    # doc.photos_and_attachments


def clear_auto_mapped_fields(doc):
    # Fields that should default to N/A when no incident is selected
    doc.nature_of_injury = NA_VALUE
    doc.nature_of_damage = NA_VALUE
    doc.nature_of_environmental_impact = NA_VALUE
    doc.name_of_injured_person = NA_VALUE
    doc.name_of_affected_person = NA_VALUE
    doc.position_of_employee = NA_VALUE
    doc.years_in_current_position = NA_VALUE
    doc.potential_severity_classification = NA_VALUE
    doc.repeat_incident = NA_VALUE
    doc.life_saving_rule = NA_VALUE

    # These must stay blank
    if hasattr(doc, "immediate_causes"):
        doc.immediate_causes = ""
    if hasattr(doc, "basic_causes"):
        doc.basic_causes = ""
    if hasattr(doc, "system_and_control_failures"):
        doc.system_and_control_failures = ""
    if hasattr(doc, "comment"):
        doc.comment = ""
    if hasattr(doc, "comments"):
        doc.comments = ""
    if hasattr(doc, "disclaimer"):
        doc.disclaimer = ""


def get_first_injured_row(incident):
    rows = getattr(incident, "injured_detail", []) or []
    for row in rows:
        if safe_strip(getattr(row, "injured_person_name", None)):
            return row
    return None


def get_first_damage_row(incident):
    rows = getattr(incident, "responsible_for_damages", []) or []
    for row in rows:
        if safe_strip(getattr(row, "damages_by_full_name", None)):
            return row
    return None


def join_child_link_values(rows, value_fieldname):
    rows = rows or []
    values = []

    for row in rows:
        value = safe_strip(getattr(row, value_fieldname, None))
        if value and value not in values:
            values.append(value)

    return ", ".join(values)


def get_repeat_incident_value(incident):
    values = []

    if cint_safe(getattr(incident, "has_happened", 0)):
        values.append("Has Happened")

    if cint_safe(getattr(incident, "first_known_case", 0)):
        values.append("First Known Case")

    return ", ".join(values)


def with_na(value):
    value = safe_strip(value)
    return value if value else NA_VALUE


def safe_strip(value):
    if value is None:
        return ""
    return str(value).strip()


def cint_safe(value):
    try:
        return int(value or 0)
    except Exception:
        return 0