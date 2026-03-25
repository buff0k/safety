# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import getdate


SERIES_KEY = "IS/RMA/"
SERIES_DIGITS = 5


def build_unique_number(date_value, sequence_number):
    d = getdate(date_value)
    return f"{d.year:04d}-{d.month:02d}/{SERIES_KEY}{int(sequence_number):0{SERIES_DIGITS}d}"


def get_current_series_value():
    row = frappe.db.sql(
        """
        select `current`
        from `tabSeries`
        where `name` = %s
        limit 1
        """,
        (SERIES_KEY,),
        as_dict=True,
    )

    if not row:
        return 0

    return int(row[0].get("current") or 0)


def get_next_sequence_preview():
    return get_current_series_value() + 1


def allocate_unique_number(date_value):
    sequence = getseries(SERIES_KEY, SERIES_DIGITS)
    d = getdate(date_value)
    return f"{d.year:04d}-{d.month:02d}/{SERIES_KEY}{sequence}"


@frappe.whitelist()
def get_next_unique_number_preview(date):
    if not date:
        return ""

    return build_unique_number(date, get_next_sequence_preview())


class RMA(Document):
    def validate(self):
        if self.incident_number and self.date and self.is_new():
            if not self.unique_number:
                self.unique_number = get_next_unique_number_preview(self.date)

    def autoname(self):
        if not self.date:
            frappe.throw(_("Date is required before generating the Unique Number."))

        if not self.incident_number:
            frappe.throw(_("Incident Number is required before generating the Unique Number."))

        self.unique_number = allocate_unique_number(self.date)
        self.name = f"{self.unique_number}-{self.incident_number}"