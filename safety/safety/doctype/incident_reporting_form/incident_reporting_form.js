frappe.ui.form.on("Incident Reporting Form", {
    onload(frm) {
        if (frm.doc.select_incident_number) {
            populate_from_incident(frm);
        }
    },

    refresh(frm) {
        if (frm.doc.select_incident_number) {
            populate_from_incident(frm);
        }
    },

    select_incident_number(frm) {
        if (!frm.doc.select_incident_number) {
            clear_incident_fields(frm);
            return;
        }
        populate_from_incident(frm);
    }
});

function na(value) {
    return (value === undefined || value === null || String(value).trim() === "") ? "N/A" : value;
}

function get_first_usable_row(rows, fields) {
    rows = rows || [];
    return rows.find(row =>
        fields.some(fieldname => row && row[fieldname] && String(row[fieldname]).trim() !== "")
    ) || null;
}

function populate_from_incident(frm) {
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Incident Report",
            name: frm.doc.select_incident_number
        },
        callback(r) {
            if (!r.message) {
                clear_incident_fields(frm);
                return;
            }

            const inc = r.message;

            // ---- Direct mappings ----
            frm.set_value("reporting_name_surname", na(inc.reporting_person_name));
            frm.set_value("reporting_coy_number", na(inc.reporting_person_coy_number));
            frm.set_value("responsible_manager_isambane", na(inc.responsible_supervisor_name));
            frm.set_value("description_of_incident", na(inc.description_of_the_event));
            frm.set_value("where_did_the_incident_happen", na(inc.location_on_site));

            // datetime_incident -> date_of_incident
            frm.set_value("date_of_incident", na(inc.datetime_incident ? String(inc.datetime_incident) : null));

            // ---- Child table mappings: injured_detail / injury_details ----
            const injured_rows = inc.injured_detail || inc.injury_details || [];
            const first_injured = get_first_usable_row(injured_rows, [
                "injured_person_name",
                "injured_person_coy_number"
            ]);

            if (first_injured) {
                frm.set_value("injured_name_and_surname", na(first_injured.injured_person_name));
                frm.set_value("injured_person_coy_number", na(first_injured.injured_person_coy_number));
            } else {
                frm.set_value("injured_name_and_surname", "N/A");
                frm.set_value("injured_person_coy_number", "N/A");
            }

            // ---- Child table mappings: responsible_for_damages ----
            const damage_rows = inc.responsible_for_damages || [];
            const first_damage = get_first_usable_row(damage_rows, [
                "damages_by_full_name",
                "damages_caused_by"
            ]);

            if (first_damage) {
                frm.set_value("involved_name_surname", na(first_damage.damages_by_full_name));
                frm.set_value("involved_person_coy_number", na(first_damage.damages_caused_by));
            } else {
                frm.set_value("involved_name_surname", "N/A");
                frm.set_value("involved_person_coy_number", "N/A");
            }
        },
        error() {
            clear_incident_fields(frm);
            frappe.msgprint({
                title: __("Unable to Load Incident"),
                indicator: "red",
                message: __("Could not load Incident Report {0}. Please confirm the linked record exists and that you have permission to read it.", [frm.doc.select_incident_number])
            });
        }
    });
}

function clear_incident_fields(frm) {
    frm.set_value("reporting_name_surname", null);
    frm.set_value("reporting_coy_number", null);
    frm.set_value("responsible_manager_isambane", null);
    frm.set_value("injured_name_and_surname", null);
    frm.set_value("injured_person_coy_number", null);
    frm.set_value("involved_name_surname", null);
    frm.set_value("involved_person_coy_number", null);
    frm.set_value("where_did_the_incident_happen", null);
    frm.set_value("date_of_incident", null);
    frm.set_value("description_of_incident", null);
}