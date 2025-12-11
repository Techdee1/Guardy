/*
  # Add Voice Recording Support to Emergency Reports

  1. Changes
    - Add `voice_recording_url` column to `emergency_reports` table to store audio file URLs
    - This will enable voice recordings to be stored and played back by authorities
    
  2. Notes
    - Voice recordings will be stored in Supabase Storage
    - The URL will reference the storage bucket location
    - Column allows null for backward compatibility with existing reports
*/

-- Add voice recording URL column to emergency_reports
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'emergency_reports' AND column_name = 'voice_recording_url'
  ) THEN
    ALTER TABLE emergency_reports ADD COLUMN voice_recording_url text;
  END IF;
END $$;
