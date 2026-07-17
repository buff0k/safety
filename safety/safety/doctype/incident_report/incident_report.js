// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Incident Report", {
    event_category(frm) {
        if (!frm.doc.incident_number) {
            generate_incident_number(frm);
        }
    },

    datetime_incident(frm) {
        if (!frm.doc.incident_number) {
            generate_incident_number(frm);
        }
    },

    hazard_consequence(frm) {
        calculate_risk_rating(frm);
        populate_impact_description(frm);
    },

    likelyhood(frm) {
        calculate_risk_rating(frm);
    },

    type_of_impact(frm) {
        populate_impact_description(frm);
    },

    specify_type(frm) {
        toggle_investigation_attachments(frm);
    },

    is_the_investigation_required(frm) {
        toggle_investigation_decision_fields(frm);
    },

    refresh(frm) {
        calculate_risk_rating(frm);
        apply_risk_level_style(frm);
        populate_impact_description(frm);
        toggle_investigation_attachments(frm);
        toggle_investigation_decision_fields(frm);
        add_related_record_buttons(frm);
        render_related_safety_records(frm);
    },

    validate(frm) {
        validate_preliminary_investigation_rows(frm);
    },
});

function add_related_record_buttons(frm) {
    if (frm.is_new()) {
        return;
    }

    frm.add_custom_button(
        __("Flash Report"),
        () => create_flash_report(frm),
        __("Create")
    );

    if (frm.doc.is_the_investigation_required === "Yes") {
        frm.add_custom_button(
            __("Incident Investigation"),
            () => create_incident_investigation(frm),
            __("Create")
        );
    }
}

function create_flash_report(frm) {
    frappe.call({
        method: "safety.safety.doctype.incident_report.incident_report.make_flash_report",
        args: { incident_report: frm.doc.name },
        freeze: true,
        freeze_message: __("Preparing Flash Report..."),
        callback(r) {
            if (!r.message) {
                return;
            }

            const doc = frappe.model.sync(r.message)[0];
            frappe.set_route("Form", doc.doctype, doc.name);
        },
    });
}

function create_incident_investigation(frm) {
    frappe.call({
        method: "safety.safety.doctype.incident_report.incident_report.make_incident_investigation",
        args: { incident_report: frm.doc.name },
        freeze: true,
        freeze_message: __("Preparing Incident Investigation..."),
        callback(r) {
            if (!r.message) {
                return;
            }

            if (r.message.existing) {
                frappe.set_route(
                    "Form",
                    "Incident Investigation",
                    r.message.existing
                );
                return;
            }

            const doc = frappe.model.sync(r.message)[0];
            frappe.set_route("Form", doc.doctype, doc.name);
        },
    });
}

function render_related_safety_records(frm) {
    const field = frm.get_field("related_safety_records_html");

    if (!field || frm.is_new()) {
        return;
    }

    field.$wrapper.html(
        `<div class="text-muted">${__("Loading related records...")}</div>`
    );

    frappe.call({
        method: "safety.safety.doctype.incident_report.incident_report.get_related_safety_records",
        args: { incident_report: frm.doc.name },
        callback(r) {
            const data = r.message || {};
            field.$wrapper.html(
                render_record_table(
                    __("Flash Reports"),
                    "Flash Reports",
                    data.flash_reports || [],
                    (row) => frappe.datetime.str_to_user(row.creation)
                ) +
                render_record_table(
                    __("Incident Investigations"),
                    "Incident Investigation",
                    data.investigations || [],
                    (row) => [
                        row.investigation_type,
                        row.investigation_kind,
                        row.workflow_state || __("Draft"),
                    ].filter(Boolean).join(" · ")
                )
            );
        },
    });
}

function render_record_table(title, doctype, rows, detail_callback) {
    let body = "";

    if (!rows.length) {
        body = `<tr><td colspan="2" class="text-muted">${__("No records")}</td></tr>`;
    } else {
        body = rows.map((row) => {
            const route = frappe.utils.get_form_link(doctype, row.name);
            const name = frappe.utils.escape_html(row.name);
            const detail = frappe.utils.escape_html(detail_callback(row) || "");
            return `<tr><td><a href="${route}">${name}</a></td><td>${detail}</td></tr>`;
        }).join("");
    }

    return `
        <div class="mb-4">
            <h5>${frappe.utils.escape_html(title)}
                <span class="badge badge-light">${rows.length}</span>
            </h5>
            <table class="table table-bordered table-sm">
                <tbody>${body}</tbody>
            </table>
        </div>
    `;
}

