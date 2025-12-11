import { ShieldAlert, Droplets } from 'lucide-react';
import { FloodEvent } from '../lib/api';

interface AlertPanelProps {
  floodEvents: FloodEvent[];
}

export default function AlertPanel({ floodEvents }: AlertPanelProps) {
  const sortedEvents = [...floodEvents].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-gradient-to-br from-red-50 to-orange-50 border-red-300 text-red-900';
      case 'medium':
        return 'bg-gradient-to-br from-yellow-50 to-amber-50 border-yellow-300 text-yellow-900';
      case 'low':
        return 'bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-300 text-blue-900';
      default:
        return 'bg-gradient-to-br from-slate-50 to-gray-50 border-slate-300 text-slate-900';
    }
  };

  const getSeverityIcon = (severity: string) => {
    const iconClass = severity === 'high' ? 'text-red-600' : severity === 'medium' ? 'text-yellow-600' : 'text-blue-600';
    return <ShieldAlert className={`w-5 h-5 ${iconClass}`} />;
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-gradient-to-r from-red-600 to-orange-600 text-white shadow-lg';
      case 'medium':
        return 'bg-gradient-to-r from-yellow-600 to-amber-600 text-white shadow-lg';
      case 'low':
        return 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg';
      default:
        return 'bg-gradient-to-r from-slate-600 to-gray-600 text-white shadow-lg';
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-slate-200 p-6 h-full overflow-hidden flex flex-col">
      <div className="flex items-center mb-6">
        <div className="relative mr-4">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-xl opacity-20 blur-md"></div>
          <div className="relative p-3 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl shadow-lg">
            <ShieldAlert className="w-6 h-6 text-white" />
          </div>
        </div>
        <div>
          <h2 className="text-2xl font-black text-slate-900">Flood Alerts</h2>
          <p className="text-sm text-slate-600 font-semibold">
            {sortedEvents.length} active alert{sortedEvents.length !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {sortedEvents.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="relative inline-block mb-4">
              <div className="absolute inset-0 bg-blue-500 rounded-full opacity-10 blur-xl"></div>
              <Droplets className="w-16 h-16 text-slate-300 relative" />
            </div>
            <p className="text-slate-500 font-medium">No flood alerts at this time</p>
            <p className="text-xs text-slate-400 mt-1">System monitoring active</p>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {sortedEvents.slice(0, 10).map((event) => (
            <div
              key={event.id}
              className={`group border-2 rounded-xl p-5 transition-all duration-300 hover:shadow-xl hover:scale-[1.02] cursor-pointer ${getSeverityStyles(
                event.severity
              )}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  {getSeverityIcon(event.severity)}
                  <h3 className="font-black text-lg">{event.location}</h3>
                </div>
                <span className={`px-3 py-1.5 rounded-lg text-xs font-black uppercase tracking-wide ${getSeverityBadge(event.severity)}`}>
                  {event.severity}
                </span>
              </div>

              {event.description && (
                <p className="text-sm mb-3 leading-relaxed">
                  <span className="font-bold">Conditions:</span> {event.description}
                </p>
              )}

              {event.rainfall !== undefined && event.rainfall > 0 && (
                <div className="flex items-center gap-2 mb-3">
                  <Droplets className="w-4 h-4" />
                  <span className="text-sm">
                    <span className="font-bold">Rainfall:</span> {event.rainfall.toFixed(1)}mm
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between pt-3 border-t border-current opacity-30">
                <p className="text-xs font-semibold">
                  {new Date(event.timestamp).toLocaleString('en-NG', {
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  })}
                </p>
                <div className="w-2 h-2 rounded-full bg-current animate-pulse"></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {sortedEvents.length > 10 && (
        <div className="mt-6 pt-4 border-t border-slate-200">
          <div className="text-center">
            <p className="text-sm font-bold text-slate-700">
              Showing 10 of {sortedEvents.length} alerts
            </p>
            <div className="w-12 h-1 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-full mx-auto mt-2"></div>
          </div>
        </div>
      )}
    </div>
  );
}
