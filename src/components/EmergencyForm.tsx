import { useState, useEffect, useRef } from 'react';
import { AlertCircle, MapPin, Send, Mic, MicOff, CheckCircle, Square } from 'lucide-react';
import { api, EmergencyReport } from '../lib/api';
import { supabase } from '../lib/supabase';

interface EmergencyFormProps {
  onSubmitSuccess: () => void;
}

export default function EmergencyForm({ onSubmitSuccess }: EmergencyFormProps) {
  const [formData, setFormData] = useState({
    name: '',
    type_of_need: 'Food' as 'Food' | 'Water' | 'Medicine' | 'Shelter',
    comments: '',
  });
  const [location, setLocation] = useState<{ latitude: number; longitude: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [gettingLocation, setGettingLocation] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string>('');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    getLocation();
  }, []);

  const getLocation = () => {
    setGettingLocation(true);
    setError('');

    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      setGettingLocation(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        setGettingLocation(false);
        setSuccess('Location detected automatically!');
        setTimeout(() => setSuccess(''), 3000);
      },
      (error) => {
        setError(`Could not detect location: ${error.message}`);
        setGettingLocation(false);
      }
    );
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(audioBlob);
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setError('');
    } catch (err) {
      setError('Microphone access denied. Please allow microphone access.');
      console.error('Recording error:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const clearRecording = () => {
    setAudioBlob(null);
    setAudioUrl('');
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!location) {
      setError('Please wait for location detection or manually detect location');
      return;
    }

    if (!formData.name.trim()) {
      setError('Please enter your name');
      return;
    }

    setLoading(true);

    try {
      const report: EmergencyReport = {
        ...formData,
        ...location,
        timestamp: new Date().toISOString(),
      };

      let voiceRecordingUrl = '';

      if (audioBlob) {
        const fileName = `voice-recordings/${Date.now()}-${Math.random().toString(36).substring(7)}.webm`;

        const { data: uploadData, error: uploadError } = await supabase.storage
          .from('emergency-assets')
          .upload(fileName, audioBlob, {
            contentType: 'audio/webm',
            cacheControl: '3600',
          });

        if (uploadError) {
          console.error('Upload error:', uploadError);
          throw uploadError;
        }

        const { data: urlData } = supabase.storage
          .from('emergency-assets')
          .getPublicUrl(fileName);

        voiceRecordingUrl = urlData.publicUrl;
        report.voice_recording_url = voiceRecordingUrl;
      }

      const result = await api.createEmergencyReport(report);
      setSuccess(
        `Emergency report submitted! ${result.nearbyCenters.length} nearby centers have been notified.`
      );
      setFormData({ name: '', type_of_need: 'Food', comments: '' });
      setLocation(null);
      clearRecording();
      onSubmitSuccess();

      setTimeout(() => {
        setSuccess('');
        getLocation();
      }, 5000);
    } catch (err) {
      setError('Failed to submit report. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
      <div className="flex items-center mb-6">
        <div className="p-2 bg-red-100 rounded-lg mr-3">
          <AlertCircle className="w-6 h-6 text-red-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-900">Emergency Report</h2>
          <p className="text-sm text-gray-600">Submit by form or voice</p>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-500 rounded text-red-800 text-sm flex items-start">
          <AlertCircle className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border-l-4 border-green-500 rounded text-green-800 text-sm flex items-start">
          <CheckCircle className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your Name
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
            placeholder="Enter your name"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Type of Emergency
          </label>
          <select
            value={formData.type_of_need}
            onChange={(e) =>
              setFormData({
                ...formData,
                type_of_need: e.target.value as 'Food' | 'Water' | 'Medicine' | 'Shelter',
              })
            }
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
          >
            <option value="Rising water level/ Imminent flood">Rising water level/ Imminent flood</option>
            <option value="Area already flooded">Area already flooded</option>
            <option value="Trapped Individuals">Trapped Individuals</option>
            <option value="Shelter">Injuries / Medical Emergency</option>
            <option value="Need clean water">Need clean water</option>
            <option value="Need food supplies">Need food supplies</option>
            <option value="Need medicine">Need medicine</option>
            <option value="Power outage">Power outage</option>
            <option value="Road blocked">Road blocked</option>
            <option value="Building damage / collapse risk">Building damage / collapse risk</option>
            <option value="Communication problem">Communication problem</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Additional Comments
          </label>
          <textarea
            value={formData.comments}
            onChange={(e) => setFormData({ ...formData, comments: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
            placeholder="Describe your situation..."
            rows={3}
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Voice Recording (Optional)
            </label>
            {audioBlob && (
              <button
                type="button"
                onClick={clearRecording}
                className="text-xs text-red-600 hover:text-red-800 font-medium"
              >
                Clear Recording
              </button>
            )}
          </div>

          {!audioBlob ? (
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              className={`w-full flex items-center justify-center px-4 py-3 rounded-lg font-medium transition-colors ${
                isRecording
                  ? 'bg-red-600 text-white hover:bg-red-700'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isRecording ? (
                <>
                  <Square className="w-5 h-5 mr-2" />
                  Stop Recording
                </>
              ) : (
                <>
                  <Mic className="w-5 h-5 mr-2" />
                  Start Voice Recording
                </>
              )}
            </button>
          ) : (
            <div className="bg-green-50 border-2 border-green-500 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-green-800">Recording saved</span>
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <audio src={audioUrl} controls className="w-full" />
            </div>
          )}

          {isRecording && (
            <div className="flex items-center mt-2 text-red-600 text-sm">
              <div className="w-2 h-2 bg-red-600 rounded-full mr-2 animate-pulse"></div>
              Recording... Speak clearly
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Location {location && '(Auto-detected)'}
          </label>
          <button
            type="button"
            onClick={getLocation}
            disabled={gettingLocation}
            className={`w-full flex items-center justify-center px-4 py-3 rounded-lg font-medium transition-colors ${
              location
                ? 'bg-green-50 border-2 border-green-500 text-green-700'
                : 'bg-blue-50 border-2 border-blue-300 text-blue-700 hover:bg-blue-100'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {location ? (
              <>
                <CheckCircle className="w-5 h-5 mr-2" />
                Location Detected
              </>
            ) : (
              <>
                <MapPin className="w-5 h-5 mr-2" />
                {gettingLocation ? 'Detecting Location...' : 'Refresh Location'}
              </>
            )}
          </button>
          {location && (
            <p className="text-xs text-gray-500 mt-1 text-center">
              {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={loading || !location}
          className="w-full bg-red-600 text-white flex items-center justify-center px-6 py-3 font-semibold rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-5 h-5 mr-2" />
          {loading ? 'Submitting...' : 'Submit Emergency Report'}
        </button>
      </form>
    </div>
  );
}
