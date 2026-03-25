# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import get_datetime


SERIES_KEY = "IS/MM/"
SERIES_DIGITS = 5


def build_unique_number(datetime_value, sequence_number):
    d = get_datetime(datetime_value)
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


def allocate_unique_number(datetime_value):
    sequence = getseries(SERIES_KEY, SERIES_DIGITS)
    d = get_datetime(datetime_value)
    return f"{d.year:04d}-{d.month:02d}/{SERIES_KEY}{sequence}"


@frappe.whitelist()
def get_next_unique_number_preview(datetime_of_meeting_end):
    if not datetime_of_meeting_end:
        return ""

    return build_unique_number(datetime_of_meeting_end, get_next_sequence_preview())


class MeetingManager(Document):
    def validate(self):
        if self.datetime_of_meeting_end and self.is_new():
            if not self.unique_number:
                self.unique_number = get_next_unique_number_preview(self.datetime_of_meeting_end)

    def autoname(self):
        if not self.datetime_of_meeting_end:
            frappe.throw(_("Date and Time of Meeting End is required before generating the Unique Number."))

        self.unique_number = allocate_unique_number(self.datetime_of_meeting_end)
        self.name = self.unique_number