// Copyright (c) 2026, BuFf0k
// For license information, please see license.txt

frappe.pages["injuries-page"].on_page_load = function (wrapper) {
	new InjuriesDashboardPage(wrapper);
};

class InjuriesDashboardPage {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Injuries Page"),
			single_column: true,
		});

		// Must match Query Report names exactly
		this.report_names = [
			"TMM and Injury per shift",
			"TMM and Injury Hour of Day",
			"TMM and Injury Specific Day",
			"TMM and Injury per day of the Month",
			"Body Part Injured",
			"Task Performed when Injured",
			"Injury Type",
		];

		// Per-report cache used by BOTH tabs (graphs built from info tab data)
		// cache[report_name] = { columns, result, message, chart }
		this.cache = {};

		// Card state holders
		this.info_cards = []; // {report_name, $host, datatable, $status}
		this.graph_cards = []; // {report_name, $host, chart_instance, $status}

		this.build_layout();
		this.bind_events();

		// Blank filters by default (as requested)
		this.clear_filters_silently();

		// Load once on page load
		this.refresh_information(true);
	}

	// --------------------- Layout ---------------------

	build_layout() {
		this.$root = $(`<div class="injuries-dashboard-root"></div>`).appendTo(this.page.main);

		// Top bar: Filters + Actions
		this.$topbar = $(`<div class="injuries-topbar"></div>`).appendTo(this.$root);

		this.start_date = frappe.ui.form.make_control({
			parent: this.$topbar,
			df: { fieldname: "start_date", label: __("Start Date"), fieldtype: "Date" },
			render_input: true,
		});

		this.end_date = frappe.ui.form.make_control({
			parent: this.$topbar,
			df: { fieldname: "end_date", label: __("End Date"), fieldtype: "Date" },
			render_input: true,
		});

		this.site = frappe.ui.form.make_control({
			parent: this.$topbar,
			df: { fieldname: "site", label: __("Site"), fieldtype: "Link", options: "Branch" },
			render_input: true,
		});

		this.$actions = $(`<div class="injuries-actions"></div>`).appendTo(this.$topbar);
		this.$apply = $(`<button class="btn btn-primary">${__("Apply")}</button>`).appendTo(this.$actions);
		this.$reset = $(`<button class="btn btn-default">${__("Reset")}</button>`).appendTo(this.$actions);

		// Tab bar like your screenshot (pill buttons)
		this.$tabbar = $(`
			<div class="injuries-tabbar">
				<button class="injuries-tab active" data-tab="info">${__("Information")}</button>
				<button class="injuries-tab" data-tab="graphs">${__("Graphs")}</button>
			</div>
		`).appendTo(this.$root);

		// Tab panels
		this.$panels = $(`<div class="injuries-panels"></div>`).appendTo(this.$root);
		this.$panel_info = $(`<div class="injuries-panel active" data-tab-panel="info"></div>`).appendTo(this.$panels);
		this.$panel_graphs = $(`<div class="injuries-panel" data-tab-panel="graphs"></div>`).appendTo(this.$panels);

		// Grids
		this.$info_grid = $(`<div class="injuries-grid"></div>`).appendTo(this.$panel_info);
		this.$graphs_grid = $(`<div class="injuries-grid"></div>`).appendTo(this.$panel_graphs);

		// Cards for Information tab
		this.report_names.forEach((report_name) => {
			const card = this.make_card(this.$info_grid, report_name, "info");
			this.info_cards.push(card);
		});

		// Cards for Graphs tab
		this.report_names.forEach((report_name) => {
			const card = this.make_card(this.$graphs_grid, report_name, "graphs");
			this.graph_cards.push(card);
		});
	}

	make_card($parent, report_name, mode) {
		const $card = $(`
			<div class="injuries-card">
				<div class="injuries-card-header">
					<div class="injuries-card-title"></div>
					<div class="injuries-card-tools">
						<button class="btn btn-xs btn-default injuries-refresh">${__("Refresh")}</button>
					</div>
				</div>
				<div class="injuries-card-body">
					<div class="injuries-card-status text-muted">${__("Ready")}</div>
					<div class="injuries-card-host"></div>
				</div>
			</div>
		`).appendTo($parent);

		$card.find(".injuries-card-title").text(report_name);

		const state = {
			mode,
			report_name,
			$card,
			$status: $card.find(".injuries-card-status"),
			$host: $card.find(".injuries-card-host"),
			datatable: null,
			chart_instance: null,
		};

		$card.find(".injuries-refresh").on("click", () => {
			if (mode === "info") this.refresh_information_one(state, true);
			else this.render_graph_one(state, true); // graphs render from cache
		});

		return state;
	}

	// --------------------- Events ---------------------

	bind_events() {
		// Apply / Reset
		this.$apply.on("click", () => this.refresh_information(true));
		this.$reset.on("click", () => {
			this.clear_filters_silently();
			this.refresh_information(true);
		});

		// Tabs
		this.$tabbar.on("click", ".injuries-tab", (e) => {
			const tab = $(e.currentTarget).data("tab");
			this.set_active_tab(tab);

			// IMPORTANT: Graphs are built from cached Information data
			// So when switching to graphs, just render from cache (no server call)
			if (tab === "graphs") {
				this.render_graphs_from_cache();
			}
		});

		// Optional: auto-run when filters change (remove if you only want Apply button)
		const on_change = () => this.refresh_information(false);
		[this.start_date, this.end_date, this.site].forEach((c) => c.$input && c.$input.on("change", on_change));
	}

	set_active_tab(tab) {
		this.$tabbar.find(".injuries-tab").removeClass("active");
		this.$tabbar.find(`.injuries-tab[data-tab="${tab}"]`).addClass("active");

		this.$panels.find(".injuries-panel").removeClass("active");
		this.$panels.find(`.injuries-panel[data-tab-panel="${tab}"]`).addClass("active");
	}

	// --------------------- Filters ---------------------

	clear_filters_silently() {
		this.start_date.set_value(null);
		this.end_date.set_value(null);
		this.site.set_value(null);
	}

	get_filters_for_report(show_messages = false) {
		const filters = {};
		const start_date = this.start_date.get_value();
		const end_date = this.end_date.get_value();
		const site = this.site.get_value();

		// Validate date range only if both provided
		if (start_date && end_date && start_date > end_date) {
			if (show_messages) {
				frappe.msgprint({
					title: __("Invalid Date Range"),
					message: __("Start Date cannot be after End Date. Dates will be ignored."),
					indicator: "red",
				});
			}
		} else {
			if (start_date) filters.start_date = start_date;
			if (end_date) filters.end_date = end_date;
		}

		if (site) filters.site = site;

		return filters;
	}

	// --------------------- Backend ---------------------

	async run_report(report_name, show_messages = false) {
		const filters = this.get_filters_for_report(show_messages);
		const r = await frappe.call({
			method: "frappe.desk.query_report.run",
			args: { report_name, filters },
			freeze: false,
		});
		return r.message; // { columns, result, message, chart, ... }
	}

	// --------------------- Information tab (fetch + render + cache) ---------------------

	async refresh_information(show_messages = false) {
		await Promise.all(this.info_cards.map((c) => this.refresh_information_one(c, show_messages)));

		// After info refresh, if user is on graphs tab, re-render graphs using new cache
		const is_graphs = this.$tabbar.find('.injuries-tab.active').data("tab") === "graphs";
		if (is_graphs) this.render_graphs_from_cache();
	}

	async refresh_information_one(card, show_messages = false) {
		card.$status.text(__("Loading…"));
		card.$card.addClass("injuries-loading");

		try {
			const data = await this.run_report(card.report_name, show_messages);

			// Cache the raw data for graphs tab
			this.cache[card.report_name] = {
				columns: data.columns || [],
				result: data.result || [],
				message: data.message || null,
				chart: data.chart || null,
			};

			this.render_table(card, data);
			card.$status.text(__("Last updated: {0}", [frappe.datetime.now_datetime()]));
		} catch (e) {
			console.error(e);
			card.$status.text(__("Failed to load report."));
			card.$host.empty().append(
				`<div class="text-danger">${__("Error running report. Check console/server logs.")}</div>`
			);
		} finally {
			card.$card.removeClass("injuries-loading");
		}
	}

	render_table(card, data) {
		card.$host.empty();

		const columns_raw = (data && data.columns) || [];
		const rows_raw = (data && data.result) || [];

		if (data && data.message) {
			card.$host.append(
				`<div class="text-muted" style="margin-bottom:8px;">${frappe.utils.escape_html(data.message)}</div>`
			);
		}

		if (!columns_raw.length) {
			card.$host.append(`<div class="text-muted">${__("No columns returned by report.")}</div>`);
			return;
		}

		const columns = columns_raw.map((c, idx) => {
			if (typeof c === "string") return { name: c, id: `col_${idx}`, editable: false, sortable: true };
			return {
				name: c.label || c.fieldname || c.name || `Column ${idx + 1}`,
				id: c.fieldname || c.name || `col_${idx}`,
				editable: false,
				sortable: true,
			};
		});

		const rows = rows_raw.map((row) => {
			if (Array.isArray(row)) {
				const obj = {};
				columns.forEach((col, i) => (obj[col.id] = row[i]));
				return obj;
			}
			return row;
		});

		if (!rows.length) {
			card.$host.append(`<div class="text-muted">${__("No data.")}</div>`);
			return;
		}

		if (card.datatable && card.datatable.destroy) {
			try {
				card.datatable.destroy();
			} catch (e) {}
			card.datatable = null;
		}

		const el = $(`<div class="injuries-datatable"></div>`).appendTo(card.$host)[0];

		card.datatable = new frappe.DataTable(el, {
			columns,
			data: rows,
			layout: "fluid",
			noDataMessage: __("No data"),
			disableReorderColumn: true,
			inlineFilters: false,
		});
	}

	// --------------------- Graphs tab (render from cache ONLY) ---------------------

	render_graphs_from_cache() {
		this.graph_cards.forEach((c) => this.render_graph_one(c, false));
	}

	render_graph_one(card, show_messages = false) {
		card.$status.text(__("Rendering…"));
		card.$card.addClass("injuries-loading");

		try {
			const cached = this.cache[card.report_name];

			if (!cached) {
				card.$host.empty().append(
					`<div class="text-muted">${__("No cached data yet. Go to Information tab and click Apply/Refresh.")}</div>`
				);
				card.$status.text(__("Waiting for data"));
				return;
			}

			this.render_chart_from_cached(card, cached, show_messages);
			card.$status.text(__("Last updated: {0}", [frappe.datetime.now_datetime()]));
		} finally {
			card.$card.removeClass("injuries-loading");
		}
	}

	render_chart_from_cached(card, cached, show_messages = false) {
		card.$host.empty();

		// destroy existing chart
		if (card.chart_instance && card.chart_instance.destroy) {
			try {
				card.chart_instance.destroy();
			} catch (e) {}
			card.chart_instance = null;
		}

		// Prefer report-provided chart if available (best)
		if (cached.chart && cached.chart.data && cached.chart.data.labels) {
			const el = $(`<div class="injuries-chart-host"></div>`).appendTo(card.$host)[0];
			card.chart_instance = new frappe.Chart(el, cached.chart);
			return;
		}

		// Fallback: infer bar chart from cached result
		const columns_raw = cached.columns || [];
		const rows_raw = cached.result || [];

		if (!columns_raw.length || !rows_raw.length) {
			card.$host.append(`<div class="text-muted">${__("No data to chart.")}</div>`);
			return;
		}

		const col_ids = columns_raw.map((c, idx) => {
			if (typeof c === "string") return `col_${idx}`;
			return c.fieldname || c.name || `col_${idx}`;
		});

		const rows_as_arrays = rows_raw.map((row) => {
			if (Array.isArray(row)) return row;
			return col_ids.map((id) => row[id]);
		});

		const is_number = (v) =>
			v !== null && v !== undefined && v !== "" && !isNaN(parseFloat(v)) && isFinite(v);

		let label_idx = -1;
		let value_idx = -1;

		for (let i = 0; i < col_ids.length; i++) {
			const sample = rows_as_arrays.slice(0, 10).map((r) => r[i]);
			const numeric_count = sample.filter(is_number).length;
			if (numeric_count <= Math.floor(sample.length / 3)) {
				label_idx = i;
				break;
			}
		}

		for (let i = 0; i < col_ids.length; i++) {
			const sample = rows_as_arrays.slice(0, 10).map((r) => r[i]);
			const numeric_count = sample.filter(is_number).length;
			if (numeric_count >= Math.ceil(sample.length / 2)) {
				value_idx = i;
				break;
			}
		}

		if (label_idx === -1) label_idx = 0;
		if (value_idx === -1) value_idx = Math.min(1, col_ids.length - 1);

		const labels = rows_as_arrays.map((r) => String(r[label_idx] ?? ""));
		const values = rows_as_arrays.map((r) => (is_number(r[value_idx]) ? parseFloat(r[value_idx]) : 0));

		const MAX_BARS = 30;
		let chart_labels = labels;
		let chart_values = values;

		if (labels.length > MAX_BARS) {
			chart_labels = labels.slice(0, MAX_BARS);
			chart_values = values.slice(0, MAX_BARS);
			card.$host.append(
				`<div class="text-muted" style="margin-bottom:8px;">${__(
					"Showing first {0} bars (report returned {1} rows).",
					[MAX_BARS, labels.length]
				)}</div>`
			);
		}

		const chart_config = {
			type: "bar",
			data: {
				labels: chart_labels,
				datasets: [{ name: __("Value"), values: chart_values }],
			},
			barOptions: { stacked: 0, spaceRatio: 0.5 },
			truncateLegends: 1,
			axisOptions: { xAxisMode: "tick", yAxisMode: "span" },
			height: 260,
		};

		const el = $(`<div class="injuries-chart-host"></div>`).appendTo(card.$host)[0];
		card.chart_instance = new frappe.Chart(el, chart_config);
	}
}