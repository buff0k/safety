# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days, get_url_to_form
from datetime import timedelta


# --------------------------
# Helpers
# --------------------------
SYSTEM_ROW_FIELDS = {
    "name", "owner", "creation", "modified", "modified_by",
    "parent", "parentfield", "parenttype", "idx", "docstatus"
}


def normalize_text(value):
    return str(value or "").strip().lower()


def row_to_values(row):
    if not row:
        return []

    row_dict = row.as_dict() if hasattr(row, "as_dict") else dict(row)
    values = []

    for key, val in row_dict.items():
        if key in SYSTEM_ROW_FIELDS:
            continue
        if isinstance(val, (str, int, float)) and val not in ("", None):
            values.append(str(val).strip())

    return values


def extract_table_values(doc, fieldname):
    rows = doc.get(fieldname) or []
    out = []

    for row in rows:
        for val in row_to_values(row):
            if val and val not in out:
                out.append(val)

    return out


def contains_any(values, targets):
    normalized_values = [normalize_text(v) for v in values if v not in (None, "")]
    for value in normalized_values:
        for target in targets:
            t = normalize_text(target)
            if value == t or t in value:
                return True
    return False


def get_incident_flags_from_report(doc):
    """
    Same incident classification logic as Site Safe Days.

    select_type_of_incident:
      - LTI
      - MTC
      - FAC
      - PDI when Trackless Mobile Machinery / Property Damage / PDI

    type_of_impact:
      - Environmental Impact -> ENV
    """
    incident_types = extract_table_values(doc, "select_type_of_incident")
    impact_types = extract_table_values(doc, "type_of_impact")

    lti = contains_any(
        incident_types,
        ["LTI", "Lost Time Injury"]
    )

    mtc = contains_any(
        incident_types,
        ["MTC", "Medical Treatment Case"]
    )

    fac = contains_any(
        incident_types,
        ["FAC", "First Aid Case", "First Aid"]
    )

    pdi = contains_any(
        incident_types,
        ["Trackless Mobile Machinery", "Property Damage", "PDI"]
    )

    env = contains_any(
        impact_types,
        ["Environmental Impact"]
    )

    tif = lti or mtc or fac

    return {
        "lti": lti,
        "mtc": mtc,
        "fac": fac,
        "pdi": pdi,
        "env": env,
        "tif": tif,
    }


# --------------------------
# Head Office Start Dates singleton
# --------------------------
def get_head_office_start_config():
    doc = frappe.get_single("Head Office Start Dates")

    out = {
        "_head_office_ltifr_target": doc.get("head_office_ltifr_target"),
        "_head_office_ltifr_actual": doc.get("head_office_ltifr_actual"),
        "_head_office_color": (doc.get("head_office_color") or "").strip(),
    }

    for row in doc.get("head_office_start_date", []):
        site = row.get("site")
        start_date = row.get("start_date")

        if not (site and start_date):
            continue

        out[site] = {
            "start_date": getdate(start_date),
            "ltifr_target": row.get("ltifr_target"),
            "ltifr": row.get("ltifr"),
            "color": (row.get("color") or "").strip(),
            "complex": row.get("complex") or "Other",
        }

    return out


@frappe.whitelist()
def get_default_from_date(site=None):
    """
    Kept only as a helper if needed elsewhere.
    Not used by the report JS, so the filter stays blank by default.
    """
    cfg = get_head_office_start_config()

    if site:
        row = cfg.get(site)
        if isinstance(row, dict) and row.get("start_date"):
            return row["start_date"].strftime("%Y-%m-%d")
        return None

    starts = [
        v["start_date"]
        for k, v in cfg.items()
        if isinstance(v, dict) and v.get("start_date")
    ]

    return min(starts).strftime("%Y-%m-%d") if starts else None


