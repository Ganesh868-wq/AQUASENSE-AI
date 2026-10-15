// AquaSense AI — API Client with Dual Mode (Live Backend API + Robust Offline State)

const API_BASE = (window.location.protocol.startsWith("http")) 
  ? `${window.location.origin}/api` 
  : "http://127.0.0.1:5000/api";

const AquaSenseAPI = {
  token: localStorage.getItem("aquasense_token") || null,
  currentUser: JSON.parse(localStorage.getItem("aquasense_user") || "null"),

  isBackendAvailable: null,

  async checkBackend() {
    if (this.isBackendAvailable !== null) return this.isBackendAvailable;
    try {
      const res = await fetch(`${API_BASE}/health`, { method: "GET", headers: { "Content-Type": "application/json" } });
      this.isBackendAvailable = res.ok;
    } catch (e) {
      this.isBackendAvailable = false;
    }
    return this.isBackendAvailable;
  },

  getHeaders() {
    const headers = { "Content-Type": "application/json" };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    return headers;
  },

  // ---------------- AUTH ----------------
  async login(email, password) {
    const backendOnline = await this.checkBackend();
    if (backendOnline) {
      try {
        const res = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (res.ok) {
          this.token = data.token;
          this.currentUser = data.user;
          localStorage.setItem("aquasense_token", this.token);
          localStorage.setItem("aquasense_user", JSON.stringify(this.currentUser));
          return { success: true, user: this.currentUser };
        }
        return { success: false, error: data.error };
      } catch (err) {
        console.warn("Backend login error, falling back to local session:", err);
      }
    }

    // Local / Offline demo login fallback
    this.token = "demo_token_offline_2026";
    this.currentUser = {
      id: "demo-user-1",
      email: email || "farmer@aquasense.ai",
      full_name: "Ganesh Rao",
      phone: "+91 98765 43210",
      preferred_language: "en"
    };
    localStorage.setItem("aquasense_token", this.token);
    localStorage.setItem("aquasense_user", JSON.stringify(this.currentUser));
    return { success: true, user: this.currentUser };
  },

  logout() {
    this.token = null;
    this.currentUser = null;
    localStorage.removeItem("aquasense_token");
    localStorage.removeItem("aquasense_user");
  },

  // ---------------- FARMS & PLOTS ----------------
  async getFarms() {
    const backendOnline = await this.checkBackend();
    if (backendOnline && this.token) {
      try {
        const res = await fetch(`${API_BASE}/farms`, { headers: this.getHeaders() });
        if (res.ok) {
          const data = await res.json();
          return data.farms;
        }
      } catch (e) {}
    }
    return this.getLocalFarms();
  },

  async getPlots(farmId) {
    const backendOnline = await this.checkBackend();
    if (backendOnline && this.token) {
      try {
        const res = await fetch(`${API_BASE}/farms/${farmId}/plots`, { headers: this.getHeaders() });
        if (res.ok) {
          const data = await res.json();
          return data.plots;
        }
      } catch (e) {}
    }
    return this.getLocalPlots(farmId);
  },

  // ---------------- SOIL READINGS ----------------
  async getSoilReadings(plotId) {
    const backendOnline = await this.checkBackend();
    if (backendOnline && this.token) {
      try {
        const res = await fetch(`${API_BASE}/plots/${plotId}/soil-readings`, { headers: this.getHeaders() });
        if (res.ok) {
          const data = await res.json();
          return data.readings;
        }
      } catch (e) {}
    }
    return this.getLocalSoilReadings(plotId);
  },

  async addSoilReading(plotId, data) {
    const backendOnline = await this.checkBackend();
    if (backendOnline && this.token) {
      try {
        const res = await fetch(`${API_BASE}/plots/${plotId}/soil-readings`, {
          method: "POST",
          headers: this.getHeaders(),
          body: JSON.stringify(data)
        });
        if (res.ok) return await res.json();
      } catch (e) {}
    }
    // Update local state
    const plots = this.getLocalPlots();
    const p = plots.find(x => x.id === plotId);
    if (p) {
      p.current_moisture = parseFloat(data.soil_moisture_pct);
      localStorage.setItem("aquasense_plots", JSON.stringify(plots));
    }
    return { message: "Recorded locally", reading: data };
  },

  // ---------------- WEATHER ----------------
  async getWeather(farmId, lat = 17.9689, lon = 79.5941) {
    const backendOnline = await this.checkBackend();
    if (backendOnline && this.token && farmId) {
      try {
        const res = await fetch(`${API_BASE}/farms/${farmId}/weather`, { headers: this.getHeaders() });
        if (res.ok) {
          const data = await res.json();
          return data.weather;
        }
      } catch (e) {}
    }

    // Direct browser fetch from Open-Meteo API (requires NO key!)
    try {
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,et0_fao_evapotranspiration&timezone=auto`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        const current = data.current || {};
        const daily = data.daily || {};
        const forecast = (daily.time || []).map((t, i) => ({
          date: t,
          temp_max: daily.temperature_2m_max[i] || 32,
          temp_min: daily.temperature_2m_min[i] || 22,
          precipitation_mm: daily.precipitation_sum[i] || 0,
          rain_prob_pct: daily.precipitation_probability_max[i] || 15
        }));
        return {
          source_type: "live_api",
          api_provider: "Open-Meteo High-Resolution Global Weather",
          location_name: "Warangal, Telangana (Live GPS)",
          temperature_c: current.temperature_2m || 31.5,
          humidity_pct: current.relative_humidity_2m || 54.0,
          wind_speed_kmh: current.wind_speed_10m || 11.2,
          rainfall_mm: current.precipitation || 0.0,
          rain_probability_pct: (forecast[0] && forecast[0].rain_prob_pct) || 20.0,
          forecast_rain_48h_mm: (forecast[0] ? forecast[0].precipitation_mm : 0) + (forecast[1] ? forecast[1].precipitation_mm * 0.5 : 0),
          daily_forecast: forecast,
          last_updated: new Date().toLocaleTimeString()
        };
      }
    } catch (err) {
      console.warn("Direct Open-Meteo query failed, using agronomic cache:", err);
    }

    // Agronomic Demo Weather Fallback
    return {
      source_type: "demo",
      api_provider: "AquaSense Agronomic Demo Cache",
      location_name: "Warangal, Telangana (Demo Mode)",
      temperature_c: 32.2,
      humidity_pct: 54.0,
      wind_speed_kmh: 11.5,
      rainfall_mm: 0.0,
      rain_probability_pct: 22.0,
      forecast_rain_48h_mm: 2.0,
      daily_forecast: [
        { date: "Today", temp_max: 33.0, temp_min: 23.0, precipitation_mm: 0.0, rain_prob_pct: 20 },
        { date: "Tomorrow", temp_max: 34.0, temp_min: 24.0, precipitation_mm: 4.0, rain_prob_pct: 45 },
        { date: "Day 3", temp_max: 31.0, temp_min: 22.0, precipitation_mm: 14.0, rain_prob_pct: 75 },
        { date: "Day 4", temp_max: 30.0, temp_min: 21.0, precipitation_mm: 2.0, rain_prob_pct: 30 },
        { date: "Day 5", temp_max: 33.0, temp_min: 23.0, precipitation_mm: 0.0, rain_prob_pct: 10 }
      ],
      last_updated: new Date().toLocaleTimeString()
    };
  },

  // ---------------- RECOMMENDATIONS ----------------
  async getRecommendation(plotId, plot, weather) {
    const backendOnline = await this.checkBackend();
    if (backendOnline && this.token) {
      try {
        const res = await fetch(`${API_BASE}/plots/${plotId}/recommendation`, { headers: this.getHeaders() });
        if (res.ok) {
          const data = await res.json();
          return data.recommendation;
        }
      } catch (e) {}
    }

    // Client-side execution
    return calculateClientRecommendation({
      crop_type: plot.crop_type,
      growth_stage: plot.growth_stage,
      soil_type: plot.soil_type,
      current_moisture_pct: plot.current_moisture,
      plot_area: plot.area,
      area_unit: plot.area_unit,
      irrigation_method: plot.irrigation_method,
      root_depth_m: plot.root_depth_m,
      pump_flow_rate_lpm: 140,
      temp_c: weather.temperature_c,
      humidity_pct: weather.humidity_pct,
      wind_speed_kmh: weather.wind_speed_kmh,
      forecast_rain_mm: weather.forecast_rain_48h_mm,
      rain_probability_pct: weather.rain_probability_pct
    });
  },

  // ---------------- SCHEDULER ----------------
  async getSchedules() {
    const backendOnline = await this.checkBackend();
    if (backendOnline && this.token) {
      try {
        const res = await fetch(`${API_BASE}/schedules`, { headers: this.getHeaders() });
        if (res.ok) {
          const data = await res.json();
          return data.schedules;
        }
      } catch (e) {}
    }
    return this.getLocalSchedules();
  },

  async createSchedule(schedData) {
    const backendOnline = await this.checkBackend();
    if (backendOnline && this.token) {
      try {
        const res = await fetch(`${API_BASE}/schedules`, {
          method: "POST",
          headers: this.getHeaders(),
          body: JSON.stringify(schedData)
        });
        if (res.ok) return await res.json();
      } catch (e) {}
    }

    const scheds = this.getLocalSchedules();
    const newEntry = {
      id: "sched-" + Date.now(),
      plot_id: schedData.plot_id,
      plot_name: schedData.plot_name || "Plot 1",
      crop_type: schedData.crop_type || "Cotton",
      scheduled_date: schedData.scheduled_date,
      scheduled_time: schedData.scheduled_time,
      duration_minutes: parseInt(schedData.duration_minutes) || 45,
      planned_water_litres: parseFloat(schedData.planned_water_litres) || 1200,
      notes: schedData.notes || "",
      status: "scheduled",
      is_hardware_executed: false
    };
    scheds.unshift(newEntry);
    localStorage.setItem("aquasense_schedules", JSON.stringify(scheds));
    return { schedule: newEntry };
  },

  // ---------------- ALERTS ----------------
  async getAlerts() {
    const backendOnline = await this.checkBackend();
    if (backendOnline && this.token) {
      try {
        const res = await fetch(`${API_BASE}/alerts`, { headers: this.getHeaders() });
        if (res.ok) {
          const data = await res.json();
          return data.alerts;
        }
      } catch (e) {}
    }
    return this.getLocalAlerts();
  },

  async updateAlertStatus(alertId, newStatus) {
    const backendOnline = await this.checkBackend();
    if (backendOnline && this.token) {
      try {
        await fetch(`${API_BASE}/alerts/${alertId}/status`, {
          method: "PUT",
          headers: this.getHeaders(),
          body: JSON.stringify({ status: newStatus })
        });
      } catch (e) {}
    }

    const alerts = this.getLocalAlerts();
    const a = alerts.find(x => x.id === alertId);
    if (a) {
      a.status = newStatus;
      localStorage.setItem("aquasense_alerts", JSON.stringify(alerts));
    }
  },

  // ---------------- WATER ANALYTICS ----------------
  async getWaterAnalytics() {
    const backendOnline = await this.checkBackend();
    if (backendOnline && this.token) {
      try {
        const res = await fetch(`${API_BASE}/analytics/water-usage`, { headers: this.getHeaders() });
        if (res.ok) return await res.json();
      } catch (e) {}
    }
    return this.getLocalAnalytics();
  },

  // ---------------- VOICE ASSISTANT ----------------
  async queryVoice(query, plotId, lang = "te") {
    const backendOnline = await this.checkBackend();
    if (backendOnline && this.token) {
      try {
        const res = await fetch(`${API_BASE}/voice/query`, {
          method: "POST",
          headers: this.getHeaders(),
          body: JSON.stringify({ query, plot_id: plotId, language: lang })
        });
        if (res.ok) return await res.json();
      } catch (e) {}
    }

    // Local client-side voice response engine
    const plots = this.getLocalPlots();
    const plot = (plotId ? plots.find(p => p.id === plotId) : plots[0]) || { name: "Plot 1", crop_type: "Cotton", current_moisture: 34.5 };
    const qLower = query.toLowerCase();

    if (qLower.includes("neeru pettala") || qLower.includes("irrigate") || qLower.includes("నీరు")) {
      if (lang === "te") {
        return {
          answer: `మీ ${plot.crop_type} ప్లాట్ '${plot.name}' లో తేమ శాతం ${plot.current_moisture}%. ఇది తక్కువగా ఉన్నందున ఇప్పుడే నీరు పెట్టండి (Irrigate Now). సుమారు 8,400 లీటర్ల నీరు అవసరం.`,
          status: "Irrigate Now"
        };
      }
      return {
        answer: `Yes, for plot '${plot.name}', soil moisture is currently ${plot.current_moisture}%. You should irrigate now with approximately 8,400 Litres (~60 mins).`,
        status: "Irrigate Now"
      };
    }

    if (qLower.includes("varsham") || qLower.includes("rain") || qLower.includes("వర్షం")) {
      if (lang === "te") {
        return {
          answer: `రాబోయే 48 గంటల్లో 40% వర్షం పడే అవకాశం ఉంది. సుమారు 4-8 మి.మీ వర్షపాతం కురిసే అవకాశం కనిపిస్తోంది.`,
          status: "Monitor"
        };
      }
      return {
        answer: `Forecast indicates a 40% probability of rainfall with 4-8 mm accumulation in the next 48 hours.`,
        status: "Monitor"
      };
    }

    if (qLower.includes("moisture") || qLower.includes("తేమ")) {
      if (lang === "te") {
        return {
          answer: `మీ ప్లాట్ '${plot.name}' లో ప్రస్తుత నేల తేమ ${plot.current_moisture}%.`,
          status: "Info"
        };
      }
      return {
        answer: `Current soil moisture in '${plot.name}' is ${plot.current_moisture}%.`,
        status: "Info"
      };
    }

    // Default response
    if (lang === "te") {
      return {
        answer: `మీ ${plot.crop_type} ప్లాట్ స్థితి: తేమ ${plot.current_moisture}%. వ్యవసాయ సిఫార్సు: ఇప్పుడే నీరు అందించాలి. మీకు వర్షం లేదా నీటి పరిమాణం గురించి వివరాలు కావాలా?`,
        status: "Irrigate Now"
      };
    }
    return {
      answer: `For ${plot.name} (${plot.crop_type}), current moisture is ${plot.current_moisture}%. Recommended action is Irrigate Now. Ask about rainfall or water volume for more info.`,
      status: "Irrigate Now"
    };
  },

  // ---------------- LOCAL STATE STORAGE DEFAULTS ----------------
  getLocalFarms() {
    const cached = localStorage.getItem("aquasense_farms");
    if (cached) return JSON.parse(cached);
    const defaults = [{
      id: "farm-1",
      name: "Sri Lakshmi Agro-Tech Farm",
      location_name: "Warangal, Telangana",
      latitude: 17.9689,
      longitude: 79.5941,
      total_area: 8.0,
      area_unit: "Acres",
      water_source_type: "Borewell + Solar Pump",
      pump_flow_rate_lpm: 140.0,
      pump_power_hp: 5.0,
      notes: "Integrated micro-irrigation farm with solar borewell."
    }];
    localStorage.setItem("aquasense_farms", JSON.stringify(defaults));
    return defaults;
  },

  getLocalPlots(farmId = "farm-1") {
    const cached = localStorage.getItem("aquasense_plots");
    if (cached) return JSON.parse(cached);
    const defaults = [
      {
        id: "plot-1",
        farm_id: farmId,
        name: "Plot 1 - North Cotton Block",
        crop_type: "Cotton",
        crop_variety: "Bt Cotton RCH-659",
        soil_type: "Black Cotton Soil",
        area: 2.5,
        area_unit: "Acres",
        planting_date: "2026-08-10",
        growth_stage: "Mid-Season",
        irrigation_method: "Drip",
        emitter_flow_rate_lph: 4.0,
        plant_spacing_m: 0.9,
        row_spacing_m: 1.2,
        root_depth_m: 0.9,
        target_moisture_min: 38.0,
        target_moisture_max: 68.0,
        current_moisture: 34.5,
        sensor_id: "SN-CTN-01"
      },
      {
        id: "plot-2",
        farm_id: farmId,
        name: "Plot 2 - South Tomato Polyhouse",
        crop_type: "Tomato",
        crop_variety: "Arka Rakshak",
        soil_type: "Red Loamy Soil",
        area: 1.5,
        area_unit: "Acres",
        planting_date: "2026-09-01",
        growth_stage: "Crop Development",
        irrigation_method: "Drip",
        emitter_flow_rate_lph: 2.5,
        plant_spacing_m: 0.5,
        row_spacing_m: 0.8,
        root_depth_m: 0.6,
        target_moisture_min: 45.0,
        target_moisture_max: 75.0,
        current_moisture: 58.0,
        sensor_id: "SN-TOM-02"
      },
      {
        id: "plot-3",
        farm_id: farmId,
        name: "Plot 3 - Lowland Paddy Basin",
        crop_type: "Paddy",
        crop_variety: "Telangana Sona (RNR 15048)",
        soil_type: "Clay Loam",
        area: 2.5,
        area_unit: "Acres",
        planting_date: "2026-08-20",
        growth_stage: "Mid-Season",
        irrigation_method: "Flood",
        emitter_flow_rate_lph: 0.0,
        plant_spacing_m: 0.15,
        row_spacing_m: 0.20,
        root_depth_m: 0.5,
        target_moisture_min: 55.0,
        target_moisture_max: 85.0,
        current_moisture: 72.0,
        sensor_id: "SN-PDY-03"
      },
      {
        id: "plot-4",
        farm_id: farmId,
        name: "Plot 4 - East Groundnut Field",
        crop_type: "Groundnut",
        crop_variety: "Kadiri-6",
        soil_type: "Sandy Loam Soil",
        area: 1.5,
        area_unit: "Acres",
        planting_date: "2026-09-15",
        growth_stage: "Initial",
        irrigation_method: "Sprinkler",
        emitter_flow_rate_lph: 15.0,
        plant_spacing_m: 0.1,
        row_spacing_m: 0.3,
        root_depth_m: 0.4,
        target_moisture_min: 40.0,
        target_moisture_max: 65.0,
        current_moisture: 36.2,
        sensor_id: "SN-GNT-04"
      }
    ];
    localStorage.setItem("aquasense_plots", JSON.stringify(defaults));
    return defaults;
  },

  getLocalSoilReadings(plotId) {
    const list = [];
    const base = 34.5;
    for (let h = 24; h >= 0; h -= 2) {
      list.push({
        id: "sr-" + h,
        plot_id: plotId,
        soil_moisture_pct: +(base + Math.sin(h / 3) * 2.2 + (h * 0.15)).toFixed(1),
        soil_temperature_c: +(27.5 + (h > 10 && h < 18 ? 3.5 : 0)).toFixed(1),
        electrical_conductivity: 1.15,
        source_type: "iot",
        sensor_battery_pct: +(96.0 - h * 0.1).toFixed(1),
        reading_timestamp: new Date(Date.now() - h * 3600 * 1000).toISOString()
      });
    }
    return list;
  },

  getLocalSchedules() {
    const cached = localStorage.getItem("aquasense_schedules");
    if (cached) return JSON.parse(cached);
    const defaults = [
      {
        id: "sched-1",
        plot_id: "plot-1",
        plot_name: "Plot 1 - North Cotton Block",
        crop_type: "Cotton",
        scheduled_date: new Date(Date.now() + 86400000).toISOString().split("T")[0],
        scheduled_time: "06:30",
        duration_minutes: 60,
        planned_water_litres: 8400,
        notes: "Morning drip cycle - peak flowering",
        status: "scheduled",
        is_hardware_executed: false
      },
      {
        id: "sched-2",
        plot_id: "plot-4",
        plot_name: "Plot 4 - East Groundnut Field",
        crop_type: "Groundnut",
        scheduled_date: new Date(Date.now() + 86400000).toISOString().split("T")[0],
        scheduled_time: "17:00",
        duration_minutes: 40,
        planned_water_litres: 5600,
        notes: "Evening sprinkler pulse",
        status: "scheduled",
        is_hardware_executed: false
      }
    ];
    localStorage.setItem("aquasense_schedules", JSON.stringify(defaults));
    return defaults;
  },

  getLocalAlerts() {
    const cached = localStorage.getItem("aquasense_alerts");
    if (cached) return JSON.parse(cached);
    const defaults = [
      {
        id: "alt-1",
        plot_name: "Plot 1 - North Cotton Block",
        alert_type: "low_moisture",
        severity: "critical",
        message: "Soil Moisture Deficit Alert (34.5%)",
        reason: "Plot 1 (Cotton) has dropped below minimum threshold (38%). Moisture stress may cause flower square shedding.",
        suggested_action: "Execute recommended drip irrigation cycle of 8,400 Litres immediately.",
        status: "active",
        created_at: new Date(Date.now() - 3600000).toISOString()
      },
      {
        id: "alt-2",
        plot_name: "Plot 1 - North Cotton Block",
        alert_type: "leakage_suspected",
        severity: "warning",
        message: "Suspected Micro-Leakage on Lateral B-4",
        reason: "Sensor telemetry indicates sharp localized pressure drop and uneven sub-surface moisture dispersion.",
        suggested_action: "Inspect lateral dripline B-4 for punctures or dislodged emitter barbs.",
        status: "active",
        created_at: new Date(Date.now() - 7200000).toISOString()
      }
    ];
    localStorage.setItem("aquasense_alerts", JSON.stringify(defaults));
    return defaults;
  },

  getLocalAnalytics() {
    const records = [];
    let totActual = 0;
    let totBase = 0;
    let totSaved = 0;
    for (let i = 14; i >= 1; i--) {
      const dt = new Date(Date.now() - i * 86400000).toISOString().split("T")[0];
      const base = 18500 + Math.round(Math.sin(i) * 2000);
      const actual = Math.round(base * 0.61);
      const saved = base - actual;
      totActual += actual;
      totBase += base;
      totSaved += saved;
      records.push({
        record_date: dt,
        measured_litres: actual,
        baseline_litres: base,
        saved_litres: saved
      });
    }
    return {
      summary: {
        total_consumed_litres: totActual,
        total_baseline_litres: totBase,
        total_saved_litres: totSaved,
        savings_pct: +((totSaved / totBase) * 100).toFixed(1),
        water_use_efficiency_score: "High (0.88 kg/m³)"
      },
      records: records
    };
  }
};
