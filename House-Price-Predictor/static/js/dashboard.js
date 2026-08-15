/**
 * dashboard.js  —  HousePrice AI  —  ML Dashboard page
 *
 * All ML logic runs on the Flask backend.
 * This file handles UI state and API communication only.
 *
 * Data flow:
 *   Upload CSV → renderDatasetPreview + renderDatasetInfo
 *   Train Model → renderMetrics + renderDatasetInfo + refreshVisualization + refreshStatus
 *   Page load (init) → always fetch latest metrics + dataset-info from API and render
 */
"use strict";

/* ── DOM refs ─────────────────────────────────────────────────── */
const dropZone       = document.getElementById("drop-zone");
const fileInput      = document.getElementById("csv-file-input");
const selectedLabel  = document.getElementById("selected-file-name");
const btnUpload      = document.getElementById("btn-upload");
const uploadFeedback = document.getElementById("upload-feedback");

const previewEmpty   = document.getElementById("preview-empty");
const previewContent = document.getElementById("preview-content");
const previewSub     = document.getElementById("preview-sub");
const dsStatsRow     = document.getElementById("ds-stats-row");
const previewThead   = document.getElementById("preview-thead");
const previewTbody   = document.getElementById("preview-tbody");

const btnTrain       = document.getElementById("btn-train");
const trainLog       = document.getElementById("train-log");

const metricsCard    = document.getElementById("metrics-card");
const vizCard        = document.getElementById("viz-card");
const statusTable    = document.getElementById("status-table");

/* ── Helpers ──────────────────────────────────────────────────── */
function show(el) { if (el) el.classList.remove("hidden"); }
function hide(el) { if (el) el.classList.add("hidden"); }

function setBtnLoading(btn, loading) {
  btn.classList.toggle("btn-loading", loading);
  btn.disabled = loading;
}

function showFeedback(type, html) {
  uploadFeedback.className = `feedback-box fb-${type}`;
  uploadFeedback.innerHTML = html;
  show(uploadFeedback);
}

function logLine(msg) {
  show(trainLog);
  trainLog.textContent += msg + "\n";
  trainLog.scrollTop = trainLog.scrollHeight;
}
function clearLog() {
  trainLog.textContent = "";
  hide(trainLog);
}

function fmt(n) {
  return new Intl.NumberFormat("en-PK").format(Math.round(Number(n)));
}

/* ═══════════════════════════════════════════════════════════════
   DROP ZONE / FILE PICKER
   ═══════════════════════════════════════════════════════════════ */
let selectedFile = null;

function onFileChosen(file) {
  if (!file) return;
  selectedFile = file;
  selectedLabel.textContent = `${file.name}  (${(file.size / 1024).toFixed(1)} KB)`;
  dropZone.classList.add("file-ok");
  btnUpload.disabled = false;
  hide(uploadFeedback);
}

fileInput.addEventListener("change", () => onFileChosen(fileInput.files[0]));

dropZone.addEventListener("dragover",  e => { e.preventDefault(); dropZone.classList.add("drag-over"); });
dropZone.addEventListener("dragleave", ()  => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", e => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const file = e.dataTransfer?.files[0];
  if (file) { fileInput.files = e.dataTransfer.files; onFileChosen(file); }
});
dropZone.addEventListener("keydown", e => {
  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); }
});

/* ═══════════════════════════════════════════════════════════════
   UPLOAD
   ═══════════════════════════════════════════════════════════════ */
btnUpload.addEventListener("click", async () => {
  if (!selectedFile) return;
  setBtnLoading(btnUpload, true);
  hide(uploadFeedback);

  const fd = new FormData();
  fd.append("file", selectedFile);

  try {
    const res  = await fetch("/api/upload-dataset", { method: "POST", body: fd });
    const json = await res.json();

    if (!res.ok || !json.success) {
      showFeedback("error", `<i class="fa-solid fa-circle-xmark"></i> ${json.error}`);
      return;
    }

    showFeedback("ok",
      `<i class="fa-solid fa-circle-check"></i>
       <strong>${json.filename}</strong> uploaded — ${json.dataset_info.rows} rows · ${json.dataset_info.columns} columns.`
    );

    // Update both preview AND dataset-information from the upload response
    renderDatasetPreview(json.dataset_info, json.preview);
    renderDatasetInfo(json.dataset_info);

  } catch (err) {
    showFeedback("error", `<i class="fa-solid fa-circle-xmark"></i> Network error: ${err.message}`);
  } finally {
    setBtnLoading(btnUpload, false);
  }
});

