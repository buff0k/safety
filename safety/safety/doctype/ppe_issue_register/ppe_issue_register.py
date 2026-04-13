# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today


class PPEIssueRegister(Document):
	def autoname(self):
		if not self.employee or not self.issue_date:
			self.name = "New PPE Issue"
			return
		self.name = f"{self.employee} - {self.issue_date}"

	def validate(self):
		self.populate_employee_details()

	def before_submit(self):
		self.validate_attachment()
		self.validate_reissue_dates()

	def populate_employee_details(self):
		if not self.employee:
			self.employee_name = None
			self.branch = None
			self.designation = None
			return

		employee = frappe.db.get_value(
			"Employee",
			self.employee,
			["employee_name", "branch", "designation"],
			as_dict=True
		)

		if employee:
			self.employee_name = employee.employee_name
			self.branch = employee.branch
			self.designation = employee.designation

	def validate_attachment(self):
		if not self.attach:
			frappe.throw("Attach Signed Issue Form is required before submitting.")

	def validate_reissue_dates(self):
		today_date = getdate(today())

		if not self.ppe_issued:
			frappe.throw("Please add at least one PPE item before submitting.")

		for row in self.ppe_issued:
			if not row.re_issue_date:
				frappe.throw(f"Row #{row.idx}: Re-Issue Date is required.")

			if getdate(row.re_issue_date) <= today_date:
				frappe.throw(
					f"Row #{row.idx}: Re-Issue Date must be in the future before submission."
				)