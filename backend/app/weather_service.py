import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from .config import Config

logger = logging.getLogger(__name__)

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_BASE_URL = "https://geocoding-api.open-meteo.com/v1/search"

def geocode_location(location_name: str) -> Optional[Dict[str, float]]:
    """Geocode city / village / district name to lat/lon."""
    try:
        response = requests.get(
            GEOCODING_BASE_URL,
            params={"name": location_name, "count": 1, "language": "en", "format": "json"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("results")
            if results and len(results) > 0:
                first = results[0]
                return {
                    "latitude": first.get("latitude"),
                    "longitude": first.get("longitude"),
                    "name": f"{first.get('name')}, {first.get('admin1', '')} {first.get('country', '')}".strip()
                }
    except Exception as e:
        logger.warning(f"Geocoding failed for {location_name}: {e}")
    return None

def fetch_weather(latitude: float = 17.3850, longitude: float = 78.4867, location_name: str = "Telangana, India") -> Dict[str, Any]:
    """
    Fetch live weather and 7-day forecast from Open-Meteo API (or OpenWeatherMap if key set).
    Falls back gracefully to labeled demo data if network fails.
    """
    # 1. Try Live Open-Meteo API
    try:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,et0_fao_evapotranspiration",
            "timezone": "auto"
        }
        res = requests.get(OPEN_METEO_BASE_URL, params=params, timeout=6)
        if res.status_code == 200:
            data = res.json()
            current = data.get("current", {})
            daily = data.get("daily", {})

            daily_forecast = []
            dates = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            precip_sums = daily.get("precipitation_sum", [])
            precip_probs = daily.get("precipitation_probability_max", [])
            et0_vals = daily.get("et0_fao_evapotranspiration", [])

            for i in range(min(len(dates), 7)):
                daily_forecast.append({
                    "date": dates[i],
                    "temp_max": max_temps[i] if i < len(max_temps) else 32.0,
                    "temp_min": min_temps[i] if i < len(min_temps) else 22.0,
                    "precipitation_mm": precip_sums[i] if i < len(precip_sums) else 0.0,
                    "rain_prob_pct": precip_probs[i] if i < len(precip_probs) else 0.0,
                    "et0_mm": et0_vals[i] if i < len(et0_vals) else 5.0
                })

            # Next 48h rain accumulation & peak probability
            next_rain_mm = 0.0
            next_rain_prob = 0.0
            if len(daily_forecast) > 0:
                next_rain_mm = daily_forecast[0]["precipitation_mm"]
                next_rain_prob = daily_forecast[0]["rain_prob_pct"]
                if len(daily_forecast) > 1:
                    next_rain_mm += daily_forecast[1]["precipitation_mm"] * 0.5
                    next_rain_prob = max(next_rain_prob, daily_forecast[1]["rain_prob_pct"])

            return {
                "source_type": "live_api",
                "api_provider": "Open-Meteo High-Resolution Global Weather",
                "location_name": location_name,
                "latitude": latitude,
                "longitude": longitude,
                "temperature_c": current.get("temperature_2m", 31.5),
                "humidity_pct": current.get("relative_humidity_2m", 58.0),
                "wind_speed_kmh": current.get("wind_speed_10m", 12.4),
                "rainfall_mm": current.get("precipitation", 0.0),
                "rain_probability_pct": next_rain_prob,
                "forecast_rain_48h_mm": round(next_rain_mm, 1),
                "daily_forecast": daily_forecast,
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
    except Exception as e:
        logger.warning(f"Live weather API query failed ({e}). Providing labeled demo fallback data.")

    # 2. Labeled Demo/Fallback Weather Data
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    return {
        "source_type": "demo",
        "api_provider": "AquaSense Offline Simulation / Demo Cache",
        "location_name": f"{location_name} (Demo Mode)",
        "latitude": latitude,
        "longitude": longitude,
        "temperature_c": 32.2,
        "humidity_pct": 54.0,
        "wind_speed_kmh": 11.5,
        "rainfall_mm": 0.0,
        "rain_probability_pct": 25.0,
        "forecast_rain_48h_mm": 2.5,
        "daily_forecast": [
            {"date": today_str, "temp_max": 33.0, "temp_min": 23.0, "precipitation_mm": 1.2, "rain_prob_pct": 25.0, "et0_mm": 5.4},
            {"date": "Day +1", "temp_max": 34.0, "temp_min": 24.0, "precipitation_mm": 4.5, "rain_prob_pct": 45.0, "et0_mm": 5.1},
            {"date": "Day +2", "temp_max": 31.0, "temp_min": 22.0, "precipitation_mm": 12.0, "rain_prob_pct": 70.0, "et0_mm": 4.2},
            {"date": "Day +3", "temp_max": 30.0, "temp_min": 21.0, "precipitation_mm": 3.0, "rain_prob_pct": 35.0, "et0_mm": 4.8},
            {"date": "Day +4", "temp_max": 32.5, "temp_min": 22.5, "precipitation_mm": 0.0, "rain_prob_pct": 10.0, "et0_mm": 5.5},
            {"date": "Day +5", "temp_max": 33.5, "temp_min": 23.0, "precipitation_mm": 0.0, "rain_prob_pct": 5.0, "et0_mm": 5.8},
            {"date": "Day +6", "temp_max": 34.0, "temp_min": 24.0, "precipitation_mm": 0.0, "rain_prob_pct": 15.0, "et0_mm": 5.6}
        ],
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "message": "Live API could not be reached. Showing realistic agronomic demo weather."
    }
