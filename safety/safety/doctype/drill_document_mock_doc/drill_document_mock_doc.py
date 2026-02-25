# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import re
import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class DrillDocumentMockDoc(Document):
    def validate(self):
        """
        Server-side enforcement:
        If date is set and unique_drill_document_number is empty, generate it.
        """
        if self.date and not (self.unique_drill_document_number or "").strip():
            self.unique_drill_document_number = generate_next_number(
                doctype=self.doctype,
                doc_date=self.date,
            )


@frappe.whitelist()
def get_next_unique_drill_document_number(doc_date):
    """
    Called from JS when date is entered.
    Returns the next number in format: YYYY-MM-IS/ED/00001
    """
    if not doc_date:
        return None

    return generate_next_number(
        doctype="DrillDocumentMockDoc",
        doc_date=doc_date,
    )


def generate_next_number(doctype: str, doc_date) -> str:
    """
    Generates the next unique number for the given doctype and date.

    Fixed format:
      YYYY-MM-IS/ED/00001

    Counting is per (YYYY-MM) prefix.
    """
    d = getdate(doc_date)

    # Fixed literal segment IS/ED with slashes exactly as required
    prefix = f"{d.year:04d}-{d.month:02d}-IS/ED/"

    table = f"tab{doctype}"
    field = "unique_drill_document_number"

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
        # Expect trailing 5 digits
        m = re.search(r"(\d{5})$", last_val)
        if m:
            next_seq = int(m.group(1)) + 1

    return f"{prefix}{next_seq:05d}"