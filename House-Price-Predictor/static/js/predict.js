/**
 * predict.js — HousePrice AI — Home / Prediction page
 *
 * Responsibilities:
 *  - Form validation + stepper UX
 *  - POST /api/predict → display result
 *  - Prediction history (localStorage, max 10 entries)
 *  - Download Report (plain-text .txt)
 *  - "New Prediction" reset
 */
"use strict";

/* ── DOM refs ──────────────────────────────────────────────────── */
const form         = document.getElementById("predict-form");
const predictBtn   = document.getElementById("predict-btn");
const btnNew       = document.getElementById("btn-new");
const btnRetry     = document.getElementById("btn-retry");
const btnDownload  = document.getElementById("btn-download");
const btnClearHist = document.getElementById("btn-clear-history");

const stateIdle    = document.getElementById("state-idle");
const stateLoading = document.getElementById("state-loading");
const stateResult  = document.getElementById("state-result");
const stateError   = document.getElementById("state-error");

const priceAmount  = document.getElementById("price-amount");
const resLocation  = document.getElementById("res-location");
const resArea      = document.getElementById("res-area");
const resPpsqft    = document.getElementById("res-ppsqft");
const errMsg       = document.getElementById("err-msg");

const historyEmpty     = document.getElementById("history-empty");
const historyTableWrap = document.getElementById("history-table-wrap");
const historyTbody     = document.getElementById("history-tbody");

/* ── State ─────────────────────────────────────────────────────── */
const HISTORY_KEY  = "houseprice_history";
const HISTORY_MAX  = 10;
let   lastResult   = null;

/* ══════════════════════════════════════════════════════════════════
   PANEL STATE MACHINE
   ══════════════════════════════════════════════════════════════════ */
const PANELS = {
  idle:    stateIdle,
  loading: stateLoading,
  result:  stateResult,
  error:   stateError,
};

function showState(name) {
  Object.values(PANELS).forEach(el => { if (el) el.classList.add("hidden"); });
  if (PANELS[name]) PANELS[name].classList.remove("hidden");
}

/* ══════════════════════════════════════════════════════════════════
   STEPPER BUTTONS
   ══════════════════════════════════════════════════════════════════ */
document.querySelectorAll(".step-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const inp   = document.getElementById(btn.dataset.for);
    if (!inp) return;
    const delta = parseInt(btn.dataset.delta, 10);
    const min   = parseInt(inp.min, 10);
    const max   = parseInt(inp.max, 10);
    inp.value   = Math.min(Math.max((parseInt(inp.value, 10) || 1) + delta, min), max);
    inp.dispatchEvent(new Event("input"));
    clearErr(inp);
  });
});

/* ══════════════════════════════════════════════════════════════════
   VALIDATION
   ══════════════════════════════════════════════════════════════════ */
const ERR_IDS = {
  area:      "area-err",
  bedrooms:  "bed-err",
  bathrooms: "bath-err",
  location:  "loc-err",
};

function validateField(id, val) {
  switch (id) {
    case "area": {
      const n = parseFloat(val);
      if (val === "" || isNaN(n)) return "Area is required.";
      if (n < 100)                return "Area must be at least 100 sq ft.";
      if (n > 50000)              return "Area cannot exceed 50,000 sq ft.";
      return "";
    }
    case "bedrooms": {
      const n = parseInt(val, 10);
      if (!val || isNaN(n)) return "Bedrooms is required.";
      if (n < 1)            return "Minimum 1 bedroom.";
      if (n > 20)           return "Maximum 20 bedrooms.";
      return "";
    }
    case "bathrooms": {
      const n = parseInt(val, 10);
      if (!val || isNaN(n)) return "Bathrooms is required.";
      if (n < 1)            return "Minimum 1 bathroom.";
      if (n > 20)           return "Maximum 20 bathrooms.";
      return "";
    }
    case "location":
      return val ? "" : "Please select a location.";
    default:
      return "";
  }
}

function setErr(inp, msg) {
  const errEl = document.getElementById(ERR_IDS[inp.id] || (inp.id + "-err"));
  inp.classList.toggle("is-invalid", !!msg);
  inp.classList.toggle("is-valid",   !msg && inp.value !== "");
  if (errEl) errEl.textContent = msg;
}

function clearErr(inp) { setErr(inp, ""); }

function validateForm() {
  const fields = {
    area:      document.getElementById("area"),
    bedrooms:  document.getElementById("bedrooms"),
    bathrooms: document.getElementById("bathrooms"),
    location:  document.getElementById("location"),
  };
  let ok = true;
  const data = {};
  for (const [id, el] of Object.entries(fields)) {
    if (!el) continue;
    const msg = validateField(id, el.value);
    setErr(el, msg);
    if (msg) ok = false;
    else data[id] = el.value;
  }
  return { ok, data };
}

/* Live blur validation */
["area", "bedrooms", "bathrooms", "location"].forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener("blur",  () => setErr(el, validateField(id, el.value)));
  el.addEventListener("input", () => { if (el.classList.contains("is-invalid")) clearErr(el); });
});

/* ══════════════════════════════════════════════════════════════════
   PRICE COUNTER ANIMATION
   ══════════════════════════════════════════════════════════════════ */