# --------------------------
# Report entrypoint
# --------------------------
def execute(filters=None):
    filters = filters or {}

    cfg = get_head_office_start_config()

    selected_site = filters.get("site")
    selected_sites = [selected_site] if selected_site else [
        k for k, v in cfg.items() if isinstance(v, dict)
    ]

    from_date = getdate(filters.get("from_date")) if filters.get("from_date") else None
    to_date = getdate(filters.get("to_date")) if filters.get("to_date") else getdate()

    columns = get_columns()

    if not selected_sites:
        return columns, []

    # Need one day before the visible start range so streak logic works correctly.
    # If from_date is blank, use the earliest configured start date across selected sites.
    effective_query_start = from_date or min(
        cfg[s]["start_date"]
        for s in selected_sites
        if s in cfg and isinstance(cfg.get(s), dict) and cfg[s].get("start_date")
    )
    query_from = add_days(effective_query_start, -1)

    incidents = fetch_incidents(
        sites=selected_sites,
        date_from=query_from,
        date_to=to_date,
        employer=filters.get("employer"),
        company=filters.get("company"),
    )

    data = []

    for site in selected_sites:
        if site not in cfg or not isinstance(cfg.get(site), dict):
            continue

        site_start = cfg[site]["start_date"]
        ltifr_target = cfg[site].get("ltifr_target")
        ltifr_value = cfg[site].get("ltifr")

        # Important behavior:
        # - if from_date is blank, start from the configured child-table date for THIS site
        # - if from_date is filled, start from max(configured start, filter date)
        start = max(site_start, from_date) if from_date else site_start

        if start > to_date:
            continue

        data.extend(
            build_site_daily_rows(
                site=site,
                start_date=start,
                end_date=to_date,
                site_start_date=site_start,
                ltifr_target=ltifr_target,
                ltifr_value=ltifr_value,
                incidents=incidents.get(site, {}),
            )
        )

    data.extend(
        build_head_office_summary(
            selected_sites=selected_sites,
            cfg=cfg,
            from_date=from_date,
            to_date=to_date,
            incidents_by_site=incidents,
            head_office_ltifr_target=cfg.get("_head_office_ltifr_target"),
            head_office_ltifr_actual=cfg.get("_head_office_ltifr_actual"),
        )
    )

    return columns, data


def get_columns():
    return [
        {"label": _("Site"), "fieldname": "site", "fieldtype": "Data", "width": 180},
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},

        {"label": _("LTI Free Days Mine Wide"), "fieldname": "lti_free_days", "fieldtype": "Int", "width": 180},
        {"label": _("TIF Days"), "fieldname": "tif_days", "fieldtype": "Int", "width": 110},
        {"label": _("Medical Treatment Case"), "fieldname": "mtc_days", "fieldtype": "Int", "width": 180},
        {"label": _("First Aid case"), "fieldname": "fac_days", "fieldtype": "Int", "width": 140},
        {"label": _("PDI"), "fieldname": "pdi_days", "fieldtype": "Int", "width": 140},
        {"label": _("Environmental Incident"), "fieldname": "env_days", "fieldtype": "Int", "width": 190},

        {"label": _("Number of LTI's"), "fieldname": "num_lti", "fieldtype": "Int", "width": 140},
        {"label": _("Number of MTC's"), "fieldname": "num_mtc", "fieldtype": "Int", "width": 150},
        {"label": _("Number of FAC"), "fieldname": "num_fac", "fieldtype": "Int", "width": 130},
        {"label": _("PDI"), "fieldname": "num_pdi", "fieldtype": "Int", "width": 80},
        {"label": _("Environmental Incidents"), "fieldname": "num_env", "fieldtype": "Int", "width": 190},

        {"label": _("LTIFR Target"), "fieldname": "ltifr_target", "fieldtype": "Float", "width": 120},
        {"label": _("LTIFR"), "fieldname": "ltifr", "fieldtype": "Float", "width": 90},
        {"label": _("FFPS"), "fieldname": "ffps", "fieldtype": "Float", "width": 90},
        {"label": _("FFMS"), "fieldname": "ffms", "fieldtype": "Float", "width": 90},

        {"label": _("Incident Link(s)"), "fieldname": "incident_links", "fieldtype": "HTML", "width": 260},

        {"label": "", "fieldname": "incident_lti_today", "fieldtype": "Int", "hidden": 1},
        {"label": "", "fieldname": "incident_tif_today", "fieldtype": "Int", "hidden": 1},
        {"label": "", "fieldname": "incident_mtc_today", "fieldtype": "Int", "hidden": 1},
        {"label": "", "fieldname": "incident_fac_today", "fieldtype": "Int", "hidden": 1},
        {"label": "", "fieldname": "incident_pdi_today", "fieldtype": "Int", "hidden": 1},
        {"label": "", "fieldname": "incident_env_today", "fieldtype": "Int", "hidden": 1},
    ]


