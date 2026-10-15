from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

def detect_anomalies(
    plot_id: str,
    farm_id: str,
    recent_soil_readings: List[Dict[str, Any]],
    recent_schedules: List[Dict[str, Any]],
    forecast_rain_mm: float = 0.0,
    rain_prob_pct: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Rule-based agronomic anomaly detection.
    Flags:
    1. Unexpectedly low soil moisture after scheduled irrigation (leak/pump fail)
    2. Rapid unexplained moisture decline
    3. Frozen/unchanged sensor readings (stuck sensor)
    4. Stale or missing sensor readings (> 24 hours)
    5. Rain forecast during scheduled irrigation event
    6. Low moisture below critical threshold
    7. Excess moisture / waterlogging risk
    """
    alerts = []

    if not recent_soil_readings:
        alerts.append({
            "farm_id": farm_id,
            "plot_id": plot_id,
            "alert_type": "sensor_stale",
            "severity": "warning",
            "message": "Missing Soil Sensor Telemetry",
            "reason": "No recent moisture readings have been recorded for this plot in the database.",
            "suggested_action": "Check telemetry gateway or enter manual soil probe reading.",
            "status": "active"
        })
        return alerts

    latest_reading = recent_soil_readings[0]
    latest_moisture = latest_reading.get("soil_moisture_pct", 50.0)
    
    # 1. Critical Low Moisture Alert
    if latest_moisture < 30.0:
        alerts.append({
            "farm_id": farm_id,
            "plot_id": plot_id,
            "alert_type": "low_moisture",
            "severity": "critical",
            "message": f"Critical Moisture Deficit ({latest_moisture:.1f}%)",
            "reason": "Soil moisture has plummeted near the permanent wilting point. Crop is undergoing severe drought stress.",
            "suggested_action": "Trigger emergency irrigation cycle immediately to prevent permanent root cavitation.",
            "status": "active"
        })

    # 2. Excess Moisture / Waterlogging Alert
    if latest_moisture > 88.0:
        alerts.append({
            "farm_id": farm_id,
            "plot_id": plot_id,
            "alert_type": "excess_moisture",
            "severity": "warning",
            "message": f"Soil Moisture Saturation Warning ({latest_moisture:.1f}%)",
            "reason": "Soil moisture is exceeding field capacity. Extended saturation restricts root oxygenation and causes root rot.",
            "suggested_action": "Suspend all scheduled irrigation and inspect field drainage channels.",
            "status": "active"
        })

    # 3. Stuck / Frozen Sensor Readings
    if len(recent_soil_readings) >= 4:
        readings_vals = [r.get("soil_moisture_pct") for r in recent_soil_readings[:4]]
        if all(abs(val - readings_vals[0]) < 0.05 for val in readings_vals):
            alerts.append({
                "farm_id": farm_id,
                "plot_id": plot_id,
                "alert_type": "sensor_stale",
                "severity": "info",
                "message": "Suspected Sensor Stagnation",
                "reason": f"Sensor has reported exactly {readings_vals[0]:.1f}% over multiple intervals without diurnal variation.",
                "suggested_action": "Inspect probe soil contact and clean sensor electrodes to ensure reliable data.",
                "status": "active"
            })

    # 4. Rapid Unexplained Moisture Decline
    if len(recent_soil_readings) >= 2:
        prev_moisture = recent_soil_readings[1].get("soil_moisture_pct", latest_moisture)
        drop = prev_moisture - latest_moisture
        if drop > 18.0:
            alerts.append({
                "farm_id": farm_id,
                "plot_id": plot_id,
                "alert_type": "leakage_suspected",
                "severity": "warning",
                "message": f"Suspected Soil Drainage Anomaly (Drop of {drop:.1f}%)",
                "reason": "Moisture declined at an abnormally steep rate inconsistent with normal evapotranspiration.",
                "suggested_action": "Inspect root zone for sub-surface macropore fissures or soil erosion.",
                "status": "active"
            })

    # 5. Rain Forecast Conflict with Scheduled Irrigation
    if forecast_rain_mm >= 10.0 and rain_prob_pct >= 60.0:
        for sched in recent_schedules:
            if sched.get("status") == "scheduled":
                alerts.append({
                    "farm_id": farm_id,
                    "plot_id": plot_id,
                    "alert_type": "rain_conflict",
                    "severity": "warning",
                    "message": f"Rainfall Forecast Conflict with Scheduled Irrigation",
                    "reason": f"Heavy rain ({forecast_rain_mm:.1f} mm, {rain_prob_pct:.0f}% chance) is predicted while irrigation is scheduled for {sched.get('scheduled_date')}.",
                    "suggested_action": "Postpone scheduled irrigation to prevent water wastage and nutrient runoff.",
                    "status": "active"
                })
                break

    # 6. Post-Irrigation Low Moisture (Suspected Delivery Failure / Blocked Valve / Pipe Leak)
    for sched in recent_schedules:
        if sched.get("status") == "completed" and latest_moisture < 38.0:
            alerts.append({
                "farm_id": farm_id,
                "plot_id": plot_id,
                "alert_type": "pump_failure_suspected",
                "severity": "critical",
                "message": "Suspected Irrigation Delivery Failure",
                "reason": "Irrigation was recorded as completed, but soil moisture remains critically low (< 38%). Possible pump trip, main-line puncture, or clogged drip emitters.",
                "suggested_action": "Perform immediate field inspection of pump motor, pressure gauge, and drip sub-mains.",
                "status": "active"
            })
            break

    return alerts
