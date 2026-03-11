frappe.ui.form.on("Incident Report", {
    // --------------------------------------------------
    // INCIDENT NUMBER
    // --------------------------------------------------
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

    // --------------------------------------------------
    // RISK RATING
    // --------------------------------------------------
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

    refresh(frm) {
        calculate_risk_rating(frm);
        apply_risk_level_style(frm);
        populate_impact_description(frm);
        toggle_investigation_attachments(frm);
    },

    specify_type(frm) {
        toggle_investigation_attachments(frm);
    },

    validate(frm) {
        validate_preliminary_investigation_rows(frm);
    }
});


// =====================================================
// INCIDENT NUMBER HELPER
// =====================================================
function generate_incident_number(frm) {
    if (!frm.doc.event_category || !frm.doc.datetime_incident) {
        return;
    }

    frappe.call({
        method: "safety.safety.doctype.incident_report.incident_report.get_next_incident_number",
        args: {
            event_category: frm.doc.event_category,
            datetime_incident: frm.doc.datetime_incident
        },
        callback(r) {
            if (r.message) {
                frm.set_value("incident_number", r.message);
            }
        }
    });
}


// =====================================================
// RISK RATING MATRIX
// =====================================================
function calculate_risk_rating(frm) {
    if (!frm.doc.hazard_consequence || !frm.doc.likelyhood) {
        frm.set_value("risk_rating", "");
        frm.set_value("risk_level", "");
        return;
    }

    const consequence = parseInt(frm.doc.hazard_consequence, 10);
    const likelihood = parseInt(frm.doc.likelyhood, 10);

    const matrix = {
        1: {1: 1, 2: 3, 3: 4, 4: 7, 5: 11},
        2: {1: 3, 2: 5, 3: 8, 4: null, 5: 16},
        3: {1: 6, 2: 9, 3: 13, 4: 17, 5: 20},
        4: {1: 10, 2: 14, 3: 18, 4: 21, 5: 23},
        5: {1: 15, 2: 19, 3: 22, 4: 24, 5: 25}
    };

    const rating = matrix[consequence]?.[likelihood] ?? "";

    frm.set_value("risk_rating", rating);

    if (rating >= 21 && rating <= 25) {
        frm.set_value("risk_level", "Extreme");
    } else if (rating >= 13 && rating <= 20) {
        frm.set_value("risk_level", "High");
    } else if (rating >= 6 && rating <= 12) {
        frm.set_value("risk_level", "Medium");
    } else if (rating >= 1 && rating <= 5) {
        frm.set_value("risk_level", "Low");
    } else {
        frm.set_value("risk_level", "");
    }

    apply_risk_level_style(frm);
}


// =====================================================
// APPLY RISK LEVEL STYLING
// =====================================================
function apply_risk_level_style(frm) {
    const field = frm.get_field("risk_level");
    if (!field) return;

    const input = field.$wrapper.find("input");
    if (!input.length) return;

    input.css({ color: "", fontWeight: "" });

    if (frm.doc.risk_level === "Extreme") {
        input.css({ color: "red", fontWeight: "bold" });
    }

    if (frm.doc.risk_level === "High") {
        input.css({ color: "orange", fontWeight: "bold" });
    }

    if (frm.doc.risk_level === "Medium") {
        input.css({ color: "#d4aa00", fontWeight: "bold" });
    }

    if (frm.doc.risk_level === "Low") {
        input.css({ color: "green", fontWeight: "bold" });
    }
}


// =====================================================
// INVESTIGATION ATTACHMENTS (5 WHY / FISHBONE / ICAM)
// =====================================================
function toggle_investigation_attachments(frm) {
    ["five_why", "fishbone", "icam"].forEach(field => {
        frm.set_df_property(field, "hidden", 1);
        frm.set_value(field, null);
    });

    if (frm.doc.specify_type === "5 Why") {
        frm.set_df_property("five_why", "hidden", 0);
    }

    if (frm.doc.specify_type === "Fishbone") {
        frm.set_df_property("fishbone", "hidden", 0);
    }

    if (frm.doc.specify_type === "ICAM") {
        frm.set_df_property("icam", "hidden", 0);
    }
}


// =====================================================
// IMPACT -> DESCRIPTION POPULATION
// =====================================================
function populate_impact_description(frm) {
    if (!frm.doc.hazard_consequence) {
        frm.set_value("description", "");
        return;
    }

    const consequence = parseInt(frm.doc.hazard_consequence, 10);
    const selected_impacts = get_table_values(frm.doc.type_of_impact || []);
    let descriptions = [];

    selected_impacts.forEach(impact => {
        const key = normalize_text(impact);

        if (key.includes("harm to people") || key.includes("safety") || key.includes("health")) {
            descriptions.push({
                1: "First aid case / Exposure to minor health risk",
                2: "Medical treatment case / Exposure to major health risk",
                3: "Lost time injury / Reversible impact on health",
                4: "Single fatality or loss of quality of life / Irreversible impact on health",
                5: "Multiple fatalities / Impact on health ultimately fatal"
            }[consequence]);
        }

        else if (key.includes("environment")) {
            descriptions.push({
                1: "Minimal environmental harm - L1 incident",
                2: "Material environmental harm - L2 incident remediable short term",
                3: "Serious environmental harm - L2 incident remediable within LOM",
                4: "Major environmental harm - L2 incident remediable post LOM",
                5: "Extreme environmental harm - L3 incident irreversible"
            }[consequence]);
        }

        else if (
            key.includes("business interruption") ||
            key.includes("material damage") ||
            key.includes("other losses")
        ) {
            descriptions.push({
                1: "No disruption to operation / US$20k to US$100k",
                2: "Brief disruption to operation / US$100k to US$1.0M",
                3: "Partial shutdown / US$1.0M to US$10.0M",
                4: "Partial loss of operation / US$10M to US$75.0M",
                5: "Substantial or total loss of operation / >US$75.0M"
            }[consequence]);
        }

        else if (key.includes("legal") || key.includes("regulatory")) {
            descriptions.push({
                1: "Low level legal issue",
                2: "Minor legal issue; non compliance and breaches of the law",
                3: "Serious breach of law; investigation/report to authority, prosecution and/or moderate penalty possible",
                4: "Major breach of the law; considerable prosecution and penalties",
                5: "Very considerable penalties & prosecutions. Multiple law suits & jail terms"
            }[consequence]);
        }

        else if (
            key.includes("community") ||
            key.includes("reputation") ||
            key.includes("social")
        ) {
            descriptions.push({
                1: "Slight impact - public awareness may exist but no public concern",
                2: "Limited impact - local public concern",
                3: "Considerable impact - regional public concern",
                4: "National impact - national public concern",
                5: "International impact - international public attention"
            }[consequence]);
        }
    });

    frm.set_value("description", descriptions.filter(Boolean).join("\n"));
}


