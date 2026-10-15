import math
from typing import Dict, Any, Optional

# FAO-56 Agronomic Crop Parameters
CROP_DATABASE = {
    "Paddy": {
        "name": "Paddy (Rice)",
        "kc": {"Initial": 1.05, "Crop Development": 1.15, "Mid-Season": 1.20, "Late Season": 0.90},
        "default_root_depth_m": 0.5,
        "depletion_fraction_p": 0.20,  # Shallow root, sensitive to moisture depletion
        "critical_moisture_pct": 55.0,
        "field_capacity_pct": 80.0
    },
    "Cotton": {
        "name": "Cotton",
        "kc": {"Initial": 0.35, "Crop Development": 0.75, "Mid-Season": 1.15, "Late Season": 0.65},
        "default_root_depth_m": 1.0,
        "depletion_fraction_p": 0.65,
        "critical_moisture_pct": 38.0,
        "field_capacity_pct": 65.0
    },
    "Groundnut": {
        "name": "Groundnut (Peanut)",
        "kc": {"Initial": 0.40, "Crop Development": 0.75, "Mid-Season": 1.05, "Late Season": 0.60},
        "default_root_depth_m": 0.6,
        "depletion_fraction_p": 0.50,
        "critical_moisture_pct": 40.0,
        "field_capacity_pct": 62.0
    },
    "Maize": {
        "name": "Maize (Corn)",
        "kc": {"Initial": 0.30, "Crop Development": 0.80, "Mid-Season": 1.20, "Late Season": 0.60},
        "default_root_depth_m": 0.9,
        "depletion_fraction_p": 0.55,
        "critical_moisture_pct": 42.0,
        "field_capacity_pct": 68.0
    },
    "Tomato": {
        "name": "Tomato",
        "kc": {"Initial": 0.45, "Crop Development": 0.75, "Mid-Season": 1.15, "Late Season": 0.80},
        "default_root_depth_m": 0.7,
        "depletion_fraction_p": 0.40,
        "critical_moisture_pct": 45.0,
        "field_capacity_pct": 70.0
    },
    "Chilli": {
        "name": "Chilli (Pepper)",
        "kc": {"Initial": 0.35, "Crop Development": 0.70, "Mid-Season": 1.05, "Late Season": 0.75},
        "default_root_depth_m": 0.6,
        "depletion_fraction_p": 0.45,
        "critical_moisture_pct": 42.0,
        "field_capacity_pct": 68.0
    },
    "Wheat": {
        "name": "Wheat",
        "kc": {"Initial": 0.30, "Crop Development": 0.75, "Mid-Season": 1.15, "Late Season": 0.40},
        "default_root_depth_m": 0.8,
        "depletion_fraction_p": 0.55,
        "critical_moisture_pct": 40.0,
        "field_capacity_pct": 65.0
    },
    "Sugarcane": {
        "name": "Sugarcane",
        "kc": {"Initial": 0.40, "Crop Development": 0.80, "Mid-Season": 1.25, "Late Season": 0.75},
        "default_root_depth_m": 1.2,
        "depletion_fraction_p": 0.65,
        "critical_moisture_pct": 48.0,
        "field_capacity_pct": 72.0
    },
    "Soybean": {
        "name": "Soybean",
        "kc": {"Initial": 0.40, "Crop Development": 0.75, "Mid-Season": 1.15, "Late Season": 0.50},
        "default_root_depth_m": 0.7,
        "depletion_fraction_p": 0.50,
        "critical_moisture_pct": 40.0,
        "field_capacity_pct": 65.0
    },
    "Onion": {
        "name": "Onion",
        "kc": {"Initial": 0.50, "Crop Development": 0.75, "Mid-Season": 1.05, "Late Season": 0.75},
        "default_root_depth_m": 0.4,
        "depletion_fraction_p": 0.30,
        "critical_moisture_pct": 48.0,
        "field_capacity_pct": 68.0
    }
}

