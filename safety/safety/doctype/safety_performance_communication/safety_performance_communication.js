frappe.ui.form.on('Safety Performance Communication', {
	refresh(frm) {
		frm.add_custom_button(__('Update Weekly Sites and Info'), function () {
			frappe.call({
				method: 'safety.safety.doctype.safety_performance_communication.safety_performance_communication.manual_sync_current_week',
				freeze: true,
				freeze_message: __('Updating Safety Performance Communication records...'),
				callback: function (r) {
					if (!r.exc && r.message) {
						let msg = `
							<b>Status:</b> ${r.message.status || 'success'}<br>
							<b>Created:</b> ${r.message.created || 0}<br>
							<b>Updated:</b> ${r.message.updated || 0}<br>
							<b>Week Start:</b> ${r.message.week_start_date || ''}<br>
							<b>Week End:</b> ${r.message.week_end_date || ''}<br>
							<b>Fallback Used:</b> ${r.message.used_fallback ? 'Yes' : 'No'}
						`;

						if (r.message.sites && r.message.sites.length) {
							msg += `<br><br><b>Sites:</b><br>${r.message.sites.join('<br>')}`;
						}

						frappe.msgprint({
							title: __('Weekly Sync Complete'),
							message: msg,
							indicator: 'green'
						});

						frm.reload_doc();
					}
				}
			});
		});
	}
});