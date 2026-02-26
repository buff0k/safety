from __future__ import annotations

from datetime import date, datetime

import frappe
from frappe import _

MONTHS = [
	("Jan", 1),
	("Feb", 2),
	("Mar", 3),
	("Apr", 4),
	("May", 5),
	("Jun", 6),
	("Jul", 7),
	("Aug", 8),
	("Sep", 9),
	("Oct", 10),
	("Nov", 11),
	("Dec", 12),
]

# Fixed order (matches your Select options exactly)
NATURE_OPTIONS = [
	"Amputation",
	"Abrasion",
	"Burn (Flame)",
	"Burn (Chemical)",
	"Burn (Steam/hot substance)",
	"Concussion",
	"Crushing (Injury)",
	"Contusion/bruise",
	"Dislocation",
	"Drowning",
	"Burn (Electric)",
	"Fracture",
	"Forgein body/splinter",
	"Heat Exhaustion",
	"Heatstroke",
	"Laceration",
	"Multiple Injury",
	"Poisoning",
	"Puncture",
	"Asphyxiation",
	"Sprain/Strain",
	"Other",
]


def execute(filters: dict | None = None):
	filters = filters or {}

	start_date, end_date = _resolve_dates(filters)
	year_cols = _years_between(start_date, end_date)

	columns = get_columns(year_cols)
	data = get_data(filters, start_date, end_date, year_cols)

	chart = get_chart(data, year_cols)
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def get_columns(year_cols: list[int]) -> list[dict]:
	cols = [
		{"label": _("NATURE OF INJURY"), "fieldname": "nature", "fieldtype": "Data", "width": 260},
		{"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 80},
	]

	for y in year_cols:
		cols.append({"label": str(y), "fieldname": f"y{y}", "fieldtype": "Int", "width": 70})

	for m_label, _m_num in MONTHS:
		cols.append({"label": _(m_label), "fieldname": m_label.lower(), "fieldtype": "Int", "width": 70})

	return cols


def get_data(filters: dict, start_date: str, end_date: str, year_cols: list[int]) -> list[dict]:
	conditions = [
		"im.incident_type = 'Injury'",
		"im.nature_of_the_injury IS NOT NULL",
		"im.nature_of_the_injury != ''",
		"DATE(im.datetime_incident) BETWEEN %(start_date)s AND %(end_date)s",
	]
	values = {"start_date": start_date, "end_date": end_date}

	if filters.get("site"):
		conditions.append("im.site = %(site)s")
		values["site"] = filters["site"]

	where_clause = " AND ".join(conditions)

	# Pull counts by Nature + Year + Month
	rows = frappe.db.sql(
		f"""
		SELECT
			im.nature_of_the_injury AS nature,
			YEAR(im.datetime_incident) AS yy,
			MONTH(im.datetime_incident) AS mm,
			COUNT(*) AS total
		FROM `tabIncident Management` im
		WHERE {where_clause}
		GROUP BY nature, yy, mm
		""",
		values=values,
		as_dict=True,
	)

	# matrix[nature]["years"][yy] and ["months"][mm]
	matrix: dict[str, dict[str, dict[int, int]]] = {}
	for r in rows:
		n = (r.get("nature") or "").strip()
		if not n:
			continue
		yy = int(r["yy"])
		mm = int(r["mm"])
		cnt = int(r["total"] or 0)

		matrix.setdefault(n, {"years": {}, "months": {}})
		matrix[n]["years"][yy] = matrix[n]["years"].get(yy, 0) + cnt
		matrix[n]["months"][mm] = matrix[n]["months"].get(mm, 0) + cnt

	# Output all options always (0s if none)
	out: list[dict] = []
	for opt in NATURE_OPTIONS:
		row = {"nature": opt}

		total = 0

		# year columns
		for y in year_cols:
			val = int(matrix.get(opt, {}).get("years", {}).get(y, 0))
			row[f"y{y}"] = val
			total += val

		# month columns (aggregated across all years in filter range)
		for m_label, m_num in MONTHS:
			val = int(matrix.get(opt, {}).get("months", {}).get(m_num, 0))
			row[m_label.lower()] = val

		row["total"] = total
		out.append(row)

	# Bottom Total Injuries row (sum of all options)
	total_row = {"nature": _("Total Injuries")}
	grand_total = 0

	# sum year cols
	for y in year_cols:
		s = sum(int(r.get(f"y{y}") or 0) for r in out)
		total_row[f"y{y}"] = s
		grand_total += s

	# sum months
	for m_label, _m_num in MONTHS:
		total_row[m_label.lower()] = sum(int(r.get(m_label.lower()) or 0) for r in out)

	total_row["total"] = grand_total
	out.append(total_row)

	return out


def get_chart(data: list[dict], year_cols: list[int]) -> dict:
	"""
	Horizontal bar chart like the TMM type chart:
	Total Injuries first, then each Nature sorted by Total desc.
	"""
	if not data:
		return {}

	total_row = data[-1] if str(data[-1].get("nature")) in ("Total Injuries", str(_("Total Injuries"))) else None
	grand_total = int(total_row.get("total") or 0) if total_row else 0

	rows = [r for r in data if str(r.get("nature")) not in ("Total Injuries", str(_("Total Injuries")))]
	rows_sorted = sorted(rows, key=lambda r: int(r.get("total") or 0), reverse=True)

	labels = ["Total Injuries"] + [r["nature"] for r in rows_sorted]
	values = [grand_total] + [int(r.get("total") or 0) for r in rows_sorted]

	return {
		"data": {
			"labels": labels,
			"datasets": [{"name": _("Total"), "values": values}],
		},
		"type": "bar",
		"barOptions": {
			"horizontal": 1,  # best compatibility
			"spaceRatio": 0.5,
		},
		"height": max(500, 26 * len(labels)),
	}


def get_report_summary(data: list[dict]) -> list[dict]:
	if not data:
		return [{"label": _("Total Injuries"), "value": 0, "datatype": "Int"}]

	last = data[-1]
	total = int(last.get("total") or 0) if "Total" in str(last.get("nature")) else 0
	return [{"label": _("Total Injuries"), "value": total, "datatype": "Int"}]


def _resolve_dates(filters: dict) -> tuple[str, str]:
	s = filters.get("start_date")
	e = filters.get("end_date")

	if s and e:
		return str(s), str(e)

	today = date.today()
	return str(s or date(today.year, 1, 1)), str(e or date(today.year, 12, 31))


def _years_between(start_date_str: str, end_date_str: str) -> list[int]:
	start = _to_date(start_date_str)
	end = _to_date(end_date_str)
	return list(range(start.year, end.year + 1))


def _to_date(d: str | date) -> date:
	if isinstance(d, date):
		return d
	try:
		return datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
	except Exception:
		return frappe.utils.getdate(d)