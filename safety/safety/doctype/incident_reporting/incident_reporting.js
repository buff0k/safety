// Copyright (c) 2025, BuFf0k and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Incident Reporting", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Incident Reporting", {
  onload(frm) {
    // Set field defaults or dynamic behaviors here if needed
  },

  refresh(frm) {
    const styleField = (fieldname, background, border, icon = "", labelOverride = "") => {
      const wrapper = frm.fields_dict[fieldname]?.$wrapper;
      if (!wrapper) return;

      // Field container styling
      wrapper.css({
        "background-color": background,
        "padding": "8px",
        "border-radius": "6px",
        "border": border,
        "margin-bottom": "10px"
      });

      // Label styling
      wrapper.find("label").css({
        "font-size": "16px",
        "font-weight": "600",
        "color": "#2c3e50"
      });

      // Optional: Update label with icon or override
      if (labelOverride || icon) {
        const originalLabel = labelOverride || frm.fields_dict[fieldname].df.label;
        const newLabel = icon ? `${icon} ${originalLabel}` : originalLabel;
        frm.fields_dict[fieldname].df.label = newLabel;
        frm.refresh_field(fieldname);
      }
    };

    const styleSection = (sectionFieldname, color = "#004085") => {
      const section = frm.fields_dict[sectionFieldname]?.wrapper?.closest(".form-section");
      if (!section) return;

      const label = section.find(".section-head");
      label.css({
        "background-color": color,
        "color": "#fff",
        "padding": "10px 16px",
        "border-radius": "6px",
        "font-size": "16px",
        "font-weight": "bold",
        "margin-bottom": "14px"
      }).prepend("📋 ");

      section.css({
        "background-color": "#f8f9fa",
        "padding": "18px",
        "border-radius": "10px",
        "box-shadow": "0 2px 8px rgba(0, 0, 0, 0.04)",
        "margin-bottom": "24px"
      });
    };

    // 🧾 Style Section Headers
    styleSection("employee_information_section", "#0a4b78");
    styleSection("section_break_lreu", "#5c2674");

    // 🧍 Employee Information Fields
    styleField("company_name", "#e8f5e9", "1px solid #a5d6a7", "🏢");
    styleField("name_and_surname_person_reporting", "#e8f5e9", "1px solid #a5d6a7", "🧑‍💼");
    styleField("employee_number_person_reporting", "#e8f5e9", "1px solid #a5d6a7", "🆔");
    styleField("responsible_managerforeman_contractor", "#e8f5e9", "1px solid #a5d6a7", "🧰");
    styleField("responsible_managerforeman_company", "#e8f5e9", "1px solid #a5d6a7", "👷‍♂️");


    styleField("name_and_surname_injuredinvolved", "#8DA9DC", "1px solidrgb(165, 182, 214)", "🤕");
    styleField("employee_number_injuredinvolved", "#8DA9DC", "1px solidrgb(165, 172, 214)", "🆔");

    // 📍 Incident Details Fields
    styleField("where_did_the_incident_happen", "#fff3e0", "1px solid #ffcc80", "📍");
    styleField("date_and_time_of_incident", "#fff3e0", "1px solid #ffcc80", "📅");
    styleField("classification", "#fff3e0", "1px solid #ffcc80", "⚠️");

    // 📝 Description Section
    styleField("full_description_of_incident", "#f3e5f5", "1px solid #ce93d8", "📝");
    styleField("immediate_actions_taken", "#f3e5f5", "1px solid #ce93d8", "🚑");
  }
});
