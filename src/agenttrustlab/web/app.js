"use strict";

const state = { reports: [], selected: null, catalog: null };
const byId = (id) => document.getElementById(id);
const node = (tag, className, text) => {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
};
const formatDate = (value) => new Intl.DateTimeFormat(undefined, {dateStyle: "medium", timeStyle: "short"}).format(new Date(value));
const formatMs = (value) => value < 1000 ? `${value.toFixed(1)} ms` : `${(value / 1000).toFixed(2)} s`;
const scoreValue = (run) => run.score ? run.score.total : null;

function showPage(id) {
  document.querySelectorAll(".page").forEach((page) => page.classList.toggle("active", page.id === id));
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.page === id));
  const titles = {overview: "Verification overview", runs: "Evaluation runs", attacks: "Attack laboratory", ci: "CI integration"};
  byId("page-title").textContent = titles[id];
  history.replaceState(null, "", `#${id}`);
}

function renderOverview(report) {
  if (!report) return;
  const passed = report.runs.filter((run) => run.status === "passed").length;
  const scored = report.runs.map(scoreValue).filter((value) => value !== null);
  const average = scored.length ? scored.reduce((sum, value) => sum + value, 0) / scored.length : null;
  const latency = report.runs.reduce((sum, run) => sum + run.latency_ms, 0);
  const cost = report.runs.reduce((sum, run) => sum + (run.result ? run.result.cost_usd : 0), 0);
  const isPassed = passed === report.runs.length && report.runs.length > 0;
  byId("hero-verdict").textContent = isPassed ? "Release evidence passed" : "Release requires attention";
  byId("hero-copy").textContent = `${report.adapter} · ${formatDate(report.created_at)} · ${report.runs.length} normalized checks`;
  byId("verdict-badge").textContent = isPassed ? "Trusted under profile" : "Gate blocked";
  byId("verdict-badge").className = `verdict ${isPassed ? "pass" : "fail"}`;
  byId("metric-checks").textContent = `${passed} / ${report.runs.length}`;
  byId("metric-checks-copy").textContent = `${report.runs.length - passed} require attention`;
  byId("metric-score").textContent = average === null ? "—" : `${Math.round(average * 100)}%`;
  byId("metric-latency").textContent = formatMs(latency);
  byId("metric-cost").textContent = cost ? `$${cost.toFixed(4)} recorded cost` : "No model cost recorded";
  byId("metric-determinism").textContent = report.deterministic ? "Stable" : "Variable";
  const list = byId("check-list");
  list.replaceChildren();
  report.runs.slice(0, 7).forEach((run) => {
    const row = node("div", "check-row");
    row.append(node("span", `check-dot ${run.status}`));
    const name = node("span", "check-name");
    name.append(node("strong", "", run.case_id));
    name.append(node("small", "", run.violations[0] || run.error || `${(run.result?.evidence || []).length} evidence item(s) · ${(run.result?.tool_calls || []).length} tool call(s)`));
    row.append(name, node("span", `check-status ${run.status}`, run.status), node("span", "check-score", run.score ? `${Math.round(run.score.total * 100)}%` : "—"));
    list.append(row);
  });
  const identity = byId("run-identity");
  const values = [report.adapter, report.id, formatDate(report.created_at), String(report.config.seed)];
  identity.querySelectorAll("dd").forEach((item, index) => { item.textContent = values[index]; });
}

function renderReportList() {
  const query = byId("report-filter").value.trim().toLowerCase();
  const reports = state.reports.filter((item) => `${item.adapter} ${item.id}`.toLowerCase().includes(query));
  const container = byId("report-list");
  container.replaceChildren();
  if (!reports.length) { container.append(node("div", "empty-inline", query ? "No matching reports." : "No stored reports.")); return; }
  reports.forEach((report) => {
    const button = node("button", `report-row ${state.selected?.id === report.id ? "active" : ""}`);
    button.type = "button";
    button.dataset.reportId = report.id;
    const meta = node("span", "report-meta");
    meta.append(node("strong", "", report.adapter), node("span", `report-state ${report.passed ? "pass" : "fail"}`, report.passed ? "passed" : "blocked"));
    button.append(meta, node("small", "", formatDate(report.created_at)), node("small", "", report.id));
    button.addEventListener("click", () => loadReport(report.id));
    container.append(button);
  });
}

