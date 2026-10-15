// AquaSense AI — Main Application Controller & UI Orchestrator

let currentLanguage = localStorage.getItem("aquasense_lang") || "en";
let currentView = "dashboard";
let selectedFarmId = "farm-1";
let selectedPlotId = "plot-1";

// Chart.js chart instances
let chartMoistureInstance = null;
let chartConsumptionInstance = null;
let chartRainIrrigationInstance = null;
let chartSavingsInstance = null;

// Speech synthesis & recognition
let speechRecognition = null;
let isListening = false;

document.addEventListener("DOMContentLoaded", async () => {
  initLanguage(currentLanguage);
  setupNavigation();
  setupSpeechRecognition();
  setupModals();
  await refreshAllData();
});

// ---------------- I18N & LANGUAGE ----------------
function initLanguage(lang) {
  currentLanguage = lang;
  localStorage.setItem("aquasense_lang", lang);
  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.lang === lang);
  });
  applyTranslations();
}

function setLanguage(lang) {
  initLanguage(lang);
  renderDashboard();
  renderAlerts();
  showToast(lang === "te" ? "భాష తెలుగులోకి మార్చబడింది" : "Language set to English", "success");
}

function applyTranslations() {
  const dict = TRANSLATIONS[currentLanguage] || TRANSLATIONS.en;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.dataset.i18n;
    if (dict[key]) {
      if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
        el.placeholder = dict[key];
      } else {
        el.innerText = dict[key];
      }
    }
  });
}

function t(key) {
  const dict = TRANSLATIONS[currentLanguage] || TRANSLATIONS.en;
  return dict[key] || key;
}

// ---------------- NAVIGATION ----------------
function setupNavigation() {
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const target = item.dataset.view;
      if (target) switchView(target);
    });
  });

  // Mobile menu button
  const mobileBtn = document.getElementById("mobileMenuBtn");
  const sidebar = document.getElementById("sidebar");
  if (mobileBtn && sidebar) {
    mobileBtn.addEventListener("click", () => {
      sidebar.classList.toggle("mobile-open");
    });
  }
}

function switchView(viewName) {
  currentView = viewName;
  document.querySelectorAll(".nav-item").forEach(n => {
    n.classList.toggle("active", n.dataset.view === viewName);
  });
  document.querySelectorAll(".view-container").forEach(c => {
    c.classList.toggle("active", c.id === `view-${viewName}`);
  });

  const headingEl = document.getElementById("pageTitle");
  const subHeadingEl = document.getElementById("pageSubtitle");
  if (headingEl) headingEl.innerText = t(viewName) || viewName.toUpperCase();
  if (subHeadingEl) subHeadingEl.innerText = t("tagline");

  // Close mobile sidebar if open
  const sidebar = document.getElementById("sidebar");
  if (sidebar) sidebar.classList.remove("mobile-open");

  // View specific refreshes
  if (viewName === "dashboard") renderDashboard();
  else if (viewName === "farms") renderFarms();
  else if (viewName === "plots") renderPlots();
  else if (viewName === "soil") renderSoilView();
  else if (viewName === "weather") renderWeatherView();
  else if (viewName === "recommendations") renderRecommendationsView();
  else if (viewName === "scheduler") renderSchedulerView();
  else if (viewName === "analytics") renderAnalyticsView();
  else if (viewName === "alerts") renderAlertsView();
  else if (viewName === "iotSimulator") renderIotSimulatorView();
}

// ---------------- GLOBAL DATA REFRESH ----------------
async function refreshAllData() {
  const farms = await AquaSenseAPI.getFarms();
  const farmSelect = document.getElementById("globalFarmSelect");
  if (farmSelect && farms.length > 0) {
    farmSelect.innerHTML = farms.map(f => `<option value="${f.id}">${f.name}</option>`).join("");
    selectedFarmId = farms[0].id;
  }
  await renderDashboard();
}

