# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import re
from datetime import datetime

import frappe
from frappe.model.document import Document


class EmergencyPreparednessSchedule(Document):
	def validate(self):
		"""
		Server-side enforcement:
		If date is set and unique_number is empty, generate it.
		"""
		if self.date and not (getattr(self, "unique_number", "") or "").strip():
			self.unique_number = generate_next_number(
				doctype=self.doctype,
				date_value=self.date
			)


@frappe.whitelist()
def get_next_unique_number(date_value=None):
	"""
	Called from JS when date is entered.
	Returns the next number in format: YYYY-MM/IS/ES/00001

	The YYYY-MM part is derived from the entered date_value.
	The numeric suffix is global and never resets.
	"""
	if not date_value:
		return ""

	return generate_next_number(
		doctype="Emergency Preparedness Schedule",
		date_value=date_value
	)


def generate_next_number(doctype: str, date_value) -> str:
	"""
	Generates the next unique number for the given doctype.

	Format:
	  YYYY-MM/IS/ES/00001

	Rules:
	- YYYY-MM comes from the entered date field
	- sequence is global across all records
	- sequence never resets
	"""
	prefix = get_prefix_from_date(date_value)

	table = f"tab{doctype}"
	field = "unique_number"

	rows = frappe.db.sql(
		f"""
		SELECT `{field}`
		FROM `{table}`
		WHERE `{field}` IS NOT NULL
		  AND `{field}` != ''
		ORDER BY CAST(SUBSTRING_INDEX(`{field}`, '/', -1) AS UNSIGNED) DESC
		LIMIT 1
		FOR UPDATE
		""",
		as_dict=True,
	)

	next_seq = 1
	if rows and rows[0].get(field):
		last_val = rows[0][field] or ""
		match = re.search(r"(\d{5})$", last_val)
		if match:
			next_seq = int(match.group(1)) + 1

	return f"{prefix}/{next_seq:05d}"


def get_prefix_from_date(date_value) -> str:
	"""
	Convert the entered date/datetime value into:
	  YYYY-MM/IS/ES

	Supports:
	- datetime/date objects
	- strings like '2026-03-13 07:24:07'
	- strings like '2026-03-13'
	"""
	if hasattr(date_value, "strftime"):
		dt = date_value
	else:
		date_str = str(date_value).strip()
		try:
			dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
		except ValueError:
			try:
				dt = datetime.strptime(date_str, "%Y-%m-%d")
			except ValueError:
				dt = frappe.utils.get_datetime(date_str)

	return f"{dt.strftime('%Y-%m')}/IS/ES"