/* ═══════════════════════════════════════════════════════════════
   RENDER — DATASET PREVIEW
   ═══════════════════════════════════════════════════════════════ */
function renderDatasetPreview(info, rows) {
  dsStatsRow.innerHTML = [
    { label: "Total Rows",     val: fmt(info.rows) },
    { label: "Columns",        val: info.columns },
    { label: "Features",       val: info.features.length },
    { label: "Locations",      val: info.locations.length },
    { label: "Missing Values", val: info.missing_values },
  ].map(s =>
    `<div class="ds-stat">
       <span class="ds-stat-label">${s.label}</span>
       <span class="ds-stat-val">${s.val}</span>
     </div>`
  ).join("");

  if (!rows || rows.length === 0) {
    previewThead.innerHTML = "<tr><th>No data</th></tr>";
    previewTbody.innerHTML = "";
  } else {
    const cols = Object.keys(rows[0]);
    previewThead.innerHTML = `<tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr>`;
    previewTbody.innerHTML = rows.map(row =>
      `<tr>${cols.map(c => `<td>${row[c] ?? ""}</td>`).join("")}</tr>`
    ).join("");
  }

  previewSub.textContent = `${info.rows} rows · ${info.columns} columns — first 10 rows shown`;
  hide(previewEmpty);
  show(previewContent);
}

/* ═══════════════════════════════════════════════════════════════
   RENDER — DATASET INFORMATION
   Always called after upload AND after training.
   Fully replaces the card body content — no stale Jinja values.
   ═══════════════════════════════════════════════════════════════ */
function renderDatasetInfo(info) {
  // Target the card-body directly so we replace whatever Jinja rendered
  const cardBody = document.querySelector("#ds-info-card .card-body");
  if (!cardBody) return;

  cardBody.innerHTML = `
    <div id="ds-info-content">
      <div class="info-cards-grid">
        ${tile("fa-table-list",         "Total Rows",     fmt(info.rows))}
        ${tile("fa-table-columns",      "Columns",        info.columns)}
        ${tile("fa-triangle-exclamation info-tile-icon--warn", "Missing Values", info.missing_values)}
        ${tile("fa-location-dot info-tile-icon--teal",         "Locations",      info.locations.length)}
      </div>
      <div class="info-detail-grid">
        ${detailBlock("fa-list-check",   "Features",            info.features.join(", "))}
        ${detailBlock("fa-bullseye",     "Target Column",       info.target)}
        ${detailBlock("fa-location-dot", "Available Locations", info.locations.join(", "))}
        ${detailBlock("fa-coins",        "Price Range",
          `PKR ${fmt(info.price_min)} — PKR ${fmt(info.price_max)}`)}
      </div>
    </div>`;
}

function renderDatasetInfoEmpty() {
  const cardBody = document.querySelector("#ds-info-card .card-body");
  if (!cardBody) return;
  cardBody.innerHTML = `
    <div class="empty-state">
      <i class="fa-solid fa-database empty-icon"></i>
      <p>No dataset loaded. Upload a CSV file to see dataset information.</p>
    </div>`;
}

function tile(icon, label, val) {
  return `<div class="info-tile">
    <i class="fa-solid ${icon} info-tile-icon"></i>
    <div class="info-tile-label">${label}</div>
    <div class="info-tile-val">${val}</div>
  </div>`;
}

function detailBlock(icon, label, val) {
  return `<div class="info-detail-block">
    <div class="idb-label"><i class="fa-solid ${icon}"></i> ${label}</div>
    <div class="idb-val">${val}</div>
  </div>`;
}

/* ═══════════════════════════════════════════════════════════════
   RENDER — METRICS
   Always replaces the entire metrics card body.
   No dependency on whether Jinja rendered the empty or filled state.
   ═══════════════════════════════════════════════════════════════ */