// ---------------- DASHBOARD RENDERING ----------------
async function renderDashboard() {
  const plots = await AquaSenseAPI.getPlots(selectedFarmId);
  const weather = await AquaSenseAPI.getWeather(selectedFarmId);
  const alerts = await AquaSenseAPI.getAlerts();
  const schedules = await AquaSenseAPI.getSchedules();
  const analytics = await AquaSenseAPI.getWaterAnalytics();

  const activePlot = (plots.find(p => p.id === selectedPlotId) || plots[0]) || {};
  selectedPlotId = activePlot.id || "plot-1";

  // Recommendation for active plot
  const rec = await AquaSenseAPI.getRecommendation(selectedPlotId, activePlot, weather);

  // Update KPI Cards
  const elTotalPlots = document.getElementById("statTotalPlots");
  if (elTotalPlots) elTotalPlots.innerText = `${plots.length} Plots (${plots.reduce((acc, p) => acc + (p.area || 0), 0)} Ac)`;

  const elMoisture = document.getElementById("statSoilMoisture");
  if (elMoisture) elMoisture.innerText = `${activePlot.current_moisture || 40.0}%`;

  const elWeather = document.getElementById("statWeather");
  if (elWeather) elWeather.innerText = `${weather.temperature_c}°C / ${weather.humidity_pct}%`;

  const elRainProb = document.getElementById("statRainProb");
  if (elRainProb) elRainProb.innerText = `${weather.rain_probability_pct}% (${weather.forecast_rain_48h_mm} mm)`;

  const elDuration = document.getElementById("statDuration");
  if (elDuration) elDuration.innerText = `${rec.suggested_duration_minutes} ${t("minutes")}`;

  const elWaterReq = document.getElementById("statWaterNeeded");
  if (elWaterReq) elWaterReq.innerText = `${rec.water_req_litres.toLocaleString()} L`;

  const elConsumedToday = document.getElementById("statWaterConsumed");
  if (elConsumedToday) elConsumedToday.innerText = `${(analytics.records[0] ? analytics.records[0].measured_litres : 8400).toLocaleString()} L`;

  const elSaved = document.getElementById("statWaterSaved");
  if (elSaved) elSaved.innerText = `${analytics.summary.total_saved_litres.toLocaleString()} L`;

  const elNextSched = document.getElementById("statNextSchedule");
  if (elNextSched) {
    const upcoming = schedules.find(s => s.status === "scheduled");
    elNextSched.innerText = upcoming ? `${upcoming.scheduled_date} ${upcoming.scheduled_time}` : "None Scheduled";
  }

  const elActiveAlerts = document.getElementById("statActiveAlerts");
  const alertBadge = document.getElementById("navAlertsBadge");
  const activeCount = alerts.filter(a => a.status === "active").length;
  if (elActiveAlerts) elActiveAlerts.innerText = `${activeCount} Issues`;
  if (alertBadge) alertBadge.innerText = activeCount;

  // Render Decision Banner
  renderDecisionBanner(rec, activePlot);

  // Render 4 Interactive Charts
  renderMoistureChart(selectedPlotId);
  renderConsumptionChart(analytics);
  renderRainVsIrrigationChart(weather, analytics);
  renderSavingsChart(analytics);

  // Render Quick Alerts Preview
  renderDashboardAlertsPreview(alerts);
}

