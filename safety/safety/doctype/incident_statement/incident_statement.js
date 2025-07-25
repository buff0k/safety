// Copyright (c) 2025, BuFf0k and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Incident Statement", {
// 	refresh(frm) {

// 	},
// });


/*********************************************************************
 * Client Script – Incident Statement styling
 * file: incident_statement_styling.js   (or save as Desk > Client Script)
 *********************************************************************/
frappe.ui.form.on('Incident Statement', {
  refresh(frm) {

    /* ---------- Utility: style a whole Section Break ---------- */
    const styleSection = (
        sectionFieldname,
        icon            = '📝',     // default icon
        background      = '#f8f9fa',
        headerColor     = '#004085',
        borderColor     = '#ced4da') => {

      const section = frm.fields_dict[sectionFieldname];
      if (!section || !section.wrapper) return;

      const $wrap  = section.wrapper.closest('.form-section');
      const $label = $wrap.find('.section-head');

      $label.css({
        'background-color': headerColor,
        'color'           : '#fff',
        'padding'         : '8px 12px',
        'border-radius'   : '6px',
        'font-size'       : '16px',
        'font-weight'     : '600',
        'margin-bottom'   : '12px'
      }).prepend(`${icon} `);

      $wrap.css({
        'background-color': background,
        'padding'         : '20px',
        'border-radius'   : '8px',
        'border'          : `1px solid ${borderColor}`,
        'box-shadow'      : '0 2px 8px rgba(0,0,0,.05)',
        'margin-bottom'   : '24px'
      });
    };

    /* ---------- Utility: style one field (wrapper + label) ---------- */
    const styleField = (
        fieldname,
        background,
        border,
        icon          = '',
        labelOverride = '') => {

      const wrapper = frm.fields_dict[fieldname]?.$wrapper;
      if (!wrapper) return;

      wrapper.css({
        'background-color': background,
        'padding'         : '6px',
        'border-radius'   : '5px',
        'border'          : border,
        'margin-bottom'   : '6px'
      });

      wrapper.find('label').css({
        'font-weight': '600',     // heavier
        'font-size'  : '16px',    // bigger
        'color'      : '#343a40'
      });

      if (labelOverride || icon) {
        const original = labelOverride || frm.fields_dict[fieldname].df.label;
        frm.fields_dict[fieldname].df.label = icon ? `${icon} ${original}` : original;
        frm.refresh_field(fieldname);
      }
    };

    /* ---------- Style the single “Incident Statement” section ---------- */
    styleSection('incident_statement_section', '📄');

    /* ---------- Style individual fields ---------- */
    // Key identifiers
    styleField('incident_classification_number', '#fef6f2', '1px solid #ff9966', '🔢', 'Incident Classification #');
    styleField('employee_name',                  '#f0fff0', '1px solid #90ee90', '👤', 'Employee Name');
    styleField('employee_number',                '#f0fff0', '1px solid #90ee90', '🆔', 'Employee #');
    styleField('employee_id_number',             '#f0fff0', '1px solid #90ee90', '🪪', 'ID Number');
    styleField('company',                        '#f0fff0', '1px solid #90ee90', '🏭', 'Company');

    // Incident basics
    styleField('date_and_time_of_incident',      '#fff7e6', '1px solid #ffd580', '📅', 'Date / Time of Incident');
    styleField('where_did_the_incident_occur',   '#e6f2ff', '1px solid #80c1ff', '📍', 'Incident Location');
    styleField('what_was_the_task_you_performed','#e6f2ff', '1px solid #80c1ff', '🛠️', 'Task being Performed');
    styleField('are_you_a_witness_of_the_incident','#e6f2ff','1px solid #80c1ff','👀', 'Witness?');

    // Narrative & supervisor
    styleField('description_of_incident_what_happened','#fff8e1', '1px solid #ffcc80', '📝', 'What Happened');
    styleField('who_is_your_supervisor',      '#ede7f6', '1px solid #b39ddb', '👔', 'Supervisor');
  }
});