def fetch_incidents(sites, date_from, date_to, employer=None, company=None):
    if not sites:
        return {}

    filters = {
        "site": ["in", sites],
        "docstatus": ["in", [0, 1]],
        "datetime_incident": ["between", [f"{date_from} 00:00:00", f"{date_to} 23:59:59"]],
    }

    rows = frappe.get_all(
        "Incident Report",
        filters=filters,
        fields=[
            "name",
            "incident_number",
            "site",
            "datetime_incident",
            "event_category",
            "employer",
            "company",
        ],
        order_by="datetime_incident asc",
    )

    out = {s: {} for s in sites}

    for r in rows:
        if employer and r.get("employer") != employer:
            continue
        if company and r.get("company") != company:
            continue

        event_category = (r.get("event_category") or "").strip()
        if event_category and event_category != "Incident (INC)":
            continue

        site = r.get("site")
        if not site or site not in sites:
            continue

        doc = frappe.get_doc("Incident Report", r["name"])
        flags = get_incident_flags_from_report(doc)

        if not any([flags["lti"], flags["mtc"], flags["fac"], flags["pdi"], flags["env"]]):
            continue

        d = getdate(doc.get("datetime_incident"))

        if d not in out[site]:
            out[site][d] = {
                "lti": False,
                "mtc": False,
                "fac": False,
                "pdi": False,
                "env": False,
                "tif": False,
                "counts": {"lti": 0, "mtc": 0, "fac": 0, "pdi": 0, "env": 0},
                "links": [],
            }

        out[site][d]["lti"] |= flags["lti"]
        out[site][d]["mtc"] |= flags["mtc"]
        out[site][d]["fac"] |= flags["fac"]
        out[site][d]["pdi"] |= flags["pdi"]
        out[site][d]["env"] |= flags["env"]
        out[site][d]["tif"] |= flags["tif"]

        out[site][d]["counts"]["lti"] += 1 if flags["lti"] else 0
        out[site][d]["counts"]["mtc"] += 1 if flags["mtc"] else 0
        out[site][d]["counts"]["fac"] += 1 if flags["fac"] else 0
        out[site][d]["counts"]["pdi"] += 1 if flags["pdi"] else 0
        out[site][d]["counts"]["env"] += 1 if flags["env"] else 0

        out[site][d]["links"].append({
            "docname": doc.name,
            "label": doc.get("incident_number") or doc.name
        })

    return out


def build_site_daily_rows(site, start_date, end_date, site_start_date, ltifr_target, ltifr_value, incidents):
    streak = {"lti": 0, "tif": 0, "mtc": 0, "fac": 0, "pdi": 0, "env": 0}
    totals = {"lti": 0, "mtc": 0, "fac": 0, "pdi": 0, "env": 0}

    data = []
    d = start_date

    while d <= end_date:
        if d == site_start_date:
            streak = {k: 0 for k in streak}
        else:
            prev = d - timedelta(days=1)
            prev_flags = incidents.get(prev) or {}

            streak["lti"] = 0 if prev_flags.get("lti") else streak["lti"] + 1
            streak["tif"] = 0 if prev_flags.get("tif") else streak["tif"] + 1
            streak["mtc"] = 0 if prev_flags.get("mtc") else streak["mtc"] + 1
            streak["fac"] = 0 if prev_flags.get("fac") else streak["fac"] + 1
            streak["pdi"] = 0 if prev_flags.get("pdi") else streak["pdi"] + 1
            streak["env"] = 0 if prev_flags.get("env") else streak["env"] + 1

        today = incidents.get(d) or {}
        c = today.get("counts") or {}

        totals["lti"] += c.get("lti", 0)
        totals["mtc"] += c.get("mtc", 0)
        totals["fac"] += c.get("fac", 0)
        totals["pdi"] += c.get("pdi", 0)
        totals["env"] += c.get("env", 0)

        incident_links_html = build_incident_links_html(today.get("links") or [])

        data.append({
            "site": site,
            "date": d,

            "lti_free_days": streak["lti"],
            "tif_days": streak["tif"],
            "mtc_days": streak["mtc"],
            "fac_days": streak["fac"],
            "pdi_days": streak["pdi"],
            "env_days": streak["env"],

            "num_lti": totals["lti"],
            "num_mtc": totals["mtc"],
            "num_fac": totals["fac"],
            "num_pdi": totals["pdi"],
            "num_env": totals["env"],

            "ltifr_target": ltifr_target,
            "ltifr": ltifr_value,

            "ffps": None,
            "ffms": None,

            "incident_links": incident_links_html,

            "incident_lti_today": 1 if today.get("lti") else 0,
            "incident_tif_today": 1 if today.get("tif") else 0,
            "incident_mtc_today": 1 if today.get("mtc") else 0,
            "incident_fac_today": 1 if today.get("fac") else 0,
            "incident_pdi_today": 1 if today.get("pdi") else 0,
            "incident_env_today": 1 if today.get("env") else 0,
        })

        d = add_days(d, 1)

    return data


