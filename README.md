# FloodGuard — Predict, Protect, Respond

A fully functional climate adaptation MVP providing real-time flood risk alerts, citizen emergency reporting with voice input, and an authority dashboard to manage and respond to emergencies in Nigeria.

**No login/signup required** — Direct access via:
- `/` → Landing page with role selection
- Citizen view → for normal users
- Authority Dashboard → for agencies, NGOs, and rescue teams

## 🏗 Tech Stack

### Frontend
- **React 18** with TypeScript
- **Tailwind CSS** for modern, clean styling
- **Leaflet.js** and React Leaflet for interactive maps
- **Lucide React** for icons
- **Browser Geolocation API** for automatic location detection
- **MediaRecorder API** for voice recording

### Backend
- **Supabase Edge Functions** (Deno runtime)
- **PostgreSQL** database with Row Level Security
- **Supabase Storage** for voice recordings
- RESTful API architecture

### External APIs
- **OpenWeatherMap API** — Live weather & rainfall data
- **OpenStreetMap Nominatim** — Reverse geocoding (coordinates to address)
- **Twilio SMS API** — Authority/emergency notifications
- **Browser Geolocation** — Auto-detect user location
- **MediaRecorder API** — Voice input for emergency reports

## 🎯 Core Features

### 🏠 Landing Page
- Clean, modern, professional interface
- Light theme with soft color palette
- Title: **FloodGuard — Predict, Protect, Respond**
- Climate resilience and emergency response messaging
- Two role buttons:
  - **👉 Continue as Citizen** (Scroll to citizen section)
  - **🛡 Continue as Authority** (Scroll to authority dashboard)

### 👤 Citizen Features

#### Real-Time Flood Risk Monitoring
- **Automatic location detection** using Browser Geolocation API
- Live flood risk assessment using OpenWeatherMap data
- Color-coded risk levels:
  - 🟢 **Safe** — Low rainfall, no risk
  - 🟡 **Moderate** — Increased rainfall, monitor conditions
  - 🟠 **Risky** — Heavy rainfall, prepare for flooding
  - 🔴 **Severe** — Extreme rainfall, immediate danger
- Rainfall predictions and severity messages
- Safety precautions based on risk level

#### Interactive Map
- **Leaflet.js** powered real-time map showing:
  - User's current location (blue marker)
  - Flood alert zones with color-coded severity circles
  - Emergency centers (hospitals marked with 'H', shelters marked with 'S')
  - All emergency reports from citizens
- Auto-centers on user location
- Click markers for detailed information

#### Emergency Request Form
- **Auto-filled location** (latitude, longitude, and human-readable address)
- Fields:
  - **Name** (text input)
  - **Type of Need** (dropdown: Food, Water, Medicine, Shelter)
  - **Additional Comments** (textarea)
  - **Voice Recording** (optional) — Record emergency message
  - **Location** (auto-detected with refresh button)

#### Voice Recording Feature
- 🎤 **Record voice messages** for emergencies
- Red pulsing indicator while recording
- **Preview recording** before submission
- **Clear and re-record** option
- Audio stored securely in Supabase Storage
- Authorities can listen to recordings in dashboard

#### Automated Response System
When emergency is submitted:
- ✅ **Saves request to database** with location name
- 📧 **Notifies 3 nearest emergency centers** (within 10km via SMS)
- 🗺️ **Displays on authority map** in real-time
- 🎯 **Calculates distance** to nearby centers using Haversine formula
- 📍 **Reverse geocodes location** to readable address (e.g., "Victoria Island, Lagos, Lagos State")

#### Weather Monitor Panel
- Select from major Nigerian cities:
  - Lagos, Abuja, Port Harcourt, Kano, Ibadan, Kaduna
- Live data display:
  - Current temperature
  - Humidity percentage
  - Wind speed and direction
  - Rainfall amount (if any)
  - Weather conditions
- Auto-refresh every 5 minutes

### 🛡 Authority Dashboard Features

#### Statistics Overview
- **Total Reports** — All emergency requests
- **Pending** — Awaiting response (yellow)
- **Responded** — Help dispatched (blue)
- **Resolved** — Emergency resolved (green)
- Visual cards with icons and color coding

#### Advanced Filter System
- **Status Filter:**
  - All Status, Pending, Responded, Resolved
- **Type of Need Filter:**
  - All Types, Food, Water, Medicine, Shelter
- **Clear Filters** button (appears when filters active)
- **Live counter:** "Showing X of Y reports"
- Empty state with helpful messaging

#### Emergency Reports Display
Each report card shows:
- **Citizen name** and **timestamp**
- **Status badge** (color-coded with icon)
- **Type of need badge** (color-coded)
- **Location section** (highlighted blue box):
  - Human-readable address (e.g., "Ikoyi, Lagos, Lagos State")
  - GPS coordinates below
- **Comments** (if provided)
- **Voice recording player** (if recorded)
  - Audio controls: play, pause, volume, seek
  - Speaker icon indicator
- **Action buttons:**
  - "Mark as Responded" (blue)
  - "Mark as Resolved" (green)