function renderReportDetail(report) {
  const detail = byId("report-detail");
  detail.replaceChildren();
  const head = node("div", "detail-head");
  const title = node("div"); title.append(node("span", "eyebrow", "NORMALIZED REPORT"), node("h3", "", report.adapter), node("small", "", report.id));
  const passed = report.runs.every((run) => run.status === "passed") && report.runs.length > 0;
  head.append(title, node("span", `verdict ${passed ? "pass" : "fail"}`, passed ? "Passed" : "Blocked"));
  detail.append(head);
  const summary = node("div", "detail-summary");
  [["Created", formatDate(report.created_at)], ["Checks", String(report.runs.length)], ["Seed", String(report.config.seed)], ["Deterministic", report.deterministic ? "Yes" : "No"]].forEach(([label, value]) => { const item = node("div"); item.append(node("small", "", label), node("strong", "", value)); summary.append(item); });
  detail.append(summary);
  report.runs.forEach((run) => {
    const card = node("article", "run-card");
    const cardHead = node("div", "run-card-head");
    cardHead.append(node("h4", "", run.case_id), node("span", `check-status ${run.status}`, run.status));
    card.append(cardHead);
    if (run.error) card.append(node("p", "error-copy", run.error));
    run.violations.forEach((violation) => card.append(node("div", "violation", violation)));
    const tags = node("div", "tags");
    tags.append(node("span", "tag", formatMs(run.latency_ms)));
    if (run.score) tags.append(node("span", "tag", `Score ${Math.round(run.score.total * 100)}%`));
    if (run.result) {
      tags.append(node("span", "tag", `${run.result.tool_calls.length} tool calls`));
      tags.append(node("span", "tag", `${run.result.evidence.length} evidence`));
      if (run.result.cost_usd) tags.append(node("span", "tag", `$${run.result.cost_usd.toFixed(4)}`));
    }
    card.append(tags); detail.append(card);
  });
}

async function loadReport(id) {
  try {
    const response = await fetch(`/api/reports/${encodeURIComponent(id)}`);
    if (!response.ok) throw new Error(`Report request failed (${response.status})`);
    state.selected = await response.json();
    renderOverview(state.selected); renderReportList(); renderReportDetail(state.selected);
  } catch (error) { showError(error.message); }
}

function renderCatalog(catalog) {
  byId("attack-count").textContent = `${catalog.attacks.length} built-in probes`;
  const grid = byId("attack-grid"); grid.replaceChildren();
  catalog.attacks.forEach((attack) => {
    const card = node("article", "panel attack-card");
    const top = node("div", "attack-top"); top.append(node("span", "severity", attack.severity), node("span", "control", attack.control));
    card.append(top, node("h3", "", attack.kind), node("p", "", attack.payload)); grid.append(card);
  });
}

function showError(message) {
  const notice = byId("notice"); notice.textContent = message; notice.classList.remove("hidden");
  byId("api-state").textContent = "API unavailable"; byId("api-state").className = "api-state";
}

async function initialize() {
  try {
    const [healthResponse, reportsResponse, catalogResponse] = await Promise.all([fetch("/health"), fetch("/api/reports"), fetch("/api/catalog")]);
    if (!healthResponse.ok || !reportsResponse.ok || !catalogResponse.ok) throw new Error("The evidence API returned an error.");
    const health = await healthResponse.json(); state.reports = await reportsResponse.json(); state.catalog = await catalogResponse.json();
    byId("api-state").textContent = `API v${health.version} online`; byId("api-state").className = "api-state ok";
    renderCatalog(state.catalog); renderReportList();
    if (state.reports.length) await loadReport(state.reports[0].id);
  } catch (error) { showError(error.message); }
}

document.querySelectorAll(".nav-item").forEach((item) => item.addEventListener("click", () => showPage(item.dataset.page)));
byId("view-runs").addEventListener("click", () => showPage("runs"));
byId("report-filter").addEventListener("input", renderReportList);
const initialPage = location.hash.slice(1);
if (["overview", "runs", "attacks", "ci"].includes(initialPage)) showPage(initialPage);
initialize();