function animatePrice(el, target, duration = 700) {
  const start = performance.now();
  const fmt   = new Intl.NumberFormat("en-PK");
  function tick(now) {
    const t = Math.min((now - start) / duration, 1);
    const e = 1 - Math.pow(2, -10 * t);           // easeOutExpo
    el.textContent = fmt.format(Math.round(target * e));
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* ══════════════════════════════════════════════════════════════════
   FORM SUBMIT → API PREDICT
   ══════════════════════════════════════════════════════════════════ */
form.addEventListener("submit", async e => {
  e.preventDefault();

  const { ok, data } = validateForm();
  if (!ok) {
    form.querySelector(".is-invalid")?.focus();
    return;
  }

  predictBtn.disabled = true;
  predictBtn.classList.add("btn-loading");
  showState("loading");

  try {
    const res = await fetch("/api/predict", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        area_sqft:  parseFloat(data.area),
        bedrooms:   parseInt(data.bedrooms,  10),
        bathrooms:  parseInt(data.bathrooms, 10),
        location:   data.location,
      }),
    });

    const json = await res.json();

    if (!res.ok || !json.success) {
      throw new Error(json.error || `Server error (${res.status})`);
    }

    lastResult = json;

    /* Populate result panel */
    animatePrice(priceAmount, json.predicted_price);
    resLocation.textContent = json.inputs.location;
    resArea.textContent     = `${json.inputs.area_sqft.toLocaleString()} sq ft`;
    resPpsqft.textContent   = `PKR ${json.price_per_sqft.toLocaleString()}`;

    showState("result");

    /* Save to history */
    addHistory({
      ts:        new Date().toLocaleString("en-PK"),
      location:  json.inputs.location,
      area:      json.inputs.area_sqft,
      bedrooms:  json.inputs.bedrooms,
      bathrooms: json.inputs.bathrooms,
      price:     json.formatted_price,
    });

  } catch (err) {
    errMsg.textContent = err.message || "Unable to generate prediction. Please check the property details.";
    showState("error");
  } finally {
    predictBtn.disabled = false;
    predictBtn.classList.remove("btn-loading");
  }
});

/* ══════════════════════════════════════════════════════════════════
   SECONDARY BUTTONS
   ══════════════════════════════════════════════════════════════════ */
btnNew?.addEventListener("click", () => {
  form.reset();
  document.querySelectorAll(".form-input").forEach(el =>
    el.classList.remove("is-valid", "is-invalid")
  );
  document.querySelectorAll(".field-err").forEach(el => el.textContent = "");
  const beds = document.getElementById("bedrooms");
  const bath = document.getElementById("bathrooms");
  if (beds) beds.value = 3;
  if (bath) bath.value = 2;
  lastResult = null;
  showState("idle");
  document.getElementById("predict-section")?.scrollIntoView({ behavior: "smooth", block: "start" });
});

btnRetry?.addEventListener("click", () => showState("idle"));

btnDownload?.addEventListener("click", () => {
  if (!lastResult) return;

  const { inputs, formatted_price, price_per_sqft } = lastResult;
  const now  = new Date().toLocaleString("en-PK");
  const lines = [
    "====================================",
    "   HousePrice AI — Prediction Report",
    "====================================",
    "",
    `Date & Time       : ${now}`,
    `Model             : Random Forest Regressor`,
    "",
    "── Property Details ────────────────",
    `Area              : ${inputs.area_sqft.toLocaleString()} sq ft`,
    `Bedrooms          : ${inputs.bedrooms}`,
    `Bathrooms         : ${inputs.bathrooms}`,
    `Location          : ${inputs.location}`,
    "",
    "── Prediction ──────────────────────",
    `Estimated Price   : ${formatted_price}`,
    `Price per sq ft   : PKR ${price_per_sqft.toLocaleString()}`,
    "",
    "====================================",
    "Disclaimer: This is an ML estimate,",
    "not a professional property appraisal.",
    "====================================",
  ];

  const blob = new Blob([lines.join("\n")], { type: "text/plain" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = `HousePriceReport_${Date.now()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
});

/* ══════════════════════════════════════════════════════════════════
   PREDICTION HISTORY  (localStorage)
   ══════════════════════════════════════════════════════════════════ */
function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveHistory(list) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(list));
}

function addHistory(entry) {
  const list = loadHistory();
  list.unshift(entry);                      // newest first
  if (list.length > HISTORY_MAX) list.length = HISTORY_MAX;
  saveHistory(list);
  renderHistory(list);
}

function renderHistory(list) {
  if (!historyTbody || !historyEmpty || !historyTableWrap) return;

  if (!list || list.length === 0) {
    historyEmpty.classList.remove("hidden");
    historyTableWrap.classList.add("hidden");
    return;
  }

  historyEmpty.classList.add("hidden");
  historyTableWrap.classList.remove("hidden");

  historyTbody.innerHTML = list.map(h => `
    <tr>
      <td>${h.ts}</td>
      <td>${h.location}</td>
      <td>${Number(h.area).toLocaleString()}</td>
      <td>${h.bedrooms}</td>
      <td>${h.bathrooms}</td>
      <td class="history-price">${h.price}</td>
    </tr>
  `).join("");
}

btnClearHist?.addEventListener("click", () => {
  localStorage.removeItem(HISTORY_KEY);
  renderHistory([]);
});

/* ══════════════════════════════════════════════════════════════════
   SMOOTH SCROLL
   ══════════════════════════════════════════════════════════════════ */
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener("click", e => {
    const target = document.querySelector(a.getAttribute("href"));
    if (!target) return;
    e.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

/* ══════════════════════════════════════════════════════════════════
   INIT
   ══════════════════════════════════════════════════════════════════ */
showState("idle");
renderHistory(loadHistory());
