import { useState, useEffect } from 'react';
import { MapPin, CloudRain, Droplets, Wind, Thermometer, AlertCircle, CheckCircle, Search, Navigation, RefreshCw, Waves } from 'lucide-react';
import { api, FloodForecast } from '../lib/api';

interface ClimateData {
  city: string;
  temperature: number;
  humidity: number;
  rainfall: number;
  windSpeed: number;
  pressure: number;
  weatherCondition: string;
  latitude: number;
  longitude: number;
  timestamp: Date;
  floodForecast?: FloodForecast;
}

interface FloodRiskStatus {
  level: 'safe' | 'low' | 'moderate' | 'high' | 'critical';
  percentage: number;
  message: string;
  factors: string[];
  riverDischarge?: number;
  riverDischargeMax?: number;
}

const NIGERIAN_CITIES = [
  { name: 'Lagos', lat: 6.5244, lon: 3.3792 },
  { name: 'Abuja', lat: 9.0765, lon: 7.3986 },
  { name: 'Port Harcourt', lat: 4.8156, lon: 7.0498 },
  { name: 'Kano', lat: 12.0022, lon: 8.5920 },
  { name: 'Ibadan', lat: 7.3775, lon: 3.9470 },
  { name: 'Kaduna', lat: 10.5105, lon: 7.4165 },
];

