let priceChart = null;
let energyChart = null;

/* Tabs */
function switchTab(tab) {
  const panels = ["price", "energy"];
  panels.forEach((p) => {
    document.getElementById(`panel-${p}`).classList.toggle("d-none", p !== tab);
    document.getElementById(`btn-${p}`).classList.toggle("active", p === tab);
  });
}

/* Health */
async function checkHealth() {
  const badge = document.getElementById("apiStatus");
  try {
    const res = await fetch("/api/health");
    if (!res.ok) throw new Error();
    const data = await res.json();
    const bothReady = data.models.price && data.models.energy;
    badge.textContent = bothReady ? "◈ SYSTEM READY" : "◈ API ONLINE — MODELS PENDING";
    badge.className = `badge spi-badge-api ${bothReady ? "online" : ""}`;
    const strip = document.getElementById("sysStatusStrip");
    if (strip) strip.innerHTML = bothReady
      ? `System: <strong>OPERATIONAL</strong>`
      : `System: <strong>MODELS NOT LOADED</strong>`;
  } catch {
    badge.textContent = "◈ SYSTEM OFFLINE";
    badge.className = "badge spi-badge-api offline";
    const strip = document.getElementById("sysStatusStrip");
    if (strip) strip.innerHTML = `System: <strong>OFFLINE</strong>`;
  }
}

/* Helpers */
function setLoading(form, loading) {
  const btn = form.querySelector("button[type=submit]");
  btn.querySelector(".btn-text").textContent = loading
    ? (form.id === "priceForm" ? "Estimating…" : "Forecasting…")
    : (form.id === "priceForm" ? "Estimate Price" : "Forecast Energy");
  btn.querySelector(".btn-spinner").classList.toggle("d-none", !loading);
  btn.disabled = loading;
}

function showError(containerId, message) {
  const container = document.getElementById(containerId);
  container.querySelectorAll(".spi-error").forEach((el) => el.remove());
  const el = document.createElement("div");
  el.className = "spi-error";
  el.textContent = `Error: ${message}`;
  container.appendChild(el);
}

function clearErrors(containerId) {
  const container = document.getElementById(containerId);
  container.querySelectorAll(".spi-error").forEach((el) => el.remove());
  container.querySelectorAll(".spi-field-error").forEach((el) => el.remove());
  container.querySelectorAll(".is-invalid").forEach((el) => el.classList.remove("is-invalid"));
}

/* Format */
const fmt = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

/* Validation rules */
const PRICE_RULES = {
  gr_liv_area:    { label: "Living Area",    min: 1,    message: "must be greater than 0 sqft" },
  year_built:     { label: "Year Built",     min: 1800, max: 2026, message: "must be between 1800 and 2026" },
  total_bsmt_sf:  { label: "Basement Area",  min: 0,    message: "cannot be negative" },
  full_bath:      { label: "Full Bathrooms", min: 0,    message: "cannot be negative" },
  bedroom_abv_gr: { label: "Bedrooms",       min: 0,    message: "cannot be negative" },
  lot_area:       { label: "Lot Area",       min: 1,    message: "must be greater than 0 sqft" },
};

const ENERGY_RULES = {
  surface_area: { label: "Surface Area", min: 1, message: "must be greater than 0 m²" },
  wall_area:    { label: "Wall Area",    min: 1, message: "must be greater than 0 m²" },
  roof_area:    { label: "Roof Area",    min: 1, message: "must be greater than 0 m²" },
};

function validateForm(form, rules) {
  let firstInvalid = null;

  form.querySelectorAll("input[type=number]").forEach((input) => {
    if (input.value.trim() === "" || isNaN(Number(input.value))) {
      _markInvalid(input, "This field is required.");
      if (!firstInvalid) firstInvalid = input;
    }
  });

  for (const [name, rule] of Object.entries(rules)) {
    const input = form.querySelector(`[name="${name}"]`);
    if (!input || input.classList.contains("is-invalid")) continue;

    const val = Number(input.value);
    if (rule.min !== undefined && val < rule.min) {
      _markInvalid(input, `${rule.label} ${rule.message}.`);
      if (!firstInvalid) firstInvalid = input;
    } else if (rule.max !== undefined && val > rule.max) {
      _markInvalid(input, `${rule.label} ${rule.message}.`);
      if (!firstInvalid) firstInvalid = input;
    }
  }

  if (firstInvalid) {
    firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
    firstInvalid.focus();
  }

  return firstInvalid === null;
}

function _markInvalid(input, message) {
  input.classList.add("is-invalid");
  const msg = document.createElement("div");
  msg.className = "spi-field-error";
  msg.textContent = message;
  input.parentElement.appendChild(msg);
}

