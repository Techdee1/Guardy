import { useState } from 'react';
import { Shield, Filter, CheckCircle, Clock, XCircle, BarChart3, Volume2 } from 'lucide-react';
import { EmergencyReport, api } from '../lib/api';

interface AdminPanelProps {
  reports: EmergencyReport[];
  onUpdate: () => void;
}

export default function AdminPanel({ reports, onUpdate }: AdminPanelProps) {
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');

  const filteredReports = reports.filter((report) => {
    const matchesStatus = filterStatus === 'all' || report.status === filterStatus;
    const matchesType = filterType === 'all' || report.type_of_need === filterType;
    return matchesStatus && matchesType;
  });

  const sortedReports = [...filteredReports].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  const handleStatusUpdate = async (reportId: string, newStatus: string) => {
    try {
      await api.updateReportStatus(reportId, newStatus);
      onUpdate();
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'resolved':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800 border border-green-300">
            <CheckCircle className="w-3 h-3 mr-1" />
            Resolved
          </span>
        );
      case 'responded':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-300">
            <Clock className="w-3 h-3 mr-1" />
            Responded
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800 border border-yellow-300">
            <XCircle className="w-3 h-3 mr-1" />
            Pending
          </span>
        );
    }
  };

  const getTypeBadge = (type: string) => {
    const colors = {
      Food: 'bg-orange-100 text-orange-800 border-orange-300',
      Water: 'bg-blue-100 text-blue-800 border-blue-300',
      Medicine: 'bg-red-100 text-red-800 border-red-300',
      Shelter: 'bg-green-100 text-green-800 border-green-300',
    };
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded text-xs font-semibold border ${
          colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800 border-gray-300'
        }`}
      >
        {type}
      </span>
    );
  };

  const stats = {
    total: reports.length,
    pending: reports.filter((r) => r.status === 'pending').length,
    responded: reports.filter((r) => r.status === 'responded').length,
    resolved: reports.filter((r) => r.status === 'resolved').length,
  };

  const clearFilters = () => {
    setFilterStatus('all');
    setFilterType('all');
  };

  const hasActiveFilters = filterStatus !== 'all' || filterType !== 'all';

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
      <div className="flex items-center mb-6">
        <div className="p-2 bg-purple-100 rounded-lg mr-3">
          <Shield className="w-6 h-6 text-purple-600" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Authority Dashboard</h2>
          <p className="text-sm text-gray-600">Manage emergency reports</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4">
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm text-gray-600 font-medium">Total Reports</p>
            <BarChart3 className="w-4 h-4 text-gray-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
        </div>
        <div className="bg-yellow-50 border-2 border-yellow-300 rounded-lg p-4">
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm text-yellow-700 font-medium">Pending</p>
            <XCircle className="w-4 h-4 text-yellow-600" />
          </div>
          <p className="text-3xl font-bold text-yellow-900">{stats.pending}</p>
        </div>
        <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-4">
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm text-blue-700 font-medium">Responded</p>
            <Clock className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-3xl font-bold text-blue-900">{stats.responded}</p>
        </div>
        <div className="bg-green-50 border-2 border-green-300 rounded-lg p-4">
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm text-green-700 font-medium">Resolved</p>
            <CheckCircle className="w-4 h-4 text-green-600" />
          </div>
          <p className="text-3xl font-bold text-green-900">{stats.resolved}</p>
        </div>
      </div>

      <div className="bg-gray-50 rounded-lg border border-gray-300 p-4 mb-6">
        <div className="flex flex-wrap items-center gap-3 mb-3">
          <div className="flex items-center">
            <Filter className="w-5 h-5 text-gray-700 mr-2" />
            <span className="text-sm font-bold text-gray-900">Filter Reports</span>
          </div>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="ml-auto px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 rounded-lg transition-colors"
            >
              Clear Filters
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-3 py-2 bg-white border-2 border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="responded">Responded</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Type of Need</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full px-3 py-2 bg-white border-2 border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
            >
              <option value="all">All Types</option>
              <option value="Food">Food</option>
              <option value="Water">Water</option>
              <option value="Medicine">Medicine</option>
              <option value="Shelter">Shelter</option>
            </select>
          </div>
        </div>

        <div className="mt-3 text-xs text-gray-600">
          Showing <span className="font-bold text-gray-900">{sortedReports.length}</span> of{' '}
          <span className="font-bold text-gray-900">{reports.length}</span> reports
        </div>
      </div>

      <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
        {sortedReports.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
            <Filter className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600 font-medium">No reports match the selected filters</p>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="mt-3 px-4 py-2 text-sm font-medium text-blue-700 hover:text-blue-800 underline"
              >
                Clear all filters
              </button>
            )}
          </div>
        ) : (
          sortedReports.map((report) => (
            <div key={report.id} className="bg-white border-2 border-gray-200 rounded-lg p-5 hover:shadow-lg transition-all">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-bold text-lg text-gray-900">{report.name}</h3>
                  <p className="text-sm text-gray-600">
                    {new Date(report.timestamp).toLocaleString('en-NG', {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })}
                  </p>
                </div>
                {getStatusBadge(report.status)}
              </div>

              <div className="mb-3">
                <p className="text-xs font-medium text-gray-600 mb-1">Type of Need</p>
                {getTypeBadge(report.type_of_need)}
              </div>

              <div className="mb-3 p-3 bg-blue-50 border-l-4 border-blue-500 rounded">
                <p className="text-xs font-medium text-blue-900 mb-1">Location</p>
                {report.location_name ? (
                  <>
                    <p className="text-sm font-semibold text-blue-900 mb-1">
                      {report.location_name}
                    </p>
                    <p className="text-xs font-mono text-blue-700">
                      {report.latitude.toFixed(4)}, {report.longitude.toFixed(4)}
                    </p>
                  </>
                ) : (
                  <p className="text-sm font-mono text-blue-900">
                    {report.latitude.toFixed(4)}, {report.longitude.toFixed(4)}
                  </p>
                )}
              </div>

              {report.comments && (
                <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-xs font-medium text-gray-600 mb-1">Comments</p>
                  <p className="text-sm text-gray-900">{report.comments}</p>
                </div>
              )}

              {report.voice_recording_url && (
                <div className="mb-4 p-4 bg-blue-50 rounded-lg border-2 border-blue-300">
                  <div className="flex items-center mb-2">
                    <Volume2 className="w-4 h-4 text-blue-700 mr-2" />
                    <p className="text-xs font-bold text-blue-900">Voice Recording</p>
                  </div>
                  <audio
                    src={report.voice_recording_url}
                    controls
                    className="w-full"
                    preload="metadata"
                  />
                </div>
              )}

              {report.status !== 'resolved' && (
                <div className="flex gap-2 pt-3 border-t border-gray-200">
                  {report.status === 'pending' && (
                    <button
                      onClick={() => handleStatusUpdate(report.id!, 'responded')}
                      className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Mark as Responded
                    </button>
                  )}
                  <button
                    onClick={() => handleStatusUpdate(report.id!, 'resolved')}
                    className="flex-1 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Mark as Resolved
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
