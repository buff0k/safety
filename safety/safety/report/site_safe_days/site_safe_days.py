# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days, get_url_to_form
from datetime import timedelta


# --------------------------
# Helpers
# --------------------------
def is_checked(v) -> bool:
    """Frappe Check fields can come back as 0/1 or '0'/'1'. Avoid bool('0') == True."""
    try:
        return int(v or 0) == 1
    except Exception:
        return False


# --------------------------
# Site Start Dates singleton
# --------------------------
def get_site_start_config():
    """
    Site Start Dates (Singleton) fields used:
      - company_ltifr_target (Float)
      - company_ltifr_actual (Float)   <-- NEW (your field)
      - company_colour (Data)          <-- NEW (your field, hex)

    Child table Site Start Date Child fields used:
      - site (Link Branch)
      - start_date (Date)
      - ltifr_target (Float)
      - ltifr (Float)                 <-- for per-site LTIFR column
      - complex (Data/Select)         <-- used by get_today_snapshot
      - color (Data)                  <-- used by get_today_snapshot
    """
    doc = frappe.get_single("Site Start Dates")

    out = {
        "_company_ltifr_target": doc.get("company_ltifr_target"),
        "_company_ltifr_actual": doc.get("company_ltifr_actual"),
        "_company_colour": (doc.get("company_colour") or "").strip(),
    }

    for row in doc.get("site_and_start_date", []):
        site = row.get("site")
        start_date = row.get("start_date")

        if not (site and start_date):
            continue

        out[site] = {
            "start_date": getdate(start_date),
            "ltifr_target": row.get("ltifr_target"),
            "ltifr": row.get("ltifr"),  # per-site LTIFR (requested)
        }

    return out