/* Price */
document.getElementById("priceForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  clearErrors("panel-price");

  const form = e.target;
  const payload = {
    overall_qual:    Number(form.overall_qual.value),
    gr_liv_area:     Number(form.gr_liv_area.value),
    year_built:      Number(form.year_built.value),
    garage_cars:     Number(form.garage_cars.value),
    total_bsmt_sf:   Number(form.total_bsmt_sf.value),
    full_bath:       Number(form.full_bath.value),
    bedroom_abv_gr:  Number(form.bedroom_abv_gr.value),
    lot_area:        Number(form.lot_area.value),
  };

  if (!validateForm(form, PRICE_RULES)) return;

  setLoading(form, true);
  try {
    const res = await fetch("/api/predict/price", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Prediction failed");
    renderPriceResult(data);
  } catch (err) {
    showError("panel-price", err.message);
  } finally {
    setLoading(form, false);
  }
});

function renderPriceResult(data) {
  const result = document.getElementById("priceResult");
  result.classList.remove("d-none");

  document.getElementById("priceValue").textContent = fmt.format(data.predicted_price);
  document.getElementById("priceRange").textContent =
    `Range: ${fmt.format(data.price_range_low)} – ${fmt.format(data.price_range_high)}`;

  const low  = data.price_range_low;
  const pred = data.predicted_price;
  const high = data.price_range_high;

  if (priceChart) priceChart.destroy();
  const ctx = document.getElementById("priceChart").getContext("2d");
  priceChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Market Value Range"],
      datasets: [
        {
          label: `Low  ${fmt.format(low)}`,
          data: [low],
          backgroundColor: "#a0b8d8",
          borderRadius: 0,
        },
        {
          label: `Est. ${fmt.format(pred)}`,
          data: [pred - low],
          backgroundColor: "#000080",
          borderRadius: 0,
        },
        {
          label: `High ${fmt.format(high)}`,
          data: [high - pred],
          backgroundColor: "#4070b0",
          borderRadius: 0,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      plugins: {
        legend: {
          position: "bottom",
          labels: { font: { family: "Verdana, Arial, sans-serif", size: 10 }, color: "#505050" },
        },
        tooltip: {
          backgroundColor: "#ffffff",
          borderColor: "#808080",
          borderWidth: 1,
          titleColor: "#000080",
          bodyColor: "#000000",
          callbacks: { label: (ctx) => ` ${ctx.dataset.label}` },
        },
      },
      scales: {
        x: {
          stacked: true,
          ticks: { callback: (v) => `$${(v / 1000).toFixed(0)}k`, color: "#505050", font: { family: "Verdana, Arial, sans-serif", size: 10 } },
          grid: { color: "rgba(0,0,0,0.08)" },
        },
        y: { stacked: true, display: false },
      },
    },
  });

  result.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/* Energy */
document.getElementById("energyForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  clearErrors("panel-energy");

  const form = e.target;
  const payload = {
    relative_compactness: Number(form.relative_compactness.value),
    surface_area:         Number(form.surface_area.value),
    wall_area:            Number(form.wall_area.value),
    roof_area:            Number(form.roof_area.value),
    overall_height:       Number(form.overall_height.value),
    orientation:          Number(form.orientation.value),
    glazing_area:         Number(form.glazing_area.value),
    glazing_area_dist:    Number(form.glazing_area_dist.value),
  };

  if (!validateForm(form, ENERGY_RULES)) return;

  setLoading(form, true);
  try {
    const res = await fetch("/api/predict/energy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Prediction failed");
    renderEnergyResult(data);
  } catch (err) {
    showError("panel-energy", err.message);
  } finally {
    setLoading(form, false);
  }
});

function renderEnergyResult(data) {
  const result = document.getElementById("energyResult");
  result.classList.remove("d-none");

  document.getElementById("heatingVal").textContent = data.heating_load_kwh_m2.toFixed(1);
  document.getElementById("coolingVal").textContent = data.cooling_load_kwh_m2.toFixed(1);
  document.getElementById("totalVal").textContent   = data.total_load_kwh_m2.toFixed(1) + " kWh/m²";

  if (energyChart) energyChart.destroy();
  const ctx = document.getElementById("energyChart").getContext("2d");
  energyChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Heating Load", "Cooling Load"],
      datasets: [
        {
          data: [data.heating_load_kwh_m2, data.cooling_load_kwh_m2],
          backgroundColor: ["#000080", "#cc0000"],
          borderWidth: 0,
          hoverOffset: 6,
        },
      ],
    },
    options: {
      responsive: true,
      cutout: "65%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { font: { family: "Verdana, Arial, sans-serif", size: 10 }, color: "#505050" },
        },
        tooltip: {
          backgroundColor: "#ffffff",
          borderColor: "#808080",
          borderWidth: 1,
          titleColor: "#000080",
          bodyColor: "#000000",
          callbacks: { label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toFixed(1)} kWh/m²` },
        },
      },
    },
  });

  result.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/* Init */
checkHealth();
