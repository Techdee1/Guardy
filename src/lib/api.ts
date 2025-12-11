const API_BASE_URL = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/floodguard-api`;

const getHeaders = () => ({
  'Authorization': `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY}`,
  'Content-Type': 'application/json',
});

export interface FloodEvent {
  id?: string;
  location: string;
  latitude: number;
  longitude: number;
  severity: 'low' | 'medium' | 'high';
  rainfall?: number;
  description?: string;
  timestamp: string;
  created_at?: string;
}

export interface EmergencyReport {
  id?: string;
  name: string;
  latitude: number;
  longitude: number;
  type_of_need: 'Food' | 'Water' | 'Medicine' | 'Shelter';
  comments: string;
  status?: 'pending' | 'responded' | 'resolved';
  timestamp: string;
  created_at?: string;
  voice_recording_url?: string;
  location_name?: string;
}

export interface EmergencyCenter {
  id?: string;
  name: string;
  type: 'shelter' | 'hospital';
  latitude: number;
  longitude: number;
  email: string;
  phone: string;
  created_at?: string;
}

export interface WeatherData {
  coord: { lon: number; lat: number };
  weather: Array<{ id: number; main: string; description: string; icon: string }>;
  main: {
    temp: number;
    feels_like: number;
    humidity: number;
    pressure: number;
  };
  wind: { speed: number; deg: number };
  clouds: { all: number };
  rain?: { '1h'?: number; '3h'?: number };
  name: string;
}

export interface FloodForecast {
  latitude: number;
  longitude: number;
  daily: {
    time: string[];
    river_discharge: number[];
    river_discharge_mean: number[];
    river_discharge_max: number[];
    river_discharge_min: number[];
  };
  daily_units: {
    river_discharge: string;
    river_discharge_mean: string;
    river_discharge_max: string;
    river_discharge_min: string;
  };
}

export const api = {
  async getFloodEvents(): Promise<FloodEvent[]> {
    const response = await fetch(`${API_BASE_URL}/floods`, {
      headers: getHeaders(),
    });
    const result = await response.json();
    return result.data || [];
  },

  async createFloodEvent(event: FloodEvent): Promise<{
    event: FloodEvent;
    notificationsSent: number;
    totalSubscribers: number;
  }> {
    const response = await fetch(`${API_BASE_URL}/floods`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(event),
    });
    const result = await response.json();
    return {
      event: result.data[0],
      notificationsSent: result.notificationsSent || 0,
      totalSubscribers: result.totalSubscribers || 0,
    };
  },

  async getEmergencyReports(): Promise<EmergencyReport[]> {
    const response = await fetch(`${API_BASE_URL}/reports`, {
      headers: getHeaders(),
    });
    const result = await response.json();
    return result.data || [];
  },

  async createEmergencyReport(report: EmergencyReport): Promise<{
    report: EmergencyReport;
    nearbyCenters: Array<EmergencyCenter & { distance: number }>;
  }> {
    const response = await fetch(`${API_BASE_URL}/reports`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(report),
    });
    const result = await response.json();
    return {
      report: result.data,
      nearbyCenters: result.nearbyCenters || [],
    };
  },

  async uploadVoiceRecording(audioBlob: Blob, reportId: string): Promise<string> {
    const formData = new FormData();
    formData.append('audio', audioBlob, `voice-${reportId}.webm`);
    formData.append('reportId', reportId);

    const response = await fetch(`${API_BASE_URL}/upload-voice`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY}`,
      },
      body: formData,
    });
    const result = await response.json();
    return result.url;
  },

  async updateReportStatus(id: string, status: string): Promise<EmergencyReport> {
    const response = await fetch(`${API_BASE_URL}/reports`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({ id, status }),
    });
    const result = await response.json();
    return result.data[0];
  },

  async getEmergencyCenters(): Promise<EmergencyCenter[]> {
    const response = await fetch(`${API_BASE_URL}/centers`, {
      headers: getHeaders(),
    });
    const result = await response.json();
    return result.data || [];
  },

  async getWeatherData(city: string): Promise<WeatherData> {
    const response = await fetch(`${API_BASE_URL}/weather?city=${city}&apiKey=53b1e8acf21399ed870cbe9fec7aa0b5`, {
      headers: getHeaders(),
    });
    const result = await response.json();
    return result.data;
  },

  async getWeatherDataByCoords(lat: number, lon: number): Promise<WeatherData> {
    const response = await fetch(`${API_BASE_URL}/weather?lat=${lat}&lon=${lon}&apiKey=53b1e8acf21399ed870cbe9fec7aa0b5`, {
      headers: getHeaders(),
    });
    const result = await response.json();
    return result.data;
  },

  async getFloodForecast(lat: number, lon: number): Promise<FloodForecast> {
    const response = await fetch(`${API_BASE_URL}/flood-forecast?lat=${lat}&lon=${lon}`, {
      headers: getHeaders(),
    });
    const result = await response.json();
    return result.data;
  },
};
