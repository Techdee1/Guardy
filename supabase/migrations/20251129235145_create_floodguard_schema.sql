/*
  # FloodGuard Nigeria Database Schema

  1. New Tables
    - `flood_events`
      - `id` (uuid, primary key)
      - `location` (text) - City/area name
      - `latitude` (decimal)
      - `longitude` (decimal)
      - `severity` (text) - low/medium/high
      - `rainfall` (decimal) - rainfall amount in mm
      - `description` (text) - weather description
      - `timestamp` (timestamptz)
      - `created_at` (timestamptz)
    
    - `emergency_reports`
      - `id` (uuid, primary key)
      - `name` (text)
      - `latitude` (decimal)
      - `longitude` (decimal)
      - `type_of_need` (text) - Food/Water/Medicine/Shelter
      - `comments` (text)
      - `status` (text) - pending/responded/resolved
      - `timestamp` (timestamptz)
      - `created_at` (timestamptz)
    
    - `emergency_centers`
      - `id` (uuid, primary key)
      - `name` (text)
      - `type` (text) - shelter/hospital
      - `latitude` (decimal)
      - `longitude` (decimal)
      - `email` (text)
      - `phone` (text)
      - `created_at` (timestamptz)

  2. Security
    - Enable RLS on all tables
    - Add policies for public read access (for demo purposes)
    - Add policies for authenticated insert operations
*/

-- Create flood_events table
CREATE TABLE IF NOT EXISTS flood_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  location text NOT NULL,
  latitude decimal(10, 7) NOT NULL,
  longitude decimal(10, 7) NOT NULL,
  severity text NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
  rainfall decimal(10, 2) DEFAULT 0,
  description text DEFAULT '',
  timestamp timestamptz NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- Create emergency_reports table
CREATE TABLE IF NOT EXISTS emergency_reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  latitude decimal(10, 7) NOT NULL,
  longitude decimal(10, 7) NOT NULL,
  type_of_need text NOT NULL CHECK (type_of_need IN ('Food', 'Water', 'Medicine', 'Shelter')),
  comments text DEFAULT '',
  status text DEFAULT 'pending' CHECK (status IN ('pending', 'responded', 'resolved')),
  timestamp timestamptz NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- Create emergency_centers table
CREATE TABLE IF NOT EXISTS emergency_centers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  type text NOT NULL CHECK (type IN ('shelter', 'hospital')),
  latitude decimal(10, 7) NOT NULL,
  longitude decimal(10, 7) NOT NULL,
  email text NOT NULL,
  phone text NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE flood_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE emergency_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE emergency_centers ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (for demo)
CREATE POLICY "Anyone can view flood events"
  ON flood_events FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Anyone can create flood events"
  ON flood_events FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

CREATE POLICY "Anyone can view emergency reports"
  ON emergency_reports FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Anyone can create emergency reports"
  ON emergency_reports FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

CREATE POLICY "Anyone can update emergency reports"
  ON emergency_reports FOR UPDATE
  TO anon, authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Anyone can view emergency centers"
  ON emergency_centers FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Anyone can create emergency centers"
  ON emergency_centers FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_flood_events_timestamp ON flood_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_flood_events_severity ON flood_events(severity);
CREATE INDEX IF NOT EXISTS idx_emergency_reports_timestamp ON emergency_reports(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_emergency_reports_status ON emergency_reports(status);
CREATE INDEX IF NOT EXISTS idx_emergency_centers_type ON emergency_centers(type);

-- Insert sample emergency centers in major Nigerian cities
INSERT INTO emergency_centers (name, type, latitude, longitude, email, phone) VALUES
  ('Lagos State Emergency Center', 'shelter', 6.5244, 3.3792, 'emergency@lagos.gov.ng', '+2348012345678'),
  ('Lagos General Hospital', 'hospital', 6.4550, 3.3841, 'info@lagosgh.ng', '+2348012345679'),
  ('Abuja Emergency Shelter', 'shelter', 9.0765, 7.3986, 'shelter@abuja.gov.ng', '+2348012345680'),
  ('National Hospital Abuja', 'hospital', 9.0579, 7.4951, 'contact@nationalhospital.ng', '+2348012345681'),
  ('Port Harcourt Relief Center', 'shelter', 4.8156, 7.0498, 'relief@portharcourt.gov.ng', '+2348012345682'),
  ('University of Port Harcourt Teaching Hospital', 'hospital', 4.9020, 6.9350, 'info@upth.ng', '+2348012345683'),
  ('Kano Emergency Response', 'shelter', 12.0022, 8.5920, 'emergency@kano.gov.ng', '+2348012345684'),
  ('Aminu Kano Teaching Hospital', 'hospital', 11.9946, 8.5320, 'contact@akth.ng', '+2348012345685')
ON CONFLICT DO NOTHING;