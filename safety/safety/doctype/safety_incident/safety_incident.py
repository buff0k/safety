# Copyright (c) 2025, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SafetyIncident(Document):
	pass

@frappe.whitelist()
def fetch_safety_data(safetyemployee):
	frappe.flags.ignore_permissions = True
	data = {
		'safetyfull_name': frappe.db.get_value('Employee', safetyemployee, 'employee_name') or '',
		'safetydesignation': frappe.db.get_value('Employee', safetyemployee, 'designation') or ''
	}

	return data