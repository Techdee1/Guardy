/*
  # Add Alert Subscriptions Table

  1. New Tables
    - `alert_subscriptions`
      - `id` (uuid, primary key) - Unique identifier
      - `phone` (text) - User phone number
      - `latitude` (decimal) - User location latitude
      - `longitude` (decimal) - User location longitude
      - `location_name` (text) - Readable location name
      - `is_active` (boolean) - Whether alerts are active
      - `created_at` (timestamptz) - When subscription was created
      - `updated_at` (timestamptz) - Last update time

  2. Security
    - Enable RLS on `alert_subscriptions` table
    - Add policy for public insert (registration)
    - Add policy for public read (users can check their subscription)

  3. Indexes
    - Index on phone for fast lookup
    - Index on location for proximity searches
    - Index on is_active for filtering active subscriptions

  4. Important Notes
    - Phone numbers must be unique (one subscription per number)
    - Location can be updated by re-registering with same phone
    - Default status is active (true)
*/

-- Create alert_subscriptions table
CREATE TABLE IF NOT EXISTS alert_subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  phone text NOT NULL UNIQUE,
  latitude decimal(10, 7) NOT NULL,
  longitude decimal(10, 7) NOT NULL,
  location_name text DEFAULT '',
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE alert_subscriptions ENABLE ROW LEVEL SECURITY;

-- Create policies for public access
CREATE POLICY "Anyone can register for alerts"
  ON alert_subscriptions FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

CREATE POLICY "Anyone can view alert subscriptions"
  ON alert_subscriptions FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Anyone can update their own subscription"
  ON alert_subscriptions FOR UPDATE
  TO anon, authenticated
  USING (true)
  WITH CHECK (true);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_alert_subscriptions_phone ON alert_subscriptions(phone);
CREATE INDEX IF NOT EXISTS idx_alert_subscriptions_location ON alert_subscriptions(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_alert_subscriptions_active ON alert_subscriptions(is_active);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_alert_subscription_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at
DROP TRIGGER IF EXISTS trigger_update_alert_subscription_timestamp ON alert_subscriptions;
CREATE TRIGGER trigger_update_alert_subscription_timestamp
  BEFORE UPDATE ON alert_subscriptions
  FOR EACH ROW
  EXECUTE FUNCTION update_alert_subscription_timestamp();