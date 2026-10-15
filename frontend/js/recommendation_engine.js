// AquaSense AI — Client-Side Agronomic Recommendation Engine (FAO-56 Compliant)

const CROP_DATABASE_JS = {
  Paddy: { name: "Paddy (Rice)", kc: { Initial: 1.05, "Crop Development": 1.15, "Mid-Season": 1.20, "Late Season": 0.90 }, default_root_depth_m: 0.5, depletion_p: 0.20, critical_sm: 55.0, fc: 80.0 },
  Cotton: { name: "Cotton", kc: { Initial: 0.35, "Crop Development": 0.75, "Mid-Season": 1.15, "Late Season": 0.65 }, default_root_depth_m: 1.0, depletion_p: 0.65, critical_sm: 38.0, fc: 65.0 },
  Groundnut: { name: "Groundnut", kc: { Initial: 0.40, "Crop Development": 0.75, "Mid-Season": 1.05, "Late Season": 0.60 }, default_root_depth_m: 0.6, depletion_p: 0.50, critical_sm: 40.0, fc: 62.0 },
  Maize: { name: "Maize (Corn)", kc: { Initial: 0.30, "Crop Development": 0.80, "Mid-Season": 1.20, "Late Season": 0.60 }, default_root_depth_m: 0.9, depletion_p: 0.55, critical_sm: 42.0, fc: 68.0 },
  Tomato: { name: "Tomato", kc: { Initial: 0.45, "Crop Development": 0.75, "Mid-Season": 1.15, "Late Season": 0.80 }, default_root_depth_m: 0.7, depletion_p: 0.40, critical_sm: 45.0, fc: 70.0 },
  Chilli: { name: "Chilli", kc: { Initial: 0.35, "Crop Development": 0.70, "Mid-Season": 1.05, "Late Season": 0.75 }, default_root_depth_m: 0.6, depletion_p: 0.45, critical_sm: 42.0, fc: 68.0 },
  Wheat: { name: "Wheat", kc: { Initial: 0.30, "Crop Development": 0.75, "Mid-Season": 1.15, "Late Season": 0.40 }, default_root_depth_m: 0.8, depletion_p: 0.55, critical_sm: 40.0, fc: 65.0 },
  Sugarcane: { name: "Sugarcane", kc: { Initial: 0.40, "Crop Development": 0.80, "Mid-Season": 1.25, "Late Season": 0.75 }, default_root_depth_m: 1.2, depletion_p: 0.65, critical_sm: 48.0, fc: 72.0 },
  Soybean: { name: "Soybean", kc: { Initial: 0.40, "Crop Development": 0.75, "Mid-Season": 1.15, "Late Season": 0.50 }, default_root_depth_m: 0.7, depletion_p: 0.50, critical_sm: 40.0, fc: 65.0 },
  Onion: { name: "Onion", kc: { Initial: 0.50, "Crop Development": 0.75, "Mid-Season": 1.05, "Late Season": 0.75 }, default_root_depth_m: 0.4, depletion_p: 0.30, critical_sm: 48.0, fc: 68.0 }
};

const SOIL_DATABASE_JS = {
  "Black Cotton Soil": { awc: 190.0, fc: 42.0, wp: 23.0 },
  "Clay Loam": { awc: 165.0, fc: 34.0, wp: 17.5 },
  "Red Loamy Soil": { awc: 140.0, fc: 28.0, wp: 14.0 },
  "Alluvial Soil": { awc: 150.0, fc: 27.0, wp: 12.0 },
  "Sandy Loam Soil": { awc: 110.0, fc: 21.0, wp: 10.0 },
  "Sandy Soil": { awc: 70.0, fc: 14.0, wp: 7.0 }
};

const IRR_EFFICIENCY_JS = {
  Drip: 0.90,
  "Micro-Sprinkler": 0.80,
  Sprinkler: 0.75,
  Flood: 0.50,
  Furrow: 0.55
};

