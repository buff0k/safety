frappe.ui.form.on("Flash Reports", {

    // ------------------------------------------------
    // FILTER INCIDENT NUMBER
    // ------------------------------------------------
    action_category(frm) {
        frm.set_value("incident_number", null);

        if (!frm.doc.action_category) return;

        frm.set_query("incident_number", () => {
            return {
                query: "safety.safety.doctype.flash_reports.flash_reports.incident_link_query",
                filters: {
                    action_category: frm.doc.action_category
                }
            };
        });
    },

    // ------------------------------------------------
    // FETCH INCIDENT DATA
    // ------------------------------------------------
    incident_number(frm) {
        if (!frm.doc.incident_number) return;

        frappe.call({
            method: "safety.safety.doctype.flash_reports.flash_reports.get_flash_report_data",
            args: {
                incident_number: frm.doc.incident_number
            },
            callback(r) {
                if (!r.message) {
                    frappe.msgprint("No matching Incident Management record found.");
                    return;
                }

                const d = r.message;

                frm.set_value("incident_classification", d.incident_classification);
                frm.set_value("date_and_time_of_incident", d.date_and_time_of_incident);
                frm.set_value("nature", d.nature);
                frm.set_value("site", d.site);
                frm.set_value("occurence", d.occurence);
                frm.set_value("description_of_incident_impact", d.description_of_incident_impact);

                frm.set_value("name_of_person", d.name_of_person);
                frm.set_value("position", d.position);
                frm.set_value("years_in_current_position", d.years_in_current_position);

                frm.set_value("responsible_person_name", d.responsible_person_name);
                frm.set_value("position_of_person_responsible", d.position_of_person_responsible);
                frm.set_value("years_in_position", d.years_in_position);

                frm.set_value("name_of_employer", d.name_of_employer);
                frm.set_value("potential_severity_classification", d.potential_severity_classification);
                frm.set_value("repeat_incident", d.repeat_incident);
                frm.set_value("applicable_life_saving_rule", d.applicable_life_saving_rule);

                // ✅ EQUIPMENT POPULATES NOW
                frm.set_value("equipment_id", d.equipment_id);
                frm.set_value("serial_number", d.serial_number);
                frm.set_value("registration_number", d.registration_number);
                frm.set_value("make", d.make);

                frm.refresh_fields();
                build_flash_html(frm);
            }
        });
    },

    photos_and_attachments(frm) {
        if (!frm.is_new()) {
            build_flash_html(frm);
        }
    },

    refresh(frm) {
        if (!frm.is_new() && !frm.doc.flash_sent) {
            frm.add_custom_button("Send Flash Report", () => {
                frappe.call({
                    method: "safety.safety.doctype.flash_reports.flash_reports.send_flash_report",
                    args: { name: frm.doc.name },
                    freeze: true,
                    callback() {
                        frappe.msgprint("Flash Report sent successfully.");
                        frm.reload_doc();
                    }
                });
            });
        }

        if (!frm.is_new()) {
            build_flash_html(frm);
        }
    }
});

function build_flash_html(frm) {
    frappe.call({
        method: "safety.safety.doctype.flash_reports.flash_reports.build_flash_html",
        args: {
            data: frm.doc
        },
        callback(r) {
            if (r.message) {
                frm.fields_dict.flash.$wrapper.html(r.message);
            }
        }
    });
}
// =====================================================
// INCIDENT PHOTOS – AUTO POPULATE DATE & TIME
// =====================================================

frappe.ui.form.on("Incident Photos", {
    photos_and_attachments(frm, cdt, cdn) {

        const row = locals[cdt][cdn];

        // Only set if attachment exists and date not already set
        if (row.photos_and_attachments && !row.date_and_time_of_photo) {
            frappe.model.set_value(
                cdt,
                cdn,
                "date_and_time_of_photo",
                frappe.datetime.now_datetime()
            );
        }
    }
});
