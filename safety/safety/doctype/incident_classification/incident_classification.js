// Copyright (c) 2025, BuFf0k and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Incident Classification", {
// 	refresh(frm) {

// 	},
// });


frappe.ui.form.on("Incident Classification", {
  check_niwr: function(frm) {
    frm.set_value("employee_name", null); // Clear any previous value
    frm.set_query("employee_name", () => {
    });
  },

  employee_name: function (frm) {
    if (frm.doc.employee_name) {
      frappe.call({
        method: "frappe.client.get",
        args: {
          doctype: "Employee",
          name: frm.doc.employee_name,
        },
        callback: function (r) {
          if (r.message) {
            let emp = r.message;
            frm.set_value("id_number", emp.id_number || ""); //ID conversion
            frm.set_value("department", emp.department || "");
            frm.set_value("section", emp.section || "");
            frm.set_value("contractors_company_name", emp.company || "");
            frm.set_value("occupation", emp.designation || "");
          }
        },
      });
    }
  }
});

frappe.ui.form.on("Incident Classification", {
  did_the_person_sustain_any_injuries: function(frm) {
    const hasInjury = frm.doc.did_the_person_sustain_any_injuries === "Yes";

    // Description field
    frm.set_df_property("description_of_injury", "read_only", !hasInjury);
    if (!hasInjury) frm.set_value("description_of_injury", "");

    // Injury classification table
    frm.fields_dict.classifying_injuries.grid.wrapper.toggle(hasInjury);
    if (!hasInjury) {
      frm.clear_table("classifying_injuries");
    }

    frm.refresh_field("description_of_injury");
    frm.refresh_field("classifying_injuries");
  },

  onload: function(frm) {
    // Trigger the function initially to enforce rules on load
    frm.trigger("did_the_person_sustain_any_injuries");
  }
});



frappe.ui.form.on('Incident Classification', {
  onload(frm) {
    toggle_reporting_criteria_fields(frm);
  },
  fatality(frm) {
    toggle_reporting_criteria_fields(frm);
  }
});

function toggle_reporting_criteria_fields(frm) {
  const is_fatal = frm.doc.fatality === 'Yes';

  // Only hide or show the additional fields, NOT the section or fatality field
  const fields_to_toggle = [
    'location_description',
    'injured_on_site',
    'injured_on_duty',
    'date_and_time_of_fatality',
    'cause_of_death'
  ];

  fields_to_toggle.forEach(field => {
    frm.set_df_property(field, 'hidden', !is_fatal);
  });

  frm.refresh_fields(fields_to_toggle);
}

frappe.ui.form.on('Incident Classification', {
  onload(frm) {
    toggle_mobile_equipment_fields(frm);
  },
  was_mobile_equipment_involved(frm) {
    toggle_mobile_equipment_fields(frm);
  }
});

function toggle_mobile_equipment_fields(frm) {
  const involved = frm.doc.was_mobile_equipment_involved === 'Yes';

  // Fields to show/hide based on involvement
  const equipment_fields = [
    'description_of_damage_if_applicable',
    'vehicle_nameid',
    'vehicle_description',
    'asset_name',
    'vehicle_manufacture',
    'vehicle_model',
    'license_plate_number',
    'plant_nameid',
    'company_owned',
    'is_the_asset_still_operational'
  ];

  equipment_fields.forEach(field => {
    frm.set_df_property(field, 'hidden', !involved);
  });

  frm.refresh_fields(equipment_fields);
}

frappe.ui.form.on('Incident Classification', {
  onload(frm) {
    toggle_investigation_fields(frm);
  },
  incident_to_be_investigated(frm) {
    toggle_investigation_fields(frm);
  }
});

