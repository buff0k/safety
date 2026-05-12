# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, add_months, getdate, today


class PPEIssueRegister(Document):
	def autoname(self):
		if not self.employee or not self.issue_date:
			self.name = "New PPE Issue"
			return

		self.name = f"{self.employee} - {self.issue_date}"

	def validate(self):
		self.populate_employee_details()
		self.set_reissue_dates_from_child_rows()

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

	def set_reissue_dates_from_child_rows(self):
		for row in self.ppe_issued or []:
			row.re_issue_date = self.get_reissue_date_from_child_row(row)

	def get_reissue_date_from_child_row(self, row):
		source_date = row.issue_day or row.date_of_re_issue

		if not source_date:
			return None

		return self.get_reissue_date(source_date)

	def get_reissue_date(self, source_date):
		if not source_date:
			return None

		reissue_date = add_months(getdate(source_date), 12)
		reissue_date = add_days(reissue_date, -1)

		return reissue_date

	def validate_attachment(self):
		if not self.attach:
			frappe.throw("Attach Signed Issue Form is required before submitting.")

	def validate_reissue_dates(self):
		today_date = getdate(today())

		if not self.ppe_issued:
			frappe.throw("Please add at least one PPE item before submitting.")

		for row in self.ppe_issued:
			source_date = row.issue_day or row.date_of_re_issue

			if not source_date:
				frappe.throw(
					f"Row #{row.idx}: Issue Day or Date of Re-Issue is required."
				)

			expected_reissue_date = self.get_reissue_date(source_date)

			if row.re_issue_date != expected_reissue_date:
				row.re_issue_date = expected_reissue_date

			if not row.re_issue_date:
				frappe.throw(f"Row #{row.idx}: Re-Issue Date is required.")

			if getdate(row.re_issue_date) <= today_date:
				frappe.throw(
					f"Row #{row.idx}: Re-Issue Date must be in the future before submission."
				)