function renderDecisionBanner(rec, plot) {
  const container = document.getElementById("decisionBannerContainer");
  if (!container) return;

  let pillClass = "status-monitor";
  let statusText = t("monitor");
  if (rec.status === "Irrigate Now") {
    pillClass = "status-irrigate";
    statusText = t("irrigateNow");
  } else if (rec.status === "Delay and Recheck") {
    pillClass = "status-delay";
    statusText = t("delayRecheck");
  }

  container.innerHTML = `
    <div class="decision-card">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
        <div>
          <span style="font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase;">Current Advisory for: ${plot.name || 'Selected Plot'} (${plot.crop_type})</span>
          <h2 style="font-size: 22px; color: var(--primary-dark); margin-top: 4px;">Agronomic Water Assessment</h2>
        </div>
        <div class="decision-status-pill ${pillClass}">
          <span>●</span> ${statusText}
        </div>
      </div>
      <p style="margin-top: 10px; color: #374151; font-size: 14px; line-height: 1.6;">${rec.reason || (rec.factors && rec.factors.reasons ? rec.factors.reasons[0] : '')}</p>
      <div class="decision-details-grid">
        <div>
          <div class="detail-item-title">${t("waterNeeded")}</div>
          <div class="detail-item-value">${rec.water_req_litres.toLocaleString()} L <span style="font-size:13px; color:var(--text-muted)">(${rec.water_req_m3} m³)</span></div>
        </div>
        <div>
          <div class="detail-item-title">${t("recDuration")}</div>
          <div class="detail-item-value">${rec.suggested_duration_minutes} Mins</div>
        </div>
        <div>
          <div class="detail-item-title">Crop Transpiration (ETc)</div>
          <div class="detail-item-value">${rec.factors ? rec.factors.etc_mm_day : 5.2} mm/day</div>
        </div>
        <div>
          <div class="detail-item-title">Effective Rain Forecast</div>
          <div class="detail-item-value">${rec.effective_rainfall_mm || 0} mm</div>
        </div>
      </div>
      <div style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
        <button class="btn btn-primary" onclick="openScheduleModalForPlot('${plot.id}')">${t("newSchedule")}</button>
        <button class="btn btn-secondary" onclick="openSoilModal('${plot.id}')">${t("manualReading")}</button>
        <button class="btn btn-secondary" onclick="switchView('recommendations')">${t("runAdvisory")}</button>
        <span style="margin-left: auto; font-size: 11px; color: var(--text-muted);">Confidence: ${rec.confidence_pct}% • FAO-56 Standard</span>
      </div>
    </div>
  `;
}

// ---------------- CHARTS RENDERING (CHART.JS) ----------------
async function renderMoistureChart(plotId) {
  const ctx = document.getElementById("chartMoisture");
  if (!ctx) return;
  const readings = await AquaSenseAPI.getSoilReadings(plotId);
  const labels = readings.slice(-12).map(r => new Date(r.reading_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
  const data = readings.slice(-12).map(r => r.soil_moisture_pct);

  if (chartMoistureInstance) chartMoistureInstance.destroy();
  chartMoistureInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Soil Moisture (%)",
          data: data,
          borderColor: "#2d6a4f",
          backgroundColor: "rgba(116, 198, 157, 0.25)",
          fill: true,
          tension: 0.35,
          borderWidth: 2.5
        },
        {
          label: "Critical Stress Threshold",
          data: labels.map(() => 38),
          borderColor: "#dc2626",
          borderDash: [5, 5],
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } },
      scales: { y: { min: 20, max: 80 } }
    }
  });
}

function renderConsumptionChart(analytics) {
  const ctx = document.getElementById("chartWaterConsumption");
  if (!ctx) return;
  const recent = analytics.records.slice(0, 7).reverse();
  const labels = recent.map(r => r.record_date.slice(5));
  const measured = recent.map(r => r.measured_litres);
  const baseline = recent.map(r => r.baseline_litres);

  if (chartConsumptionInstance) chartConsumptionInstance.destroy();
  chartConsumptionInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Optimized Consumption (L)",
          data: measured,
          backgroundColor: "#40916c",
          borderRadius: 4
        },
        {
          label: "Traditional Baseline (L)",
          data: baseline,
          backgroundColor: "#cbd5e1",
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } }
    }
  });
}

function renderRainVsIrrigationChart(weather, analytics) {
  const ctx = document.getElementById("chartRainVsIrrigation");
  if (!ctx) return;
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const rain = [0, 0, 4.5, 12.0, 2.0, 0, 0];
  const irrigation = [22, 0, 0, 0, 18, 0, 20]; // mm equivalent

  if (chartRainIrrigationInstance) chartRainIrrigationInstance.destroy();
  chartRainIrrigationInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: days,
      datasets: [
        {
          label: "Rainfall (mm)",
          data: rain,
          backgroundColor: "#00b4d8",
          borderRadius: 4
        },
        {
          label: "Irrigation (mm)",
          data: irrigation,
          backgroundColor: "#2d6a4f",
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } }
    }
  });
}

function renderSavingsChart(analytics) {
  const ctx = document.getElementById("chartWaterSavings");
  if (!ctx) return;
  const recent = analytics.records.slice(0, 10).reverse();
  const labels = recent.map(r => r.record_date.slice(5));
  let running = 0;
  const cumulative = recent.map(r => {
    running += r.saved_litres;
    return running;
  });

  if (chartSavingsInstance) chartSavingsInstance.destroy();
  chartSavingsInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "Cumulative Water Saved (Litres)",
        data: cumulative,
        borderColor: "#0077b6",
        backgroundColor: "rgba(0, 180, 216, 0.15)",
        fill: true,
        tension: 0.3,
        borderWidth: 2.5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } }
    }
  });
}

