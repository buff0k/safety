# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


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
    doc.nature_of_injury = join_child_link_values(
        getattr(incident, "nature_of_the_injury", []),
        "nature_of_injury"
    )

    # Nature of Damage -> type_of_damage child table -> specify_type_of_damage
    doc.nature_of_damage = join_child_link_values(
        getattr(incident, "type_of_damage", []),
        "specify_type_of_damage"
    )

    # Nature of Environmental Impact -> description only if type_of_impact contains Environmental Impact
    doc.nature_of_environmental_impact = get_environmental_impact_description(incident)

    # Name of Injured Person -> Responsible Person child table -> injured_person_name
    doc.name_of_injured_person = safe_strip(
        getattr(injured_row, "injured_person_name", None)
    )

    # Name of Affected Person -> Person Responsible for Damages child table -> damages_by_full_name
    doc.name_of_affected_person = safe_strip(
        getattr(damage_row, "damages_by_full_name", None)
    )

    # Position of Employee
    # Rule given:
    # - if injured_person_name has a value -> position_of_injured
    # - if damages_by_full_name has a value -> damages_caused_by_position
    # Implemented with injury first, then damage if injury blank.
    doc.position_of_employee = (
        safe_strip(getattr(injured_row, "position_of_injured", None))
        or safe_strip(getattr(damage_row, "damages_caused_by_position", None))
        or ""
    )

    # Years in Current Position
    # Rule given:
    # - if damages_by_full_name has a value -> damages_caused_by_years_in_current_position
    # - if injured_person_name has a value -> years_in_current_position
    # Implemented with damage first, then injury if damage blank.
    doc.years_in_current_position = (
        safe_strip(getattr(damage_row, "damages_caused_by_years_in_current_position", None))
        or safe_strip(getattr(injured_row, "years_in_current_position", None))
        or ""
    )

    # Potential Severity Classification -> select_severity child table -> classify
    doc.potential_severity_classification = join_child_link_values(
        getattr(incident, "select_severity", []),
        "classify"
    )

    # Repeat Incident -> checkboxes in Incident Report
    doc.repeat_incident = get_repeat_incident_value(incident)

    # Life Saving Rule -> life_save_rule child table -> specify_life_saving_rule
    doc.life_saving_rule = join_child_link_values(
        getattr(incident, "life_save_rule", []),
        "specify_life_saving_rule"
    )

    # Not mapped yet from your instructions, so left unchanged:
    # doc.photos_and_attachments
    # doc.immediate_causes
    # doc.basic_causes
    # doc.system_and_control_failures


def clear_auto_mapped_fields(doc):
    doc.nature_of_injury = ""
    doc.nature_of_damage = ""
    doc.nature_of_environmental_impact = ""
    doc.name_of_injured_person = ""
    doc.name_of_affected_person = ""
    doc.position_of_employee = ""
    doc.years_in_current_position = ""
    doc.potential_severity_classification = ""
    doc.repeat_incident = ""
    doc.life_saving_rule = ""


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


def get_environmental_impact_description(incident):
    impact_rows = getattr(incident, "type_of_impact", []) or []

    for row in impact_rows:
        impact_value = safe_strip(getattr(row, "describe_type_of_impact", None))
        if impact_value and impact_value.strip().lower() == "environmental impact":
            return safe_strip(getattr(incident, "description", None))

    return ""


def get_repeat_incident_value(incident):
    values = []

    if cint_safe(getattr(incident, "has_happened", 0)):
        values.append("Has Happened")

    if cint_safe(getattr(incident, "first_known_case", 0)):
        values.append("First Known Case")

    return ", ".join(values)


def safe_strip(value):
    if value is None:
        return ""
    return str(value).strip()


def cint_safe(value):
    try:
        return int(value or 0)
    except Exception:
        return 0