function renderMetrics(m) {
  const cardBody = document.querySelector("#metrics-card .card-body");
  if (!cardBody) return;

  // Support both field names: r2_score (new) and r2 (legacy)
  const r2    = m.r2_score !== undefined ? m.r2_score : m.r2;
  const mae   = m.mae;
  const rmse  = m.rmse;
  const train = m.train_size  !== undefined ? m.train_size  : m.train_records;
  const test  = m.test_size   !== undefined ? m.test_size   : m.test_records;
  const total = m.dataset_records !== undefined ? m.dataset_records : (train + test);

  cardBody.innerHTML = `
    <div class="metrics-grid" id="metrics-grid">
      <div class="metric-tile metric-tile--accent">
        <div class="mt-label">R² Score</div>
        <div class="mt-value" id="mt-r2">${r2}</div>
        <div class="mt-desc">Variance explained</div>
      </div>
      <div class="metric-tile">
        <div class="mt-label">MAE</div>
        <div class="mt-value mt-value--sm" id="mt-mae">PKR ${fmt(mae)}</div>
        <div class="mt-desc">Mean Absolute Error</div>
      </div>
      <div class="metric-tile">
        <div class="mt-label">RMSE</div>
        <div class="mt-value mt-value--sm" id="mt-rmse">PKR ${fmt(rmse)}</div>
        <div class="mt-desc">Root Mean Squared Error</div>
      </div>
      <div class="metric-tile">
        <div class="mt-label">Train Size</div>
        <div class="mt-value" id="mt-train">${train}</div>
        <div class="mt-desc">80% of dataset</div>
      </div>
      <div class="metric-tile">
        <div class="mt-label">Test Size</div>
        <div class="mt-value" id="mt-test">${test}</div>
        <div class="mt-desc">20% of dataset</div>
      </div>
      <div class="metric-tile">
        <div class="mt-label">Total Records</div>
        <div class="mt-value" id="mt-total">${total}</div>
        <div class="mt-desc">Rows used</div>
      </div>
    </div>
    <p class="trained-at-note" id="trained-at-note">
      <i class="fa-regular fa-clock"></i> Trained at: ${m.trained_at || "—"}
    </p>`;
}

function renderMetricsEmpty() {
  const cardBody = document.querySelector("#metrics-card .card-body");
  if (!cardBody) return;
  cardBody.innerHTML = `
    <div class="empty-state">
      <i class="fa-solid fa-chart-column empty-icon"></i>
      <p>Model not trained yet. Upload a dataset and train the model to see metrics here.</p>
    </div>`;
}

/* ═══════════════════════════════════════════════════════════════
   VISUALIZATION REFRESH
   Uses timestamp cache-bust. Handles both the initial Jinja-rendered
   img and the JS-injected one — always targets #viz-img.
   ═══════════════════════════════════════════════════════════════ */
function refreshVisualization(vizUrl) {
  const ts  = Date.now();
  const src = (vizUrl || "/visualization") + `?t=${ts}`;

  // The fallback empty-state and container may be either element depending
  // on which Jinja branch rendered. Find them by class, not by assumed id.
  const cardBody    = document.querySelector("#viz-card .card-body");
  if (!cardBody) return;

  // Always rebuild the card body so we definitely show the new image
  cardBody.innerHTML = `
    <div id="viz-container">
      <img id="viz-img"
           src="${src}"
           alt="Actual vs Predicted chart"
           class="viz-img"
           onerror="this.parentElement.innerHTML='<div class=\\'empty-state\\'><i class=\\'fa-solid fa-chart-scatter empty-icon\\'></i><p>Chart could not load. Try retraining.</p></div>'" />
    </div>`;
}

function renderVizEmpty() {
  const cardBody = document.querySelector("#viz-card .card-body");
  if (!cardBody) return;
  cardBody.innerHTML = `
    <div class="empty-state">
      <i class="fa-solid fa-chart-scatter empty-icon"></i>
      <p>No visualization yet. Train the model to generate the chart.</p>
    </div>`;
}

/* ═══════════════════════════════════════════════════════════════
   STATUS PANEL REFRESH
   Replaces individual table cells and the badge.
   ═══════════════════════════════════════════════════════════════ */
function renderStatus(s) {
  // Badge
  const badgeWrap = document.querySelector(".status-badge-wrap");
  if (badgeWrap) {
    if (s.trained) {
      badgeWrap.innerHTML = `<div class="status-badge status-badge--ok">
        <i class="fa-solid fa-circle-check"></i> Trained</div>`;
    } else {
      badgeWrap.innerHTML = `<div class="status-badge status-badge--warn">
        <i class="fa-solid fa-circle-xmark"></i> Not Trained</div>`;
    }
  }

  // Table rows — update by position (order matches the template)
  const vals = [
    s.model         || "Random Forest Regressor",
    s.dataset_file  || "—",
    s.trained_at    || "—",
    s.train_records !== null ? s.train_records : "—",
    s.test_records  !== null ? s.test_records  : "—",
  ];
  const tbody = document.querySelector("#status-table tbody");
  if (tbody) {
    tbody.querySelectorAll("tr").forEach((tr, i) => {
      const td = tr.querySelector("td");
      if (td && vals[i] !== undefined) td.textContent = vals[i];
    });
  }

  // Remove "not trained" note if now trained
  if (s.trained) {
    const note = document.querySelector("#status-card .card-note");
    if (note) note.remove();
  }
}