function renderDashboardAlertsPreview(alerts) {
  const container = document.getElementById("dashboardAlertsList");
  if (!container) return;
  const activeAlerts = alerts.filter(a => a.status === "active").slice(0, 3);
  if (activeAlerts.length === 0) {
    container.innerHTML = `<div style="padding: 16px; color: #059669; font-weight: 500;">✓ No active irrigation anomalies detected. System operating within optimal agronomic thresholds.</div>`;
    return;
  }
  container.innerHTML = activeAlerts.map(a => `
    <div class="alert-item-card ${a.severity}">
      <div>
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
          <span class="alert-tag tag-${a.severity}">${a.severity}</span>
          <strong style="font-size: 14px; color: var(--text-dark);">${a.message}</strong>
        </div>
        <p style="font-size: 13px; color: var(--text-muted);">${a.reason}</p>
        <p style="font-size: 12px; color: var(--primary); font-weight: 600; margin-top: 4px;">Suggested Action: ${a.suggested_action}</p>
      </div>
      <div>
        <button class="btn btn-secondary btn-sm" onclick="resolveAlert('${a.id}')">Acknowledge</button>
      </div>
    </div>
  `).join("");
}

// ---------------- SOIL MONITORING VIEW ----------------
async function renderSoilView() {
  const plots = await AquaSenseAPI.getPlots(selectedFarmId);
  const plot = plots.find(p => p.id === selectedPlotId) || plots[0] || {};
  const readings = await AquaSenseAPI.getSoilReadings(plot.id);

  const container = document.getElementById("soilPlotGrid");
  if (!container) return;

  container.innerHTML = plots.map(p => {
    const isSelected = p.id === selectedPlotId;
    let badge = `<span style="background:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:700;">IOT SENSOR</span>`;
    if (!p.sensor_id) badge = `<span style="background:#fef3c7; color:#b45309; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:700;">MANUAL INPUT</span>`;

    return `
      <div class="stat-card" style="border: ${isSelected ? '2px solid var(--primary)' : '1px solid var(--border-color)'}; cursor: pointer;" onclick="selectPlot('${p.id}')">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h4 style="font-size:15px; font-weight:700;">${p.name}</h4>
          ${badge}
        </div>
        <p style="font-size:12px; color:var(--text-muted); margin:4px 0 12px;">${p.crop_type} • ${p.soil_type}</p>
        <div style="font-size:28px; font-weight:800; color:${p.current_moisture < p.target_moisture_min ? '#dc2626' : '#2d6a4f'}">
          ${p.current_moisture}%
        </div>
        <div style="font-size:12px; color:var(--text-muted); margin-top:6px;">
          Target Zone: ${p.target_moisture_min}% - ${p.target_moisture_max}%
        </div>
      </div>
    `;
  }).join("");

  // Populate readings table
  const tableBody = document.getElementById("soilReadingsTableBody");
  if (tableBody) {
    tableBody.innerHTML = readings.slice(0, 15).map(r => `
      <tr>
        <td>${new Date(r.reading_timestamp).toLocaleString()}</td>
        <td><strong>${r.soil_moisture_pct}%</strong></td>
        <td>${r.soil_temperature_c || 27.5}°C</td>
        <td>${r.electrical_conductivity || 1.15} dS/m</td>
        <td><span class="alert-tag ${r.source_type === 'iot' ? 'tag-info' : 'tag-warning'}">${r.source_type.toUpperCase()}</span></td>
        <td>${r.sensor_battery_pct || 95}%</td>
      </tr>
    `).join("");
  }
}

function selectPlot(plotId) {
  selectedPlotId = plotId;
  renderDashboard();
  renderSoilView();
}

