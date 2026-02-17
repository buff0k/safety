frappe.pages["safety-dashboard"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Safety Dashboard",
    single_column: true
  });

  inject_css(wrapper);

  const root = document.createElement("div");
  root.className = "isd-wrap";
  page.main[0].appendChild(root);

  // ---------------------------
  // On-the-hour refresh helpers
  // ---------------------------
  let refreshTimer = null;

  function ms_until_next_hour() {
    const now = new Date();
    const next = new Date(now);
    next.setMinutes(0, 0, 0);
    next.setHours(now.getHours() + 1);
    return Math.max(0, next.getTime() - now.getTime());
  }

  function schedule_on_the_hour_refresh(loadFn) {
    // Clear any existing timer(s)
    if (refreshTimer) {
      clearTimeout(refreshTimer);
      refreshTimer = null;
    }

    const wait = ms_until_next_hour();

    // First tick aligns to next whole hour,
    // then we re-schedule again so it stays aligned even if load time varies.
    refreshTimer = setTimeout(async () => {
      try {
        await loadFn();
      } finally {
        schedule_on_the_hour_refresh(loadFn);
      }
    }, wait);
  }

  async function load() {
    root.innerHTML = `<div class="isd-loading">Loading…</div>`;

    const r = await frappe.call({
      method: "safety.safety.report.site_safe_days.site_safe_days.get_today_snapshot",
      args: { filters: {} }
    });

    const payload = r.message || {};
    const rows = payload.rows || {};
    const complexBySite = payload.complex_by_site || {};
    const colorBySite = payload.color_by_site || {};
    const companyColor = (payload.company_colour || "").trim();

    const companyRow = rows["Company"] || null;

    // Group sites by complex
    const groups = {};
    Object.keys(rows)
      .filter(site => site && site !== "Company")
      .forEach(site => {
        const complex = (complexBySite[site] || "Other").toString().trim() || "Other";
        if (!groups[complex]) groups[complex] = [];
        groups[complex].push(site);
      });

    // Stable ordering
    const complexNames = Object.keys(groups).sort((a, b) => a.localeCompare(b));
    complexNames.forEach(c => groups[c].sort((a, b) => a.localeCompare(b)));

    // Render
    root.innerHTML = "";

    const top = document.createElement("div");
    top.className = "isd-top";
    top.appendChild(render_company_card(companyRow, companyColor));
    root.appendChild(top);

    const grid = document.createElement("div");
    grid.className = "isd-grid-2";
    root.appendChild(grid);

    const left = document.createElement("div");
    left.className = "isd-col";
    const right = document.createElement("div");
    right.className = "isd-col";

    complexNames.forEach((complex, idx) => {
      const col = (idx % 2 === 0) ? left : right;
      col.appendChild(render_heading(complex.toUpperCase()));

      (groups[complex] || []).forEach(site => {
        const row = rows[site] || {};
        const siteColor = (colorBySite[site] || "").trim();
        col.appendChild(render_site_card(site, row, siteColor));
      });
    });

    grid.appendChild(left);
    grid.appendChild(render_divider());
    grid.appendChild(right);

    if (!left.children.length || !right.children.length) {
      grid.classList.add("isd-no-divider");
    }
  }

  // Initial load immediately
  load();

  // Refresh exactly on the hour (e.g., 10:00, 11:00, 12:00...)
  schedule_on_the_hour_refresh(load);

  // Optional: clean up timers when navigating away
  if (page && page.wrapper) {
    $(page.wrapper).on("page-change", function () {
      if (refreshTimer) clearTimeout(refreshTimer);
    });
  }
};


// ---------------------------
// Rendering helpers
// ---------------------------
function render_heading(text) {
  const h = document.createElement("div");
  h.className = "isd-heading";
  h.innerText = text;
  return h;
}

function render_divider() {
  const d = document.createElement("div");
  d.className = "isd-divider";
  return d;
}

function render_company_card(row, companyColor) {
  const card = document.createElement("div");
  card.className = "isd-card isd-company";

  // company colour from Site Start Dates.company_colour (fallback to red if missing/invalid)
  if (companyColor && is_valid_hex(companyColor)) card.style.background = companyColor;
  else card.style.background = "#FF0000";

  const ltifrTarget = row?.ltifr_target ?? "";
  const ltifrActual = (row?.ltifr ?? "—");
  const scratchFree = row?.tif_days ?? "—";

  const ltiFree = row?.lti_free_days ?? "";
  const mtcFree = row?.mtc_days ?? "";
  const facFree = row?.fac_days ?? "";
  const pdiFree = row?.pdi_days ?? "";

  card.innerHTML = build_card_html(
    "Isambane Mining",
    ltifrTarget,
    ltifrActual,
    scratchFree,
    ltiFree,
    mtcFree,
    facFree,
    pdiFree
  );
  return card;
}