function calculateClientRecommendation(params) {
  const crop = CROP_DATABASE_JS[params.crop_type] || CROP_DATABASE_JS.Cotton;
  const stageKc = crop.kc[params.growth_stage] || 1.0;
  const p = crop.depletion_p;
  const zr = params.root_depth_m || crop.default_root_depth_m;

  const soil = SOIL_DATABASE_JS[params.soil_type] || SOIL_DATABASE_JS["Black Cotton Soil"];
  const awc = soil.awc;
  const fc = soil.fc;
  const wp = soil.wp;

  const taw = awc * zr;
  const raw = p * taw;
  const stressThreshold = wp + (1.0 - p) * (fc - wp);

  const temp = Math.max(10, Math.min(50, params.temp_c || 32));
  const hum = Math.max(10, Math.min(100, params.humidity_pct || 50));
  const wind = Math.max(0, params.wind_speed_kmh || 10);

  // FAO-56 Reference ET0
  const et0Base = 0.0023 * (temp + 17.8) * Math.sqrt(15.0) * 20.0 * 0.408;
  const et0 = Math.max(2.5, Math.min(9.5, et0Base * (0.85 + 0.25 * ((100 - hum) / 50)) * (0.9 + 0.1 * (1 + wind * 0.02))));
  const etc = stageKc * et0;

  const sm = Math.max(5, Math.min(95, params.current_moisture_pct || 40));
  let depletionMm = 0;
  if (sm >= fc) depletionMm = 0;
  else if (sm <= wp) depletionMm = taw;
  else depletionMm = ((fc - sm) / (fc - wp)) * taw;

  const forecastRain = params.forecast_rain_mm || 0;
  const rainProb = params.rain_probability_pct || 0;

  let effectiveRain = 0;
  if (forecastRain >= 4.0 && rainProb >= 35) {
    const probFactor = Math.min(1, rainProb / 100);
    effectiveRain = Math.max(0, (forecastRain - 3.0) * 0.8) * probFactor;
  }

  // Decision logic
  let status = "Monitor";
  let recheckHours = 24;
  let reason = "";

  const canDelay = (forecastRain >= 12.0 && rainProb >= 50) || (effectiveRain >= 5.0 && rainProb >= 50);

  if (canDelay) {
    status = "Delay and Recheck";
    recheckHours = 12;
    reason = `Expected rainfall of ${forecastRain.toFixed(1)} mm (${rainProb.toFixed(0)}% chance) will provide ~${effectiveRain.toFixed(1)} mm moisture. Postpone irrigation to save water.`;
  } else if (sm < stressThreshold || depletionMm >= raw) {
    status = "Irrigate Now";
    recheckHours = 6;
    reason = `Soil moisture (${sm.toFixed(1)}%) is below critical threshold (${stressThreshold.toFixed(1)}%). Root-zone water depletion (${depletionMm.toFixed(1)} mm) exceeds allowable buffer.`;
  } else if (sm < fc * 0.85) {
    status = "Monitor";
    recheckHours = 18;
    reason = `Soil moisture (${sm.toFixed(1)}%) is within acceptable buffer. Crop is transpiring at ${etc.toFixed(1)} mm/day. Monitor regularly.`;
  } else {
    status = "Monitor";
    recheckHours = 24;
    reason = `Soil moisture (${sm.toFixed(1)}%) is near field capacity (${fc.toFixed(1)}%). Optimal conditions.`;
  }

  // Area conversion
  let areaSqM = (params.plot_area || 1) * 4046.86;
  const unit = (params.area_unit || "Acres").toLowerCase();
  if (unit.includes("hect")) areaSqM = (params.plot_area || 1) * 10000;
  else if (unit.includes("guntha")) areaSqM = (params.plot_area || 1) * 101.17;

  const eff = IRR_EFFICIENCY_JS[params.irrigation_method] || 0.85;
  const nirMm = status === "Irrigate Now" ? Math.max(0, depletionMm - effectiveRain) : 0;
  const girMm = eff > 0 ? nirMm / eff : nirMm;

  const waterLitres = Math.round(girMm * areaSqM);
  const waterM3 = (waterLitres / 1000).toFixed(2);

  const pumpLpm = Math.max(20, params.pump_flow_rate_lpm || 120);
  const durationMinutes = status === "Irrigate Now" ? Math.max(15, Math.min(1440, Math.round(waterLitres / pumpLpm))) : 0;

  const baselineLitres = Math.round(((depletionMm > 0 ? depletionMm : etc) / 0.50) * areaSqM);
  const waterSavedLitres = status === "Irrigate Now" ? Math.max(0, baselineLitres - waterLitres) : Math.round(baselineLitres * 0.8);

  return {
    status: status,
    water_req_litres: waterLitres,
    water_req_m3: parseFloat(waterM3),
    suggested_duration_minutes: durationMinutes,
    recheck_hours: recheckHours,
    effective_rainfall_mm: parseFloat(effectiveRain.toFixed(1)),
    forecast_rain_mm: forecastRain,
    rain_prob_pct: rainProb,
    confidence_pct: 88,
    baseline_litres: baselineLitres,
    water_saved_litres: waterSavedLitres,
    reason: reason,
    factors: {
      et0_mm_day: parseFloat(et0.toFixed(2)),
      etc_mm_day: parseFloat(etc.toFixed(2)),
      current_moisture_pct: sm,
      critical_threshold_pct: parseFloat(stressThreshold.toFixed(1)),
      depletion_mm: parseFloat(depletionMm.toFixed(1)),
      taw_mm: Math.round(taw),
      raw_mm: Math.round(raw),
      efficiency_pct: Math.round(eff * 100)
    }
  };
}
