from __future__ import annotations

import calendar
from datetime import date, datetime

import frappe
from frappe import _

# Excel layout: Mon..Sun
DOW_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


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
		{"label": _("Day of Week"), "fieldname": "month", "fieldtype": "Data", "width": 90},
		{"label": _("Type"), "fieldname": "type", "fieldtype": "Data", "width": 80},
	]
	for d in DOW_ORDER:
		cols.append({"label": _(d), "fieldname": d.lower(), "fieldtype": "Int", "width": 75})
	cols.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 85})
	return cols


def get_data(filters: dict, start_date: str, end_date: str, years: list[int]) -> list[dict]:
	conditions = ["DATE(im.datetime_incident) BETWEEN %(start_date)s AND %(end_date)s"]
	values = {"start_date": start_date, "end_date": end_date}

	if filters.get("site"):
		conditions.append("im.site = %(site)s")
		values["site"] = filters["site"]

	where_clause = " AND ".join(conditions)

	# WEEKDAY(): 0=Mon..6=Sun
	rows = frappe.db.sql(
		f"""
		SELECT
			YEAR(im.datetime_incident) AS yy,
			MONTH(im.datetime_incident) AS mm,
			WEEKDAY(im.datetime_incident) AS wd,
			SUM(CASE WHEN im.tmm = 1 THEN 1 ELSE 0 END) AS tmm_cnt,
			SUM(CASE WHEN im.incident_type = 'Injury' THEN 1 ELSE 0 END) AS inj_cnt
		FROM `tabIncident Management` im
		WHERE {where_clause}
		GROUP BY yy, mm, wd
		ORDER BY yy, mm, wd
		""",
		values=values,
		as_dict=True,
	)

	# matrices: (yy, mm) -> dow -> count
	tmm = {}
	inj = {}
	for r in rows:
		key = (int(r["yy"]), int(r["mm"]))
		dow = DOW_ORDER[int(r["wd"])]
		tmm.setdefault(key, {})
		inj.setdefault(key, {})
		tmm[key][dow] = int(r.get("tmm_cnt") or 0)
		inj[key][dow] = int(r.get("inj_cnt") or 0)

	out: list[dict] = []

	# Month rows (Jan..Dec), each month has TMM row then INJURY row
	for mm in range(1, 13):
		month_label = calendar.month_abbr[mm]
		# aggregate across all years in range for this month (like the sheet top section)
		tmm_month = _sum_across_years_for_month(tmm, years, mm)
		inj_month = _sum_across_years_for_month(inj, years, mm)

		out.append(_build_row(month_label, "TMM", tmm_month))
		out.append(_build_row("", "INJURY", inj_month))

	# Year totals (2025 TMM / 2025 INJURY, 2026 TMM / 2026 INJURY ...)
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


def _build_row(month_label: str, type_label: str, dow_map: dict[str, int]) -> dict:
	row = {"month": month_label, "type": type_label}
	total = 0
	for d in DOW_ORDER:
		val = int(dow_map.get(d, 0))
		row[d.lower()] = val
		total += val
	row["total"] = total
	return row


def _sum_across_years_for_month(matrix: dict, years: list[int], mm: int) -> dict[str, int]:
	out = {d: 0 for d in DOW_ORDER}
	for yy in years:
		for d in DOW_ORDER:
			out[d] += int(matrix.get((yy, mm), {}).get(d, 0))
	return out


def _sum_for_year(matrix: dict, yy: int) -> dict[str, int]:
	out = {d: 0 for d in DOW_ORDER}
	for mm in range(1, 13):
		for d in DOW_ORDER:
			out[d] += int(matrix.get((yy, mm), {}).get(d, 0))
	return out


def _sum_all_years(matrix: dict, years: list[int]) -> dict[str, int]:
	out = {d: 0 for d in DOW_ORDER}
	for yy in years:
		for mm in range(1, 13):
			for d in DOW_ORDER:
				out[d] += int(matrix.get((yy, mm), {}).get(d, 0))
	return out


def get_chart(data: list[dict]) -> dict:
	"""
	Chart: weekday totals for Total TMM and Total INJURY + Total bar.
	"""
	if not data:
		return {}

	total_tmm = next((r for r in reversed(data) if r.get("month") == "Total" and r.get("type") == "TMM"), None)
	total_inj = next((r for r in reversed(data) if r.get("month") == "Total" and r.get("type") == "INJURY"), None)
	if not total_tmm or not total_inj:
		return {}

	labels = DOW_ORDER + ["Total"]

	tmm_vals = [int(total_tmm.get(d.lower()) or 0) for d in DOW_ORDER] + [int(total_tmm.get("total") or 0)]
	inj_vals = [int(total_inj.get(d.lower()) or 0) for d in DOW_ORDER] + [int(total_inj.get("total") or 0)]

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