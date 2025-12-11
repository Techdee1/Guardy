import { useState, useEffect } from 'react';
import { ShieldCheck, Home, Shield, ArrowLeft, Phone } from 'lucide-react';
import LandingPage from './components/LandingPage';
import FloodRiskMonitor from './components/FloodRiskMonitor';
import EmergencyForm from './components/EmergencyForm';
import AlertPanel from './components/AlertPanel';
import AdminPanel from './components/AdminPanel';
import WeatherMonitor from './components/WeatherMonitor';
import { api, FloodEvent, EmergencyReport, EmergencyCenter } from './lib/api';

type ViewMode = 'landing' | 'citizen' | 'authority';

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('landing');
  const [floodEvents, setFloodEvents] = useState<FloodEvent[]>([]);
  const [emergencyReports, setEmergencyReports] = useState<EmergencyReport[]>([]);
  const [emergencyCenters, setEmergencyCenters] = useState<EmergencyCenter[]>([]);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    if (viewMode === 'landing') return;

    try {
      const [floods, reports, centers] = await Promise.all([
        api.getFloodEvents(),
        api.getEmergencyReports(),
        api.getEmergencyCenters(),
      ]);
      setFloodEvents(floods);
      setEmergencyReports(reports);
      setEmergencyCenters(centers);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (viewMode !== 'landing') {
      setLoading(true);
      loadData();
      const interval = setInterval(loadData, 30000);
      return () => clearInterval(interval);
    }
  }, [viewMode]);

  const handleRoleSelect = (role: 'citizen' | 'authority') => {
    setViewMode(role);
  };

  if (viewMode === 'landing') {
    return <LandingPage onRoleSelect={handleRoleSelect} />;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-xl font-semibold text-gray-900">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 from-slate-50 via-blue-50/30 to-cyan-50/30">
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 shadow-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-xl opacity-20 blur-md animate-pulse"></div>
                <div className="relative bg-gradient-to-br from-blue-600 to-cyan-600 p-2.5 rounded-xl shadow-lg">
                  <ShieldCheck className="w-7 h-7 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-black text-slate-900 tracking-tight">
                  <span className="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">FloodGuard</span> Nigeria
                </h1>
                <p className="text-xs text-slate-600 font-semibold">
                  {viewMode === 'citizen' ? 'Citizen Portal' : 'Authority Dashboard'}
                </p>
              </div>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:gap-3 w-full justify-end items-end">
              {viewMode === 'citizen' && (
                <button
                  onClick={() => setViewMode('authority')}
                  className="group w-full sm:w-auto flex items-center px-5 py-2.5 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl font-bold hover:shadow-xl transition-all duration-300 hover:scale-105"
                >
                  <Shield className="w-4 h-4 mr-2 group-hover:rotate-12 transition-transform" />
                  Authority
                </button>
              )}
            
              {viewMode === 'authority' && (
                <button
                  onClick={() => setViewMode('citizen')}
                  className="group w-full sm:w-auto flex items-center px-5 py-2.5 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-xl font-bold hover:shadow-xl transition-all duration-300 hover:scale-105"
                >
                  <Home className="w-4 h-4 mr-2 group-hover:scale-110 transition-transform" />
                  Citizen
                </button>
              )}
            
              <button
                onClick={() => setViewMode('landing')}
                className="w-full sm:w-auto flex items-center px-5 py-2.5 rounded-xl font-semibold border-2 border-slate-300 text-slate-700 hover:bg-white hover:border-slate-400 transition-all duration-300 bg-slate-50"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Home
              </button>
            </div>

          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {viewMode === 'citizen' ? (
          <div className="space-y-6">
            <FloodRiskMonitor />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <EmergencyForm onSubmitSuccess={loadData} />
                  <WeatherMonitor onFloodEventCreated={loadData} />
                </div>
              </div>

              <div className="lg:col-span-1">
                <div className="h-[500px]">
                  <AlertPanel floodEvents={floodEvents} />
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            <AdminPanel reports={emergencyReports} onUpdate={loadData} />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
                <div className="flex items-center mb-4">
                  <div className="p-2 bg-blue-100 rounded-lg mr-3">
                    <ShieldCheck className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Recent Flood Events</h3>
                    <p className="text-sm text-gray-600">{floodEvents.length} events recorded</p>
                  </div>
                </div>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {floodEvents.slice(0, 5).map((event) => (
                    <div key={event.id} className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <p className="font-bold text-gray-900">{event.location}</p>
                          <p className="text-sm text-gray-600">{event.description}</p>
                          <p className="text-xs font-mono text-gray-500 mt-1">
                            {event.latitude.toFixed(4)}, {event.longitude.toFixed(4)}
                          </p>
                        </div>
                        <span
                          className={`px-2 py-1 rounded text-xs font-bold uppercase ml-2 ${
                            event.severity === 'high'
                              ? 'bg-red-600 text-white'
                              : event.severity === 'medium'
                              ? 'bg-yellow-600 text-white'
                              : 'bg-blue-600 text-white'
                          }`}
                        >
                          {event.severity}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-gray-500">
                          {new Date(event.timestamp).toLocaleString('en-NG', {
                            dateStyle: 'medium',
                            timeStyle: 'short',
                          })}
                        </p>
                        {event.rainfall && (
                          <p className="text-xs font-semibold text-blue-600">
                            {event.rainfall.toFixed(1)}mm rain
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                  {floodEvents.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <p>No flood events recorded</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-slate-200 p-6">
                <div className="flex items-center mb-6">
                  <div className="relative mr-4">
                    <div className="absolute inset-0 bg-gradient-to-r from-green-600 to-emerald-600 rounded-xl opacity-20 blur-md"></div>
                    <div className="relative p-3 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl shadow-lg">
                      <Shield className="w-6 h-6 text-white" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-2xl font-black text-slate-900">Emergency Centers</h3>
                    <p className="text-sm text-slate-600 font-semibold">{emergencyCenters.length} centers available</p>
                  </div>
                </div>
                <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
                  {emergencyCenters.map((center) => (
                    <div key={center.id} className="group bg-gradient-to-br from-white to-slate-50 border-2 border-slate-200 rounded-xl p-5 hover:shadow-xl hover:border-green-300 transition-all duration-300 hover:-translate-y-1">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <p className="font-black text-lg text-slate-900 mb-1">{center.name}</p>
                          <div className="flex items-center gap-2 text-slate-600">
                            <Phone className="w-4 h-4" />
                            <p className="text-sm font-semibold">{center.phone}</p>
                          </div>
                        </div>
                        <span
                          className={`px-3 py-1.5 rounded-lg text-xs font-black uppercase tracking-wide shadow-md ${
                            center.type === 'hospital'
                              ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white'
                              : 'bg-gradient-to-r from-green-600 to-emerald-600 text-white'
                          }`}
                        >
                          {center.type}
                        </span>
                      </div>
                      <div className="pt-3 border-t border-slate-200">
                        <a
                          href={`tel:${center.phone}`}
                          className="group/btn flex items-center justify-center gap-2 w-full px-4 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-xl font-bold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02]"
                        >
                          <div className="relative">
                            <Phone className="w-5 h-5 group-hover/btn:rotate-12 transition-transform" />
                            <span className="absolute -top-1 -right-1 flex h-3 w-3">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                              <span className="relative inline-flex rounded-full h-3 w-3 bg-white"></span>
                            </span>
                          </div>
                          <span>Call Now</span>
                        </a>
                      </div>
                    </div>
                  ))}
                  {emergencyCenters.length === 0 && (
                    <div className="text-center py-12 bg-slate-50 rounded-xl border-2 border-dashed border-slate-200">
                      <Shield className="w-16 h-16 text-slate-300 mx-auto mb-3" />
                      <p className="text-slate-500 font-medium">No emergency centers available</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="bg-white mt-12 py-6 border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-gray-600 text-sm">
            FloodGuard Nigeria - Real-time flood monitoring and emergency response system
          </p>
          <p className="text-center text-gray-500 text-xs mt-2">
            Powered by OpenWeatherMap & OpenMeteo | Emergency response within 10km radius
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
