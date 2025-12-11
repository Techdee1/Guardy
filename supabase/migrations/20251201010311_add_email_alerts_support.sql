/*
  # Update Alert Subscriptions to Support Email

  1. Changes
    - Add email column to alert_subscriptions table
    - Keep phone column for backward compatibility
    - Make both phone and email optional (at least one required via app logic)
  
  2. Notes
    - Existing phone subscriptions remain intact
    - New subscriptions can use email instead of phone
    - RLS policies remain unchanged
*/

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'alert_subscriptions' AND column_name = 'email'
  ) THEN
    ALTER TABLE alert_subscriptions ADD COLUMN email text;
  END IF;
END $$;

-- Make phone nullable since we now support email
ALTER TABLE alert_subscriptions ALTER COLUMN phone DROP NOT NULL;

-- Add check constraint to ensure at least email or phone is provided
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint 
    WHERE conname = 'alert_subscriptions_contact_check'
  ) THEN
    ALTER TABLE alert_subscriptions 
    ADD CONSTRAINT alert_subscriptions_contact_check 
    CHECK (email IS NOT NULL OR phone IS NOT NULL);
  END IF;
END $$;