function toggle_investigation_fields(frm) {
  const needs_investigation = frm.doc.incident_to_be_investigated === 'Yes';

  // Always show the investigation selector field
  frm.set_df_property('incident_to_be_investigated', 'hidden', false);

  // Conditionally hide/show the other related fields
  const investigation_fields = [
    'person_responsable_for_investigation',
    'department_of_investigator',
    'full_name_of_person_responsable_for_investigation'
  ];

  investigation_fields.forEach(field => {
    frm.set_df_property(field, 'hidden', !needs_investigation);
  });

  frm.refresh_fields(investigation_fields);
}


/////////////////STYLINNGGGGGGG///////////////////////
frappe.ui.form.on('Incident Classification', {
  refresh(frm) {
    // 🔧 Utility: Style individual fields
    const styleField = (fieldname, background, border, icon = "", labelOverride = "") => {
      const wrapper = frm.fields_dict[fieldname]?.$wrapper;
      if (!wrapper) return;

      wrapper.css({
        "background-color": background,
        "padding": "6px",
        "border-radius": "5px",
        "border": border,
        "margin-bottom": "6px"
      });

      wrapper.find('label').css({
        "font-weight": "600",    
        "font-size": "16px",     
        "color": "#343a40"       
      });

      if (labelOverride || icon) {
        const originalLabel = labelOverride || frm.fields_dict[fieldname].df.label;
        const newLabel = icon ? `${icon} ${originalLabel}` : originalLabel;
        frm.fields_dict[fieldname].df.label = newLabel;
        frm.refresh_field(fieldname);
      }
    };

    // 🔧 Utility: Style section containers and labels
    const styleSection = (frm, sectionFieldname, icon, background = '#f8f9fa', headerColor = '#004085', borderColor = '#ced4da') => {
      const section = frm.fields_dict[sectionFieldname];
      if (!section || !section.wrapper) return;

      const $sectionWrapper = section.wrapper.closest('.form-section');
      const $sectionLabel = $sectionWrapper.find('.section-head');

      $sectionLabel.css({
        'background-color': headerColor,
        'color': '#fff',
        'padding': '8px 12px',
        'border-radius': '6px',
        'font-size': '20px',
        'font-weight': '800',
        'margin-bottom': '12px'
      }).prepend(`${icon} `);

      $sectionWrapper.css({
        'background-color': background,
        'padding': '20px',
        'border-radius': '8px',
        'border': `1px solid ${borderColor}`,
        'box-shadow': '0 2px 8px rgba(0, 0, 0, 0.25)',
        'margin-bottom': '24px'
      });
    };


    // 🎨 Style Sections
    styleSection(frm, 'incident_details_section', '📋');
    styleSection(frm, 'employee_details_section', '🧑‍🏭');
    styleSection(frm,'section_break_edgv', '🔢')
    styleSection(frm, 'injury_classification_section', '🩹');
    styleSection(frm, 'body_injury_section', '🦵');
    styleSection(frm, 'reporting_criteria_section', '📋');
    styleSection(frm, 'mobile_equipment_section', '🚜');
    styleSection(frm, 'incident_investigation_section', '🔍');
    styleSection(frm, 'asset_insurance_information_section', '🛡️');
    styleSection(frm, 'document_revision_section', '🛡️');
    styleSection(frm, 'incident_location_section', '📌');
    styleSection(frm, 'incident_descriptions_section', '📃');
    styleSection(frm, 'statements_section', '📃');

    // 🗂️ Incident Details Fields
    styleField("incident_number", "#fef6f2", "1px solid #ff9966", "🔢", "Incident Number");
    styleField("incident_date_and_time", "#fff7e6", "1px solid #ffd580", "📅", "Incident Date and Time");
    styleField("short_description_of_incident", "#f0f8ff", "1px solid #a0c4ff", "📝", "Short Description");
    styleField("revision", "#fff7e6", "1px solid #ffd580", "📝", "Revision (Version)");
    styleField("effective_date", "#f0f8ff", "1px solid #a0c4ff", "📅", "Effective Date (Last updated)");
    styleField("incident_reference_number", "#fff7e6", "1px solid #ffd580", "📝", "Reference Number");
    styleField("safety_incident_classification", "#ffe6e6ff", "1px solid #ff8080ff", "📝", "Incident Classification");
    

    // 👷 Employee Details Fields
    styleField("check_niwr", "#f0fff0", "1px solid #90ee90", "🧑‍🏭", "Employee Type");
    styleField("employee_name", "#f0fff0", "1px solid #90ee90", "🔍", "Search for Employee");
    styleField("employee_full_name", "#f0fff0", "1px solid #90ee90", "📛", "Employee Full Name");
    styleField("employee_number", "#f0fff0", "1px solid #90ee90", "🔢", "Employee Number");
    styleField("occupation", "#f0fff0", "1px solid #90ee90", "⚙️", "Occupation");
    styleField("department", "#f0fff0", "1px solid #90ee90", "🏢", "Department");
    styleField("contractors_company_name", "#f0fff0", "1px solid #90ee90", "🏭", "Company Name");
    styleField("passengers_involved", "#f0fff0", "1px solid #90ee90", "🚗", "Passengers Involved");
    styleField("id_number", "#f0fff0", "1px solid #90ee90", "📃", "RSA - ID Number");
    styleField("branch", "#f0fff0", "1px solid #90ee90", "📃", "Branch");
    


    // 🩹 Injury Classification Fields
    styleField("did_the_person_sustain_any_injuries", "#FFF59C", "1px solid #ffcc80", "🩺", "Did the person sustain any injuries");
    styleField("description_of_injury", "#FFF59C", "1px solid #ffcc80", "📄", "Description of Injury");
    styleField("classifying_injuries", "#FFF59C", "1px solid #ffcc80", "🗂️", "Classifying Injuries");

    // 🦵 Body Injury Fields
    styleField("body_part", "#9CE0FF", "1px solid #80c1ff", "🦵", "Body Part");
    styleField("body_part_description", "#9CE0FF", "1px solid #80c1ff", "📝", "Body Part Description");
    styleField("body_side", "#9CE0FF", "1px solid #80c1ff", "➡️", "Body Side");

    // 📋 Reporting Criteria Fields
    styleField("privacy_case", "#FAD370", "1px solid #dce775", "🔐", "Privacy Case");
    styleField("injured_on_site", "#FAD370", "1px solid #dce775", "🏗️", "Injured on Site");
    styleField("injured_on_duty", "#FAD370", "1px solid #dce775", "🕒", "Injured on Duty");
    styleField("fatality", "#FAD370", "1px solid #dce775", "⚠️", "Fatality");
    styleField("date_and_time_of_fatality", "#FAD370", "1px solid #dce775", "📅", "Date and Time of Fatality");
    styleField("location_of_death", "#FAD370", "1px solid #dce775", "📍", "Location of Death");
    styleField("location_description", "#FAD370", "1px solid #dce775", "🗺️", "Location Description");
    styleField("cause_of_death", "#FAD370", "1px solid #dce775", "☠️", "Cause of Death");

        // 🏗️ Asset Involvement
    styleField("was_mobile_equipment_involved", "#e0f7fa", "1px solid #4dd0e1", "🏗️", "Was any assets involved?");
    styleField("description_of_damage_if_applicable", "#e0f7fa", "1px solid #4dd0e1", "📝", "Description of Damage");
    styleField("classifying_mobile_equipment_damage", "#e0f7fa", "1px solid #4dd0e1", "🧾", "Classifying Equipment Damage");

    // 🚜 Asset Details
    styleField("vehicle_nameid", "#f1f8e9", "1px solid #aed581", "🔧", "Asset Name/ID");
    styleField("vehicle_description", "#f1f8e9", "1px solid #aed581", "📦", "Asset Category");
    styleField("asset_name", "#f1f8e9", "1px solid #aed581", "🏷️", "Asset Name");
    styleField("vehicle_manufacture", "#f1f8e9", "1px solid #aed581", "🏭", "Vehicle Manufacture");
    styleField("vehicle_model", "#f1f8e9", "1px solid #aed581", "🚗", "Vehicle Model");
    styleField("license_plate_number", "#f1f8e9", "1px solid #aed581", "🪪", "License Plate Number");
    styleField("plant_nameid", "#f1f8e9", "1px solid #aed581", "📍", "Location");
    styleField("company_owned", "#f1f8e9", "1px solid #aed581", "🏢", "Company Owned");
    styleField("is_the_asset_still_operational", "#f1f8e9", "1px solid #aed581", "⚙️", "Is the Asset Still Operational?");

    // 🛡️ Insurance Info
    styleField("insurance_company", "#fbe9e7", "1px solid #ffab91", "🏢", "Insurance Company");
    styleField("policy_number", "#fbe9e7", "1px solid #ffab91", "📄", "Policy Number");
    styleField("start_date", "#fbe9e7", "1px solid #ffab91", "📅", "Start Date");
    styleField("end_date", "#fbe9e7", "1px solid #ffab91", "📅", "End Date");

        // 🕵️ Investigation Section
    styleField("incident_to_be_investigated", "#ede7f6", "1px solid #b39ddb", "🕵️", "Incident to be Investigated");
    styleField("person_responsable_for_investigation", "#ede7f6", "1px solid #b39ddb", "👤", "Person Responsible for Investigation");
    styleField("department_of_investigator", "#ede7f6", "1px solid #b39ddb", "🏢", "Department of Investigator");


    styleField("incident_site", "#e3f2fd", "1px solid #64b5f6", "📌", "Incident Site");
    styleField("incident_location", "#e3f2fd", "1px solid #64b5f6", "📍", "Incident Location");
    styleField("area", "#e3f2fd", "1px solid #64b5f6", "🗺️", "Area");
    styleField("reporting_person", "#e3f2fd", "1px solid #64b5f6", "🧑‍💼", "Reporting Person");
    styleField("impact_of_incident", "#e3f2fd", "1px solid #64b5f6", "💥", "Impact of Incident");
    styleField("urgency", "#e3f2fd", "1px solid #64b5f6", "⏱️", "Urgency");
    styleField("priority", "#e3f2fd", "1px solid #64b5f6", "⚠️", "Priority");


    styleField("immediate_actions", "#f3e5f5", "1px solid #ce93d8", "⚡", "Immediate Actions Taken");
    styleField("description_of_events", "#f3e5f5", "1px solid #ce93d8", "📜", "Description of Events");
    styleField("storyline", "#f3e5f5", "1px solid #ce93d8", "🎞️", "Storyline Attachment");
    styleField("initial_record", "#f3e5f5", "1px solid #ce93d8", "📄", "Initial Record");
    styleField("shift_group", "#f3e5f5", "1px solid #ce93d8", "👥", "Shift Group");
    styleField("shift", "#f3e5f5", "1px solid #ce93d8", "🕒", "Shift");

    styleField("employee_statements", "#fff3e0", "1px solid #ffb74d", "📝", "Employee Statements");


    // 🔽 Create a custom Download button below the "storyline" field
    if (!frm.fields_dict.storyline.$wrapper.find('.download-template-btn').length) {
      const downloadBtnHtml = `
        <div style="margin-top: 10px;">
          <button class="btn btn-primary download-template-btn">
            ⬇️ Download Storyline Template
          </button>
        </div>
      `;

      // Append after the storyline field
      frm.fields_dict.storyline.$wrapper.append(downloadBtnHtml);

      // Attach click event
      frm.fields_dict.storyline.$wrapper.find('.download-template-btn').on('click', () => {
        const fileUrl = '/files/IS-SHEQ-DT-STORY-056 Storyline - template.pptx'; // Replace with your actual file URL
        window.open(fileUrl, '_blank');
      });
    }



  }
});











