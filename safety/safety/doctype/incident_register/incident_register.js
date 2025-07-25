// Copyright (c) 2025, BuFf0k and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Incident Register", {
// 	refresh(frm) {

// 	},
// });
// 🧾 Incident Register Sections

frappe.ui.form.on('Incident Register', {
  onload(frm) {
    toggle_fields(frm);
  },

  incident_classification(frm) {
    toggle_fields(frm);
  }
});

// 🔄 Utility Function to Toggle Field Visibility
function toggle_fields(frm) {
  const has_classification = !!frm.doc.incident_classification;

  // List of fieldnames to toggle (everything after incident_classification)
  const fields_to_toggle = [
    "incident_details_section",
    "incident_date_and_time",
    "injury",
    "section",
    "area",
    "column_break_velu",
    "incident_reference_number",
    "description_of_incident",
    "employees_involved_section",
    "employee_involved",
    "employee_department",
    "shift",
    "column_break_lyju",
    "investigation_needed",
    "select_juix",
    "foreman"
  ];

  // Loop through and toggle each field
  fields_to_toggle.forEach(fieldname => {
    frm.toggle_display(fieldname, has_classification);
  });
}


frappe.ui.form.on('Incident Register', {
  refresh(frm) {
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

// 🎨 Field Styling Utility
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

// 🧾 Style Sections
styleSection(frm, 'incident_register_details_section', '📘');
styleSection(frm, 'incident_classification_section', '🏷️');
styleSection(frm, 'incident_details_section', '📄');
styleSection(frm, 'employees_involved_section', '👷');

// 🔢 Incident Register Fields
styleField("incident_number", "#fef6f2", "1px solid #ff9966", "🔢", "Incident Number");
styleField("incident_classification", "#e0f7fa", "1px solid #4dd0e1", "🔗", "Linked Classification");

// 📄 Incident Details
styleField("incident_date_and_time", "#fff7e6", "1px solid #ffd580", "📅", "Incident Date and Time");
styleField("injury", "#FFF59C", "1px solid #ffcc80", "🩺", "Injury");
styleField("injury_classification", "#FFF59C", "1px solid #ffcc80", "🩺", "Injury Classification");
styleField("section", "#f0fff0", "1px solid #90ee90", "📍", "Site");
styleField("area", "#f0fff0", "1px solid #90ee90", "🗺️", "Area");
styleField("incident_reference_number", "#f0f8ff", "1px solid #a0c4ff", "📎", "Reference Number");
styleField("description_of_incident", "#f0f8ff", "1px solid #a0c4ff", "📝", "Description of Incident");

// 👥 Employees Involved
styleField("employee_involved", "#e8f5e9", "1px solid #a5d6a7", "👤", "Employee Involved");
styleField("employee_department", "#e8f5e9", "1px solid #a5d6a7", "🏢", "Employee Department");
styleField("shift", "#e8f5e9", "1px solid #a5d6a7", "🕒", "Shift");

// 🔍 Investigation
styleField("investigation_needed", "#ede7f6", "1px solid #b39ddb", "🔍", "Investigation Needed");
styleField("select_juix", "#ede7f6", "1px solid #b39ddb", "🧑‍💼", "Responsible Person");
styleField("foreman", "#ede7f6", "1px solid #b39ddb", "🧰", "Foreman");
styleField("responsible_person_full_name", "#ede7f6", "1px solid #b39ddb", "🧑‍💼", "Responsible Person Full Name");
styleField("foreman_full_name", "#ede7f6", "1px solid #b39ddb", "🧰", "ForemanFull Name");


  }
});