@frappe.whitelist()
def get_default_from_date(sites=None):
    sites = sites or []
    cfg = get_site_start_config()

    if sites:
        starts = [
            cfg[s]["start_date"]
            for s in sites
            if s in cfg and isinstance(cfg.get(s), dict) and cfg[s].get("start_date")
        ]
    else:
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

    selected_sites = filters.get("site") or []
    if isinstance(selected_sites, str):
        try:
            parsed = frappe.parse_json(selected_sites)
            selected_sites = parsed if isinstance(parsed, list) else [parsed]
        except Exception:
            selected_sites = [selected_sites]

    cfg = get_site_start_config()
    company_ltifr_target = cfg.get("_company_ltifr_target")
    company_ltifr_actual = cfg.get("_company_ltifr_actual")

    # If no site filter, include all configured sites (excluding internal keys)
    if not selected_sites:
        selected_sites = [k for k, v in cfg.items() if isinstance(v, dict)]

    from_date = getdate(filters.get("from_date")) if filters.get("from_date") else None
    to_date = getdate(filters.get("to_date")) if filters.get("to_date") else getdate()

    columns = get_columns()

    # Include 1 day before start (streak depends on previous day)
    query_from = add_days(from_date, -1) if from_date else add_days(to_date, -365)

    incidents = fetch_incidents(selected_sites, query_from, to_date)

    data = []

    for site in selected_sites:
        if site not in cfg or not isinstance(cfg.get(site), dict):
            continue

        site_start = cfg[site]["start_date"]
        ltifr_target = cfg[site].get("ltifr_target")
        ltifr_value = cfg[site].get("ltifr")

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

    # Company summary at bottom (Company LTIFR Target + Actual)
    data.extend(
        build_company_summary(
            selected_sites=selected_sites,
            cfg=cfg,
            from_date=from_date,
            to_date=to_date,
            incidents_by_site=incidents,
            company_ltifr_target=company_ltifr_target,
            company_ltifr_actual=company_ltifr_actual,
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
        {"label": _("Property Damage"), "fieldname": "pdi_days", "fieldtype": "Int", "width": 140},
        {"label": _("Environmental Incident"), "fieldname": "env_days", "fieldtype": "Int", "width": 190},

        {"label": _("Number of LTI's"), "fieldname": "num_lti", "fieldtype": "Int", "width": 140},
        {"label": _("Number of MTC's"), "fieldname": "num_mtc", "fieldtype": "Int", "width": 150},
        {"label": _("Number of FAC"), "fieldname": "num_fac", "fieldtype": "Int", "width": 130},
        {"label": _("PDI"), "fieldname": "num_pdi", "fieldtype": "Int", "width": 80},
        {"label": _("Environmental Incidents"), "fieldname": "num_env", "fieldtype": "Int", "width": 190},

        {"label": _("LTIFR Target"), "fieldname": "ltifr_target", "fieldtype": "Float", "width": 120},

        # LTIFR column:
        # - Per site: Site Start Date Child.ltifr
        # - Company: Site Start Dates.company_ltifr_actual
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


def fetch_incidents(sites, date_from, date_to):
    rows = frappe.get_all(
        "Incident Management",
        filters={
            "site": ["in", sites],
            "event_category": "Incident (INC)",
            "docstatus": ["in", [0, 1]],
            "datetime_incident": ["between", [f"{date_from} 00:00:00", f"{date_to} 23:59:59"]],
        },
        fields=[
            "name",
            "site",
            "datetime_incident",
            "lti",
            "medical_treatment_case",
            "first_aid_case",
            "property_damage",
            "tmm",
            "environmental_impact",
        ],
        order_by="datetime_incident asc",
    )

    out = {s: {} for s in sites}

    for r in rows:
        d = getdate(r["datetime_incident"])
        site = r["site"]

        if site not in out:
            out[site] = {}

        if d not in out[site]:
            out[site][d] = {
                "lti": False, "mtc": False, "fac": False, "pdi": False, "env": False, "tif": False,
                "counts": {"lti": 0, "mtc": 0, "fac": 0, "pdi": 0, "env": 0},
                "names": [],
            }

        docname = r["name"]

        lti = is_checked(r.get("lti"))
        mtc = is_checked(r.get("medical_treatment_case"))
        fac = is_checked(r.get("first_aid_case"))
        pdi = is_checked(r.get("property_damage")) or is_checked(r.get("tmm"))
        env = is_checked(r.get("environmental_impact"))
        tif = lti or mtc or fac

        out[site][d]["lti"] |= lti
        out[site][d]["mtc"] |= mtc
        out[site][d]["fac"] |= fac
        out[site][d]["pdi"] |= pdi
        out[site][d]["env"] |= env
        out[site][d]["tif"] |= tif

        out[site][d]["counts"]["lti"] += 1 if lti else 0
        out[site][d]["counts"]["mtc"] += 1 if mtc else 0
        out[site][d]["counts"]["fac"] += 1 if fac else 0
        out[site][d]["counts"]["pdi"] += 1 if pdi else 0
        out[site][d]["counts"]["env"] += 1 if env else 0

        out[site][d]["names"].append(docname)

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

        incident_links_html = build_incident_links_html(today.get("names") or [])

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


def build_incident_links_html(docnames):
    if not docnames:
        return ""

    parts = []
    for name in docnames:
        url = get_url_to_form("Incident Management", name)
        safe_name = frappe.utils.escape_html(name)
        parts.append(f"<div><a href='{url}' target='_blank'>View {safe_name}</a></div>")

    return "".join(parts)


def build_company_summary(selected_sites, cfg, from_date, to_date, incidents_by_site,
                          company_ltifr_target=None, company_ltifr_actual=None):
    if not selected_sites:
        return []

    starts = [cfg[s]["start_date"] for s in selected_sites if s in cfg and isinstance(cfg.get(s), dict)]
    if not starts:
        return []

    company_start = min(starts)
    start = max(company_start, from_date) if from_date else company_start
    if start > to_date:
        return []

    merged = {}
    for site in selected_sites:
        for d, info in (incidents_by_site.get(site) or {}).items():
            if d not in merged:
                merged[d] = {
                    "lti": False, "tif": False, "mtc": False, "fac": False, "pdi": False, "env": False,
                    "counts": {"lti": 0, "mtc": 0, "fac": 0, "pdi": 0, "env": 0},
                    "names": [],
                }

            for k in ["lti", "tif", "mtc", "fac", "pdi", "env"]:
                merged[d][k] = merged[d][k] or bool(info.get(k))

            for k in ["lti", "mtc", "fac", "pdi", "env"]:
                merged[d]["counts"][k] += (info.get("counts") or {}).get(k, 0)

    out = []
    out.extend(
        build_site_daily_rows(
            site="Company",
            start_date=start,
            end_date=to_date,
            site_start_date=company_start,
            ltifr_target=company_ltifr_target,   # Target from singleton
            ltifr_value=company_ltifr_actual,    # Actual from singleton (your new field)
            incidents=merged,
        )
    )

    for row in out:
        row["site"] = "Company"
        row["incident_links"] = ""

    return out


@frappe.whitelist()
def get_today_snapshot(filters=None):
    """
    Runs Site Safe Days report and returns ONLY today's rows.

    Adds:
      - complex_by_site: from Site Start Date Child.complex
      - color_by_site: from Site Start Date Child.color (hex)
      - company_colour: from Site Start Dates.company_colour (hex)  <-- NEW
        and maps it as color_by_site["Company"]
    """
    from frappe.utils import getdate

    # normalize filters
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

    if not filters.get("from_date"):
        try:
            filters["from_date"] = get_default_from_date([])
        except Exception:
            filters["from_date"] = today.strftime("%Y-%m-%d")

    columns, data = execute(filters)

    today_rows = [r for r in data if r.get("date") == today and r.get("site")]
    by_site = {r.get("site"): r for r in today_rows if r.get("site")}

    complex_by_site = {}
    color_by_site = {}
    company_colour = ""

    try:
        ssd = frappe.get_single("Site Start Dates")
        company_colour = (ssd.get("company_colour") or "").strip()

        for row in ssd.get("site_and_start_date", []):
            site = row.get("site")
            if not site:
                continue

            complex_by_site[site] = row.get("complex") or "Other"
            color_by_site[site] = (row.get("color") or "").strip()
    except Exception:
        pass

    # Ensure company is always available to the dashboard
    if "Company" in by_site:
        complex_by_site.setdefault("Company", "Company")
        if company_colour:
            color_by_site["Company"] = company_colour

    for site in by_site.keys():
        if site == "Company":
            continue
        complex_by_site.setdefault(site, "Other")
        color_by_site.setdefault(site, "")

    return {
        "today": today.strftime("%Y-%m-%d"),
        "rows": by_site,
        "complex_by_site": complex_by_site,
        "color_by_site": color_by_site,
        "company_colour": company_colour,
    }
