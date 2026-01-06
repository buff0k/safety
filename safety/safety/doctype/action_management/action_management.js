frappe.ui.form.on("Action Management", {
    onload(frm) {
        // Always show both fields
        frm.toggle_display("action_category", true);
        frm.toggle_display("incident_number", true);

        set_incident_query(frm);

        // 🔒 Enforce overdue rule when form loads
        enforce_overdue_status(frm);
    },

    reactive_actions_taken(frm) {
        if (frm.doc.reactive_actions_taken) {
            frm.set_value("proactive_actions_taken", 0);
            frm.set_value("action_number", null);
        }
    },

    proactive_actions_taken(frm) {
        if (frm.doc.proactive_actions_taken) {
            frm.set_value("reactive_actions_taken", 0);
            frm.set_value("action_number", null);
        }
    },

    action_category(frm) {
        frm.set_value("incident_number", null);
        frm.set_value("action_number", null);
        set_incident_query(frm);

        if (frm.doc.proactive_actions_taken && frm.doc.action_category) {
            frappe.call({
                method:
                    "safety.safety.doctype.action_management.action_management.get_next_action_number",
                args: {
                    action_category: frm.doc.action_category
                },
                callback(r) {
                    if (r.message !== undefined) {
                        frm.set_value("action_number", r.message);
                    }
                }
            });
        }
    },

    incident_number(frm) {
        if (!frm.doc.incident_number) return;

        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Incident Management",
                name: frm.doc.incident_number
            },
            callback(r) {
                if (!r.message) return;

                const inc = r.message;

                if (inc.datetime_incident) {
                    const date = inc.datetime_incident.split(" ")[0];
                    frm.set_value("date", date);
                    set_month_from_date(frm, date);
                }

                frm.set_value("site", inc.site || null);
                frm.set_value("non_conformance", inc.event_category || null);
                frm.set_value("select_area", inc.location_on_site || null);

                reset_departments(frm);

                if (inc.departmentx) {
                    tick_departments(frm, inc.departmentx);
                }
            }
        });

        if (frm.doc.reactive_actions_taken) {
            frappe.call({
                method:
                    "safety.safety.doctype.action_management.action_management.get_next_action_number",
                args: {
                    incident_number: frm.doc.incident_number
                },
                callback(r) {
                    if (r.message !== undefined) {
                        frm.set_value("action_number", r.message);
                    }
                }
            });
        }
    },

    date(frm) {
        if (frm.doc.date) {
            set_month_from_date(frm, frm.doc.date);
        }
    },

    // 🔒 NEW: check overdue whenever target_date changes
    target_date(frm) {
        enforce_overdue_status(frm);
    }
});

/* ---------------- Helper Functions ---------------- */

function enforce_overdue_status(frm) {
    if (!frm.doc.target_date) return;

    const today = frappe.datetime.get_today();
    const target_date = frm.doc.target_date;

    const COMPLETE_STATUS =
        "Complete: Action have been closed and Non-Conformance rectified";

    if (today > target_date && frm.doc.status !== COMPLETE_STATUS) {
        frm.set_value("status", "Overdue");
    }
}

function set_incident_query(frm) {
    frm.set_query("incident_number", function () {
        if (!frm.doc.action_category) return {};

        const category_map = {
            "Incident (INC)": "INC",
            "Inspection (INS)": "INS",
            "Planned Task Observation (PTO)": "PTO",
            "Visible Field Leadership (VFL)": "VFL",
            "Audits (AUD)": "AUD"
        };

        const code = category_map[frm.doc.action_category];
        if (!code) return {};

        return {
            filters: [["Incident Management", "name", "like", `%${code}%`]]
        };
    });
}

function set_month_from_date(frm, date_str) {
    const month = frappe.datetime
        .str_to_obj(date_str)
        .toLocaleString("default", { month: "long" });
    frm.set_value("month", month);
}

function reset_departments(frm) {
    frm.set_value("engineering", 0);
    frm.set_value("drill_and_blast", 0);
    frm.set_value("mining", 0);
    frm.set_value("safety", 0);
    frm.set_value("other_department", null);
}

function tick_departments(frm, departmentx) {
    const map = {
        Engineering: "engineering",
        "Drill and Blast": "drill_and_blast",
        Mining: "mining",
        Safety: "safety"
    };

    if (map[departmentx]) {
        frm.set_value(map[departmentx], 1);
    } else {
        frm.set_value("other_department", departmentx);
    }
}
