frappe.ui.form.on("Incident Reporting Form", {
    onload(frm) {
        // If already selected (e.g. loaded from draft), populate
        if (frm.doc.select_incident_number) {
            populate_from_incident(frm);
        }
    },

    refresh(frm) {
        // Keep in sync on refresh too
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

function populate_from_incident(frm) {
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Incident Management",
            name: frm.doc.select_incident_number
        },
        callback(r) {
            if (!r.message) return;

            const inc = r.message;

            // ---- Direct mappings ----
            frm.set_value("reporting_name_surname", inc.reporting_person_name || null);
            frm.set_value("reporting_coy_number", inc.reporting_person_coy_number || null);
            frm.set_value("responsible_manager_isambane", inc.responsible_supervisor_name || null);
            frm.set_value("description_of_incident", inc.description_of_the_event || null);

            // Helpful mapping for "Where did the incident happen"
            frm.set_value("where_did_the_incident_happen", inc.location_on_site || null);

            // datetime_incident -> date_of_incident (your field is Data, so store as string)
            if (inc.datetime_incident) {
                // keeps full datetime string if present
                frm.set_value("date_of_incident", String(inc.datetime_incident));
            } else {
                frm.set_value("date_of_incident", null);
            }

            // ---- Child table mappings (first usable injury row) ----
            const injuries = inc.injury_details || [];
            const first = injuries.find(row =>
                row.injured_person_name || row.injured_person_coy_number
            );

            if (first) {
                frm.set_value("injured_name_and_surname", first.injured_person_name || null);
                frm.set_value("injured_person_coy_number", first.injured_person_coy_number || null);
            } else {
                frm.set_value("injured_name_and_surname", null);
                frm.set_value("injured_person_coy_number", null);
            }
        }
    });
}

function clear_incident_fields(frm) {
    frm.set_value("reporting_name_surname", null);
    frm.set_value("reporting_coy_number", null);
    frm.set_value("responsible_manager_isambane", null);
    frm.set_value("injured_name_and_surname", null);
    frm.set_value("injured_person_coy_number", null);
    frm.set_value("where_did_the_incident_happen", null);
    frm.set_value("date_of_incident", null);
    frm.set_value("description_of_incident", null);
}