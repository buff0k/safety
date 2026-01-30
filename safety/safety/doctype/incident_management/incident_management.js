frappe.ui.form.on("Incident Management", {

    // --------------------------------------------------
    // INCIDENT NUMBER (CATEGORY + DATETIME AWARE)
    // --------------------------------------------------
    event_category(frm) {
        handle_event_category_view(frm);
        toggle_vfl_team_table(frm);

        if (!frm.doc.incident_number) {
            generate_incident_number(frm);
        }
    },

    datetime_incident(frm) {
        if (!frm.doc.incident_number) {
            generate_incident_number(frm);
        }
    },

    site(frm) {
        // site no longer triggers numbering
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

    harm_to_people(frm) {
        populate_impact_description(frm);
        toggle_all_attachments(frm);
    },

    environmental_impact(frm) {
        populate_impact_description(frm);
        toggle_all_attachments(frm);
    },

    business_interruption(frm) {
        populate_impact_description(frm);
        toggle_all_attachments(frm);
    },

    legal_and_regulatory(frm) {
        populate_impact_description(frm);
        toggle_all_attachments(frm);
    },

    impact_on_community(frm) {
        populate_impact_description(frm);
        toggle_all_attachments(frm);
    },

    storyline(frm) { toggle_all_attachments(frm); },
    investigation_report(frm) { toggle_all_attachments(frm); },
    affected_person_statement(frm) { toggle_all_attachments(frm); },
    incident_notification(frm) { toggle_all_attachments(frm); },
    induction_records(frm) { toggle_all_attachments(frm); },
    training_records(frm) { toggle_all_attachments(frm); },
    issue_based_risk_assessment(frm) { toggle_all_attachments(frm); },
    mini_hira(frm) { toggle_all_attachments(frm); },
    applicable_procedure(frm) { toggle_all_attachments(frm); },
    planned_task_observation(frm) { toggle_all_attachments(frm); },
    safety_caucus(frm) { toggle_all_attachments(frm); },
    investigation_register(frm) { toggle_all_attachments(frm); },
    tmm_records(frm) { toggle_all_attachments(frm); },
    alcohol_and_drug_test(frm) { toggle_all_attachments(frm); },
    action_list(frm) { toggle_all_attachments(frm); },
    evidence_of_actions(frm) { toggle_all_attachments(frm); },
    medical_certificate_of_fitness(frm) { toggle_all_attachments(frm); },
    license_authorisation(frm) { toggle_all_attachments(frm); },

    refresh(frm) {
        handle_event_category_view(frm);
        toggle_investigation_attachments(frm);
        toggle_incident_type_fields(frm);
        toggle_vfl_team_table(frm);
        calculate_risk_rating(frm);
        apply_risk_level_style(frm);
        populate_impact_description(frm);
        toggle_all_attachments(frm);
    },

    specify_type(frm) {
        toggle_investigation_attachments(frm);
    },

    incident_type(frm) {
        toggle_incident_type_fields(frm);
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
        method: "safety.safety.doctype.incident_management.incident_management.get_next_incident_number",
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
// EVENT CATEGORY VIEW HANDLER (SAFE)
// =====================================================
function handle_event_category_view(frm) {

    if (!frm.doc.event_category) return;

    const restricted_categories = [
        "Planned Task Observation (PTO)",
        "Visible Field Leadership (VFL)",
        "Inspection (INS)",
        "Audit (AUD)"
    ];

    const allowed_fields = [
        "event_category",
        "region",
        "site",
        "location_on_site",
        "datetime_incident",
        "reporting_person_coy_number",
        "reporting_person_name",
        "employee_id",
        "incident_number",
        "description_of_the_event",
        "employer",
        "vfl_team_member_details"
    ];

    if (!restricted_categories.includes(frm.doc.event_category)) {
        frm.fields.forEach(f => {
            if (f.df.fieldname) {
                frm.set_df_property(f.df.fieldname, "hidden", 0);
            }
        });
        return;
    }

    frm.fields.forEach(f => {
        if (
            f.df.fieldname &&
            !["Section Break", "Column Break", "Tab Break", "Heading"].includes(f.df.fieldtype)
        ) {
            frm.set_df_property(f.df.fieldname, "hidden", 1);
        }
    });

    allowed_fields.forEach(field => {
        frm.set_df_property(field, "hidden", 0);
    });

    ensure_parent_layout_visible(frm, allowed_fields);
}


// =====================================================
// ENSURE LAYOUT VISIBILITY
// =====================================================
function ensure_parent_layout_visible(frm, fieldnames) {

    fieldnames.forEach(fieldname => {
        const field = frm.fields_dict[fieldname];
        if (!field) return;

        let df = field.df;
        while (df && df.parent) {
            const parent = frm.fields_dict[df.parent];
            if (parent) {
                frm.set_df_property(parent.df.fieldname, "hidden", 0);
                df = parent.df;
            } else {
                break;
            }
        }
    });
}


// =====================================================
// VFL TEAM VISIBILITY
// =====================================================
function toggle_vfl_team_table(frm) {

    const field = "vfl_team_member_details";

    if (frm.doc.event_category === "Visible Field Leadership (VFL)") {
        frm.set_df_property(field, "hidden", 0);
    } else {
        frm.set_df_property(field, "hidden", 1);

        if (frm.doc[field] && frm.doc[field].length) {
            frm.clear_table(field);
            frm.refresh_field(field);
        }
    }
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

    // Hide all by default
    ["five_why", "fishbone", "icam"].forEach(field => {
        frm.set_df_property(field, "hidden", 1);
        frm.set_value(field, null);
    });

    // Show based on specify_type
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
// IMPACT → DESCRIPTION POPULATION
// =====================================================
function populate_impact_description(frm) {

    if (!frm.doc.hazard_consequence) {
        frm.set_value("description", "");
        return;
    }

    const consequence = parseInt(frm.doc.hazard_consequence, 10);
    let descriptions = [];

    if (frm.doc.harm_to_people) {
        descriptions.push({
            1: "First aid case / Exposure to minor health risk",
            2: "Medical treatment case / Exposure to major health risk",
            3: "Lost time injury / Reversible impact on health",
            4: "Single fatality or loss of quality of life / Irreversible impact on health",
            5: "Multiple fatalities / Impact on health ultimately fatal"
        }[consequence]);
    }

    if (frm.doc.environmental_impact) {
        descriptions.push({
            1: "Minimal environmental harm – L1 incident",
            2: "Material environmental harm – L2 incident remediable short term",
            3: "Serious environmental harm – L2 incident remediable within LOM",
            4: "Major environmental harm – L2 incident remediable post LOM",
            5: "Extreme environmental harm – L3 incident irreversible"
        }[consequence]);
    }

    if (frm.doc.business_interruption) {
        descriptions.push({
            1: "No disruption to operation / US$20k to US$100k",
            2: "Brief disruption to operation / US$100k to US$1.0M",
            3: "Partial shutdown / US$1.0M to US$10.0M",
            4: "Partial loss of operation / US$10M to US$75.0M",
            5: "Substantial or total loss of operation / >US$75.0M"
        }[consequence]);
    }

    if (frm.doc.legal_and_regulatory) {
        descriptions.push({
            1: "Low level legal issue",
            2: "Minor legal issue; non compliance and breaches of the law",
            3: "Serious breach of law; investigation/report to authority, prosecution and/or moderate penalty possible",
            4: "Major breach of the law; considerable prosecution and penalties",
            5: "Very considerable penalties & prosecutions. Multiple law suits & jail terms"
        }[consequence]);
    }

    if (frm.doc.impact_on_community) {
        descriptions.push({
            1: "Slight impact - public awareness may exist but no public concern",
            2: "Limited impact - local public concern",
            3: "Considerable impact - regional public concern",
            4: "National impact - national public concern",
            5: "International impact - international public attention"
        }[consequence]);
    }

    frm.set_value("description", descriptions.join("\n"));
}



// =====================================================
// CHILD TABLE AGE CALCULATION (UI ONLY)
// =====================================================

// Responsible Person (Injury)
frappe.ui.form.on("Responsible Person", {
    injured_id(frm, cdt, cdn) {
        calculate_child_age(cdt, cdn, "injured_id", "age_of_injured");
    }
});

// Person Responsible for Damages
frappe.ui.form.on("Person Responsible for Damages", {
    damages_caused_by_id(frm, cdt, cdn) {
        calculate_child_age(
            cdt,
            cdn,
            "damages_caused_by_id",
            "damages_caused_by_age"
        );
    }
});

// Shared age calculator
function calculate_child_age(cdt, cdn, source_field, target_field) {

    const row = locals[cdt][cdn];

    if (!row[source_field]) {
        frappe.model.set_value(cdt, cdn, target_field, "");
        return;
    }

    const dob = frappe.datetime.str_to_obj(row[source_field]);
    const today = frappe.datetime.str_to_obj(frappe.datetime.get_today());

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
// =====================================================
// PRELIMINARY INVESTIGATION ATTACHMENT VALIDATION (UI)
// =====================================================

frappe.ui.form.on("Incident Management", {
    validate(frm) {
        validate_preliminary_investigation_attachments(frm);
    }
});

function validate_preliminary_investigation_attachments(frm) {

    const mapping = {
        storyline: ["attach_one", "attach_five", "attach_six"],
        investigation_report: ["attach_two", "attach_three", "attach_four"],
        affected_person_statement: ["attach_seven", "attach_eight", "attach_nine"],
        incident_notification: ["attach_ten", "attach_eleven", "attach_twelve"],
        induction_records: ["attach_nine", "attach_ten", "attach_eleven"],
        training_records: ["attach_twelve", "attach_thirteen", "attach_fourteen"],
        issue_based_risk_assessment: ["attach_fifteen", "attach_sixteen", "attach_seventeen"],
        mini_hira: ["attach_eighteen"],
        applicable_procedure: ["attach_nineteen", "attach_twenty", "attach_twenty_one"],
        planned_task_observation: ["attach_twenty_two", "attach_twenty_three", "attach_twenty_four"],
        safety_caucus: ["attach_twenty_five", "attach_twenty_six", "attach_twenty_seven"],
        investigation_register: ["attach_twenty_eight", "attach_twenty_nine", "attach_thirty"],
        tmm_records: ["attach_thirty_one", "attach_thirty_two", "attach_thirty_three"],
        alcohol_and_drug_test: ["attach_thirty_four", "attach_thirty_five", "attach_thirty_six"],
        action_list: ["attach_thrity_seven", "attach_thirty_eight", "attach_thirty_nine"],
        evidence_of_actions: ["attach_forty", "attach_forty_one", "attach_forty_two"],
        medical_certificate_of_fitness: ["attach_forty_three"],
        license_authorisation: ["attach_forty_four", "attach_forty_five", "attach_forty_six"]
    };

    let errors = [];

    Object.keys(mapping).forEach(check_field => {

        if (frm.doc[check_field]) {

            const attachments = mapping[check_field];
            const has_attachment = attachments.some(f => frm.doc[f]);

            if (!has_attachment) {
                errors.push(
                    `Please upload at least one attachment for "${frappe.meta.get_label(frm.doc.doctype, check_field)}"`
                );
            }
        }
    });

    if (errors.length) {
        frappe.throw({
            title: __("Missing Attachments"),
            message: errors.join("<br>")
        });
    }
}
