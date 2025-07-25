// Copyright (c) 2025, BuFf0k and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Flash report", {
// 	refresh(frm) {

// 	},
// });




frappe.ui.form.on('Flash report', {
  incident_reference: function(frm) {
    if (frm.doc.incident_reference) {
      frappe.call({
        method: 'frappe.client.get',
        args: {
          doctype: 'Incident Classification',
          name: frm.doc.incident_reference
        },
        callback: function(r) {
          if (r.message) {
            const incident = r.message;

            frm.set_value('date_and_time_of_incident', incident.incident_date_and_time || "");
            frm.set_value('name_of_injured_or_affected_person', incident.employee_name || "");
            frm.set_value('employee_full_name', incident.employee_full_name || "");
            frm.set_value('site', incident.fr_site || "");
            frm.set_value('position', incident.position || "");
            frm.set_value('description_of_incidentimpact', incident.description_of_incidentimpact || "");

            frm.refresh_fields();
          }
        }
      });
    }
  }
});

frappe.ui.form.on('Flash report', {
  refresh(frm) {
    // Utility: Style individual fields
    const styleField = (fieldname, background, border, icon = "", labelOverride = "") => {
      const wrapper = frm.fields_dict[fieldname]?.$wrapper;
      if (!wrapper) return;

      wrapper.css({
        "background-color": background,
        "padding": "8px",
        "border-radius": "5px",
        "border": border,
        "margin-bottom": "8px"
      });

        // Style the label itself
      wrapper.find("label").css({
        "font-size": "16px",         // Increase font size
        "font-weight": "600",        // Make label bold
        "color": "#333"              // Optional: slightly darker for better readability
      });


      const originalLabel = labelOverride || frm.fields_dict[fieldname].df.label;
      if (icon) {
        frm.fields_dict[fieldname].df.label = `${icon} ${originalLabel}`;
        frm.refresh_field(fieldname);
      }
    };

    // Utility: Style section headers
    const styleSection = (fieldname, icon = "📁") => {
      const section = frm.fields_dict[fieldname]?.wrapper.closest('.form-section');
      if (!section) return;

      // Header
      const header = section.find('.section-head');
      header.css({
        "background-color": "#003366",
        "color": "#fff",
        "padding": "10px 14px",
        "border-radius": "6px",
        "font-size": "16px",
        "font-weight": "700",
        "margin-bottom": "10px"
      }).prepend(`${icon} `);

      // Container
      section.css({
        "background-color": "#f8f9fa",
        "padding": "20px",
        "border-radius": "10px",
        "box-shadow": "0 2px 8px rgba(0, 0, 0, 0.05)",
        "margin-bottom": "20px"
      });
    };

    // SECTION STYLING
    styleSection("flash_report_section", "⚡");
    styleSection("personal_information_section", "🙍");
    styleSection("date_and_location_section", "📅");
    styleSection("description_and_photos_section", "📝");

    // FIELD STYLING
    styleField("incident_number", "#e6f7ff", "1px solid #91d5ff", "🔢");
    styleField("incident_classification", "#fffbe6", "1px solid #ffe58f", "📊");
    styleField("date_and_time_of_incident", "#e6f7ff", "1px solid #91d5ff", "⏰");
    styleField("nature_of_injurydamage", "#f9f0ff", "1px solid #d3adf7", "💥");
    styleField("potential_severity_classification", "#fff0f6", "1px solid #ffadd2", "⚠️");
    styleField("repeat_incident", "#fff0f6", "1px solid #ffadd2", "🔁");
    styleField("applicable_life_saving_rules", "#fffbe6", "1px solid #ffe58f", "🚧");

    // PERSONAL INFO
    styleField("name_of_injured_or_affected_person", "#e6ffe6", "1px solid #b7eb8f", "🧍‍♂️");
    styleField("employee_full_name", "#e6ffe6", "1px solid #b7eb8f", "📛");
    styleField("name_of_employer_or_contractor", "#f6ffed", "1px solid #d9f7be", "🏭");
    styleField("position", "#f6ffed", "1px solid #d9f7be", "🪪");

    // DATE & LOCATION
    styleField("site", "#e6f7ff", "1px solid #91d5ff", "🌍");
    styleField("where_did_the_incident_occur", "#e6f7ff", "1px solid #91d5ff", "📍");

    // DESCRIPTION & PHOTOS
    styleField("description_of_incidentimpact", "#fff0f6", "1px solid #ffadd2", "📝");
    styleField("photos_and_attachment", "#fff0f6", "1px solid #ffadd2", "📸");
  }
});






