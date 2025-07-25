// Copyright (c) 2025, BuFf0k and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Emergency Drill", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Emergency Drill', {
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

    // 🧯 Emergency Drill Section
    styleSection(frm, 'emergency_drill_section', '🧯');
    styleField('date', '#fff9c4', '1px solid #fbc02d', '📅', 'Drill Date');
    styleField('time_started', '#e1f5fe', '1px solid #81d4fa', '⏱️', 'Time Started');
    styleField('time_stopped', '#e1f5fe', '1px solid #81d4fa', '⏱️', 'Time Stopped');
    styleField('planned_or_unplanned', '#fce4ec', '1px solid #f06292', '📋', 'Planned or Unplanned');
    styleField('procedure_tested_as_per_scheduleprocedure', '#e8f5e9', '1px solid #81c784', '🧪', 'Procedure Tested');
    styleField('scenario', '#e0f7fa', '1px solid #4dd0e1', '🧠', 'Scenario');
    styleField('departmentsection', '#f3e5f5', '1px solid #ba68c8', '🏢', 'Department / Section');

    // 👷 Employees Present
    styleSection(frm, 'employees_present_section', '👷');
    styleField('employees_present', '#f0fff0', '1px solid #66bb6a', '🧑‍🤝‍🧑', 'Employees Present');

    // 💡 Suggested Improvement
    styleSection(frm, 'suggested_improvement_section', '💡');
    styleField('suggested_improvement', '#fff3e0', '1px solid #ffb74d', '✍️', 'Suggested Improvement');

    // ✅ Actions Completed
    styleSection(frm, 'actions_completed_section', '✅');
    styleField('actions', '#e3f2fd', '1px solid #64b5f6', '📋', 'Actions Taken');
  }
});
