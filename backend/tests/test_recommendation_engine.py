import pytest
from backend.app.recommendation_engine import calculate_recommendation, estimate_et0, convert_area_to_sq_meters

def test_et0_estimation():
    et0 = estimate_et0(temp_c=32.0, humidity_pct=50.0, wind_speed_kmh=10.0)
    assert 3.0 <= et0 <= 8.0, "ET0 should be within realistic summer agricultural range"

def test_area_conversion():
    sq_m = convert_area_to_sq_meters(1.0, "Acres")
    assert round(sq_m, 1) == 4046.9

    sq_m_ha = convert_area_to_sq_meters(1.0, "Hectares")
    assert sq_m_ha == 10000.0

def test_recommendation_irrigate_now_when_moisture_depleted():
    rec = calculate_recommendation(
        crop_type="Cotton",
        growth_stage="Mid-Season",
        soil_type="Black Cotton Soil",
        current_moisture_pct=28.0,  # Below threshold
        plot_area=2.0,
        area_unit="Acres",
        irrigation_method="Drip",
        pump_flow_rate_lpm=120.0,
        temp_c=32.0,
        forecast_rain_mm=0.0,
        rain_probability_pct=10.0
    )
    assert rec["status"] == "Irrigate Now"
    assert rec["water_req_litres"] > 0
    assert rec["suggested_duration_minutes"] > 0
    assert "depletion" in str(rec["factors"]["reasons"]).lower()

def test_recommendation_monitor_when_moisture_optimal():
    rec = calculate_recommendation(
        crop_type="Tomato",
        growth_stage="Mid-Season",
        soil_type="Red Loamy Soil",
        current_moisture_pct=60.0,  # Well above threshold
        plot_area=1.0,
        area_unit="Acres",
        irrigation_method="Drip",
        temp_c=28.0,
        forecast_rain_mm=0.0
    )
    assert rec["status"] == "Monitor"
    assert rec["water_req_litres"] == 0.0

def test_recommendation_delay_and_recheck_when_rain_forecast():
    rec = calculate_recommendation(
        crop_type="Cotton",
        growth_stage="Mid-Season",
        soil_type="Black Cotton Soil",
        current_moisture_pct=34.0,  # Low, would otherwise irrigate
        plot_area=2.0,
        area_unit="Acres",
        irrigation_method="Drip",
        temp_c=30.0,
        forecast_rain_mm=25.0,     # Substantial rain forecast
        rain_probability_pct=75.0  # High probability
    )
    assert rec["status"] == "Delay and Recheck"
    assert "rainfall" in str(rec["factors"]["reasons"]).lower()