#### Map View
- All emergency reports displayed with markers
- Flood event zones color-coded by severity
- Emergency centers (hospitals and shelters)
- Click markers for details

#### Flood Events Panel
- Recent flood events list (top 5)
- Shows:
  - City/location name
  - Weather description
  - GPS coordinates
  - Severity badge (red/yellow/green)
  - Rainfall amount
  - Timestamp
- Color-coded severity indicators

## 🗄 Database Schema

### Tables

**flood_events**
```sql
- id (uuid, primary key)
- location (text) — City/area name
- latitude (decimal)
- longitude (decimal)
- severity (text) — low/medium/high
- rainfall (decimal) — rainfall in mm
- description (text)
- timestamp (timestamptz)
- created_at (timestamptz)
```

**emergency_reports**
```sql
- id (uuid, primary key)
- name (text) — Citizen name
- latitude (decimal)
- longitude (decimal)
- type_of_need (text) — Food/Water/Medicine/Shelter
- comments (text)
- voice_recording_url (text) — URL to audio file
- location_name (text) — Human-readable address
- status (text) — pending/responded/resolved
- timestamp (timestamptz)
- created_at (timestamptz)
```

**emergency_centers**
```sql
- id (uuid, primary key)
- name (text)
- type (text) — shelter/hospital
- latitude (decimal)
- longitude (decimal)
- email (text)
- phone (text) — For SMS notifications
- created_at (timestamptz)
```

**Storage Bucket**
- **emergency-assets** — Stores voice recordings
  - Public access for emergency playback
  - 10MB file size limit
  - Supports: audio/webm, audio/wav, audio/mp3

## 🛠 API Endpoints

Base URL: `https://<your-supabase-url>/functions/v1/floodguard-api`

### GET /floods
Returns all flood events (sorted by timestamp)

### POST /floods
Create a new flood event
```json
{
  "location": "Lagos",
  "latitude": 6.5244,
  "longitude": 3.3792,
  "severity": "high",
  "rainfall": 45.5,
  "description": "Heavy rainfall",
  "timestamp": "2025-11-30T10:00:00Z"
}
```

### GET /reports
Returns all emergency reports with location names

### POST /reports
Submit emergency report (auto-notifies centers & geocodes location)
```json
{
  "name": "Amina Bello",
  "latitude": 6.5244,
  "longitude": 3.3792,
  "type_of_need": "Water",
  "comments": "Need clean water urgently",
  "voice_recording_url": "https://...",
  "timestamp": "2025-11-30T10:15:00Z"
}
```

Response includes:
- Inserted report with location_name
- List of nearby centers (within 10km)
- SMS notification results

### PUT /reports
Update report status
```json
{
  "id": "uuid",
  "status": "responded"
}
```

### GET /centers
Returns all emergency centers

### GET /weather?city=Lagos
Get live weather data for Nigerian city
- Supports: Lagos, Abuja, Port Harcourt, Kano, Ibadan, Kaduna

### GET /weather?lat=6.5244&lon=3.3792
Get weather by coordinates

## 🎨 UI/UX Design

### Design Principles
- **Light theme only** — Clean, professional, trust-driven
- **Soft color palette** — Blues, greens, grays, with red/yellow alerts
- **Modern spacing** — Generous padding and margins
- **Smooth animations** — Subtle hover effects and transitions
- **Clear hierarchy** — Important info stands out
- **Professional typography** — Clean, readable fonts

### Color Scheme
- **Primary Blue:** Buttons, links, active states
- **Green:** Success, resolved, safe status
- **Yellow:** Warnings, pending, moderate risk
- **Red:** Emergencies, severe risk, danger
- **Gray:** Neutral backgrounds, borders, text
- **Purple:** Authority dashboard accent

### Responsive Design
- **Mobile:** Single column, stacked cards
- **Tablet:** Two columns where appropriate
- **Desktop:** Full multi-column layout
- Breakpoints optimized for all devices

## 🎤 Voice Recording Demo

### For Citizens:
1. Open emergency form
2. Click **"Start Voice Recording"** (blue button)
3. Browser requests microphone permission
4. Red pulsing dot indicates recording
5. Speak emergency details clearly
6. Click **"Stop Recording"** (red button)
7. Preview audio in green success box
8. Can clear and re-record if needed
9. Submit form — audio saved to database

### For Authorities:
1. View emergency report in dashboard
2. See **"Voice Recording"** section (blue box)
3. Click play on audio player
4. Listen to citizen's emergency message
5. Hear urgency in their voice
6. Update status accordingly

## 📡 Real-Time Features

### Auto-Refresh
- **Emergency reports:** Every 30 seconds
- **Flood events:** Every 30 seconds
- **Weather data:** Every 5 minutes
- Ensures authorities see latest information

### Automatic Location Detection
- Runs on page load
- No user interaction needed
- Falls back to manual refresh if permission denied
- Shows success message when detected

### Reverse Geocoding
- Converts GPS coordinates to addresses
- Format: "Suburb, City, State"
- Runs automatically on report submission
- Uses OpenStreetMap Nominatim API
- Stored in database for quick access

