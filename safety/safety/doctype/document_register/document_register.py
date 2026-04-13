# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DocumentRegister(Document):
	def autoname(self):
		company_abbrev = self.get_company_abbrev()
		department_abbrev = self.get_department_abbrev()
		subclass_abbrev = self.get_subclass_abbrev()

		prefix = f"{company_abbrev}-{department_abbrev}-{subclass_abbrev}"
		next_number = self.get_next_number(prefix)

		self.name = f"{prefix}-{next_number}"
		self.document_no = self.name

	def before_insert(self):
		# Safety fallback in case autoname ran before document_no was set
		if not self.document_no:
			self.document_no = self.name

	def validate(self):
		# Keep document_no synced with the generated name
		if self.name and not self.is_new() and not self.document_no:
			self.document_no = self.name

	def before_submit(self):
		if not self.attach:
			frappe.throw(_("You cannot submit this document unless 'Attach Executed Document' is populated."))

	def get_company_abbrev(self):
		if not self.company:
			frappe.throw(_("Company is required."))

		company_abbrev = frappe.db.get_value(
			"Company Abbreviation",
			self.company,
			"company_abbrev"
		)

		if not company_abbrev:
			frappe.throw(_("Company Abbreviation is missing for company {0}.").format(self.company))

		return company_abbrev.strip()

	def get_department_abbrev(self):
		if not self.department:
			frappe.throw(_("Department is required."))

		# In your setup, the Document Register links directly to the
		# Department Abbreviation doctype, whose name is the abbreviation.
		return self.department.strip()

	def get_subclass_abbrev(self):
		if not self.document_subclass:
			frappe.throw(_("Document Subclass is required."))

		subclass_abbrev = frappe.db.get_value(
			"Document Register Subclass",
			self.document_subclass,
			"subclass_abbrev"
		)

		if not subclass_abbrev:
			frappe.throw(_("Subclass Abbreviation is missing for subclass {0}.").format(self.document_subclass))

		return subclass_abbrev.strip()

	def get_next_number(self, prefix):
		like_pattern = f"{prefix}-%"

		existing = frappe.db.sql(
			"""
			SELECT name
			FROM `tabDocument Register`
			WHERE name LIKE %s
			ORDER BY creation DESC
			""",
			(like_pattern,),
			as_dict=True
		)

		max_number = 0

		for row in existing:
			name = row.name or ""
			parts = name.split("-")
			if len(parts) < 4:
				continue

			last_part = parts[-1]
			if last_part.isdigit():
				max_number = max(max_number, int(last_part))

		return str(max_number + 1).zfill(3)