// ---------------- WEATHER VIEW ----------------
async function renderWeatherView() {
  const weather = await AquaSenseAPI.getWeather(selectedFarmId);
  const container = document.getElementById("weatherForecastCards");
  if (!container) return;

  container.innerHTML = (weather.daily_forecast || []).map(day => `
    <div class="stat-card" style="text-align: center;">
      <div style="font-weight:700; font-size:14px; color:var(--primary-dark);">${day.date}</div>
      <div style="font-size:32px; margin: 8px 0;">⛅</div>
      <div style="font-size:18px; font-weight:700;">${day.temp_max}° / ${day.temp_min}°C</div>
      <div style="font-size:12px; color:#0284c7; font-weight:600; margin-top:4px;">
        🌧 Rain: ${day.rain_prob_pct}% (${day.precipitation_mm} mm)
      </div>
    </div>
  `).join("");
}

// ---------------- RECOMMENDATIONS VIEW ----------------
async function renderRecommendationsView() {
  const plots = await AquaSenseAPI.getPlots(selectedFarmId);
  const plot = plots.find(p => p.id === selectedPlotId) || plots[0] || {};
  const weather = await AquaSenseAPI.getWeather(selectedFarmId);
  const rec = await AquaSenseAPI.getRecommendation(plot.id, plot, weather);

  const container = document.getElementById("recommendationSimulatorResults");
  if (!container) return;

  container.innerHTML = `
    <div class="decision-card">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h3>Advisory Output: ${rec.status}</h3>
        <span class="decision-status-pill ${rec.status === 'Irrigate Now' ? 'status-irrigate' : (rec.status === 'Delay and Recheck' ? 'status-delay' : 'status-monitor')}">${rec.status}</span>
      </div>
      <p style="margin: 12px 0; font-size: 14px;">${rec.reason || (rec.factors && rec.factors.reasons ? rec.factors.reasons[0] : '')}</p>
      <div class="decision-details-grid">
        <div>
          <div class="detail-item-title">Gross Water Requirement</div>
          <div class="detail-item-value">${rec.water_req_litres.toLocaleString()} Litres</div>
        </div>
        <div>
          <div class="detail-item-title">Suggested Pump Duration</div>
          <div class="detail-item-value">${rec.suggested_duration_minutes} Minutes</div>
        </div>
        <div>
          <div class="detail-item-title">Effective Rain Offset</div>
          <div class="detail-item-value">${rec.effective_rainfall_mm || 0} mm</div>
        </div>
        <div>
          <div class="detail-item-title">Recheck Interval</div>
          <div class="detail-item-value">${rec.recheck_hours} Hours</div>
        </div>
      </div>
      <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px; font-size:12px; color:var(--text-muted);">
        <strong>Safety Note & Scientific Transparency:</strong><br>
        ${rec.safety_notes || t("advisoryDisclaimer")}
      </div>
    </div>
  `;
}

// ---------------- SCHEDULER VIEW ----------------
async function renderSchedulerView() {
  const schedules = await AquaSenseAPI.getSchedules();
  const tableBody = document.getElementById("schedulerTableBody");
  if (!tableBody) return;

  tableBody.innerHTML = schedules.map(s => `
    <tr>
      <td><strong>${s.plot_name}</strong> (${s.crop_type || 'Crop'})</td>
      <td>${s.scheduled_date} at ${s.scheduled_time}</td>
      <td>${s.duration_minutes} Mins</td>
      <td>${s.planned_water_litres.toLocaleString()} L</td>
      <td><span class="alert-tag ${s.status === 'completed' ? 'tag-info' : 'tag-warning'}">${s.status.toUpperCase()}</span></td>
      <td>
        ${s.status === 'scheduled' ? `<button class="btn btn-secondary btn-sm" onclick="markScheduleComplete('${s.id}')">Complete</button>` : 'Logged'}
      </td>
    </tr>
  `).join("");
}

async function markScheduleComplete(schedId) {
  const schedules = await AquaSenseAPI.getSchedules();
  const s = schedules.find(x => x.id === schedId);
  if (s) {
    s.status = "completed";
    await AquaSenseAPI.createSchedule(s);
    showToast("Schedule marked as completed and added to history", "success");
    renderSchedulerView();
  }
}

