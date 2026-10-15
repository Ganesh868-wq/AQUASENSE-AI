import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(50), nullable=True)
    preferred_language = Column(String(10), default="en")  # 'en' or 'te'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farms = relationship("Farm", back_populates="user", cascade="all, delete-orphan")
    schedules = relationship("IrrigationSchedule", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "preferred_language": self.preferred_language,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Farm(Base):
    __tablename__ = "farms"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    location_name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    total_area = Column(Float, default=1.0)
    area_unit = Column(String(20), default="Acres")  # Acres, Hectares, Gunthas
    water_source_type = Column(String(100), default="Borewell")  # Borewell, Canal, Farm Pond, River
    pump_flow_rate_lpm = Column(Float, default=120.0)  # Litres Per Minute
    pump_power_hp = Column(Float, default=3.0)  # HP
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="farms")
    plots = relationship("Plot", back_populates="farm", cascade="all, delete-orphan")
    weather_records = relationship("WeatherRecord", back_populates="farm", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="farm", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "total_area": self.total_area,
            "area_unit": self.area_unit,
            "water_source_type": self.water_source_type,
            "pump_flow_rate_lpm": self.pump_flow_rate_lpm,
            "pump_power_hp": self.pump_power_hp,
            "notes": self.notes,
            "plots_count": len(self.plots) if self.plots else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Plot(Base):
    __tablename__ = "plots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    farm_id = Column(String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    crop_type = Column(String(100), nullable=False)  # Paddy, Cotton, Groundnut, Maize, Tomato, Chilli, etc.
    crop_variety = Column(String(100), nullable=True)
    soil_type = Column(String(100), default="Black Cotton Soil")  # Black Cotton, Red Loamy, Sandy Loam, Clay Loam
    area = Column(Float, default=1.0)
    area_unit = Column(String(20), default="Acres")
    planting_date = Column(String(20), nullable=True)
    growth_stage = Column(String(50), default="Mid-Season")  # Initial, Crop Development, Mid-Season, Late Season
    irrigation_method = Column(String(50), default="Drip")  # Drip, Sprinkler, Micro-Sprinkler, Flood
    emitter_flow_rate_lph = Column(Float, default=4.0)  # Litres per hour per emitter
    plant_spacing_m = Column(Float, default=0.6)
    row_spacing_m = Column(Float, default=1.2)
    root_depth_m = Column(Float, default=0.6)
    target_moisture_min = Column(Float, default=45.0)  # % depletion threshold
    target_moisture_max = Column(Float, default=80.0)  # % field capacity upper bound
    current_moisture = Column(Float, default=52.0)     # latest known moisture %
    sensor_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm", back_populates="plots")
    soil_readings = relationship("SoilReading", back_populates="plot", cascade="all, delete-orphan", order_by="desc(SoilReading.reading_timestamp)")
    recommendations = relationship("IrrigationRecommendation", back_populates="plot", cascade="all, delete-orphan", order_by="desc(IrrigationRecommendation.created_at)")
    schedules = relationship("IrrigationSchedule", back_populates="plot", cascade="all, delete-orphan")
    history = relationship("IrrigationHistory", back_populates="plot", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="plot", cascade="all, delete-orphan")
    water_usages = relationship("WaterUsage", back_populates="plot", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "name": self.name,
            "crop_type": self.crop_type,
            "crop_variety": self.crop_variety,
            "soil_type": self.soil_type,
            "area": self.area,
            "area_unit": self.area_unit,
            "planting_date": self.planting_date,
            "growth_stage": self.growth_stage,
            "irrigation_method": self.irrigation_method,
            "emitter_flow_rate_lph": self.emitter_flow_rate_lph,
            "plant_spacing_m": self.plant_spacing_m,
            "row_spacing_m": self.row_spacing_m,
            "root_depth_m": self.root_depth_m,
            "target_moisture_min": self.target_moisture_min,
            "target_moisture_max": self.target_moisture_max,
            "current_moisture": self.current_moisture,
            "sensor_id": self.sensor_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class SoilReading(Base):
    __tablename__ = "soil_readings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    plot_id = Column(String(36), ForeignKey("plots.id", ondelete="CASCADE"), nullable=False, index=True)
    soil_moisture_pct = Column(Float, nullable=False)
    soil_temperature_c = Column(Float, default=27.5)
    electrical_conductivity = Column(Float, default=1.1)  # dS/m
    source_type = Column(String(30), default="manual")  # 'manual', 'iot', 'demo'
    sensor_battery_pct = Column(Float, nullable=True)
    reading_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    plot = relationship("Plot", back_populates="soil_readings")

    def to_dict(self):
        return {
            "id": self.id,
            "plot_id": self.plot_id,
            "soil_moisture_pct": round(self.soil_moisture_pct, 1),
            "soil_temperature_c": round(self.soil_temperature_c, 1) if self.soil_temperature_c is not None else None,
            "electrical_conductivity": round(self.electrical_conductivity, 2) if self.electrical_conductivity is not None else None,
            "source_type": self.source_type,
            "sensor_battery_pct": self.sensor_battery_pct,
            "reading_timestamp": self.reading_timestamp.isoformat() if self.reading_timestamp else None
        }

class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    farm_id = Column(String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)
    temperature_c = Column(Float, nullable=False)
    humidity_pct = Column(Float, nullable=False)
    wind_speed_kmh = Column(Float, default=10.0)
    rainfall_mm = Column(Float, default=0.0)
    rain_probability_pct = Column(Float, default=0.0)
    solar_radiation = Column(Float, nullable=True)
    source_type = Column(String(30), default="live_api")  # 'live_api', 'manual', 'demo'
    forecast_json = Column(JSON, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    farm = relationship("Farm", back_populates="weather_records")

    def to_dict(self):
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "temperature_c": round(self.temperature_c, 1),
            "humidity_pct": round(self.humidity_pct, 1),
            "wind_speed_kmh": round(self.wind_speed_kmh, 1),
            "rainfall_mm": round(self.rainfall_mm, 1),
            "rain_probability_pct": round(self.rain_probability_pct, 1),
            "source_type": self.source_type,
            "forecast_json": self.forecast_json,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None
        }

class IrrigationRecommendation(Base):
    __tablename__ = "irrigation_recommendations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    plot_id = Column(String(36), ForeignKey("plots.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # 'Irrigate Now', 'Monitor', 'Delay and Recheck'
    water_req_litres = Column(Float, default=0.0)
    water_req_m3 = Column(Float, default=0.0)
    suggested_duration_minutes = Column(Integer, default=0)
    recheck_hours = Column(Integer, default=24)
    effective_rainfall_mm = Column(Float, default=0.0)
    forecast_rain_mm = Column(Float, default=0.0)
    rain_prob_pct = Column(Float, default=0.0)
    confidence_pct = Column(Float, default=85.0)
    factors_json = Column(JSON, nullable=True)
    safety_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    plot = relationship("Plot", back_populates="recommendations")

    def to_dict(self):
        return {
            "id": self.id,
            "plot_id": self.plot_id,
            "status": self.status,
            "water_req_litres": round(self.water_req_litres, 1),
            "water_req_m3": round(self.water_req_m3, 2),
            "suggested_duration_minutes": self.suggested_duration_minutes,
            "recheck_hours": self.recheck_hours,
            "effective_rainfall_mm": round(self.effective_rainfall_mm, 1),
            "forecast_rain_mm": round(self.forecast_rain_mm, 1),
            "rain_prob_pct": round(self.rain_prob_pct, 1),
            "confidence_pct": round(self.confidence_pct, 1),
            "factors": self.factors_json or {},
            "safety_notes": self.safety_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class IrrigationSchedule(Base):
    __tablename__ = "irrigation_schedules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    plot_id = Column(String(36), ForeignKey("plots.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_date = Column(String(20), nullable=False)  # YYYY-MM-DD
    scheduled_time = Column(String(10), nullable=False)  # HH:MM
    duration_minutes = Column(Integer, default=45)
    planned_water_litres = Column(Float, default=1000.0)
    notes = Column(Text, nullable=True)
    status = Column(String(30), default="scheduled")  # 'scheduled', 'in_progress', 'completed', 'cancelled'
    is_hardware_executed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    plot = relationship("Plot", back_populates="schedules")
    user = relationship("User", back_populates="schedules")

    def to_dict(self):
        return {
            "id": self.id,
            "plot_id": self.plot_id,
            "plot_name": self.plot.name if self.plot else "Unknown Plot",
            "crop_type": self.plot.crop_type if self.plot else "Unknown",
            "scheduled_date": self.scheduled_date,
            "scheduled_time": self.scheduled_time,
            "duration_minutes": self.duration_minutes,
            "planned_water_litres": round(self.planned_water_litres, 1),
            "notes": self.notes,
            "status": self.status,
            "is_hardware_executed": self.is_hardware_executed,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class IrrigationHistory(Base):
    __tablename__ = "irrigation_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    plot_id = Column(String(36), ForeignKey("plots.id", ondelete="CASCADE"), nullable=False, index=True)
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)
    duration_minutes = Column(Integer, default=45)
    actual_water_litres = Column(Float, default=1200.0)
    method = Column(String(50), default="Drip")
    status = Column(String(30), default="completed")  # completed, aborted, manual
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    plot = relationship("Plot", back_populates="history")

    def to_dict(self):
        return {
            "id": self.id,
            "plot_id": self.plot_id,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "duration_minutes": self.duration_minutes,
            "actual_water_litres": round(self.actual_water_litres, 1),
            "method": self.method,
            "status": self.status,
            "notes": self.notes
        }

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    farm_id = Column(String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)
    plot_id = Column(String(36), ForeignKey("plots.id", ondelete="CASCADE"), nullable=True, index=True)
    alert_type = Column(String(60), nullable=False)  # leakage_suspected, pump_failure_suspected, low_moisture, excess_moisture, rain_conflict, sensor_stale
    severity = Column(String(20), default="warning")  # critical, warning, info
    message = Column(String(255), nullable=False)
    reason = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=False)
    status = Column(String(30), default="active")  # active, acknowledged, resolved
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

    farm = relationship("Farm", back_populates="alerts")
    plot = relationship("Plot", back_populates="alerts")

    def to_dict(self):
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "plot_id": self.plot_id,
            "plot_name": self.plot.name if self.plot else "Farm Wide",
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "reason": self.reason,
            "suggested_action": self.suggested_action,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }

class WaterUsage(Base):
    __tablename__ = "water_usage"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    farm_id = Column(String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)
    plot_id = Column(String(36), ForeignKey("plots.id", ondelete="CASCADE"), nullable=False, index=True)
    record_date = Column(String(20), nullable=False, index=True)  # YYYY-MM-DD
    measured_litres = Column(Float, default=0.0)
    estimated_litres = Column(Float, default=0.0)
    baseline_litres = Column(Float, default=0.0)  # Traditional flood baseline
    saved_litres = Column(Float, default=0.0)     # baseline - actual
    created_at = Column(DateTime, default=datetime.utcnow)

    plot = relationship("Plot", back_populates="water_usages")

    def to_dict(self):
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "plot_id": self.plot_id,
            "record_date": self.record_date,
            "measured_litres": round(self.measured_litres, 1),
            "estimated_litres": round(self.estimated_litres, 1),
            "baseline_litres": round(self.baseline_litres, 1),
            "saved_litres": round(self.saved_litres, 1)
        }

class IoTDevice(Base):
    __tablename__ = "iot_devices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    farm_id = Column(String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)
    plot_id = Column(String(36), ForeignKey("plots.id", ondelete="CASCADE"), nullable=True, index=True)
    device_token = Column(String(100), unique=True, nullable=False)
    device_name = Column(String(100), nullable=False)
    device_type = Column(String(50), default="soil_sensor")  # soil_sensor, weather_station, flow_meter, pump_controller
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    battery_pct = Column(Float, default=95.0)
    pump_state = Column(String(10), default="off")  # off, on

    def to_dict(self):
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "plot_id": self.plot_id,
            "device_token": self.device_token,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "is_active": self.is_active,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "battery_pct": round(self.battery_pct, 1) if self.battery_pct is not None else None,
            "pump_state": self.pump_state
        }