def build_incident_links_html(link_rows):
    if not link_rows:
        return ""

    parts = []
    for row in link_rows:
        docname = row.get("docname")
        label = row.get("label") or docname

        if not docname:
            continue

        url = get_url_to_form("Incident Report", docname)
        safe_label = frappe.utils.escape_html(label)
        parts.append(f"<div><a href='{url}' target='_blank'>View {safe_label}</a></div>")

    return "".join(parts)


def build_head_office_summary(
    selected_sites,
    cfg,
    from_date,
    to_date,
    incidents_by_site,
    head_office_ltifr_target=None,
    head_office_ltifr_actual=None
):
    if not selected_sites:
        return []

    starts = [
        cfg[s]["start_date"]
        for s in selected_sites
        if s in cfg and isinstance(cfg.get(s), dict) and cfg[s].get("start_date")
    ]
    if not starts:
        return []

    head_office_start = min(starts)

    # If from_date is blank, summary starts from earliest configured start date
    # among selected sites.
    start = max(head_office_start, from_date) if from_date else head_office_start
    if start > to_date:
        return []

    merged = {}
    for site in selected_sites:
        for d, info in (incidents_by_site.get(site) or {}).items():
            if d not in merged:
                merged[d] = {
                    "lti": False,
                    "tif": False,
                    "mtc": False,
                    "fac": False,
                    "pdi": False,
                    "env": False,
                    "counts": {"lti": 0, "mtc": 0, "fac": 0, "pdi": 0, "env": 0},
                    "links": [],
                }

            for k in ["lti", "tif", "mtc", "fac", "pdi", "env"]:
                merged[d][k] = merged[d][k] or bool(info.get(k))

            for k in ["lti", "mtc", "fac", "pdi", "env"]:
                merged[d]["counts"][k] += (info.get("counts") or {}).get(k, 0)

            merged[d]["links"].extend(info.get("links") or [])

    out = []
    out.extend(
        build_site_daily_rows(
            site="Head Office",
            start_date=start,
            end_date=to_date,
            site_start_date=head_office_start,
            ltifr_target=head_office_ltifr_target,
            ltifr_value=head_office_ltifr_actual,
            incidents=merged,
        )
    )

    for row in out:
        row["site"] = "Head Office"
        row["incident_links"] = ""

    return out


@frappe.whitelist()
def get_today_snapshot(filters=None):
    if filters is None:
        filters = {}
    elif isinstance(filters, str):
        try:
            filters = frappe.parse_json(filters) or {}
        except Exception:
            filters = {}
    elif not isinstance(filters, dict):
        filters = {}

    today = getdate()
    filters["to_date"] = today.strftime("%Y-%m-%d")

    columns, data = execute(filters)

    today_rows = [r for r in data if r.get("date") == today and r.get("site")]
    by_site = {r.get("site"): r for r in today_rows if r.get("site")}

    complex_by_site = {}
    color_by_site = {}
    head_office_color = ""

    try:
        hod = frappe.get_single("Head Office Start Dates")
        head_office_color = (hod.get("head_office_color") or "").strip()

        for row in hod.get("head_office_start_date", []):
            site = row.get("site")
            if not site:
                continue

            complex_by_site[site] = row.get("complex") or "Other"
            color_by_site[site] = (row.get("color") or "").strip()
    except Exception:
        pass

    if "Head Office" in by_site:
        complex_by_site.setdefault("Head Office", "Head Office")
        if head_office_color:
            color_by_site["Head Office"] = head_office_color

    for site in by_site.keys():
        if site == "Head Office":
            continue
        complex_by_site.setdefault(site, "Other")
        color_by_site.setdefault(site, "")

    return {
        "today": today.strftime("%Y-%m-%d"),
        "rows": by_site,
        "complex_by_site": complex_by_site,
        "color_by_site": color_by_site,
        "head_office_color": head_office_color,
    }