// ---------------- ALERTS VIEW ----------------
async function renderAlertsView() {
  const alerts = await AquaSenseAPI.getAlerts();
  const container = document.getElementById("fullAlertsList");
  if (!container) return;

  container.innerHTML = alerts.map(a => `
    <div class="alert-item-card ${a.severity} ${a.status === 'resolved' ? 'resolved' : ''}">
      <div>
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
          <span class="alert-tag tag-${a.severity}">${a.severity}</span>
          <strong style="font-size:15px;">${a.message}</strong>
          <span style="font-size:11px; color:var(--text-muted);">${a.plot_name || 'Farm'}</span>
        </div>
        <p style="font-size:13px; color:var(--text-muted); margin:4px 0;">${a.reason}</p>
        <p style="font-size:13px; color:var(--primary); font-weight:600;">Action Required: ${a.suggested_action}</p>
      </div>
      <div>
        ${a.status === 'active' ? `<button class="btn btn-primary btn-sm" onclick="resolveAlert('${a.id}')">Resolve Issue</button>` : `<span style="font-size:12px; color:#10b981; font-weight:700;">RESOLVED ✓</span>`}
      </div>
    </div>
  `).join("");
}

async function resolveAlert(alertId) {
  await AquaSenseAPI.updateAlertStatus(alertId, "resolved");
  showToast("Alert resolved successfully", "success");
  renderAlertsView();
  renderDashboard();
}

// ---------------- IOT SIMULATOR VIEW ----------------
function renderIotSimulatorView() {
  const output = document.getElementById("iotConsoleLog");
  if (output && !output.hasChildNodes()) {
    output.innerText = "[SYSTEM] LoRa Gateway Connected. Telemetry port 5000 listening...\n[NODE-01] RSSI: -68 dBm, Batt: 94.5%, Moisture: 34.5%, Temp: 27.5°C";
  }
}

function sendSimulatedPacket() {
  const moistureVal = parseFloat(document.getElementById("simMoistureInput").value) || 35.0;
  const tempVal = parseFloat(document.getElementById("simTempInput").value) || 28.0;

  AquaSenseAPI.addSoilReading(selectedPlotId, {
    soil_moisture_pct: moistureVal,
    soil_temperature_c: tempVal,
    source_type: "iot",
    sensor_battery_pct: 95.0
  });

  const output = document.getElementById("iotConsoleLog");
  if (output) {
    const timeStr = new Date().toLocaleTimeString();
    output.innerText = `[${timeStr}] TX Packet -> Plot: ${selectedPlotId} | Moisture: ${moistureVal}% | Temp: ${tempVal}°C | Status: 200 OK\n` + output.innerText;
  }

  showToast(`Simulated IoT telemetry injected: ${moistureVal}%`, "success");
  renderDashboard();
}

function triggerEmergencyStop() {
  if (confirm("EMERGENCY STOP: Do you want to immediately shut down all pump actuators and close automated valves?")) {
    showToast("EMERGENCY STOP ACTIVATED: All pumps turned OFF immediately.", "error");
    const output = document.getElementById("iotConsoleLog");
    if (output) {
      output.innerText = `[${new Date().toLocaleTimeString()}] !!! EMERGENCY STOP SIGNAL BROADCAST TO ALL HARDWARE RELAYS !!!\n` + output.innerText;
    }
  }
}

// ---------------- VOICE ASSISTANT ----------------
function setupSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn("Web Speech API not supported in this browser. Typed fallback is active.");
    return;
  }

  speechRecognition = new SpeechRecognition();
  speechRecognition.continuous = false;
  speechRecognition.interimResults = false;
  speechRecognition.lang = currentLanguage === "te" ? "te-IN" : "en-IN";

  speechRecognition.onstart = () => {
    isListening = true;
    const micBtn = document.getElementById("micButton");
    if (micBtn) micBtn.classList.add("listening");
    const promptEl = document.getElementById("voicePromptText");
    if (promptEl) promptEl.innerText = t("listening");
  };

  speechRecognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    handleVoiceInput(text);
  };

  speechRecognition.onerror = (event) => {
    console.warn("Speech error:", event.error);
    stopListening();
  };

  speechRecognition.onend = () => {
    stopListening();
  };
}

function toggleVoiceListen() {
  if (!speechRecognition) {
    showToast("Web Speech API unavailable in this browser. Please use the text input below.", "warning");
    return;
  }
  if (isListening) {
    speechRecognition.stop();
  } else {
    speechRecognition.lang = currentLanguage === "te" ? "te-IN" : "en-IN";
    try {
      speechRecognition.start();
    } catch (e) {
      speechRecognition.stop();
    }
  }
}