export default function FloodRiskMonitor() {
  const [currentLocation, setCurrentLocation] = useState<ClimateData | null>(null);
  const [selectedCity, setSelectedCity] = useState<string>('');
  const [otherLocations, setOtherLocations] = useState<ClimateData[]>([]);
  const [loading, setLoading] = useState(true);
  const [detectingLocation, setDetectingLocation] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const calculateFloodRisk = (data: ClimateData): FloodRiskStatus => {
    const factors: string[] = [];
    let riskScore = 0;

    let riverDischarge: number | undefined;
    let riverDischargeMax: number | undefined;

    if (data.floodForecast && data.floodForecast.daily.river_discharge.length > 0) {
      riverDischarge = data.floodForecast.daily.river_discharge[0];
      riverDischargeMax = data.floodForecast.daily.river_discharge_max[0];

      if (riverDischarge > 1000) {
        riskScore += 50;
        factors.push('Extreme river discharge');
      } else if (riverDischarge > 500) {
        riskScore += 35;
        factors.push('Very high river discharge');
      } else if (riverDischarge > 200) {
        riskScore += 20;
        factors.push('High river discharge');
      } else if (riverDischarge > 50) {
        riskScore += 10;
        factors.push('Elevated river discharge');
      }

      const dischargeTrend = data.floodForecast.daily.river_discharge;
      if (dischargeTrend.length >= 3) {
        const isIncreasing = dischargeTrend[1] > dischargeTrend[0] && dischargeTrend[2] > dischargeTrend[1];
        if (isIncreasing && riverDischarge > 100) {
          riskScore += 15;
          factors.push('Rising river levels');
        }
      }
    }

    if (data.rainfall > 50) {
      riskScore += 30;
      factors.push('Extreme rainfall');
    } else if (data.rainfall > 25) {
      riskScore += 20;
      factors.push('Heavy rainfall');
    } else if (data.rainfall > 10) {
      riskScore += 10;
      factors.push('Moderate rainfall');
    }

    if (data.humidity > 85) {
      riskScore += 10;
      factors.push('Very high humidity');
    } else if (data.humidity > 70) {
      riskScore += 5;
      factors.push('High humidity');
    }

    if (data.weatherCondition.toLowerCase().includes('thunderstorm')) {
      riskScore += 15;
      factors.push('Thunderstorm');
    } else if (data.weatherCondition.toLowerCase().includes('rain')) {
      riskScore += 10;
      factors.push('Rainy weather');
    }

    if (data.pressure < 1000) {
      riskScore += 5;
      factors.push('Low pressure');
    }

    let level: FloodRiskStatus['level'] = 'safe';
    let message = 'No flood risk detected. Conditions are normal.';

    if (riskScore >= 80) {
      level = 'critical';
      message = 'CRITICAL FLOOD RISK! Evacuate immediately if instructed.';
    } else if (riskScore >= 60) {
      level = 'high';
      message = 'High flood risk. Stay alert and prepare for evacuation.';
    } else if (riskScore >= 40) {
      level = 'moderate';
      message = 'Moderate flood risk. Monitor weather and river levels closely.';
    } else if (riskScore >= 20) {
      level = 'low';
      message = 'Low flood risk. Stay informed about updates.';
    }

    if (factors.length === 0) {
      factors.push('Normal weather conditions');
    }

    return {
      level,
      percentage: Math.min(riskScore, 100),
      message,
      factors,
      riverDischarge,
      riverDischargeMax,
    };
  };

  const fetchWeatherByCoords = async (lat: number, lon: number, cityName?: string): Promise<ClimateData> => {
    const [weatherData, floodForecast] = await Promise.all([
      api.getWeatherDataByCoords(lat, lon),
      api.getFloodForecast(lat, lon).catch(() => undefined),
    ]);

    return {
      city: cityName || weatherData.name,
      temperature: weatherData.main.temp,
      humidity: weatherData.main.humidity,
      rainfall: weatherData.rain?.['1h'] || weatherData.rain?.['3h'] || 0,
      windSpeed: weatherData.wind.speed,
      pressure: weatherData.main.pressure,
      weatherCondition: weatherData.weather[0]?.description || 'Unknown',
      latitude: lat,
      longitude: lon,
      timestamp: new Date(),
      floodForecast,
    };
  };

  const fetchWeatherByCity = async (cityName: string): Promise<ClimateData> => {
    const weatherData = await api.getWeatherData(cityName);
    const floodForecast = await api.getFloodForecast(weatherData.coord.lat, weatherData.coord.lon).catch(() => undefined);

    return {
      city: cityName,
      temperature: weatherData.main.temp,
      humidity: weatherData.main.humidity,
      rainfall: weatherData.rain?.['1h'] || weatherData.rain?.['3h'] || 0,
      windSpeed: weatherData.wind.speed,
      pressure: weatherData.main.pressure,
      weatherCondition: weatherData.weather[0]?.description || 'Unknown',
      latitude: weatherData.coord.lat,
      longitude: weatherData.coord.lon,
      timestamp: new Date(),
      floodForecast,
    };
  };

  const detectUserLocation = async () => {
    setDetectingLocation(true);
    if (!navigator.geolocation) {
      console.error('Geolocation not supported');
      setDetectingLocation(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const data = await fetchWeatherByCoords(
            position.coords.latitude,
            position.coords.longitude
          );
          setCurrentLocation(data);
          setLastUpdate(new Date());
        } catch (error) {
          console.error('Error fetching location weather:', error);
        }
        setDetectingLocation(false);
        setLoading(false);
      },
      (error) => {
        console.error('Geolocation error:', error);
        fetchDefaultLocation();
        setDetectingLocation(false);
      }
    );
  };

  const fetchDefaultLocation = async () => {
    try {
      const data = await fetchWeatherByCity('Lagos');
      setCurrentLocation(data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching default location:', error);
    }
    setLoading(false);
  };

  const handleCitySelect = async (cityName: string) => {
    if (!cityName || cityName === currentLocation?.city) return;

    setSelectedCity(cityName);
    try {
      const data = await fetchWeatherByCity(cityName);
      setOtherLocations(prev => {
        const filtered = prev.filter(loc => loc.city !== cityName);
        return [data, ...filtered].slice(0, 3);
      });
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching city weather:', error);
    }
    setSelectedCity('');
  };

  const refreshData = async () => {
    if (currentLocation) {
      try {
        const data = await fetchWeatherByCoords(
          currentLocation.latitude,
          currentLocation.longitude,
          currentLocation.city
        );
        setCurrentLocation(data);
        setLastUpdate(new Date());
      } catch (error) {
        console.error('Error refreshing data:', error);
      }
    }
  };

  useEffect(() => {
    detectUserLocation();
    const interval = setInterval(refreshData, 120000);
    return () => clearInterval(interval);
  }, []);

  const getRiskColor = (level: FloodRiskStatus['level']) => {
    switch (level) {
      case 'critical': return 'bg-red-600';
      case 'high': return 'bg-orange-600';
      case 'moderate': return 'bg-yellow-600';
      case 'low': return 'bg-blue-600';
      default: return 'bg-green-600';
    }
  };

  const getRiskBg = (level: FloodRiskStatus['level']) => {
    switch (level) {
      case 'critical': return 'bg-red-50 border-red-300';
      case 'high': return 'bg-orange-50 border-orange-300';
      case 'moderate': return 'bg-yellow-50 border-yellow-300';
      case 'low': return 'bg-blue-50 border-blue-300';
      default: return 'bg-green-50 border-green-300';
    }
  };

  const getRiskTextColor = (level: FloodRiskStatus['level']) => {
    switch (level) {
      case 'critical': return 'text-red-900';
      case 'high': return 'text-orange-900';
      case 'moderate': return 'text-yellow-900';
      case 'low': return 'text-blue-900';
      default: return 'text-green-900';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow border border-gray-200 p-12">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading climate data...</p>
        </div>
      </div>
    );
  }

  if (!currentLocation) {
    return (
      <div className="bg-white rounded-lg shadow border border-gray-200 p-12">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Unable to load climate data</p>
        </div>
      </div>
    );
  }

  const currentRisk = calculateFloodRisk(currentLocation);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="border-b border-gray-200 bg-blue-600 text-white p-6 rounded-t-lg">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-1">Flood Risk Monitor</h2>
              <p className="text-blue-100 text-sm">Real-time climate analysis</p>
            </div>
            <button
              onClick={detectUserLocation}
              disabled={detectingLocation}
              className="flex items-center gap-2 px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-colors disabled:opacity-50 font-medium"
            >
              <Navigation className={`w-4 h-4 ${detectingLocation ? 'animate-spin' : ''}`} />
              Detect Location
            </button>
          </div>
        </div>

        <div className="p-6">
          <div className={`${getRiskBg(currentRisk.level)} rounded-lg border-2 p-6 mb-6`}>
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <MapPin className="w-6 h-6 text-gray-700" />
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">{currentLocation.city}</h3>
                  <p className="text-sm text-gray-600 capitalize">{currentLocation.weatherCondition}</p>
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-2 mb-1">
                  <div className={`w-3 h-3 ${getRiskColor(currentRisk.level)} rounded-full`}></div>
                  <span className={`text-sm font-bold uppercase ${getRiskTextColor(currentRisk.level)}`}>
                    {currentRisk.level}
                  </span>
                </div>
                <div className={`text-4xl font-bold ${getRiskTextColor(currentRisk.level)}`}>
                  {currentRisk.percentage}%
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-4 mb-4 border border-gray-200">
              <div className="flex items-start gap-2">
                {currentRisk.level === 'safe' ? (
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                ) : (
                  <AlertCircle className={`w-5 h-5 ${getRiskTextColor(currentRisk.level)} mt-0.5 flex-shrink-0`} />
                )}
                <p className="text-gray-900 font-medium">{currentRisk.message}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <Thermometer className="w-5 h-5 text-gray-600" />
                  <span className="text-xs text-gray-600 font-medium">Temperature</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">{currentLocation.temperature.toFixed(1)}°C</p>
              </div>

              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <CloudRain className="w-5 h-5 text-gray-600" />
                  <span className="text-xs text-gray-600 font-medium">Rainfall</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">{currentLocation.rainfall.toFixed(1)}mm</p>
              </div>

              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <Droplets className="w-5 h-5 text-gray-600" />
                  <span className="text-xs text-gray-600 font-medium">Humidity</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">{currentLocation.humidity}%</p>
              </div>

              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <Wind className="w-5 h-5 text-gray-600" />
                  <span className="text-xs text-gray-600 font-medium">Wind</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">{currentLocation.windSpeed.toFixed(1)}m/s</p>
              </div>

              {currentRisk.riverDischarge !== undefined && (
                <div className="bg-blue-50 rounded-lg p-4 border-2 border-blue-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Waves className="w-5 h-5 text-blue-600" />
                    <span className="text-xs text-blue-700 font-medium">River Flow</span>
                  </div>
                  <p className="text-2xl font-bold text-blue-900">{currentRisk.riverDischarge.toFixed(0)}m³/s</p>
                  {currentRisk.riverDischargeMax && currentRisk.riverDischargeMax > currentRisk.riverDischarge && (
                    <p className="text-xs text-blue-600 mt-1">Peak: {currentRisk.riverDischargeMax.toFixed(0)}m³/s</p>
                  )}
                </div>
              )}
            </div>

            <div>
              <p className="text-xs text-gray-700 font-semibold mb-2">Contributing Factors:</p>
              <div className="flex flex-wrap gap-2">
                {currentRisk.factors.map((factor, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-white rounded-md text-xs font-medium text-gray-700 border border-gray-300"
                  >
                    {factor}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Search className="w-5 h-5 text-blue-600" />
              Check Other Locations
            </h3>
            <button
              onClick={refreshData}
              className="flex items-center gap-2 px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors border border-blue-200"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          <select
            value={selectedCity}
            onChange={(e) => handleCitySelect(e.target.value)}
            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white mb-4"
          >
            <option value="">Select a city to monitor...</option>
            {NIGERIAN_CITIES.filter(city => city.name !== currentLocation.city).map((city) => (
              <option key={city.name} value={city.name}>
                {city.name}
              </option>
            ))}
          </select>

          {otherLocations.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {otherLocations.map((location) => {
                const risk = calculateFloodRisk(location);
                return (
                  <div
                    key={location.city}
                    className="bg-white rounded-lg border-2 border-gray-200 p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-bold text-gray-900 flex items-center gap-2">
                        <MapPin className="w-4 h-4" />
                        {location.city}
                      </h4>
                      <div className="flex items-center gap-1">
                        <div className={`w-2 h-2 ${getRiskColor(risk.level)} rounded-full`}></div>
                        <span className={`text-xs font-bold ${getRiskTextColor(risk.level)}`}>
                          {risk.percentage}%
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-gray-600 mb-3 capitalize">{location.weatherCondition}</p>

                    <div className="grid grid-cols-2 gap-2 text-xs bg-gray-50 rounded p-2">
                      <div>
                        <p className="text-gray-600">Temp</p>
                        <p className="font-semibold text-gray-900">{location.temperature.toFixed(1)}°C</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Rain</p>
                        <p className="font-semibold text-gray-900">{location.rainfall.toFixed(1)}mm</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="mt-6 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              Last updated: {lastUpdate.toLocaleTimeString()} • Refreshes every 2 minutes
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
