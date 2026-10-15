-- ========================================================
-- AQUASENSE AI: Supabase Setup Script with Row Level Security
-- Run this in your Supabase SQL Editor if using Supabase!
-- ========================================================

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable Row Level Security (RLS) on tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE farms ENABLE ROW LEVEL SECURITY;
ALTER TABLE plots ENABLE ROW LEVEL SECURITY;
ALTER TABLE soil_readings ENABLE ROW LEVEL SECURITY;
ALTER TABLE weather_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE irrigation_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE irrigation_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE water_usage ENABLE ROW LEVEL SECURITY;

-- 1. Farms Policy: Farmers can only see their own farms
CREATE POLICY "Users can only access their own farms"
ON farms FOR ALL
USING (auth.uid()::text = user_id::text);

-- 2. Plots Policy: Farmers can only access plots belonging to their farms
CREATE POLICY "Users can only access their own plots"
ON plots FOR ALL
USING (
    farm_id IN (
        SELECT id FROM farms WHERE user_id::text = auth.uid()::text
    )
);

-- 3. Soil Readings Policy
CREATE POLICY "Users can access soil readings for their plots"
ON soil_readings FOR ALL
USING (
    plot_id IN (
        SELECT p.id FROM plots p
        JOIN farms f ON p.farm_id = f.id
        WHERE f.user_id::text = auth.uid()::text
    )
);

-- 4. Irrigation Schedules Policy
CREATE POLICY "Users can only access their own schedules"
ON irrigation_schedules FOR ALL
USING (auth.uid()::text = user_id::text);

-- 5. Alerts Policy
CREATE POLICY "Users can access alerts for their farms"
ON alerts FOR ALL
USING (
    farm_id IN (
        SELECT id FROM farms WHERE user_id::text = auth.uid()::text
    )
);

-- 6. Water Usage Policy
CREATE POLICY "Users can access water usage for their farms"
ON water_usage FOR ALL
USING (
    farm_id IN (
        SELECT id FROM farms WHERE user_id::text = auth.uid()::text
    )
);