function toggle_investigation_decision_fields(frm) {
    const required = frm.doc.is_the_investigation_required === "Yes";
    const not_required = frm.doc.is_the_investigation_required === "No";

    frm.toggle_display("investigation_type", required);
    frm.toggle_reqd("investigation_type", required);
    frm.toggle_display("investigation_not_required_reason", not_required);
    frm.toggle_reqd("investigation_not_required_reason", not_required);
}

function generate_incident_number(frm) {
    if (!frm.doc.event_category || !frm.doc.datetime_incident) {
        return;
    }

    frappe.call({
        method: "safety.safety.doctype.incident_report.incident_report.get_next_incident_number",
        type: "POST",
        args: {
            event_category: frm.doc.event_category,
            datetime_incident: frm.doc.datetime_incident,
        },
        callback(r) {
            if (r.message) {
                frm.set_value("incident_number", r.message);
            }
        },
    });
}

function calculate_risk_rating(frm) {
    if (!frm.doc.hazard_consequence || !frm.doc.likelyhood) {
        frm.set_value("risk_rating", "");
        frm.set_value("risk_level", "");
        return;
    }

    const consequence = parseInt(frm.doc.hazard_consequence, 10);
    const likelihood = parseInt(frm.doc.likelyhood, 10);
    const matrix = {
        1: { 1: 1, 2: 3, 3: 4, 4: 7, 5: 11 },
        2: { 1: 3, 2: 5, 3: 8, 4: null, 5: 16 },
        3: { 1: 6, 2: 9, 3: 13, 4: 17, 5: 20 },
        4: { 1: 10, 2: 14, 3: 18, 4: 21, 5: 23 },
        5: { 1: 15, 2: 19, 3: 22, 4: 24, 5: 25 },
    };

    const rating = matrix[consequence]?.[likelihood] ?? "";
    frm.set_value("risk_rating", rating);

    if (rating >= 21) {
        frm.set_value("risk_level", "Extreme");
    } else if (rating >= 13) {
        frm.set_value("risk_level", "High");
    } else if (rating >= 6) {
        frm.set_value("risk_level", "Medium");
    } else if (rating >= 1) {
        frm.set_value("risk_level", "Low");
    } else {
        frm.set_value("risk_level", "");
    }

    apply_risk_level_style(frm);
}

function apply_risk_level_style(frm) {
    const field = frm.get_field("risk_level");
    if (!field) {
        return;
    }

    const input = field.$wrapper.find("input");
    if (!input.length) {
        return;
    }

    input.css({ color: "", fontWeight: "" });

    const colours = {
        Extreme: "red",
        High: "orange",
        Medium: "#d4aa00",
        Low: "green",
    };

    const colour = colours[frm.doc.risk_level];
    if (colour) {
        input.css({ color: colour, fontWeight: "bold" });
    }
}

function toggle_investigation_attachments(frm) {
    const fields = ["five_why", "fishbone", "icam"];
    const selected = {
        "5 Why": "five_why",
        Fishbone: "fishbone",
        ICAM: "icam",
    }[frm.doc.specify_type];

    fields.forEach((fieldname) => {
        frm.set_df_property(fieldname, "hidden", fieldname !== selected);
    });
}

function populate_impact_description(frm) {
    if (!frm.doc.hazard_consequence) {
        frm.set_value("description", "");
        return;
    }

    const consequence = parseInt(frm.doc.hazard_consequence, 10);
    const selected_impacts = get_table_values(frm.doc.type_of_impact || []);
    const descriptions = [];

    selected_impacts.forEach((impact) => {
        const key = String(impact || "").trim().toLowerCase();
        let values = null;

        if (key.includes("harm to people") || key.includes("safety") || key.includes("health")) {
            values = {
                1: "First aid case / Exposure to minor health risk",
                2: "Medical treatment case / Exposure to major health risk",
                3: "Lost time injury / Reversible impact on health",
                4: "Single fatality or loss of quality of life / Irreversible impact on health",
                5: "Multiple fatalities / Impact on health ultimately fatal",
            };
        } else if (key.includes("environment")) {
            values = {
                1: "Minimal environmental harm - L1 incident",
                2: "Material environmental harm - L2 incident remediable short term",
                3: "Serious environmental harm - L2 incident remediable within LOM",
                4: "Major environmental harm - L2 incident remediable post LOM",
                5: "Extreme environmental harm - L3 incident irreversible",
            };
        } else if (
            key.includes("business interruption") ||
            key.includes("material damage") ||
            key.includes("other losses")
        ) {
            values = {
                1: "No disruption to operation / US$20k to US$100k",
                2: "Brief disruption to operation / US$100k to US$1.0M",
                3: "Partial shutdown / US$1.0M to US$10.0M",
                4: "Partial loss of operation / US$10M to US$75.0M",
                5: "Substantial or total loss of operation / >US$75.0M",
            };
        } else if (key.includes("legal") || key.includes("regulatory")) {
            values = {
                1: "Low level legal issue",
                2: "Minor legal issue; non compliance and breaches of the law",
                3: "Serious breach of law; investigation/report to authority, prosecution and/or moderate penalty possible",
                4: "Major breach of the law; considerable prosecution and penalties",
                5: "Very considerable penalties & prosecutions. Multiple law suits & jail terms",
            };
        } else if (
            key.includes("community") ||
            key.includes("reputation") ||
            key.includes("social")
        ) {
            values = {
                1: "Slight impact - public awareness may exist but no public concern",
                2: "Limited impact - local public concern",
                3: "Considerable impact - regional public concern",
                4: "National impact - national public concern",
                5: "International impact - international public attention",
            };
        }

        if (values?.[consequence]) {
            descriptions.push(values[consequence]);
        }
    });

    frm.set_value("description", descriptions.join("\n"));
}

