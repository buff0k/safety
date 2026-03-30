# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days, nowdate


class SafetyPerformanceCommunication(Document):
    pass


@frappe.whitelist()
def manual_sync_current_week():
    """
    Manual button action.
    Re-syncs the current week's Safety Performance Communication records.
    Creates missing records and updates existing ones.
    """
    result = sync_weekly_safety_performance_communications()
    frappe.db.commit()
    return result


def generate_weekly_safety_performance_communications():
    """
    Scheduler entry point for every Monday at 04:00.
    """
    result = sync_weekly_safety_performance_communications()
    frappe.db.commit()
    return result


def sync_weekly_safety_performance_communications(target_date=None):
    """
    Main process:
    1. Determine current Monday-Sunday week
    2. Find Talk Topics Child rows for that exact week
    3. If none exist, fall back to latest available Talk Topics week
    4. Create/update one Safety Performance Communication record per site
    5. Pull latest Injury and latest TMM/Property Damage incident info
    """
    current_week_start, current_week_end = get_monday_sunday_week(target_date)

    topic_rows, source_week_start, source_week_end, used_fallback = get_talk_topic_rows_for_sync(
        current_week_start=current_week_start,
        current_week_end=current_week_end,
    )

    if not topic_rows:
        return {
            "status": "warning",
            "message": "No Talk Topics rows were found for the current week or any previous week.",
            "created": 0,
            "updated": 0,
            "week_start_date": str(current_week_start),
            "week_end_date": str(current_week_end),
            "used_fallback": False,
            "sites": [],
        }

    created = 0
    updated = 0
    processed_sites = []

    # Keep one row per site for the selected source week
    latest_row_per_site = {}

    for row in topic_rows:
        site = row.get("site")
        if not site:
            continue

        existing = latest_row_per_site.get(site)
        if not existing:
            latest_row_per_site[site] = row
            continue

        existing_start = getdate(existing.get("start_date_of_week"))
        row_start = getdate(row.get("start_date_of_week"))

        # Prefer the latest row if duplicates somehow exist
        if row_start and existing_start and row_start >= existing_start:
            latest_row_per_site[site] = row

    for site, row in latest_row_per_site.items():
        talking_topic_attachment = row.get("attach_talk_topic_here")

        was_created = create_or_update_spc_record(
            site=site,
            week_start_date=source_week_start,
            week_end_date=source_week_end,
            talking_topic=talking_topic_attachment,
        )

        if was_created:
            created += 1
        else:
            updated += 1

        processed_sites.append(site)

    return {
        "status": "success",
        "message": "Safety Performance Communication sync completed.",
        "created": created,
        "updated": updated,
        "week_start_date": str(source_week_start),
        "week_end_date": str(source_week_end),
        "used_fallback": used_fallback,
        "sites": processed_sites,
    }


def create_or_update_spc_record(site, week_start_date, week_end_date, talking_topic=None):
    """
    Upsert one Safety Performance Communication record per site/week.
    """
    existing_name = frappe.db.get_value(
        "Safety Performance Communication",
        {
            "site": site,
            "week_start_date": week_start_date,
            "week_end_date": week_end_date,
        },
        "name",
    )

    injury = get_latest_incident_for_site(site=site, incident_group="injury")
    damage = get_latest_incident_for_site(site=site, incident_group="damage")

    values = {
        "site": site,
        "week_start_date": week_start_date,
        "week_end_date": week_end_date,
        "talking_topic": talking_topic or None,
        "latest_incident_description": injury.get("description_of_the_event") if injury else None,
        "latest_incident_date": getdate(injury.get("datetime_incident")) if injury and injury.get("datetime_incident") else None,
        "last_damage_description": damage.get("description_of_the_event") if damage else None,
        "latest_damage_date": getdate(damage.get("datetime_incident")) if damage and damage.get("datetime_incident") else None,
    }

    if existing_name:
        doc = frappe.get_doc("Safety Performance Communication", existing_name)
        doc.update(values)
        doc.save(ignore_permissions=True)
        return False

    doc = frappe.new_doc("Safety Performance Communication")
    doc.update(values)
    doc.insert(ignore_permissions=True)
    return True


def get_talk_topic_rows_for_sync(current_week_start, current_week_end):
    """
    Try exact current week first.
    If no rows are found, fall back to the latest available week.
    """
    current_rows = frappe.get_all(
        "Talk Topics Child",
        filters={
            "start_date_of_week": current_week_start,
            "end_date_of_week": current_week_end,
        },
        fields=[
            "name",
            "parent",
            "site",
            "company",
            "week",
            "start_date_of_week",
            "end_date_of_week",
            "attach_talk_topic_here",
            "idx",
        ],
        order_by="start_date_of_week desc, idx asc",
    )

    if current_rows:
        return current_rows, current_week_start, current_week_end, False

    latest_week = get_latest_available_talk_topic_week()
    if not latest_week:
        return [], current_week_start, current_week_end, False

    latest_start = latest_week["start_date_of_week"]
    latest_end = latest_week["end_date_of_week"]

    fallback_rows = frappe.get_all(
        "Talk Topics Child",
        filters={
            "start_date_of_week": latest_start,
            "end_date_of_week": latest_end,
        },
        fields=[
            "name",
            "parent",
            "site",
            "company",
            "week",
            "start_date_of_week",
            "end_date_of_week",
            "attach_talk_topic_here",
            "idx",
        ],
        order_by="start_date_of_week desc, idx asc",
    )

    return fallback_rows, latest_start, latest_end, True


def get_latest_available_talk_topic_week():
    """
    Find the latest available Talk Topics Child week.
    """
    result = frappe.db.sql(
        """
        SELECT
            start_date_of_week,
            end_date_of_week
        FROM `tabTalk Topics Child`
        WHERE start_date_of_week IS NOT NULL
          AND end_date_of_week IS NOT NULL
        ORDER BY start_date_of_week DESC, end_date_of_week DESC
        LIMIT 1
        """,
        as_dict=True,
    )

    if not result:
        return None

    return {
        "start_date_of_week": getdate(result[0].start_date_of_week),
        "end_date_of_week": getdate(result[0].end_date_of_week),
    }


def get_latest_incident_for_site(site, incident_group):
    """
    Fetch latest incident by site and incident type group.

    injury:
        Injury

    damage:
        TMM/Property Damage
        Property Damage
        TMM Damage
        TMM / Property Damage
    """
    if incident_group == "injury":
        incident_types = ["Injury"]
    elif incident_group == "damage":
        incident_types = [
            "TMM/Property Damage",
            "Property Damage",
            "TMM Damage",
            "TMM / Property Damage",
        ]
    else:
        return None

    placeholders = ", ".join(["%s"] * len(incident_types))
    values = [site] + incident_types

    result = frappe.db.sql(
        f"""
        SELECT
            name,
            site,
            incident_type,
            datetime_incident,
            description_of_the_event
        FROM `tabIncident Report`
        WHERE site = %s
          AND incident_type IN ({placeholders})
          AND datetime_incident IS NOT NULL
        ORDER BY datetime_incident DESC, creation DESC
        LIMIT 1
        """,
        values,
        as_dict=True,
    )

    return result[0] if result else None


def get_monday_sunday_week(target_date=None):
    """
    Return Monday and Sunday dates for the given date.
    """
    base_date = getdate(target_date or nowdate())
    monday = add_days(base_date, -base_date.weekday())
    sunday = add_days(monday, 6)
    return monday, sunday