import frappe
from frappe.model.document import Document
from frappe.utils import get_url, now


class FlashReports(Document):

    def validate(self):
        self.set_photo_timestamps()

    def set_photo_timestamps(self):
        for row in self.get("photos_and_attachments", []):
            if row.photos_and_attachments and not row.date_and_time_of_photo:
                row.date_and_time_of_photo = now()


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
def _first_non_empty(row, fieldnames):
    if not row:
        return None

    for fieldname in fieldnames:
        value = row.get(fieldname)
        if value not in (None, "", []):
            return value

    return None


def _extract_table_multiselect_values(doc, table_fieldname):
    """
    Generic reader for Table MultiSelect / child table rows.
    Returns a list of readable values from each row.
    """
    rows = doc.get(table_fieldname) or []
    values = []

    system_fields = {
        "name", "owner", "creation", "modified", "modified_by",
        "parent", "parentfield", "parenttype", "idx", "docstatus"
    }

    for row in rows:
        row_dict = row.as_dict() if hasattr(row, "as_dict") else dict(row)

        picked = None

        # Prefer obvious label/value style fields first
        preferred_fields = [
            "incident_type",
            "severity",
            "life_saving_rule",
            "body_part",
            "nature_of_injury",
            "type_of_damage",
            "task",
            "description",
            "title",
            "name1",
            "value",
            "item",
            "type"
        ]

        for field in preferred_fields:
            if row_dict.get(field) not in (None, "", []):
                picked = row_dict.get(field)
                break

        # Otherwise pick the first meaningful scalar field
        if picked is None:
            for key, val in row_dict.items():
                if key in system_fields:
                    continue
                if isinstance(val, (str, int, float)) and val not in ("", None):
                    picked = val
                    break

        if picked not in (None, ""):
            values.append(str(picked))

    # remove duplicates while preserving order
    seen = set()
    clean_values = []
    for value in values:
        if value not in seen:
            seen.add(value)
            clean_values.append(value)

    return clean_values


def _join_table_multiselect(doc, table_fieldname):
    return ", ".join(_extract_table_multiselect_values(doc, table_fieldname))


# ------------------------------------------------------------------
# LINK FIELD QUERY — FILTER INCIDENT NUMBER
# ------------------------------------------------------------------
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def incident_link_query(doctype, txt, searchfield, start, page_len, filters):
    action_category = (filters or {}).get("action_category")

    conditions = ["docstatus < 2"]
    values = {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    }

    # New Incident Report uses event_category
    if action_category:
        conditions.append("event_category = %(action_category)s")
        values["action_category"] = action_category

    where_clause = " AND ".join(conditions)

    return frappe.db.sql(
        f"""
        SELECT
            name,
            COALESCE(incident_number, name) AS incident_number
        FROM `tabIncident Report`
        WHERE {where_clause}
          AND (
              name LIKE %(txt)s
              OR incident_number LIKE %(txt)s
          )
        ORDER BY creation DESC
        LIMIT %(start)s, %(page_len)s
        """,
        values
    )


