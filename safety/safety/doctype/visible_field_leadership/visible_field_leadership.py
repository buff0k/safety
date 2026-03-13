import re
from datetime import datetime

import frappe
from frappe.model.document import Document


class VisibleFieldLeadership(Document):
	def validate(self):
		self.set_unique_number()

	def before_insert(self):
		self.set_unique_number()

	def set_unique_number(self):
		if not self.date:
			return

		expected_prefix = get_prefix_from_date(self.date)

		# Keep the current value if this is an existing record
		# and the prefix still matches the selected date.
		if self.unique_number and self.unique_number.startswith(expected_prefix + "/"):
			return

		self.unique_number = build_next_unique_number(self.date, self.name)


@frappe.whitelist()
def get_next_unique_number(date_value, docname=None):
	if not date_value:
		return ""

	return build_next_unique_number(date_value, docname)


def build_next_unique_number(date_value, docname=None):
	prefix = get_prefix_from_date(date_value)
	next_counter = get_next_global_counter(docname)
	return f"{prefix}/{next_counter:05d}"


def get_next_global_counter(docname=None):
	"""
	Get the next running number across ALL Visible Field Leadership records.
	The numeric suffix never resets, regardless of year/month.
	"""
	filters = {}

	if docname:
		filters["name"] = ["!=", docname]

	existing = frappe.get_all(
		"Visible Field Leadership",
		filters=filters,
		fields=["unique_number"],
		limit_page_length=0
	)

	max_counter = 0

	for row in existing:
		value = (row.get("unique_number") or "").strip()
		match = re.search(r"/(\d{5})$", value)
		if match:
			number = int(match.group(1))
			if number > max_counter:
				max_counter = number

	return max_counter + 1


def get_prefix_from_date(date_value):
	if hasattr(date_value, "strftime"):
		dt = date_value
	else:
		dt = datetime.strptime(str(date_value), "%Y-%m-%d")

	return f"{dt.strftime('%Y-%m')}/IS/VFL"