// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.query_reports["Site Safe Days"] = {
  filters: [
    {
      fieldname: "site",
      label: __("Site"),
      fieldtype: "MultiSelectList",
      get_data: function (txt) {
        return frappe.db.get_link_options("Branch", txt);
      }
    },
    {
      fieldname: "employer",
      label: __("Employer"),
      fieldtype: "Link",
      options: "DocType",
      get_query: () => ({
        filters: [["DocType", "name", "in", ["Supplier", "Company"]]]
      })
    },
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Dynamic Link",
      options: "employer"
    },
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date"
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      default: frappe.datetime.get_today()
    }
  ],

  onload: async function (report) {
    // Default from_date to earliest configured Site Start Date
    const r = await frappe.call({
      method: "safety.safety.report.site_safe_days.site_safe_days.get_default_from_date",
      args: { sites: [] }
    });

    if (r.message && !report.get_values().from_date) {
      report.set_filter_value("from_date", r.message);
    }

    // ----------------------------------------------------
    // Auto-refresh exactly on the hour (HH:00), then hourly
    // ----------------------------------------------------
    // Avoid stacking timers if report is opened multiple times
    if (report._isd_refresh_timer) {
      clearInterval(report._isd_refresh_timer);
      report._isd_refresh_timer = null;
    }
    if (report._isd_refresh_timeout) {
      clearTimeout(report._isd_refresh_timeout);
      report._isd_refresh_timeout = null;
    }

    const refresh_if_visible = () => {
      try {
        if (cur_report && cur_report.report_name === "Site Safe Days") {
          report.refresh();
        }
      } catch (e) {
        // ignore
      }
    };

    // milliseconds until next exact hour
    const ms_until_next_hour = () => {
      const now = new Date();
      const next = new Date(now);
      next.setMinutes(0, 0, 0);        // HH:00:00.000
      next.setHours(now.getHours() + 1); // next hour
      return Math.max(0, next.getTime() - now.getTime());
    };

    // 1) wait until next hour boundary
    report._isd_refresh_timeout = setTimeout(() => {
      refresh_if_visible();

      // 2) then refresh every hour exactly
      report._isd_refresh_timer = setInterval(() => {
        refresh_if_visible();
      }, 60 * 60 * 1000);
    }, ms_until_next_hour());

    // Clear timers when leaving the report view
    if (!report._isd_route_hooked) {
      report._isd_route_hooked = true;

      frappe.router.on("change", () => {
        try {
          const route = frappe.get_route();
          const is_on_this_report =
            route &&
            route[0] === "query-report" &&
            route[1] === "Site Safe Days";

          if (!is_on_this_report) {
            if (report._isd_refresh_timer) {
              clearInterval(report._isd_refresh_timer);
              report._isd_refresh_timer = null;
            }
            if (report._isd_refresh_timeout) {
              clearTimeout(report._isd_refresh_timeout);
              report._isd_refresh_timeout = null;
            }
          }
        } catch (e) {
          // ignore
        }
      });
    }
  },

  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);

    // Bigger font everywhere (1–1.5 sizes, safe)
    const big = (html) =>
      `<span style="font-size:14px; line-height:1.25;">${html}</span>`;

    if (!data) return big(value);

    // Do not highlight group/separator rows
    if (data.site === "Company" && !data.date) return big(value);
    if (!data.date) return big(value);

    // Map report columns -> incident flags set by Python
    const flag_map = {
      "lti_free_days": "incident_lti_today",
      "tif_days": "incident_tif_today",
      "mtc_days": "incident_mtc_today",
      "fac_days": "incident_fac_today",
      "pdi_days": "incident_pdi_today",
      "env_days": "incident_env_today",

      "num_lti": "incident_lti_today",
      "num_mtc": "incident_mtc_today",
      "num_fac": "incident_fac_today",
      "num_pdi": "incident_pdi_today",
      "num_env": "incident_env_today"
    };

    const flag_field = flag_map[column.fieldname];
    const is_incident_cell =
      flag_field && (data[flag_field] === 1 || data[flag_field] === true);

    if (is_incident_cell) {
      return `
        <span style="
          display:inline-block;
          width:100%;
          padding:3px 6px;
          background:#d90429;
          color:#fff;
          font-weight:700;
          border-radius:3px;
          font-size:14px;
          line-height:1.25;
        ">${value}</span>
      `;
    }

    return big(value);
  }
};
