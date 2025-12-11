import { useState, useEffect } from 'react';
import { CloudRain, Wind, Droplets, ThermometerSun, Upload, RefreshCw, Cloud, Bell, Check } from 'lucide-react';
import { api, FloodEvent } from '../lib/api';

interface WeatherMonitorProps {
  onFloodEventCreated: () => void;
}

const NIGERIAN_CITIES = [
  { name: 'Lagos', lat: 6.5244, lon: 3.3792 },
  { name: 'Abuja', lat: 9.0765, lon: 7.3986 },
  { name: 'Port Harcourt', lat: 4.8156, lon: 7.0498 },
  { name: 'Kano', lat: 12.0022, lon: 8.5920 },
  { name: 'Ibadan', lat: 7.3775, lon: 3.9470 },
  { name: 'Kaduna', lat: 10.5105, lon: 7.4165 },
];

export default function WeatherMonitor({ onFloodEventCreated }: WeatherMonitorProps) {
  const [selectedCity, setSelectedCity] = useState('Lagos');
  const [weatherData, setWeatherData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [jsonInput, setJsonInput] = useState('');
  const [showJsonUpload, setShowJsonUpload] = useState(false);
  const [lastNotification, setLastNotification] = useState<{
    sent: number;
    total: number;
    timestamp: Date;
  } | null>(null);

  const fetchWeather = async (city: string) => {
    setLoading(true);
    try {
      const data = await api.getWeatherData(city);
      setWeatherData(data);

      const rainfall = data.rain?.['1h'] || data.rain?.['3h'] || 0;
      let severity: 'low' | 'medium' | 'high' = 'low';

      if (rainfall > 50 || data.weather[0]?.main === 'Thunderstorm') {
        severity = 'high';
      } else if (rainfall > 25 || data.weather[0]?.main === 'Rain') {
        severity = 'medium';
      }

      if (rainfall > 10 || severity === 'high') {
        const cityInfo = NIGERIAN_CITIES.find((c) => c.name === city);
        if (cityInfo) {
          const floodEvent: FloodEvent = {
            location: city,
            latitude: cityInfo.lat,
            longitude: cityInfo.lon,
            severity,
            rainfall,
            description: data.weather[0]?.description || '',
            timestamp: new Date().toISOString(),
          };

          const result = await api.createFloodEvent(floodEvent);
          setLastNotification({
            sent: result.notificationsSent,
            total: result.totalSubscribers,
            timestamp: new Date(),
          });
          onFloodEventCreated();
        }
      }
    } catch (error) {
      console.error('Error fetching weather:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWeather(selectedCity);
    const interval = setInterval(() => fetchWeather(selectedCity), 300000);
    return () => clearInterval(interval);
  }, [selectedCity]);

  const handleJsonUpload = async () => {
    try {
      const events = JSON.parse(jsonInput);
      const eventsArray = Array.isArray(events) ? events : [events];

      let totalSent = 0;
      let totalSubs = 0;

      for (const event of eventsArray) {
        const result = await api.createFloodEvent(event);
        totalSent += result.notificationsSent;
        totalSubs = Math.max(totalSubs, result.totalSubscribers);
      }

      setLastNotification({
        sent: totalSent,
        total: totalSubs,
        timestamp: new Date(),
      });

      onFloodEventCreated();
      setJsonInput('');
      setShowJsonUpload(false);
      alert(`Flood events uploaded successfully! ${totalSent} SMS alerts sent.`);
    } catch (error) {
      alert('Invalid JSON format. Please check your input.');
      console.error('JSON upload error:', error);
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <div className="relative mr-4">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-xl opacity-20 blur-md"></div>
            <div className="relative p-3 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl shadow-lg">
              <CloudRain className="w-6 h-6 text-white" />
            </div>
          </div>
          <div>
            <h2 className="text-2xl font-black text-slate-900">Weather Monitor</h2>
            <p className="text-sm text-slate-600 font-semibold">Live weather tracking</p>
          </div>
        </div>
        <button
          onClick={() => setShowJsonUpload(!showJsonUpload)}
          className="group flex items-center px-4 py-2.5 bg-slate-100 hover:bg-white text-slate-700 rounded-xl transition-all text-sm font-bold border-2 border-slate-200 hover:border-slate-300 hover:shadow-lg"
        >
          <Upload className="w-4 h-4 mr-2 group-hover:scale-110 transition-transform" />
          Upload Data
        </button>
      </div>

      {showJsonUpload && (
        <div className="mb-4 p-4 bg-gray-50 border border-gray-300 rounded-lg">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Flood Event JSON
          </label>
          <textarea
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono mb-2 text-gray-900 bg-white"
            rows={5}
            placeholder={`{\n  "location": "Lagos",\n  "latitude": 6.5244,\n  "longitude": 3.3792,\n  "severity": "high",\n  "timestamp": "2025-11-29T10:00:00Z"\n}`}
          />
          <div className="flex gap-2">
            <button
              onClick={handleJsonUpload}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              Submit
            </button>
            <button
              onClick={() => {
                setShowJsonUpload(false);
                setJsonInput('');
              }}
              className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {lastNotification && (
        <div className="mb-6 p-5 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl flex items-start gap-4 shadow-lg animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="flex-shrink-0">
            <div className="relative">
              <div className="absolute inset-0 bg-green-500 rounded-full opacity-20 blur-md animate-pulse"></div>
              <div className="relative p-2 bg-gradient-to-br from-green-500 to-emerald-500 rounded-lg">
                <Bell className="w-5 h-5 text-white" />
              </div>
              <div className="absolute -top-1 -right-1 bg-white rounded-full p-0.5">
                <Check className="w-3 h-3 text-green-600" />
              </div>
            </div>
          </div>
          <div className="flex-1">
            <p className="font-black text-green-900 mb-1 text-lg">
              SMS Alerts Sent Successfully!
            </p>
            <p className="text-sm text-green-800 font-semibold">
              {lastNotification.sent} notification{lastNotification.sent !== 1 ? 's' : ''} delivered to nearby subscribers. If the email doesn’t show up in your inbox, remember to check your Spam or Junk folder.
              {lastNotification.total > 0 && ` • ${lastNotification.total} active users`}
            </p>
            <p className="text-xs text-green-600 mt-2 font-medium">
              {lastNotification.timestamp.toLocaleTimeString()}
            </p>
          </div>
          <button
            onClick={() => setLastNotification(null)}
            className="text-green-600 hover:text-green-800 text-lg font-bold hover:scale-110 transition-transform"
          >
            ✕
          </button>
        </div>
      )}

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Select City</label>
        <select
          value={selectedCity}
          onChange={(e) => setSelectedCity(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
        >
          {NIGERIAN_CITIES.map((city) => (
            <option key={city.name} value={city.name}>
              {city.name}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="text-center py-8">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading weather data...</p>
        </div>
      ) : weatherData ? (
        <div className="space-y-4">
          <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">{weatherData.name}</h3>
                <p className="text-gray-600 capitalize">{weatherData.weather[0]?.description}</p>
              </div>
              <div className="text-right">
                <p className="text-4xl font-bold text-gray-900">{weatherData.main.temp.toFixed(1)}°C</p>
                <p className="text-sm text-gray-600">Feels like {weatherData.main.feels_like.toFixed(1)}°C</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center bg-white rounded-lg p-3 border border-gray-200">
                <Droplets className="w-5 h-5 text-blue-600 mr-2" />
                <div>
                  <p className="text-xs text-gray-600">Humidity</p>
                  <p className="text-lg font-semibold text-gray-900">{weatherData.main.humidity}%</p>
                </div>
              </div>

              <div className="flex items-center bg-white rounded-lg p-3 border border-gray-200">
                <Wind className="w-5 h-5 text-blue-600 mr-2" />
                <div>
                  <p className="text-xs text-gray-600">Wind Speed</p>
                  <p className="text-lg font-semibold text-gray-900">{weatherData.wind.speed} m/s</p>
                </div>
              </div>

              <div className="flex items-center bg-white rounded-lg p-3 border border-gray-200">
                <ThermometerSun className="w-5 h-5 text-blue-600 mr-2" />
                <div>
                  <p className="text-xs text-gray-600">Pressure</p>
                  <p className="text-lg font-semibold text-gray-900">{weatherData.main.pressure} hPa</p>
                </div>
              </div>

              <div className="flex items-center bg-white rounded-lg p-3 border border-gray-200">
                <Cloud className="w-5 h-5 text-blue-600 mr-2" />
                <div>
                  <p className="text-xs text-gray-600">Clouds</p>
                  <p className="text-lg font-semibold text-gray-900">{weatherData.clouds.all}%</p>
                </div>
              </div>
            </div>

            {weatherData.rain && (
              <div className="mt-4 p-3 bg-yellow-50 border-2 border-yellow-400 rounded-lg">
                <p className="text-sm font-semibold text-yellow-900 flex items-center">
                  <CloudRain className="w-4 h-4 mr-2" />
                  Rainfall: {weatherData.rain['1h'] || weatherData.rain['3h'] || 0}mm
                </p>
              </div>
            )}
          </div>

          <button
            onClick={() => fetchWeather(selectedCity)}
            className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh Data
          </button>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <p>No weather data available</p>
        </div>
      )}
    </div>
  );
}