function stopListening() {
  isListening = false;
  const micBtn = document.getElementById("micButton");
  if (micBtn) micBtn.classList.remove("listening");
  const promptEl = document.getElementById("voicePromptText");
  if (promptEl) promptEl.innerText = t("voicePrompt");
}

async function handleVoiceInput(query) {
  if (!query || !query.trim()) return;
  appendChatMessage(query, "user");

  const response = await AquaSenseAPI.queryVoice(query, selectedPlotId, currentLanguage);
  appendChatMessage(response.answer, "assistant");
  speakAnswer(response.answer);
}

function submitTypedVoice() {
  const input = document.getElementById("typedVoiceInput");
  if (!input || !input.value.trim()) return;
  const q = input.value.trim();
  input.value = "";
  handleVoiceInput(q);
}

function sendSampleVoiceQuery(sampleText) {
  handleVoiceInput(sampleText);
}

function appendChatMessage(text, sender) {
  const history = document.getElementById("chatTranscriptHistory");
  if (!history) return;
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble bubble-${sender}`;
  bubble.innerText = text;
  history.appendChild(bubble);
  history.scrollTop = history.scrollHeight;
}

function speakAnswer(text) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = currentLanguage === "te" ? "te-IN" : "en-IN";
  window.speechSynthesis.speak(utterance);
}

// ---------------- CSV EXPORT ----------------
async function exportCsvReport() {
  const analytics = await AquaSenseAPI.getWaterAnalytics();
  let csv = "Date,Measured Water (Litres),Traditional Baseline (Litres),Water Saved (Litres),Savings (%)\n";
  analytics.records.forEach(r => {
    const pct = r.baseline_litres > 0 ? ((r.saved_litres / r.baseline_litres) * 100).toFixed(1) : "0";
    csv += `${r.record_date},${r.measured_litres},${r.baseline_litres},${r.saved_litres},${pct}%\n`;
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `aquasense_water_report_${new Date().toISOString().split("T")[0]}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast("CSV water usage report downloaded", "success");
}

// ---------------- TOAST NOTIFICATIONS ----------------
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ---------------- MODALS LOGIC ----------------
function setupModals() {
  document.querySelectorAll(".modal-close-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".modal-overlay").forEach(m => m.classList.remove("active"));
    });
  });
}

function openSoilModal(plotId) {
  const modal = document.getElementById("soilReadingModal");
  if (modal) modal.classList.add("active");
}

function openScheduleModalForPlot(plotId) {
  const modal = document.getElementById("scheduleModal");
  if (modal) modal.classList.add("active");
}

function closeAllModals() {
  document.querySelectorAll(".modal-overlay").forEach(m => m.classList.remove("active"));
}

function submitSoilReadingModal() {
  const moisture = parseFloat(document.getElementById("modalMoistureInput").value);
  if (isNaN(moisture)) {
    showToast("Please enter a valid moisture percentage", "error");
    return;
  }
  AquaSenseAPI.addSoilReading(selectedPlotId, {
    soil_moisture_pct: moisture,
    source_type: "manual",
    soil_temperature_c: 28.0
  });
  closeAllModals();
  showToast(`Soil reading of ${moisture}% recorded`, "success");
  renderDashboard();
}

function submitScheduleModal() {
  const dateVal = document.getElementById("modalSchedDate").value;
  const timeVal = document.getElementById("modalSchedTime").value;
  const durationVal = parseInt(document.getElementById("modalSchedDuration").value) || 45;
  const litresVal = parseFloat(document.getElementById("modalSchedLitres").value) || 1200;
  const notesVal = document.getElementById("modalSchedNotes").value || "";

  if (!dateVal || !timeVal) {
    showToast("Date and time are required", "error");
    return;
  }

  AquaSenseAPI.createSchedule({
    plot_id: selectedPlotId,
    scheduled_date: dateVal,
    scheduled_time: timeVal,
    duration_minutes: durationVal,
    planned_water_litres: litresVal,
    notes: notesVal
  });

  closeAllModals();
  showToast("Irrigation session scheduled successfully", "success");
  renderDashboard();
  renderSchedulerView();
}
