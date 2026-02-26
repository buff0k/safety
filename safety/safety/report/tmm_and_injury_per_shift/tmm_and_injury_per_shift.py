from __future__ import annotations

import calendar
from datetime import date, datetime

import frappe
from frappe import _

# Shift values exactly as in DocType
SHIFT_DAY_1 = "Day 1"
SHIFT_DAY_2 = "Day 2"
SHIFT_DAY_3 = "Day 3"
SHIFT_NIGHT_1 = "Night 1"
SHIFT_NIGHT_2 = "Night 2"
SHIFT_NIGHT_3 = "Night 3"

SHIFT_COLS = [
	("day1", _("1st Day Shift"), SHIFT_DAY_1),
	("day2", _("2nd Day Shift"), SHIFT_DAY_2),
	("day3", _("3rd Day Shift"), SHIFT_DAY_3),
	("night1", _("1st Night Shift"), SHIFT_NIGHT_1),
	("night2", _("2nd Night Shift"), SHIFT_NIGHT_2),
	("night3", _("3rd Night Shift"), SHIFT_NIGHT_3),
]


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
		{"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 90},
		{"label": _("Type"), "fieldname": "type", "fieldtype": "Data", "width": 80},
	]

	for fieldname, label, _shift_value in SHIFT_COLS:
		cols.append({"label": label, "fieldname": fieldname, "fieldtype": "Int", "width": 110})

	cols.append({"label": _("Day Shift Only"), "fieldname": "day_only", "fieldtype": "Int", "width": 120})
	cols.append({"label": _("Total / Month"), "fieldname": "total", "fieldtype": "Int", "width": 120})
	return cols


def get_data(filters: dict, start_date: str, end_date: str, years: list[int]) -> list[dict]:
	conditions = ["DATE(im.datetime_incident) BETWEEN %(start_date)s AND %(end_date)s"]
	values = {"start_date": start_date, "end_date": end_date}

	if filters.get("site"):
		conditions.append("im.site = %(site)s")
		values["site"] = filters["site"]

	where_clause = " AND ".join(conditions)

	# Aggregate by year, month, shift for both series (TMM vs Injury)
	rows = frappe.db.sql(
		f"""
		SELECT
			YEAR(im.datetime_incident) AS yy,
			MONTH(im.datetime_incident) AS mm,
			im.shift AS shift,
			SUM(CASE WHEN im.tmm = 1 THEN 1 ELSE 0 END) AS tmm_cnt,
			SUM(CASE WHEN im.incident_type = 'Injury' THEN 1 ELSE 0 END) AS inj_cnt
		FROM `tabIncident Management` im
		WHERE {where_clause}
		  AND IFNULL(im.shift, '') <> ''
		GROUP BY yy, mm, shift
		ORDER BY yy, mm, shift
		""",
		values=values,
		as_dict=True,
	)

	# matrices: (yy, mm) -> shift_value -> count
	tmm = {}
	inj = {}
	for r in rows:
		yy = int(r["yy"])
		mm = int(r["mm"])
		shift_val = (r.get("shift") or "").strip()
		key = (yy, mm)

		tmm.setdefault(key, {})
		inj.setdefault(key, {})

		tmm[key][shift_val] = int(r.get("tmm_cnt") or 0)
		inj[key][shift_val] = int(r.get("inj_cnt") or 0)

	out: list[dict] = []

	# Month rows (Jan..Dec) aggregated across years (matches your sheet layout)
	for mm in range(1, 13):
		month_label = calendar.month_abbr[mm]
		tmm_month = _sum_across_years_for_month(tmm, years, mm)
		inj_month = _sum_across_years_for_month(inj, years, mm)

		out.append(_build_row(month_label, "TMM", tmm_month))
		out.append(_build_row("", "INJURY", inj_month))

	# Year rows (2025/2026 etc)
	for yy in years:
		tmm_year = _sum_for_year(tmm, yy)
		inj_year = _sum_for_year(inj, yy)

		out.append(_build_row(str(yy), "TMM", tmm_year))
		out.append(_build_row("", "INJURY", inj_year))

	# Totals
	tmm_total = _sum_all_years(tmm, years)
	inj_total = _sum_all_years(inj, years)

	out.append(_build_row("Total", "TMM", tmm_total))
	out.append(_build_row("Total", "INJURY", inj_total))

	return out