# ------------------------------------------------------------------
# FETCH INCIDENT DATA FROM INCIDENT REPORT
# ------------------------------------------------------------------
@frappe.whitelist()
def get_flash_report_data(incident_number):
    ir = frappe.get_doc("Incident Report", incident_number)

    # ---------------- INCIDENT CLASSIFICATION ----------------
    incident_classification = _join_table_multiselect(ir, "select_type_of_incident")

    # ---------------- POTENTIAL SEVERITY ----------------
    potential_severity = _join_table_multiselect(ir, "select_severity")

    # ---------------- REPEAT INCIDENT ----------------
    repeat_values = []
    if ir.get("has_happened"):
        repeat_values.append("Has Happened")
    if ir.get("first_known_case"):
        repeat_values.append("First Known Case")
    repeat_incident = ", ".join(repeat_values)

    # ---------------- LIFE SAVING RULES ----------------
    life_saving_rules = _join_table_multiselect(ir, "life_save_rule")

    # ---------------- INJURED PERSON ----------------
    injured_name = injured_position = injured_years = None
    if ir.get("injured_detail"):
        row = ir.get("injured_detail")[0]
        injured_name = _first_non_empty(row, [
            "injured_person_name",
            "name_of_person",
            "employee_name",
            "full_name",
            "person_name",
            "responsible_person_name"
        ])
        injured_position = _first_non_empty(row, [
            "position_of_injured",
            "position",
            "designation"
        ])
        injured_years = _first_non_empty(row, [
            "years_in_current_position",
            "years_in_position",
            "years"
        ])

    # ---------------- RESPONSIBLE PERSON ----------------
    damage_name = damage_position = damage_years = None
    if ir.get("responsible_for_damages"):
        row = ir.get("responsible_for_damages")[0]
        damage_name = _first_non_empty(row, [
            "damages_by_full_name",
            "responsible_person_name",
            "employee_name",
            "full_name",
            "person_name"
        ])
        damage_position = _first_non_empty(row, [
            "damages_caused_by_position",
            "position_of_person_responsible",
            "position",
            "designation"
        ])
        damage_years = _first_non_empty(row, [
            "damages_caused_by_years_in_current_position",
            "years_in_position",
            "years_in_current_position",
            "years"
        ])

    # ---------------- EQUIPMENT ----------------
    equipment_id = serial_number = registration_number = make = None
    if ir.get("equipment_details"):
        row = ir.get("equipment_details")[0]
        equipment_id = _first_non_empty(row, [
            "equipment_id",
            "equipment",
            "equipment_number",
            "equipment_name"
        ])
        serial_number = _first_non_empty(row, [
            "serial_number",
            "serial_no"
        ])
        registration_number = _first_non_empty(row, [
            "registration_number_if_applicable",
            "registration_number",
            "registration_no"
        ])
        make = _first_non_empty(row, [
            "make",
            "manufacturer"
        ])

    # ---------------- NATURE ----------------
    nature_parts = []

    if ir.get("incident_type"):
        nature_parts.append(str(ir.get("incident_type")))

    injury_nature = _join_table_multiselect(ir, "nature_of_the_injury")
    if injury_nature:
        nature_parts.append(injury_nature)

    damage_type = _join_table_multiselect(ir, "type_of_damage")
    if damage_type:
        nature_parts.append(damage_type)

    nature = ", ".join([x for x in nature_parts if x])

    # ---------------- EMPLOYER DISPLAY ----------------
    employer_display = ir.get("company") or ir.get("employer")

    # ---------------- DESCRIPTION ----------------
    description_of_incident_impact = (
        ir.get("description")
        or ir.get("description_of_the_event")
    )

    return {
        "incident_classification": incident_classification,
        "date_and_time_of_incident": ir.get("datetime_incident"),
        "nature": nature,
        "site": ir.get("site"),
        "occurence": ir.get("location_on_site"),
        "description_of_incident_impact": description_of_incident_impact,

        "name_of_person": injured_name,
        "position": injured_position,
        "years_in_current_position": injured_years,

        "responsible_person_name": damage_name,
        "position_of_person_responsible": damage_position,
        "years_in_position": damage_years,

        "name_of_employer": employer_display,
        "potential_severity_classification": potential_severity,
        "repeat_incident": repeat_incident,
        "applicable_life_saving_rule": life_saving_rules,

        "equipment_id": equipment_id,
        "serial_number": serial_number,
        "registration_number": registration_number,
        "make": make
    }


# ------------------------------------------------------------------
# BUILD FLASH REPORT HTML
# ------------------------------------------------------------------
@frappe.whitelist()
def build_flash_html(data):
    d = frappe.parse_json(data)
    logo_url = get_url("/files/isambane_logo.png")

    image_urls = []
    for row in d.get("photos_and_attachments", []):
        if row.get("photos_and_attachments"):
            image_urls.append(get_url(row.get("photos_and_attachments")))

    photo_html = ""
    if image_urls:
        imgs = "".join(
            f'<img src="{url}" style="max-width:90%;max-height:500px;border:1px solid #999;margin:10px;">'
            for url in image_urls
        )

        photo_html = f"""
            <hr>
            <h3 style="text-align:center;margin-top:20px;">
                Incident Photos / Attachments
            </h3>
            <div style="text-align:center;">{imgs}</div>
        """

    return f"""
    <div style="padding:10px;border:1px solid #ccc;">
        <img src="{logo_url}" style="max-height:60px;">
        {photo_html}
    </div>
    """


# ------------------------------------------------------------------
# SEND FLASH REPORT
# ------------------------------------------------------------------
@frappe.whitelist()
def send_flash_report(name):
    doc = frappe.get_doc("Flash Reports", name)

    if doc.flash_sent:
        frappe.throw("Flash Report has already been sent.")

    frappe.sendmail(
        recipients=["hse@isambane.co.za", "site.manager@isambane.co.za"],
        subject=f"FLASH REPORT – Incident {doc.incident_number}",
        message=doc.flash,
        now=True
    )

    doc.flash_sent = 1
    doc.flash_sent_on = now()
    doc.save(ignore_permissions=True)

    return True