# Soil Characteristics (Available Water Capacity AWC in mm per meter of depth)
SOIL_DATABASE = {
    "Black Cotton Soil": {
        "awc_mm_per_m": 190.0,
        "field_capacity_pct": 42.0,
        "wilting_point_pct": 23.0,
        "infiltration_rate_mm_hr": 4.0,
        "drainage_speed": "Slow"
    },
    "Clay Loam": {
        "awc_mm_per_m": 165.0,
        "field_capacity_pct": 34.0,
        "wilting_point_pct": 17.5,
        "infiltration_rate_mm_hr": 10.0,
        "drainage_speed": "Moderate"
    },
    "Red Loamy Soil": {
        "awc_mm_per_m": 140.0,
        "field_capacity_pct": 28.0,
        "wilting_point_pct": 14.0,
        "infiltration_rate_mm_hr": 16.0,
        "drainage_speed": "Good"
    },
    "Alluvial Soil": {
        "awc_mm_per_m": 150.0,
        "field_capacity_pct": 27.0,
        "wilting_point_pct": 12.0,
        "infiltration_rate_mm_hr": 14.0,
        "drainage_speed": "Moderate-Good"
    },
    "Sandy Loam Soil": {
        "awc_mm_per_m": 110.0,
        "field_capacity_pct": 21.0,
        "wilting_point_pct": 10.0,
        "infiltration_rate_mm_hr": 25.0,
        "drainage_speed": "Fast"
    },
    "Sandy Soil": {
        "awc_mm_per_m": 70.0,
        "field_capacity_pct": 14.0,
        "wilting_point_pct": 7.0,
        "infiltration_rate_mm_hr": 40.0,
        "drainage_speed": "Very Fast"
    }
}

# Irrigation Efficiency Factors
IRRIGATION_EFFICIENCIES = {
    "Drip": 0.90,            # 90%
    "Micro-Sprinkler": 0.80, # 80%
    "Sprinkler": 0.75,       # 75%
    "Flood": 0.50,           # 50%
    "Furrow": 0.55           # 55%
}

def convert_area_to_sq_meters(area: float, unit: str) -> float:
    """Convert plot area to square meters."""
    u = unit.lower().strip()
    if "acre" in u:
        return area * 4046.86
    elif "hectare" in u or "ha" in u:
        return area * 10000.0
    elif "guntha" in u:
        return area * 101.17
    elif "sq" in u and "m" in u:
        return area
    return area * 4046.86  # Default fallback 1 acre

def estimate_et0(temp_c: float, humidity_pct: float, wind_speed_kmh: float) -> float:
    """
    FAO-56 Hargreaves-Samani simplified reference evapotranspiration (ET0) approximation.
    Returns reference ET0 in mm/day.
    """
    t = max(10.0, min(50.0, temp_c))
    h = max(10.0, min(100.0, humidity_pct))
    w = max(0.0, wind_speed_kmh)

    # Standard FAO-56 empirical solar radiation / temperature relation
    # Daily solar radiation proxy in sub-tropics: ~ 18-22 MJ/m2/day
    et0_base = 0.0023 * (t + 17.8) * math.sqrt(15.0) * 20.0 * 0.408
    humidity_factor = (100.0 - h) / 50.0
    wind_factor = 1.0 + (w * 0.02)
    et0 = et0_base * (0.85 + 0.25 * humidity_factor) * (0.9 + 0.1 * wind_factor)
    return round(max(2.5, min(9.5, et0)), 2)