async function refreshStatus() {
  try {
    const res  = await fetch("/api/model-status");
    const json = await res.json();
    if (res.ok && json.success) renderStatus(json.status);
  } catch (_) { /* non-critical */ }
}

/* ═══════════════════════════════════════════════════════════════
   TRAIN
   After success: refresh metrics, dataset-info, viz, status.
   ═══════════════════════════════════════════════════════════════ */
btnTrain.addEventListener("click", async () => {
  clearLog();
  setBtnLoading(btnTrain, true);

  logLine("Starting model training...");
  logLine("  Algorithm : Random Forest Regressor");
  logLine("  Split     : 80% train / 20% test");
  logLine("  Encoding  : One-Hot (location)");

  try {
    const res  = await fetch("/api/train", { method: "POST" });
    const json = await res.json();

    if (!res.ok || !json.success) {
      logLine(`\nTraining failed: ${json.error}`);
      return;
    }

    const m = json.metrics;
    logLine("\nTraining complete!");
    logLine(`  R2 Score : ${m.r2_score}`);
    logLine(`  MAE      : PKR ${fmt(m.mae)}`);
    logLine(`  RMSE     : PKR ${fmt(m.rmse)}`);
    logLine(`  Train    : ${m.train_size} records`);
    logLine(`  Test     : ${m.test_size} records`);
    logLine(`  Trained  : ${m.trained_at}`);
    logLine("  Model    : model/house_price_model.pkl");
    logLine("  Chart    : static/visualizations/actual_vs_predicted.png");

    // ── Update every section immediately ──────────────────────
    renderMetrics(m);

    // Refresh dataset info from API (reflects the CSV used for training)
    try {
      const dr   = await fetch("/api/dataset-info");
      const dinf = await dr.json();
      if (dr.ok && dinf.success) renderDatasetInfo(dinf.dataset_info);
    } catch (_) { /* silent */ }

    // Refresh visualization — use the viz_path returned by the train API
    refreshVisualization(json.viz_url || "/visualization");

    // Refresh status panel
    await refreshStatus();

  } catch (err) {
    logLine(`\nNetwork error: ${err.message}`);
  } finally {
    setBtnLoading(btnTrain, false);
  }
});

/* ═══════════════════════════════════════════════════════════════
   INIT — runs on every page load
   Always fetches from APIs — never relies on what Jinja rendered.
   This ensures the dashboard is always in sync after any action.
   ═══════════════════════════════════════════════════════════════ */
(async function init() {

  // ── 1. Metrics ───────────────────────────────────────────────
  try {
    const res  = await fetch("/api/metrics");
    const json = await res.json();
    if (res.ok && json.success && json.metrics) {
      renderMetrics(json.metrics);
    } else {
      renderMetricsEmpty();
    }
  } catch (_) {
    renderMetricsEmpty();
  }

  // ── 2. Dataset information + preview ─────────────────────────
  // /api/preview returns both dataset_info AND first 10 rows in one call.
  // This ensures the Dataset Preview table is always populated on load,
  // not just after an upload in the current browser session.
  try {
    const res  = await fetch("/api/preview");
    const json = await res.json();
    if (res.ok && json.success && json.dataset_info) {
      renderDatasetInfo(json.dataset_info);
      renderDatasetPreview(json.dataset_info, json.preview || []);
    } else {
      renderDatasetInfoEmpty();
    }
  } catch (_) {
    renderDatasetInfoEmpty();
  }

  // ── 3. Model status ───────────────────────────────────────────
  await refreshStatus();

  // ── 4. Visualization ─────────────────────────────────────────
  try {
    const res = await fetch("/visualization");
    if (res.ok) {
      refreshVisualization("/visualization");
    } else {
      renderVizEmpty();
    }
  } catch (_) {
    renderVizEmpty();
  }

})();
