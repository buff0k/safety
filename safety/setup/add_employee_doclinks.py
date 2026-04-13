# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe


def ensure_employee_links():
	"""Ensure required Safety document links exist in the Employee DocType."""

	required_links = [
		{
			"link_doctype": "PPE Issue Register",
			"link_fieldname": "employee"
		}
	]

	existing_links = frappe.get_all(
		"DocType Link",
		filters={"parent": "Employee"},
		fields=[
			"link_doctype",
			"link_fieldname",
			"parent_doctype",
			"table_fieldname",
			"is_child_table",
			"group"
		]
	)

	existing_links_set = {
		(
			link["link_doctype"],
			link["link_fieldname"],
			link.get("parent_doctype") or "",
			link.get("table_fieldname") or "",
			int(link.get("is_child_table", 0))
		)
		for link in existing_links
	}

	for link in required_links:
		key = (
			link["link_doctype"],
			link["link_fieldname"],
			link.get("parent_doctype", ""),
			link.get("table_fieldname", ""),
			int(link.get("is_child_table", 0))
		)

		if key not in existing_links_set:
			doc = frappe.get_doc({
				"doctype": "DocType Link",
				"parent": "Employee",
				"parentfield": "links",
				"parenttype": "DocType",
				"link_doctype": link["link_doctype"],
				"link_fieldname": link["link_fieldname"],
				"parent_doctype": link.get("parent_doctype"),
				"table_fieldname": link.get("table_fieldname"),
				"is_child_table": link.get("is_child_table", 0),
				"group": "Safety"
			})
			doc.insert(ignore_permissions=True)
			frappe.db.commit()
			frappe.msgprint(f"✅ Added: {link['link_doctype']} (direct)")