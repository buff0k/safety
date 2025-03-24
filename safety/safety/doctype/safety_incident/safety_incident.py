# Copyright (c) 2025, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SafetyIncident(Document):
	pass

@frappe.whitelist()
def fetch_employee_data(employee_id):
	frappe.flags.ignore_permissions = True
	data = {
		'employee_name': frappe.db.get_value('Employee', employee_id, 'employee_name') or '',
		'designation': frappe.db.get_value('Employee', employee_id, 'designation') or ''
	}
	return data

@frappe.whitelist()
def fetch_asset_data(asset_id):
	frappe.flags.ignore_permissions = True
	data = {
		'asset_name': frappe.db.get_value('Asset', asset_id, 'asset_name') or '',
		'asset_category': frappe.db.get_value('Asset', asset_id, 'asset_category') or ''
	}
	return data