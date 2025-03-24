# Copyright (c) 2025, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SafetyIncident(Document):
	def autoname(self):
		if not self.incident_date:
			frappe.throw("Incident Date is required to generate the document name.")
		# Format date as YY/MM/DD
		date_prefix = frappe.utils.getdate(self.incident_date).strftime("%y/%m/%d")
		# Count existing documents with the same date prefix
		last_entry = frappe.db.sql(
			"""
			SELECT name FROM `tabSafety Incident`
			WHERE name LIKE %s
			ORDER BY name DESC LIMIT 1
			""",
			(date_prefix + "-%"),
			as_dict=True
		)
		if last_entry:
			# Extract the last counter and increment it
			last_counter = int(last_entry[0]["name"].split("-")[-1])
			new_counter = last_counter + 1
		else:
			new_counter = 1
		# Set the document name
		self.name = f"{date_prefix}-{new_counter}"

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