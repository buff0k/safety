from __future__ import annotations

import calendar
from datetime import date, datetime

import frappe
from frappe import _

# Match your sheet column order: 06:00..23:00 then 00:00..05:00
HOURS_ORDER = list(range(6, 24)) + list(range(0, 6))


def execute(filters: dict | None = None):
	filters = filters or {}

	start_date, end_date = _resolve_dates(filters)
	start_dt = _to_date(start_date)
	end_dt = _to_date(end_date)
	years = list(range(start_dt.year, end_dt.year + 1))

	columns = get_columns()
	data = get_data(filters, start_date, end_date, years)

	chart = get_chart(data)
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def get_columns() -> list[dict]:
	cols = [
		{"label": _("Time"), "fieldname": "month", "fieldtype": "Data", "width": 90},
		{"label": _("Type"), "fieldname": "type", "fieldtype": "Data", "width": 80},
	]

	for h in HOURS_ORDER:
		cols.append(
			{
				"label": f"{h:02d}:00",
				"fieldname": f"h{h:02d}",
				"fieldtype": "Int",
				"width": 60,
			}
		)

	cols.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 85})
	return cols


def get_data(filters: dict, start_date: str, end_date: str, years: list[int]) -> list[dict]:
	conditions = ["DATE(im.datetime_incident) BETWEEN %(start_date)s AND %(end_date)s"]
	values = {"start_date": start_date, "end_date": end_date}

	if filters.get("site"):
		conditions.append("im.site = %(site)s")
		values["site"] = filters["site"]

	where_clause = " AND ".join(conditions)

	# One query to get both series counts by year, month, hour
	rows = frappe.db.sql(
		f"""
		SELECT
			YEAR(im.datetime_incident) AS yy,
			MONTH(im.datetime_incident) AS mm,
			HOUR(im.datetime_incident) AS hh,
			SUM(CASE WHEN im.tmm = 1 THEN 1 ELSE 0 END) AS tmm_cnt,
			SUM(CASE WHEN im.incident_type = 'Injury' THEN 1 ELSE 0 END) AS inj_cnt
		FROM `tabIncident Management` im
		WHERE {where_clause}
		GROUP BY yy, mm, hh
		ORDER BY yy, mm, hh
		""",
		values=values,
		as_dict=True,
	)

	# matrices: (yy, mm) -> hour -> count
	tmm = {}
	inj = {}
	for r in rows:
		key = (int(r["yy"]), int(r["mm"]))
		hh = int(r["hh"])
		tmm.setdefault(key, {})
		inj.setdefault(key, {})
		tmm[key][hh] = int(r.get("tmm_cnt") or 0)
		inj[key][hh] = int(r.get("inj_cnt") or 0)

	out: list[dict] = []

	# Month rows (Jan..Dec) aggregated across all years in range (like your sheet top section)
	for mm in range(1, 13):
		month_label = calendar.month_abbr[mm]
		tmm_month = _sum_across_years_for_month(tmm, years, mm)
		inj_month = _sum_across_years_for_month(inj, years, mm)
		out.append(_build_row(month_label, "TMM", tmm_month))
		out.append(_build_row("", "INJURY", inj_month))

	# Year rows (2025 TMM/INJURY, 2026 TMM/INJURY ...)
	for yy in years:
		tmm_year = _sum_for_year(tmm, yy)
		inj_year = _sum_for_year(inj, yy)
		out.append(_build_row(str(yy), "TMM", tmm_year))
		out.append(_build_row("", "INJURY", inj_year))

	# Final Total rows (Total TMM / Total INJURY)
	tmm_total = _sum_all_years(tmm, years)
	inj_total = _sum_all_years(inj, years)
	out.append(_build_row("Total", "TMM", tmm_total))
	out.append(_build_row("Total", "INJURY", inj_total))

	return out


def _build_row(month_label: str, type_label: str, hour_map: dict[int, int]) -> dict:
	row = {"month": month_label, "type": type_label}
	total = 0
	for h in HOURS_ORDER:
		val = int(hour_map.get(h, 0))
		row[f"h{h:02d}"] = val
		total += val
	row["total"] = total
	return row


def _sum_across_years_for_month(matrix: dict, years: list[int], mm: int) -> dict[int, int]:
	out = {h: 0 for h in range(0, 24)}
	for yy in years:
		for h, v in matrix.get((yy, mm), {}).items():
			out[int(h)] += int(v)
	return out


def _sum_for_year(matrix: dict, yy: int) -> dict[int, int]:
	out = {h: 0 for h in range(0, 24)}
	for mm in range(1, 13):
		for h, v in matrix.get((yy, mm), {}).items():
			out[int(h)] += int(v)
	return out


def _sum_all_years(matrix: dict, years: list[int]) -> dict[int, int]:
	out = {h: 0 for h in range(0, 24)}
	for yy in years:
		for mm in range(1, 13):
			for h, v in matrix.get((yy, mm), {}).items():
				out[int(h)] += int(v)
	return out


def get_chart(data: list[dict]) -> dict:
	"""
	Chart: hour totals from the bottom Total rows + Total bar.
	"""
	if not data:
		return {}

	total_tmm = next((r for r in reversed(data) if r.get("month") == "Total" and r.get("type") == "TMM"), None)
	total_inj = next((r for r in reversed(data) if r.get("month") == "Total" and r.get("type") == "INJURY"), None)
	if not total_tmm or not total_inj:
		return {}

	labels = [f"{h:02d}:00" for h in HOURS_ORDER] + ["Total"]

	tmm_vals = [int(total_tmm.get(f"h{h:02d}") or 0) for h in HOURS_ORDER] + [int(total_tmm.get("total") or 0)]
	inj_vals = [int(total_inj.get(f"h{h:02d}") or 0) for h in HOURS_ORDER] + [int(total_inj.get("total") or 0)]

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("TMM"), "values": tmm_vals},
				{"name": _("INJURY"), "values": inj_vals},
			],
		},
		"type": "bar",
	}


def get_report_summary(data: list[dict]) -> list[dict]:
	if not data:
		return [{"label": _("Grand Total (TMM + Injury)"), "value": 0, "datatype": "Int"}]

	total_tmm = next((r for r in reversed(data) if r.get("month") == "Total" and r.get("type") == "TMM"), None)
	total_inj = next((r for r in reversed(data) if r.get("month") == "Total" and r.get("type") == "INJURY"), None)

	total = int(total_tmm.get("total") or 0) + int(total_inj.get("total") or 0) if (total_tmm and total_inj) else 0
	return [{"label": _("Grand Total (TMM + Injury)"), "value": total, "datatype": "Int"}]


def _resolve_dates(filters: dict) -> tuple[str, str]:
	s = filters.get("start_date")
	e = filters.get("end_date")
	if s and e:
		return str(s), str(e)

	today = date.today()
	return str(s or date(today.year, 1, 1)), str(e or date(today.year, 12, 31))


def _to_date(d: str | date) -> date:
	if isinstance(d, date):
		return d
	try:
		return datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
	except Exception:
		return frappe.utils.getdate(d)