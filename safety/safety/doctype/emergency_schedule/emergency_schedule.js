// Copyright (c) 2025, BuFf0k and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Emergency Schedule", {
// 	refresh(frm) {

// 	},
// });


frappe.ui.form.on('Emergency Schedule', {
  onload: function (frm) {
    setTimeout(() => {
      adjustChildTableRowHeight(frm);
    }, 100);
  },

  refresh: function (frm) {
    setTimeout(() => {
      adjustChildTableRowHeight(frm);
    }, 100);
  }
});

function adjustChildTableRowHeight(frm) {
  const grid_rows = frm.fields_dict["emergency_drill_schedule"].grid.grid_rows;

  grid_rows.forEach(row => {
    const $wrapper = row.$wrapper;

    // 1. Adjust overall row padding and height
    $wrapper.css({
      'padding': '12px 0',
      'min-height': '130px',
      'display': 'flex',
      'align-items': 'center'
    });

    // 2. Adjust all field wrappers in the row
    $wrapper.find('.form-group').css({
      'margin-bottom': '0px',
      'height': '100%'
    });

    // 3. Set consistent height for inputs and selects
    $wrapper.find('select.form-control, select.form-control, smalltext.form-control').css({
      'height': '100px',
      'padding': '10px 12px',
      'font-size': '14px'
    });

    // 4. Make the textarea taller than selects if needed
    const safetyField = row.grid_form?.fields_dict?.safety_drills;
    if (safetyField && safetyField.$wrapper) {
      safetyField.$wrapper.find('textarea').css({
        'height': '120px'
      });
    }
  });
}

