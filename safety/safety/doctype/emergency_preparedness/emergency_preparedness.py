# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import re
import frappe
from frappe.model.document import Document


class EmergencyPreparedness(Document):
    def validate(self):
        """
        Server-side enforcement:
        If site is set and unique_number is empty, generate it.
        """
        if self.site and not (getattr(self, "unique_number", "") or "").strip():
            self.unique_number = generate_next_number(doctype=self.doctype)


@frappe.whitelist()
def get_next_unique_number():
    """
    Called from JS when site is entered.
    Returns the next number in format: YYYY-MM-IS/ES/00001
    Year-month is derived from server current datetime.
    """
    return generate_next_number(doctype="Emergency Preparedness")


def generate_next_number(doctype: str) -> str:
    """
    Generates the next unique number for the given doctype.

    Fixed format:
      YYYY-MM-IS/ES/00001

    Counting is per (YYYY-MM) prefix.
    """
    now = frappe.utils.now_datetime()
    prefix = f"{now.year:04d}-{now.month:02d}-IS/ES/"

    table = f"tab{doctype}"
    field = "unique_number"

    # Find latest number for this YYYY-MM prefix
    rows = frappe.db.sql(
        f"""
        SELECT `{field}`
        FROM `{table}`
        WHERE `{field}` LIKE %s
        ORDER BY `{field}` DESC
        LIMIT 1
        FOR UPDATE
        """,
        (prefix + "%",),
        as_dict=True,
    )

    next_seq = 1
    if rows and rows[0].get(field):
        last_val = rows[0][field] or ""
        m = re.search(r"(\d{5})$", last_val)
        if m:
            next_seq = int(m.group(1)) + 1

    return f"{prefix}{next_seq:05d}"