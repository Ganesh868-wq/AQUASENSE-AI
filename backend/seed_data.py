import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.database import SessionLocal, init_db
from backend.app.models import (
    User, Farm, Plot, SoilReading, WeatherRecord,
    IrrigationSchedule, IrrigationHistory, Alert, WaterUsage, IoTDevice
)
from backend.app.auth import hash_password

def seed_database():
    print("Initializing AquaSense AI database...")
    init_db()
    db = SessionLocal()

    try:
        # Check if demo user already exists
        existing_user = db.query(User).filter(User.email == "farmer@aquasense.ai").first()
        if existing_user:
            print("Demo user already exists. Cleaning up previous demo data for fresh seed...")
            db.query(User).filter(User.email == "farmer@aquasense.ai").delete()
            db.commit()

        # 1. Create Demo Farmer
        demo_user = User(
            email="farmer@aquasense.ai",
            password_hash=hash_password("password123"),
            full_name="Ganesh Rao",
            phone="+91 98765 43210",
            preferred_language="en"
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        print(f"Created demo user: {demo_user.email} (Password: password123)")

        # 2. Create Farm
        farm = Farm(
            user_id=demo_user.id,
            name="Sri Lakshmi Agro-Tech Farm",
            location_name="Warangal, Telangana",
            latitude=17.9689,
            longitude=79.5941,
            total_area=8.0,
            area_unit="Acres",
            water_source_type="Borewell + Solar Pump",
            pump_flow_rate_lpm=140.0,
            pump_power_hp=5.0,
            notes="Integrated micro-irrigation farm with solar borewell and rainwater catchment pond."
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)

        # 3. Create Plots
        plots_data = [
            {
                "name": "Plot 1 - North Cotton Block",
                "crop_type": "Cotton",
                "crop_variety": "Bt Cotton RCH-659",
                "soil_type": "Black Cotton Soil",
                "area": 2.5,
                "area_unit": "Acres",
                "planting_date": (datetime.utcnow() - timedelta(days=65)).strftime("%Y-%m-%d"),
                "growth_stage": "Mid-Season",
                "irrigation_method": "Drip",
                "emitter_flow_rate_lph": 4.0,
                "plant_spacing_m": 0.9,
                "row_spacing_m": 1.2,
                "root_depth_m": 0.9,
                "target_moisture_min": 38.0,
                "target_moisture_max": 68.0,
                "current_moisture": 34.5,  # Low! Will trigger "Irrigate Now"
                "sensor_id": "SN-CTN-01"
            },
            {
                "name": "Plot 2 - South Tomato Polyhouse",
                "crop_type": "Tomato",
                "crop_variety": "Arka Rakshak",
                "soil_type": "Red Loamy Soil",
                "area": 1.5,
                "area_unit": "Acres",
                "planting_date": (datetime.utcnow() - timedelta(days=40)).strftime("%Y-%m-%d"),
                "growth_stage": "Crop Development",
                "irrigation_method": "Drip",
                "emitter_flow_rate_lph": 2.5,
                "plant_spacing_m": 0.5,
                "row_spacing_m": 0.8,
                "root_depth_m": 0.6,
                "target_moisture_min": 45.0,
                "target_moisture_max": 75.0,
                "current_moisture": 58.0,  # Optimal! Will trigger "Monitor"
                "sensor_id": "SN-TOM-02"
            },
            {
                "name": "Plot 3 - Lowland Paddy Basin",
                "crop_type": "Paddy",
                "crop_variety": "Telangana Sona (RNR 15048)",
                "soil_type": "Clay Loam",
                "area": 2.5,
                "area_unit": "Acres",
                "planting_date": (datetime.utcnow() - timedelta(days=50)).strftime("%Y-%m-%d"),
                "growth_stage": "Mid-Season",
                "irrigation_method": "Flood",
                "emitter_flow_rate_lph": 0.0,
                "plant_spacing_m": 0.15,
                "row_spacing_m": 0.20,
                "root_depth_m": 0.5,
                "target_moisture_min": 55.0,
                "target_moisture_max": 85.0,
                "current_moisture": 72.0,  # Adequate
                "sensor_id": "SN-PDY-03"
            },
            {
                "name": "Plot 4 - East Groundnut Field",
                "crop_type": "Groundnut",
                "crop_variety": "Kadiri-6",
                "soil_type": "Sandy Loam Soil",
                "area": 1.5,
                "area_unit": "Acres",
                "planting_date": (datetime.utcnow() - timedelta(days=25)).strftime("%Y-%m-%d"),
                "growth_stage": "Initial",
                "irrigation_method": "Sprinkler",
                "emitter_flow_rate_lph": 15.0,
                "plant_spacing_m": 0.1,
                "row_spacing_m": 0.3,
                "root_depth_m": 0.4,
                "target_moisture_min": 40.0,
                "target_moisture_max": 65.0,
                "current_moisture": 36.2,  # Low!
                "sensor_id": "SN-GNT-04"
            }
        ]

        created_plots = []
        for p_data in plots_data:
            plot = Plot(farm_id=farm.id, **p_data)
            db.add(plot)
            db.commit()
            db.refresh(plot)
            created_plots.append(plot)

            # Generate 24 hours of soil moisture telemetry
            base_moisture = plot.current_moisture
            for h in range(24, 0, -2):
                timestamp = datetime.utcnow() - timedelta(hours=h)
                # Diurnal drift
                var = math_sin_val = round(1.5 * (1 if h % 4 == 0 else -1) + random.uniform(-0.4, 0.4), 1)
                reading = SoilReading(
                    plot_id=plot.id,
                    soil_moisture_pct=max(15.0, min(85.0, base_moisture + var + (h * 0.2))),
                    soil_temperature_c=round(26.0 + (3.0 if 10 <= h <= 18 else 0.5) + random.uniform(-0.5, 0.5), 1),
                    electrical_conductivity=round(1.15 + random.uniform(-0.08, 0.08), 2),
                    source_type="iot",
                    sensor_battery_pct=round(96.0 - (h * 0.1), 1),
                    reading_timestamp=timestamp
                )
                db.add(reading)
            db.commit()

        # 4. Weather Record
        weather = WeatherRecord(
            farm_id=farm.id,
            temperature_c=31.8,
            humidity_pct=52.0,
            wind_speed_kmh=11.2,
            rainfall_mm=0.0,
            rain_probability_pct=20.0,
            source_type="live_api",
            recorded_at=datetime.utcnow()
        )
        db.add(weather)

        # 5. Irrigation Schedules
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d")

        s1 = IrrigationSchedule(
            plot_id=created_plots[0].id,
            user_id=demo_user.id,
            scheduled_date=tomorrow,
            scheduled_time="06:30",
            duration_minutes=60,
            planned_water_litres=8400.0,
            notes="Morning drip cycle for Cotton - flowering stage.",
            status="scheduled",
            is_hardware_executed=False
        )
        s2 = IrrigationSchedule(
            plot_id=created_plots[3].id,
            user_id=demo_user.id,
            scheduled_date=tomorrow,
            scheduled_time="17:00",
            duration_minutes=40,
            planned_water_litres=5600.0,
            notes="Evening sprinkler pulse for Groundnut.",
            status="scheduled",
            is_hardware_executed=False
        )
        s3 = IrrigationSchedule(
            plot_id=created_plots[1].id,
            user_id=demo_user.id,
            scheduled_date=(datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
            scheduled_time="07:00",
            duration_minutes=45,
            planned_water_litres=3500.0,
            notes="Automated drip fertigation.",
            status="completed",
            is_hardware_executed=True
        )
        db.add_all([s1, s2, s3])
        db.commit()

        # 6. Irrigation History
        h1 = IrrigationHistory(
            plot_id=created_plots[1].id,
            executed_at=datetime.utcnow() - timedelta(days=1),
            duration_minutes=45,
            actual_water_litres=3500.0,
            method="Drip",
            status="completed",
            notes="Executed automatically via schedule."
        )
        h2 = IrrigationHistory(
            plot_id=created_plots[0].id,
            executed_at=datetime.utcnow() - timedelta(days=4),
            duration_minutes=75,
            actual_water_litres=9800.0,
            method="Drip",
            status="completed",
            notes="Regular cycle."
        )
        db.add_all([h1, h2])

        # 7. Alerts
        a1 = Alert(
            farm_id=farm.id,
            plot_id=created_plots[0].id,
            alert_type="low_moisture",
            severity="critical",
            message="Soil Moisture Deficit Alert (34.5%)",
            reason="Plot 1 (Cotton) has dropped below the minimum critical threshold of 38%. Moisture stress may impede square retention.",
            suggested_action="Execute recommended drip irrigation cycle of ~8,400 Litres immediately.",
            status="active"
        )
        a2 = Alert(
            farm_id=farm.id,
            plot_id=created_plots[0].id,
            alert_type="leakage_suspected",
            severity="warning",
            message="Suspected Micro-Leakage on Lateral Line B",
            reason="Sensor telemetry indicates sharp localized pressure drop and uneven sub-surface moisture dispersion.",
            suggested_action="Inspect lateral dripline B-4 for rodent bite punctures or dislodged emitter barbs.",
            status="active"
        )
        db.add_all([a1, a2])

        # 8. 14 Days of Water Usage & Savings Analytics
        for d in range(14, 0, -1):
            date_str = (datetime.utcnow() - timedelta(days=d)).strftime("%Y-%m-%d")
            # Base flood baseline: ~18,000 Litres
            baseline = round(16000 + random.uniform(1000, 4000), 1)
            # Optimized drip consumption: ~9,500 Litres
            actual = round(baseline * random.uniform(0.55, 0.65), 1)
            saved = round(baseline - actual, 1)

            u = WaterUsage(
                farm_id=farm.id,
                plot_id=created_plots[0].id,
                record_date=date_str,
                measured_litres=actual,
                estimated_litres=actual * 0.95,
                baseline_litres=baseline,
                saved_litres=saved
            )
            db.add(u)
        db.commit()

        # 9. IoT Devices
        dev1 = IoTDevice(
            farm_id=farm.id,
            plot_id=created_plots[0].id,
            device_token="AQUASENSE-IOT-NODE-01",
            device_name="LoRa Soil Sensor Node #1",
            device_type="soil_sensor",
            is_active=True,
            battery_pct=94.5,
            pump_state="off"
        )
        dev2 = IoTDevice(
            farm_id=farm.id,
            plot_id=created_plots[1].id,
            device_token="AQUASENSE-IOT-PUMP-MAIN",
            device_name="Smart Pump Actuator Gateway",
            device_type="pump_controller",
            is_active=True,
            battery_pct=100.0,
            pump_state="off"
        )
        db.add_all([dev1, dev2])
        db.commit()

        print("AquaSense AI database successfully populated with realistic agricultural demonstration data!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
