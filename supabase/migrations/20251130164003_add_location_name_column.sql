/*
  # Add Location Name Column to Emergency Reports

  1. Changes
    - Add `location_name` column to `emergency_reports` table
    - This will store the human-readable address/place name
    - Generated via reverse geocoding from latitude/longitude
    
  2. Notes
    - Column allows null for backward compatibility
    - Contains format like: "Suburb, City, State"
    - Makes it easier for authorities to understand location
*/

-- Add location name column to emergency_reports
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'emergency_reports' AND column_name = 'location_name'
  ) THEN
    ALTER TABLE emergency_reports ADD COLUMN location_name text;
  END IF;
END $$;