def calculate_recommendation(
    crop_type: str,
    growth_stage: str,
    soil_type: str,
    current_moisture_pct: float,
    plot_area: float,
    area_unit: str = "Acres",
    irrigation_method: str = "Drip",
    root_depth_m: Optional[float] = None,
    pump_flow_rate_lpm: float = 120.0,
    temp_c: float = 30.0,
    humidity_pct: float = 55.0,
    wind_speed_kmh: float = 12.0,
    forecast_rain_mm: float = 0.0,
    rain_probability_pct: float = 0.0,
    data_source_soil: str = "manual",
    data_source_weather: str = "live_api"
) -> Dict[str, Any]:
    """
    Core Agronomic Recommendation Algorithm.
    Computes soil water depletion, effective rainfall, net/gross water requirement,
    duration, and operational status ('Irrigate Now', 'Monitor', 'Delay and Recheck').
    """
    # 1. Resolve crop parameters
    crop_info = CROP_DATABASE.get(crop_type, CROP_DATABASE["Cotton"])
    stage_kc = crop_info["kc"].get(growth_stage, 1.0)
    p = crop_info["depletion_fraction_p"]
    zr = root_depth_m if (root_depth_m and root_depth_m > 0.1) else crop_info["default_root_depth_m"]

    # 2. Resolve soil parameters
    soil_info = SOIL_DATABASE.get(soil_type, SOIL_DATABASE["Black Cotton Soil"])
    awc = soil_info["awc_mm_per_m"]
    fc = soil_info["field_capacity_pct"]
    wp = soil_info["wilting_point_pct"]

    # Total Available Water (TAW) in mm
    taw = awc * zr
    # Readily Available Water (RAW) in mm before stress
    raw = p * taw

    # Critical threshold for soil moisture (depletion boundary)
    # When moisture drops below this, plant enters stress
    stress_threshold_pct = wp + (1.0 - p) * (fc - wp)

    # 3. Calculate Reference and Crop Evapotranspiration
    et0 = estimate_et0(temp_c, humidity_pct, wind_speed_kmh)
    etc = round(stage_kc * et0, 2)  # mm/day

    # 4. Current Depletion Calculation
    # Normalize current moisture
    sm = max(5.0, min(95.0, current_moisture_pct))
    
    # Depletion fraction of available water
    if sm >= fc:
        depletion_fraction = 0.0
        current_depletion_mm = 0.0
    elif sm <= wp:
        depletion_fraction = 1.0
        current_depletion_mm = taw
    else:
        # Linear depletion within available range
        depletion_fraction = (fc - sm) / (fc - wp)
        current_depletion_mm = depletion_fraction * taw

    # 5. Rainfall Accounting and Postponement Evaluation
    # Effective rainfall formula (FAO standard: only rain > 5mm replenishes root zone)
    effective_rain_mm = 0.0
    rain_discount_active = False

    if forecast_rain_mm >= 4.0 and rain_probability_pct >= 35.0:
        # Weight by probability
        prob_factor = min(1.0, rain_probability_pct / 100.0)
        usable_rain = max(0.0, (forecast_rain_mm - 3.0) * 0.8)
        effective_rain_mm = round(usable_rain * prob_factor, 1)

    # 6. Recommendation Decision Logic
    area_sq_m = convert_area_to_sq_meters(plot_area, area_unit)
    efficiency = IRRIGATION_EFFICIENCIES.get(irrigation_method, 0.85)

    status = "Monitor"
    recheck_hours = 24
    reasons = []

    # Check if high rainfall is anticipated
    can_delay_due_to_rain = False
    if (forecast_rain_mm >= 12.0 and rain_probability_pct >= 50.0) or (effective_rain_mm >= 5.0 and rain_probability_pct >= 50.0):
        can_delay_due_to_rain = True

    if can_delay_due_to_rain:
        status = "Delay and Recheck"
        recheck_hours = 12
        reasons.append(
            f"Expected rainfall of {forecast_rain_mm:.1f} mm ({rain_probability_pct:.0f}% probability) "
            f"will provide ~{effective_rain_mm:.1f} mm of effective root-zone moisture. "
            f"Postponing irrigation saves water and prevents waterlogging."
        )
    elif sm < stress_threshold_pct or current_depletion_mm >= raw:
        status = "Irrigate Now"
        recheck_hours = 6
        reasons.append(
            f"Soil moisture ({sm:.1f}%) has fallen below critical agronomic threshold "
            f"({stress_threshold_pct:.1f}%). Root-zone water depletion ({current_depletion_mm:.1f} mm) "
            f"exceeds allowable limit ({raw:.1f} mm)."
        )
    elif sm < (fc * 0.85):
        status = "Monitor"
        recheck_hours = 18
        reasons.append(
            f"Soil moisture ({sm:.1f}%) is within optimal buffer zone ({stress_threshold_pct:.1f}% - {fc:.1f}%). "
            f"Crop is transpiring at {etc:.1f} mm/day. Immediate irrigation not required."
        )
    else:
        status = "Monitor"
        recheck_hours = 24
        reasons.append(
            f"Soil moisture ({sm:.1f}%) is near field capacity ({fc:.1f}%). Adequate moisture present."
        )

    # 7. Water Quantity Calculation
    # Net Irrigation Requirement (mm)
    nir_mm = max(0.0, current_depletion_mm - effective_rain_mm) if status == "Irrigate Now" else 0.0
    # Gross Irrigation Requirement (mm) factoring in system efficiency
    gir_mm = nir_mm / efficiency if efficiency > 0 else nir_mm

    # 1 mm of water over 1 square meter = 1 litre
    water_req_litres = round(gir_mm * area_sq_m, 1)
    water_req_m3 = round(water_req_litres / 1000.0, 2)

    # 8. Suggested Duration Calculation
    suggested_duration_minutes = 0
    if status == "Irrigate Now" and water_req_litres > 0:
        pump_lpm = max(20.0, pump_flow_rate_lpm)
        # Duration = Volume (L) / Flow rate (LPM)
        duration_mins = int(round(water_req_litres / pump_lpm))
        suggested_duration_minutes = max(15, min(1440, duration_mins))

    # 9. Traditional Baseline and Savings Estimation
    # Baseline assumes unoptimized flood irrigation (50% efficiency) without rainfall subtraction
    baseline_litres = round(((current_depletion_mm if current_depletion_mm > 0 else etc) / 0.50) * area_sq_m, 1)
    water_saved_litres = max(0.0, round(baseline_litres - water_req_litres, 1)) if status == "Irrigate Now" else round(baseline_litres * 0.8, 1)

    # 10. Confidence & Data Quality Score
    confidence = 90.0
    if data_source_soil == "demo":
        confidence -= 20.0
    elif data_source_soil == "manual":
        confidence -= 10.0
    if data_source_weather != "live_api":
        confidence -= 15.0
    confidence = max(40.0, min(98.0, confidence))

    safety_notes = (
        "Advisory Note: These calculations are derived from FAO-56 Penman-Monteith crop coefficients "
        "and soil water depletion parameters. Recommendations are decision-support advisories and should "
        "be cross-verified with local field observations and state agricultural extension guidelines."
    )

    return {
        "status": status,
        "water_req_litres": water_req_litres,
        "water_req_m3": water_req_m3,
        "suggested_duration_minutes": suggested_duration_minutes,
        "recheck_hours": recheck_hours,
        "effective_rainfall_mm": effective_rain_mm,
        "forecast_rain_mm": forecast_rain_mm,
        "rain_prob_pct": rain_probability_pct,
        "confidence_pct": confidence,
        "baseline_litres": baseline_litres,
        "water_saved_litres": water_saved_litres,
        "factors": {
            "crop_type": crop_type,
            "growth_stage": growth_stage,
            "kc": stage_kc,
            "et0_mm_day": et0,
            "etc_mm_day": etc,
            "soil_type": soil_type,
            "root_depth_m": zr,
            "field_capacity_pct": fc,
            "wilting_point_pct": wp,
            "critical_threshold_pct": round(stress_threshold_pct, 1),
            "current_moisture_pct": round(sm, 1),
            "depletion_mm": round(current_depletion_mm, 1),
            "raw_mm": round(raw, 1),
            "taw_mm": round(taw, 1),
            "irrigation_efficiency_pct": int(efficiency * 100),
            "reasons": reasons
        },
        "safety_notes": safety_notes,
        "is_ai_rule_based": True  # Explicitly transparent
    }