function render_site_card(site, row, siteColor) {
  const card = document.createElement("div");
  card.className = "isd-card";

  if (siteColor && is_valid_hex(siteColor)) card.style.background = siteColor;
  else card.style.background = "#4f86c6";

  const ltifrTarget = row?.ltifr_target ?? "";
  const ltifrActual = (row?.ltifr ?? "—");
  const scratchFree = row?.tif_days ?? "—";

  const ltiFree = row?.lti_free_days ?? "";
  const mtcFree = row?.mtc_days ?? "";
  const facFree = row?.fac_days ?? "";
  const pdiFree = row?.pdi_days ?? "";

  card.innerHTML = build_card_html(
    site,
    ltifrTarget,
    ltifrActual,
    scratchFree,
    ltiFree,
    mtcFree,
    facFree,
    pdiFree
  );
  return card;
}

function build_card_html(siteName, ltifrTarget, ltifrActual, scratchFree, ltiFree, mtcFree, facFree, pdiFree) {
  return `
    <div class="isd-card-inner">

      <div class="isd-sitebar">
        <div class="isd-site-pill">Site</div>
        <div class="isd-site-name">${frappe.utils.escape_html(siteName)}</div>
      </div>

      <div class="isd-kpi-row">
        <div class="isd-kpi">
          <div class="isd-kpi-label">LTIFR Target</div>
          <div class="isd-kpi-val">${ltifrTarget}</div>
        </div>
        <div class="isd-kpi">
          <div class="isd-kpi-label">LTIFR Actual</div>
          <div class="isd-kpi-val">${ltifrActual}</div>
        </div>
        <div class="isd-kpi">
          <div class="isd-kpi-label">Scratch Free Days</div>
          <div class="isd-kpi-val">${scratchFree}</div>
        </div>
      </div>

      <div class="isd-safe-title">Safe Days</div>

      <div class="isd-safe-row">
        <div class="isd-safe-col">
          <div class="isd-safe-h">LTI</div>
          <div class="isd-safe-v">${ltiFree}</div>
        </div>
        <div class="isd-safe-col">
          <div class="isd-safe-h">MTC</div>
          <div class="isd-safe-v">${mtcFree}</div>
        </div>
        <div class="isd-safe-col">
          <div class="isd-safe-h">FA</div>
          <div class="isd-safe-v">${facFree}</div>
        </div>
        <div class="isd-safe-col">
          <div class="isd-safe-h">Property Damage - TMM</div>
          <div class="isd-safe-v">${pdiFree}</div>
        </div>
      </div>

    </div>
  `;
}

function is_valid_hex(s) {
  return /^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$/.test(s);
}


