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
# LINK FIELD QUERY — FILTER INCIDENT NUMBER
# ------------------------------------------------------------------
@frappe.whitelist()
def incident_link_query(doctype, txt, searchfield, start, page_len, filters):
    action_category = filters.get("action_category")

    prefix_map = {
        "Incident (INC)": "IS/INC/",
        "Inspection (INS)": "IS/INS/",
        "Planned Task Observation (PTO)": "IS/PTO/",
        "Visible Field Leadership (VFL)": "IS/VFL/",
        "Audits (AUD)": "IS/AUD/"
    }

    prefix = prefix_map.get(action_category)
    if not prefix:
        return []

    return frappe.db.sql(
        """
        SELECT name, name
        FROM `tabIncident Management`
        WHERE name LIKE %(prefix)s
          AND name LIKE %(txt)s
        ORDER BY modified DESC
        LIMIT %(start)s, %(page_len)s
        """,
        {
            "prefix": f"{prefix}%",
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        }
    )


# ------------------------------------------------------------------
# FETCH INCIDENT DATA (FIXED EQUIPMENT CHILD TABLE)
# ------------------------------------------------------------------
@frappe.whitelist()
def get_flash_report_data(incident_number):
    im = frappe.get_doc("Incident Management", incident_number)

    # ---------------- INCIDENT CLASSIFICATION ----------------
    type_map = {
        "tmm": "TMM",
        "property_damage": "Property Damage",
        "fatality": "Fatality",
        "lti": "LTI",
        "medical_treatment_case": "MTC",
        "first_aid_case": "FAC"
    }

    incident_classification = ", ".join(
        label for field, label in type_map.items() if im.get(field)
    )

    severity_map = {"high": "High", "medium": "Medium", "low": "Low"}
    potential_severity = ", ".join(
        label for field, label in severity_map.items() if im.get(field)
    )

    repeat_map = {
        "has_happened": "Has Happened",
        "first_known_case": "First Known Case"
    }

    repeat_incident = ", ".join(
        label for field, label in repeat_map.items() if im.get(field)
    )

    life_saving_rules_map = {
        "drugs_alcohol": "No Alcohol or Drugs",
        "wear_your_ppe": "Wear Your PPE",
        "safety_belt": "Safety Belt",
        "competent_and_licensed": "Competent and Licensed"
    }

    life_saving_rules = ", ".join(
        label for field, label in life_saving_rules_map.items() if im.get(field)
    )

    # ---------------- INJURED PERSON ----------------
    injured_name = injured_position = injured_years = None
    if im.get("injury_details"):
        row = im.injury_details[0]
        injured_name = row.injured_person_name
        injured_position = row.position_of_injured
        injured_years = row.years_in_current_position

    # ---------------- RESPONSIBLE PERSON ----------------
    damage_name = damage_position = damage_years = None
    if im.get("damage_details"):
        row = im.damage_details[0]
        damage_name = row.damages_by_full_name
        damage_position = row.damages_caused_by_position
        damage_years = row.damages_caused_by_years_in_current_position

    # ---------------- EQUIPMENT (✅ FIXED) ----------------
    equipment_id = serial_number = registration_number = make = None

    if im.get("equipment_details"):
        row = im.equipment_details[0]
        equipment_id = row.equipment_id
        serial_number = row.serial_number
        registration_number = row.registration_number_if_applicable
        make = row.make

    return {
        "incident_classification": incident_classification,
        "date_and_time_of_incident": im.datetime_incident,
        "nature": incident_classification,
        "site": im.site,
        "occurence": im.location_on_site,
        "description_of_incident_impact": im.description_of_the_event,

        "name_of_person": injured_name,
        "position": injured_position,
        "years_in_current_position": injured_years,

        "responsible_person_name": damage_name,
        "position_of_person_responsible": damage_position,
        "years_in_position": damage_years,

        "name_of_employer": im.employer,
        "potential_severity_classification": potential_severity,
        "repeat_incident": repeat_incident,
        "applicable_life_saving_rule": life_saving_rules,

        # EQUIPMENT VALUES
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
