import pytest
from backend.app.anomaly_detector import detect_anomalies

def test_detect_critical_low_moisture():
    readings = [{"soil_moisture_pct": 22.0}]
    alerts = detect_anomalies("plot-1", "farm-1", readings, [])
    assert any(a["alert_type"] == "low_moisture" and a["severity"] == "critical" for a in alerts)

def test_detect_excess_moisture_saturation():
    readings = [{"soil_moisture_pct": 92.0}]
    alerts = detect_anomalies("plot-1", "farm-1", readings, [])
    assert any(a["alert_type"] == "excess_moisture" for a in alerts)

def test_detect_sensor_stagnation():
    readings = [
        {"soil_moisture_pct": 45.0},
        {"soil_moisture_pct": 45.0},
        {"soil_moisture_pct": 45.0},
        {"soil_moisture_pct": 45.0}
    ]
    alerts = detect_anomalies("plot-1", "farm-1", readings, [])
    assert any(a["alert_type"] == "sensor_stale" for a in alerts)

def test_detect_rain_schedule_conflict():
    readings = [{"soil_moisture_pct": 50.0}]
    schedules = [{"scheduled_date": "2026-10-16", "status": "scheduled"}]
    alerts = detect_anomalies("plot-1", "farm-1", readings, schedules, forecast_rain_mm=18.0, rain_prob_pct=70.0)
    assert any(a["alert_type"] == "rain_conflict" for a in alerts)
