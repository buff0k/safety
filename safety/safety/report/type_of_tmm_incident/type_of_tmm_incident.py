from __future__ import annotations

from datetime import date

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

# This is the fixed order you requested (matches your Select options)
INCIDENT_TYPES = [
	"ADT overturned (Bowl)",
	"ADT overturned (Head)",
	"ADT overturned (Head &Bowl)",
	"TMM overturned on it side",
	"TMM drove into/onto safety berm",
	"TMM drove into a stationary TMM",
	"TMM reverse into a stationary TMM",
	"TMM drove into a structure",
	"TMM reverse into a structure",
	"TMM Moved forward - damage",
	"TMM Moved forward - no damage",
	"TMM running out of control",
	"TMM hooked overhead powerline",
	"TMM Smoldering (Smoke Only)",
	"TMM Fire (Engine)",
	"TMM Fire (Complete Machine)",
	"TMM Damaged (Other)",
	"TMM Damaged by rocks",
	"TMM Struck by lightning",
	"LDV Struck by Lightning",
	"LDV Overturned",
	"LDV Drove into/onto safety berm",
	"LDV reverse into a stationary LDV",
	"LDV Drove forward into structure",
	"LDV Reverse into structure/Equipment",
	"LDV Fire",
	"LDV Other (Animals)",
	"Private Vehicle Other",
]


def execute(filters: dict | None = None):
	filters = filters or {}

	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def get_columns() -> list[dict]:
	cols = [
		{"label": _("Type of TMM Incident"), "fieldname": "incident_type", "fieldtype": "Data", "width": 320},
	]
	for m_label, _m_num in MONTHS:
		cols.append({"label": _(m_label), "fieldname": m_label.lower(), "fieldtype": "Int", "width": 80})
	cols.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 90})
	return cols


def get_data(filters: dict) -> list[dict]:
	start_date, end_date = _resolve_dates(filters)

	conditions = [
		"im.tmm = 1",
		"im.type_of_tmm_incident IS NOT NULL",
		"im.type_of_tmm_incident != ''",
		"DATE(im.datetime_incident) BETWEEN %(start_date)s AND %(end_date)s",
	]
	values = {"start_date": start_date, "end_date": end_date}

	if filters.get("site"):
		conditions.append("im.site = %(site)s")
		values["site"] = filters["site"]

	where_clause = " AND ".join(conditions)

	# Aggregate counts by type and month
	rows = frappe.db.sql(
		f"""
		SELECT
			im.type_of_tmm_incident AS incident_type,
			MONTH(im.datetime_incident) AS mm,
			COUNT(*) AS total
		FROM `tabIncident Management` im
		WHERE {where_clause}
		GROUP BY incident_type, mm
		""",
		values=values,
		as_dict=True,
	)

	# Build a lookup: (incident_type -> month -> count)
	matrix: dict[str, dict[int, int]] = {}
	for r in rows:
		it = (r.get("incident_type") or "").strip()
		if not it:
			continue
		matrix.setdefault(it, {})
		matrix[it][int(r["mm"])] = int(r["total"] or 0)

	# Always output ALL incident types in the fixed order
	out: list[dict] = []
	for it in INCIDENT_TYPES:
		row = {"incident_type": it}
		row_total = 0
		for m_label, m_num in MONTHS:
			val = int(matrix.get(it, {}).get(m_num, 0))
			row[m_label.lower()] = val
			row_total += val
		row["total"] = row_total
		out.append(row)

	# Bottom Total row
	total_row = {"incident_type": _("Total")}
	grand_total = 0
	for m_label, _m_num in MONTHS:
		s = sum(int(r.get(m_label.lower()) or 0) for r in out)
		total_row[m_label.lower()] = s
		grand_total += s
	total_row["total"] = grand_total
	out.append(total_row)

	return out


def get_chart(data: list[dict]) -> dict:
	"""
	Chart: Top 10 incident types by Total (excluding the Total row) + a Total bar.
	"""
	if not data:
		return {}

	rows = [r for r in data if str(r.get("incident_type")) not in ("Total", str(_("Total")))]
	rows_sorted = sorted(rows, key=lambda r: int(r.get("total") or 0), reverse=True)
	top = rows_sorted[:10]

	labels = [r["incident_type"] for r in top]
	values = [int(r.get("total") or 0) for r in top]

	labels.append("Total")
	values.append(sum(values))

	return {
		"data": {
			"labels": labels,
			"datasets": [{"name": _("Incidents"), "values": values}],
		},
		"type": "bar",
	}


def get_report_summary(data: list[dict]) -> list[dict]:
	if not data:
		return [{"label": _("Total TMM Incidents"), "value": 0, "datatype": "Int"}]

	last = data[-1]
	total = int(last.get("total") or 0) if str(last.get("incident_type")) in ("Total", str(_("Total"))) else 0
	return [{"label": _("Total TMM Incidents"), "value": total, "datatype": "Int"}]


def _resolve_dates(filters: dict) -> tuple[str, str]:
	s = filters.get("start_date")
	e = filters.get("end_date")

	if s and e:
		return str(s), str(e)

	today = date.today()
	return str(s or date(today.year, 1, 1)), str(e or date(today.year, 12, 31))