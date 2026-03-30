frappe.ui.form.on('Lessons Learnt', {
	refresh(frm) {
		if (frm.doc.incident_number) {
			frm.add_custom_button(__('Repopulate From Incident'), function () {
				if (frm.is_new()) {
					frappe.show_alert({
						message: __('Please save the document first.'),
						indicator: 'orange'
					});
					return;
				}

				if (frm.is_dirty()) {
					frm.save().then(() => {
						run_lessons_learnt_population(frm);
					});
				} else {
					run_lessons_learnt_population(frm);
				}
			});
		}
	},

	incident_number(frm) {
		if (!frm.doc.incident_number) {
			clear_mapped_fields(frm);
			return;
		}

		if (frm.is_new()) {
			frappe.show_alert({
				message: __('Save the document to populate mapped fields from Incident Report.'),
				indicator: 'orange'
			});
			return;
		}

		run_lessons_learnt_population(frm);
	}
});

function run_lessons_learnt_population(frm) {
	frappe.call({
		method: 'safety.safety.doctype.lessons_learnt.lessons_learnt.populate_lessons_learnt_from_incident',
		args: {
			lessons_learnt_name: frm.doc.name
		},
		freeze: true,
		freeze_message: __('Populating fields from Incident Report...'),
		callback: function (r) {
			if (!r.exc) {
				frm.reload_doc();
			}
		}
	});
}

function clear_mapped_fields(frm) {
	const naFields = [
		'nature_of_injury',
		'nature_of_damage',
		'nature_of_environmental_impact',
		'name_of_injured_person',
		'name_of_affected_person',
		'position_of_employee',
		'years_in_current_position',
		'potential_severity_classification',
		'repeat_incident',
		'life_saving_rule'
	];

	const blankFields = [
		'immediate_causes',
		'basic_causes',
		'system_and_control_failures',
		'comments',
		'disclaimer'
	];

	naFields.forEach(fieldname => {
		frm.set_value(fieldname, 'N/A');
	});

	blankFields.forEach(fieldname => {
		if (frm.fields_dict[fieldname]) {
			frm.set_value(fieldname, '');
		}
	});
}