// ---------------------------
// CSS Injection
// ---------------------------
function inject_css(wrapper) {
  const style = document.createElement("style");
  style.textContent = `
    :root{
      --isd-inner: #F5F2F2;
      --isd-white: #ffffff;
      --isd-ink: #0f172a;
      --isd-border: #0b0b0b;
      --isd-border-w: 1px;
      --isd-radius: 6px;
    }

    /* Slight font bump (+~1px) but safe (no overflow) */
    .isd-wrap, .isd-wrap * {
      font-family: "Segoe UI", Inter, Roboto, Arial, system-ui, -apple-system;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      text-rendering: geometricPrecision;
    }

    .isd-wrap { padding: 12px; }

    .isd-loading { padding: 12px; font-weight: 700; text-align: center; color: var(--isd-ink); font-size: 13px; }

    .isd-top { display: flex; justify-content: center; margin-bottom: 10px; }

    .isd-grid-2 {
      display: grid;
      grid-template-columns: 1fr 14px 1fr;
      gap: 12px;
      align-items: start;
    }
    .isd-grid-2.isd-no-divider { grid-template-columns: 1fr; }
    .isd-grid-2.isd-no-divider .isd-divider { display: none; }

    .isd-divider { width: 1px; background: #7a8791; height: 100%; margin: 0 auto; opacity: 0.7; }

    .isd-col { display: grid; gap: 12px; }

    .isd-heading {
      text-align: center;
      font-weight: 900;
      letter-spacing: .6px;
      color: var(--isd-ink);
      margin: 4px 0 0;
      font-size: 14px;
    }

    .isd-card {
      border: var(--isd-border-w) solid var(--isd-border);
      padding: 8px;
      border-radius: var(--isd-radius);
    }

    .isd-card, .isd-card * { text-align: center; }

    .isd-card-inner { display: grid; gap: 6px; }

    .isd-sitebar{
      display: grid;
      grid-template-columns: 56px 1fr;
      gap: 8px;
      align-items: center;
      min-width: 0;
    }

    .isd-site-pill{
      background: var(--isd-inner);
      border: var(--isd-border-w) solid var(--isd-border);
      border-radius: 4px;
      padding: 3px 8px;
      font-weight: 800;
      font-size: 12px;
      min-height: 26px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-sizing: border-box;
      min-width: 0;
    }

    .isd-site-name{
      width: 100%;
      background: var(--isd-inner);
      border: var(--isd-border-w) solid var(--isd-border);
      border-radius: 4px;
      padding: 3px 10px;
      font-weight: 900;
      font-size: 13px;
      min-height: 26px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-sizing: border-box;

      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .isd-kpi-row {
      display: grid;
      grid-template-columns: repeat(3, minmax(120px, 1fr));
      gap: 8px;
      margin: 0;
    }

    .isd-kpi {
      background: var(--isd-inner);
      border: var(--isd-border-w) solid var(--isd-border);
      padding: 5px 6px;
      border-radius: 4px;
      box-sizing: border-box;
      min-width: 0;
      overflow: hidden;
    }

    .isd-kpi-label {
      font-size: 12px;
      font-weight: 800;
      color: var(--isd-ink);
      margin-bottom: 3px;
      line-height: 1.15;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .isd-kpi-val {
      font-size: 13px;
      font-weight: 900;
      color: var(--isd-ink);
      background: var(--isd-white);
      border: var(--isd-border-w) solid var(--isd-border);
      padding: 3px 6px;
      border-radius: 4px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 22px;
      box-sizing: border-box;
      width: 100%;
    }

    .isd-safe-title {
      width: fit-content;
      margin: 0 auto;
      font-size: 12px;
      font-weight: 900;
      color: var(--isd-ink);
      background: var(--isd-inner);
      border: var(--isd-border-w) solid var(--isd-border);
      padding: 3px 12px;
      border-radius: 4px;
      box-sizing: border-box;
      max-width: 100%;
    }

    .isd-safe-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      border: var(--isd-border-w) solid var(--isd-border);
      border-radius: 4px;
      overflow: hidden;
      background: var(--isd-inner);
      margin: 0;
      box-sizing: border-box;
    }

    .isd-safe-col {
      border-right: var(--isd-border-w) solid var(--isd-border);
      min-width: 0;
    }
    .isd-safe-col:last-child { border-right: none; }

    .isd-safe-h {
      font-size: 12px;
      font-weight: 900;
      padding: 6px 4px;
      color: var(--isd-ink);
      background: var(--isd-inner);

      display: flex;
      justify-content: center;
      align-items: center;
      box-sizing: border-box;

      white-space: normal;
      word-break: break-word;
      overflow-wrap: anywhere;
      hyphens: auto;
      line-height: 1.12;
      min-height: 30px;
    }

    .isd-safe-v {
      font-size: 13px;
      font-weight: 900;
      padding: 6px 4px;
      color: var(--isd-ink);
      background: var(--isd-white);
      border-top: var(--isd-border-w) solid var(--isd-border);

      display: flex;
      justify-content: center;
      align-items: center;
      box-sizing: border-box;

      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    @media (max-width: 1200px) {
      .isd-grid-2 { grid-template-columns: 1fr; }
      .isd-divider { display: none; }
      .isd-kpi-row { grid-template-columns: 1fr; }
      .isd-safe-row { grid-template-columns: 1fr; }
      .isd-safe-col { border-right: none; border-bottom: var(--isd-border-w) solid var(--isd-border); }
      .isd-safe-col:last-child { border-bottom: none; }
      .isd-sitebar { grid-template-columns: 1fr; }
      .isd-site-name { white-space: normal; }
    }
  `;
  wrapper.appendChild(style);
}