// =====================================================
// GENERIC TABLE MULTISELECT VALUE READER
// =====================================================
function get_table_values(rows) {
    const ignore = new Set([
        "name", "owner", "creation", "modified", "modified_by",
        "parent", "parentfield", "parenttype", "idx", "docstatus", "doctype"
    ]);

    return rows.map(row => {
        for (const key in row) {
            if (ignore.has(key)) continue;
            const val = row[key];
            if (
                typeof val === "string" &&
                val.trim() &&
                !["0", "1"].includes(val.trim())
            ) {
                return val.trim();
            }
        }
        return "";
    }).filter(Boolean);
}

function normalize_text(value) {
    return (value || "")
        .toString()
        .trim()
        .toLowerCase();
}


// =====================================================
// CHILD TABLE AGE CALCULATION (UI ONLY)
// SA ID NUMBER VERSION
// =====================================================

// Responsible Person
frappe.ui.form.on("Responsible Person", {
    injured_id(frm, cdt, cdn) {
        calculate_child_age(cdt, cdn, "injured_id", "age_of_injured");
    }
});

// Person Responsible for Damages
frappe.ui.form.on("Person Responsible for Damages", {
    damages_caused_by_id(frm, cdt, cdn) {
        calculate_child_age(cdt, cdn, "damages_caused_by_id", "damages_caused_by_age");
    }
});

function calculate_child_age(cdt, cdn, source_field, target_field) {
    const row = locals[cdt][cdn];
    const rawValue = (row[source_field] || "").toString().trim();

    if (!rawValue) {
        frappe.model.set_value(cdt, cdn, target_field, "");
        return;
    }

    const dob = extract_dob_from_value(rawValue);
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

function extract_dob_from_value(value) {
    value = (value || "").toString().trim();

    // SA ID number
    if (/^\d{6,}$/.test(value)) {
        const yy = parseInt(value.slice(0, 2), 10);
        const mm = parseInt(value.slice(2, 4), 10) - 1;
        const dd = parseInt(value.slice(4, 6), 10);

        const today = new Date();
        const currentYY = today.getFullYear() % 100;
        const fullYear = yy > currentYY ? 1900 + yy : 2000 + yy;

        const dob = new Date(fullYear, mm, dd);

        if (
            dob.getFullYear() === fullYear &&
            dob.getMonth() === mm &&
            dob.getDate() === dd
        ) {
            return dob;
        }
    }

    // Fallback normal date string
    const parsed = new Date(value);
    if (!isNaN(parsed.getTime())) {
        return parsed;
    }

    return null;
}


// =====================================================
// PRELIMINARY INVESTIGATION ROW VALIDATION
// =====================================================
function validate_preliminary_investigation_rows(frm) {
    const rows = frm.doc.investigation_type_and_attachments || [];
    const errors = [];

    rows.forEach((row, index) => {
        const attachment_fields = get_attachment_fields_from_row(row);
        const has_any_attachment = attachment_fields.some(field => row[field]);
        const descriptor = get_row_descriptor(row) || `Row ${index + 1}`;

        if (!has_any_attachment) {
            errors.push(`Please upload at least one attachment for "${descriptor}" in Investigation Type and Attachments row ${index + 1}`);
        }
    });

    if (errors.length) {
        frappe.throw({
            title: __("Missing Attachments"),
            message: errors.join("<br>")
        });
    }
}

function get_attachment_fields_from_row(row) {
    const docfields = frappe.meta.get_docfields(row.doctype) || [];
    return docfields
        .filter(df => ["Attach", "Attach Image"].includes(df.fieldtype))
        .map(df => df.fieldname);
}

function get_row_descriptor(row) {
    const docfields = frappe.meta.get_docfields(row.doctype) || [];
    const ignore = new Set([
        "name", "owner", "creation", "modified", "modified_by",
        "parent", "parentfield", "parenttype", "idx", "docstatus"
    ]);

    for (const df of docfields) {
        if (ignore.has(df.fieldname)) continue;
        if (["Link", "Dynamic Link", "Select", "Data", "Small Text"].includes(df.fieldtype)) {
            const value = row[df.fieldname];
            if (value) return value;
        }
    }

    return row.name || "";
}