## 🚨 Emergency Centers (Pre-loaded)

The system includes 8 emergency centers across Nigeria:

**Lagos:**
1. Lagos State Emergency Center (Shelter)
2. Lagos General Hospital (Hospital)

**Abuja:**
3. Abuja Emergency Shelter (Shelter)
4. National Hospital Abuja (Hospital)

**Port Harcourt:**
5. Port Harcourt Relief Center (Shelter)
6. University of Port Harcourt Teaching Hospital (Hospital)

**Kano:**
7. Kano Emergency Response (Shelter)
8. Aminu Kano Teaching Hospital (Hospital)

## 📱 SMS Notifications

### When Emergency is Reported:
System finds 3 nearest centers within 10km and sends:

```
EMERGENCY ALERT: Amina Bello needs Water.
Location: Victoria Island, Lagos (6.5244, 3.3792).
Distance: 2.5km.
Comments: Need clean water urgently
```

### Twilio Setup:
See `TWILIO_SETUP.md` for configuration instructions.

## 🎯 Demo Flow (for Hackathon)

### 1. Show Flood Risk Detection
- Open landing page
- Scroll to citizen view
- Point to auto-detected location
- Show color-coded risk level
- Explain rainfall thresholds

### 2. Submit Emergency with Voice
- Fill in name: "Amina Bello"
- Select need: "Water"
- Click **"Start Voice Recording"**
- Record: "We need clean drinking water urgently, water supply is contaminated"
- Stop recording and preview
- Show auto-detected location with address
- Submit report

### 3. Show Real-Time Notification
- SMS sent instantly to 3 nearest centers
- Show SMS content with location name

### 4. Authority Dashboard
- Switch to authority view
- Point to new report appearing
- Show location name: "Victoria Island, Lagos, Lagos State"
- Click play on voice recording
- Listen to emergency message
- Update status to "Responded"

### 5. Map Visualization
- Show all emergency markers
- Point to flood risk zones (colored circles)
- Show emergency centers
- Demonstrate click for details

## 🧪 Testing the Application

### Test Flood Risk
1. Allow location permission
2. System auto-detects coordinates
3. Weather Monitor shows live data
4. Risk level calculated automatically
5. Color changes based on rainfall

### Test Emergency Report
1. Fill out form with test data
2. Record voice message
3. Submit report
4. Check map for new marker
5. Check authority dashboard
6. Verify SMS sent (if Twilio configured)
7. Listen to voice recording

### Test Filter System
1. Open authority dashboard
2. Apply status filter: "Pending"
3. Apply type filter: "Water"
4. Verify showing X of Y counter
5. Click "Clear Filters"

### Test Voice Recording
1. Start recording
2. See pulsing red dot
3. Speak for 10 seconds
4. Stop recording
5. See green success box
6. Play preview
7. Clear and re-record
8. Submit with form

## 🔐 Security

- **Row Level Security (RLS)** enabled on all tables
- Public access policies for demo (can restrict for production)
- **Voice recordings** stored in secure Supabase Storage bucket
- **API authentication** via Supabase keys
- **SMS credentials** stored as environment variables
- **CORS headers** properly configured

## 🚀 Production Deployment

For production use:
1. ✅ Restrict RLS policies to authenticated users
2. ✅ Add user authentication system
3. ✅ Set up rate limiting on API endpoints
4. ✅ Configure Twilio with paid account
5. ✅ Monitor API usage and costs
6. ✅ Set up error tracking and logging
7. ✅ Add data backup and recovery
8. ✅ Implement GDPR compliance for voice recordings

## 📊 System Architecture

```
┌─────────────┐
│   Browser   │
│  (React)    │
└──────┬──────┘
       │
       ├──────► Geolocation API (location)
       ├──────► MediaRecorder API (voice)
       │
       v
┌─────────────────┐
│  Supabase       │
│  Edge Function  │
│  (Deno)         │
└────────┬────────┘
         │
         ├──────► PostgreSQL (data)
         ├──────► Storage (audio files)
         ├──────► OpenWeatherMap (weather)
         ├──────► Nominatim (geocoding)
         └──────► Twilio (SMS)
```

## 🎓 Key Technical Achievements

✅ **Real-time flood risk detection** with live API integration
✅ **Voice recording** with browser MediaRecorder API
✅ **Automatic location detection** with GPS and reverse geocoding
✅ **Smart proximity algorithm** (Haversine formula for distance)
✅ **SMS notifications** to nearest emergency centers
✅ **Interactive maps** with Leaflet.js
✅ **Advanced filtering** with clear UX
✅ **Responsive design** across all devices
✅ **Clean architecture** with TypeScript
✅ **Secure storage** for audio files
✅ **No authentication required** for emergency access

## 📄 License

MIT License — Free to use and modify

## 🆘 Support

For issues or questions:
- Check browser console for errors
- Verify environment variables in Supabase
- Check Supabase logs for backend errors
- Review Twilio dashboard for SMS status
- Test microphone permissions for voice recording

---

**Built for climate resilience and emergency response in Nigeria** 🇳🇬
