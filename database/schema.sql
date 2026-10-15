-- ========================================================
-- AQUASENSE AI: Smart Irrigation & Water Optimization System
-- Database Schema (PostgreSQL & SQLite Compatible)
-- ========================================================

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(50),
    preferred_language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS farms (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    location_name VARCHAR(255) NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    total_area FLOAT DEFAULT 1.0,
    area_unit VARCHAR(20) DEFAULT 'Acres',
    water_source_type VARCHAR(100) DEFAULT 'Borewell',
    pump_flow_rate_lpm FLOAT DEFAULT 120.0,
    pump_power_hp FLOAT DEFAULT 3.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plots (
    id VARCHAR(36) PRIMARY KEY,
    farm_id VARCHAR(36) NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    crop_type VARCHAR(100) NOT NULL,
    crop_variety VARCHAR(100),
    soil_type VARCHAR(100) DEFAULT 'Black Cotton Soil',
    area FLOAT DEFAULT 1.0,
    area_unit VARCHAR(20) DEFAULT 'Acres',
    planting_date VARCHAR(20),
    growth_stage VARCHAR(50) DEFAULT 'Mid-Season',
    irrigation_method VARCHAR(50) DEFAULT 'Drip',
    emitter_flow_rate_lph FLOAT DEFAULT 4.0,
    plant_spacing_m FLOAT DEFAULT 0.6,
    row_spacing_m FLOAT DEFAULT 1.2,
    root_depth_m FLOAT DEFAULT 0.6,
    target_moisture_min FLOAT DEFAULT 42.0,
    target_moisture_max FLOAT DEFAULT 78.0,
    current_moisture FLOAT DEFAULT 50.0,
    sensor_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS soil_readings (
    id VARCHAR(36) PRIMARY KEY,
    plot_id VARCHAR(36) NOT NULL REFERENCES plots(id) ON DELETE CASCADE,
    soil_moisture_pct FLOAT NOT NULL,
    soil_temperature_c FLOAT DEFAULT 27.5,
    electrical_conductivity FLOAT DEFAULT 1.1,
    source_type VARCHAR(30) DEFAULT 'manual', -- 'manual', 'iot', 'demo'
    sensor_battery_pct FLOAT,
    reading_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weather_records (
    id VARCHAR(36) PRIMARY KEY,
    farm_id VARCHAR(36) NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    temperature_c FLOAT NOT NULL,
    humidity_pct FLOAT NOT NULL,
    wind_speed_kmh FLOAT DEFAULT 10.0,
    rainfall_mm FLOAT DEFAULT 0.0,
    rain_probability_pct FLOAT DEFAULT 0.0,
    solar_radiation FLOAT,
    source_type VARCHAR(30) DEFAULT 'live_api',
    forecast_json TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS irrigation_recommendations (
    id VARCHAR(36) PRIMARY KEY,
    plot_id VARCHAR(36) NOT NULL REFERENCES plots(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL, -- 'Irrigate Now', 'Monitor', 'Delay and Recheck'
    water_req_litres FLOAT DEFAULT 0.0,
    water_req_m3 FLOAT DEFAULT 0.0,
    suggested_duration_minutes INTEGER DEFAULT 0,
    recheck_hours INTEGER DEFAULT 24,
    effective_rainfall_mm FLOAT DEFAULT 0.0,
    forecast_rain_mm FLOAT DEFAULT 0.0,
    rain_prob_pct FLOAT DEFAULT 0.0,
    confidence_pct FLOAT DEFAULT 85.0,
    factors_json TEXT,
    safety_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS irrigation_schedules (
    id VARCHAR(36) PRIMARY KEY,
    plot_id VARCHAR(36) NOT NULL REFERENCES plots(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheduled_date VARCHAR(20) NOT NULL,
    scheduled_time VARCHAR(10) NOT NULL,
    duration_minutes INTEGER DEFAULT 45,
    planned_water_litres FLOAT DEFAULT 1000.0,
    notes TEXT,
    status VARCHAR(30) DEFAULT 'scheduled',
    is_hardware_executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS irrigation_history (
    id VARCHAR(36) PRIMARY KEY,
    plot_id VARCHAR(36) NOT NULL REFERENCES plots(id) ON DELETE CASCADE,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_minutes INTEGER DEFAULT 45,
    actual_water_litres FLOAT DEFAULT 1200.0,
    method VARCHAR(50) DEFAULT 'Drip',
    status VARCHAR(30) DEFAULT 'completed',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(36) PRIMARY KEY,
    farm_id VARCHAR(36) NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    plot_id VARCHAR(36) REFERENCES plots(id) ON DELETE CASCADE,
    alert_type VARCHAR(60) NOT NULL,
    severity VARCHAR(20) DEFAULT 'warning', -- 'critical', 'warning', 'info'
    message VARCHAR(255) NOT NULL,
    reason TEXT NOT NULL,
    suggested_action TEXT NOT NULL,
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS water_usage (
    id VARCHAR(36) PRIMARY KEY,
    farm_id VARCHAR(36) NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    plot_id VARCHAR(36) NOT NULL REFERENCES plots(id) ON DELETE CASCADE,
    record_date VARCHAR(20) NOT NULL,
    measured_litres FLOAT DEFAULT 0.0,
    estimated_litres FLOAT DEFAULT 0.0,
    baseline_litres FLOAT DEFAULT 0.0,
    saved_litres FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS iot_devices (
    id VARCHAR(36) PRIMARY KEY,
    farm_id VARCHAR(36) NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    plot_id VARCHAR(36) REFERENCES plots(id) ON DELETE CASCADE,
    device_token VARCHAR(100) UNIQUE NOT NULL,
    device_name VARCHAR(100) NOT NULL,
    device_type VARCHAR(50) DEFAULT 'soil_sensor',
    is_active BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    battery_pct FLOAT DEFAULT 95.0,
    pump_state VARCHAR(10) DEFAULT 'off'
);