def _build_row(month_label: str, type_label: str, shift_map: dict[str, int]) -> dict:
	row = {"month": month_label, "type": type_label}

	day1 = int(shift_map.get(SHIFT_DAY_1, 0))
	day2 = int(shift_map.get(SHIFT_DAY_2, 0))
	day3 = int(shift_map.get(SHIFT_DAY_3, 0))

	night1 = int(shift_map.get(SHIFT_NIGHT_1, 0))
	night2 = int(shift_map.get(SHIFT_NIGHT_2, 0))
	night3 = int(shift_map.get(SHIFT_NIGHT_3, 0))

	# Fill individual columns
	row["day1"] = day1
	row["day2"] = day2
	row["day3"] = day3
	row["night1"] = night1
	row["night2"] = night2
	row["night3"] = night3

	# Computed columns (matches Excel)
	row["day_only"] = day1 + day2 + day3
	row["total"] = day1 + day2 + day3 + night1 + night2 + night3

	return row


def _sum_across_years_for_month(matrix: dict, years: list[int], mm: int) -> dict[str, int]:
	out = {SHIFT_DAY_1: 0, SHIFT_DAY_2: 0, SHIFT_DAY_3: 0, SHIFT_NIGHT_1: 0, SHIFT_NIGHT_2: 0, SHIFT_NIGHT_3: 0}
	for yy in years:
		key = (yy, mm)
		for shift in out.keys():
			out[shift] += int(matrix.get(key, {}).get(shift, 0))
	return out


def _sum_for_year(matrix: dict, yy: int) -> dict[str, int]:
	out = {SHIFT_DAY_1: 0, SHIFT_DAY_2: 0, SHIFT_DAY_3: 0, SHIFT_NIGHT_1: 0, SHIFT_NIGHT_2: 0, SHIFT_NIGHT_3: 0}
	for mm in range(1, 13):
		key = (yy, mm)
		for shift in out.keys():
			out[shift] += int(matrix.get(key, {}).get(shift, 0))
	return out


def _sum_all_years(matrix: dict, years: list[int]) -> dict[str, int]:
	out = {SHIFT_DAY_1: 0, SHIFT_DAY_2: 0, SHIFT_DAY_3: 0, SHIFT_NIGHT_1: 0, SHIFT_NIGHT_2: 0, SHIFT_NIGHT_3: 0}
	for yy in years:
		for mm in range(1, 13):
			key = (yy, mm)
			for shift in out.keys():
				out[shift] += int(matrix.get(key, {}).get(shift, 0))
	return out


def get_chart(data: list[dict]) -> dict:
	"""
	Chart: totals by shift (from the bottom Total rows).
	"""
	if not data:
		return {}

	total_tmm = next((r for r in reversed(data) if r.get("month") == "Total" and r.get("type") == "TMM"), None)
	total_inj = next((r for r in reversed(data) if r.get("month") == "Total" and r.get("type") == "INJURY"), None)
	if not total_tmm or not total_inj:
		return {}

	labels = [label for _fn, label, _sv in SHIFT_COLS] + [_("Day Shift Only"), _("Total / Month")]

	tmm_vals = [
		int(total_tmm.get("day1") or 0),
		int(total_tmm.get("day2") or 0),
		int(total_tmm.get("day3") or 0),
		int(total_tmm.get("night1") or 0),
		int(total_tmm.get("night2") or 0),
		int(total_tmm.get("night3") or 0),
		int(total_tmm.get("day_only") or 0),
		int(total_tmm.get("total") or 0),
	]

	inj_vals = [
		int(total_inj.get("day1") or 0),
		int(total_inj.get("day2") or 0),
		int(total_inj.get("day3") or 0),
		int(total_inj.get("night1") or 0),
		int(total_inj.get("night2") or 0),
		int(total_inj.get("night3") or 0),
		int(total_inj.get("day_only") or 0),
		int(total_inj.get("total") or 0),
	]

	return {
		"data": {"labels": labels, "datasets": [{"name": _("TMM"), "values": tmm_vals}, {"name": _("INJURY"), "values": inj_vals}]},
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