function get_table_values(rows) {
    const ignored = new Set([
        "name", "owner", "creation", "modified", "modified_by",
        "parent", "parentfield", "parenttype", "idx", "docstatus", "doctype",
    ]);

    return rows.map((row) => {
        for (const [key, value] of Object.entries(row)) {
            if (ignored.has(key)) {
                continue;
            }
            if (
                typeof value === "string" &&
                value.trim() &&
                !["0", "1"].includes(value.trim())
            ) {
                return value.trim();
            }
        }
        return "";
    }).filter(Boolean);
}

function validate_preliminary_investigation_rows(frm) {
    const errors = [];

    (frm.doc.investigation_type_and_attachments || []).forEach((row, index) => {
        const attachment_fields = (frappe.meta.get_docfields(row.doctype) || [])
            .filter((df) => ["Attach", "Attach Image"].includes(df.fieldtype))
            .map((df) => df.fieldname);

        if (
            attachment_fields.length &&
            !attachment_fields.some((fieldname) => row[fieldname])
        ) {
            errors.push(
                __("Please upload at least one attachment in row {0}.", [index + 1])
            );
        }
    });

    if (errors.length) {
        frappe.throw({
            title: __("Missing Attachments"),
            message: errors.join("<br>"),
        });
    }
}

frappe.ui.form.on("Responsible Person", {
    injured_id(frm, cdt, cdn) {
        calculate_child_age(cdt, cdn, "injured_id", "age_of_injured");
    },
});

frappe.ui.form.on("Person Responsible for Damages", {
    damages_caused_by_id(frm, cdt, cdn) {
        calculate_child_age(
            cdt,
            cdn,
            "damages_caused_by_id",
            "damages_caused_by_age"
        );
    },
});

function calculate_child_age(cdt, cdn, source_field, target_field) {
    const row = locals[cdt][cdn];
    const value = String(row[source_field] || "").trim();

    if (!value) {
        frappe.model.set_value(cdt, cdn, target_field, "");
        return;
    }

    const dob = extract_date_of_birth(value);
    if (!dob) {
        frappe.model.set_value(cdt, cdn, target_field, "");
        return;
    }

    const today = new Date();
    let years = today.getFullYear() - dob.getFullYear();
    let months = today.getMonth() - dob.getMonth();

    if (today.getDate() < dob.getDate()) {
        months -= 1;
    }

    if (months < 0) {
        years -= 1;
        months += 12;
    }

    frappe.model.set_value(
        cdt,
        cdn,
        target_field,
        `${years} years ${months} months`
    );
}

function extract_date_of_birth(value) {
    if (/^\d{6,}$/.test(value)) {
        const yy = parseInt(value.slice(0, 2), 10);
        const mm = parseInt(value.slice(2, 4), 10) - 1;
        const dd = parseInt(value.slice(4, 6), 10);
        const today = new Date();
        const current_yy = today.getFullYear() % 100;
        const year = yy > current_yy ? 1900 + yy : 2000 + yy;
        const result = new Date(year, mm, dd);

        if (
            result.getFullYear() === year &&
            result.getMonth() === mm &&
            result.getDate() === dd
        ) {
            return result;
        }
    }

    const result = new Date(value);
    return Number.isNaN(result.getTime()) ? null : result;
}
