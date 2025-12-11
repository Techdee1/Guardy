import { Shield, Users, ShieldCheck, Droplets, Bell, TrendingUp, MapPin, Home as HomeIcon, Zap, UsersRound, ArrowRight } from 'lucide-react';
import AlertRegistration from './AlertRegistration';

interface LandingPageProps {
  onRoleSelect: (role: 'citizen' | 'authority') => void;
}


export default function LandingPage({ onRoleSelect }: LandingPageProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50 relative overflow-hidden">
      <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] -z-10"></div>

      <div className="absolute top-20 left-10 w-72 h-72 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
      <div className="absolute top-40 right-10 w-72 h-72 bg-cyan-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
      <div className="absolute -bottom-8 left-1/2 w-72 h-72 bg-teal-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>

      <div className="relative flex-1 flex flex-col items-center px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-16 max-w-4xl">
          <div className="flex items-center justify-center mb-8">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-2xl opacity-20 blur-xl animate-pulse"></div>
              <div className="relative bg-gradient-to-br from-blue-600 to-cyan-600 p-4 rounded-2xl shadow-2xl">
                <ShieldCheck className="w-16 h-16 text-white" />
              </div>
            </div>
          </div>

          <h1 className="text-5xl md:text-7xl font-black mb-6 tracking-tight">
            <span className="bg-gradient-to-r from-blue-600 via-cyan-600 to-teal-600 bg-clip-text text-transparent">
              FloodGuard
            </span>
            <br />
            <span className="text-slate-900">Nigeria</span>
          </h1>

          <p className="text-xl md:text-2xl text-slate-600 mb-8 font-medium leading-relaxed">
            Advanced flood monitoring and emergency response system
            <br />
            <span className="text-lg text-slate-500">Protecting communities with real-time alerts and data-driven insights</span>
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 mb-8">
            <div className="inline-flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-xl text-sm font-bold shadow-lg hover:shadow-xl transition-all">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-white"></span>
              </span>
              Live Monitoring Active
            </div>
            <div className="inline-flex items-center gap-2 px-5 py-3 bg-white text-slate-700 rounded-xl text-sm font-semibold shadow-md border border-slate-200">
              <Bell className="w-4 h-4" />
              SMS & Email Alert System
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 max-w-2xl mx-auto">
            <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 shadow-lg border border-slate-200">
              <Droplets className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-slate-900">24/7</div>
              <div className="text-xs text-slate-600 font-medium">Monitoring</div>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 shadow-lg border border-slate-200">
              <MapPin className="w-8 h-8 text-cyan-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-slate-900">20km</div>
              <div className="text-xs text-slate-600 font-medium">Coverage</div>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 shadow-lg border border-slate-200">
              <TrendingUp className="w-8 h-8 text-teal-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-slate-900">Real-Time</div>
              <div className="text-xs text-slate-600 font-medium">Alerts</div>
            </div>
          </div>
        </div>

        <div className="w-full max-w-6xl mb-20">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-black text-slate-900 mb-4">
              Why <span className="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">FloodGuard</span>?
            </h2>
            <p className="text-lg text-slate-600 font-medium max-w-2xl mx-auto">
              Advanced technology and community-driven insights to keep you safe from flooding
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            <div className="group relative bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-500 border-2 border-blue-100 hover:border-blue-400 overflow-hidden hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-blue-400/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

              <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl group-hover:bg-blue-500/20 transition-all duration-500"></div>

              <div className="relative">
                <div className="mb-6">
                  <div className="relative inline-block">
                    <div className="absolute inset-0 bg-blue-500 rounded-2xl opacity-20 blur-xl group-hover:opacity-30 transition-opacity"></div>
                    <div className="relative p-4 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl shadow-lg group-hover:scale-110 transition-transform duration-300">
                      <HomeIcon className="w-10 h-10 text-white" />
                    </div>
                  </div>
                </div>

                <h3 className="text-2xl font-black text-slate-900 mb-3 group-hover:text-blue-600 transition-colors">
                  Safety First
                </h3>
                <p className="text-slate-600 font-medium leading-relaxed mb-6">
                  Stay ahead of floods and protect your home and family with real-time monitoring and instant alerts.
                </p>

                <div className="flex items-center text-blue-600 font-bold text-sm group-hover:gap-3 gap-2 transition-all">
                  <span>Learn more</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </div>

            <div className="group relative bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-500 border-2 border-orange-100 hover:border-orange-400 overflow-hidden hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 via-amber-400/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

              <div className="absolute top-0 right-0 w-32 h-32 bg-orange-500/10 rounded-full blur-3xl group-hover:bg-orange-500/20 transition-all duration-500"></div>

              <div className="relative">
                <div className="mb-6">
                  <div className="relative inline-block">
                    <div className="absolute inset-0 bg-orange-500 rounded-2xl opacity-20 blur-xl group-hover:opacity-30 transition-opacity"></div>
                    <div className="relative p-4 bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl shadow-lg group-hover:scale-110 transition-transform duration-300">
                      <Zap className="w-10 h-10 text-white" />
                    </div>
                  </div>
                </div>

                <h3 className="text-2xl font-black text-slate-900 mb-3 group-hover:text-orange-600 transition-colors">
                  Predictive Alerts
                </h3>
                <p className="text-slate-600 font-medium leading-relaxed mb-6">
                  Know flood risks before they happen with advanced weather data and AI-powered predictions.
                </p>

                <div className="flex items-center text-orange-600 font-bold text-sm group-hover:gap-3 gap-2 transition-all">
                  <span>Learn more</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </div>

            <div className="group relative bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-500 border-2 border-green-100 hover:border-green-400 overflow-hidden hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 via-emerald-400/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

              <div className="absolute top-0 right-0 w-32 h-32 bg-green-500/10 rounded-full blur-3xl group-hover:bg-green-500/20 transition-all duration-500"></div>

              <div className="relative">
                <div className="mb-6">
                  <div className="relative inline-block">
                    <div className="absolute inset-0 bg-green-500 rounded-2xl opacity-20 blur-xl group-hover:opacity-30 transition-opacity"></div>
                    <div className="relative p-4 bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl shadow-lg group-hover:scale-110 transition-transform duration-300">
                      <UsersRound className="w-10 h-10 text-white" />
                    </div>
                  </div>
                </div>

                <h3 className="text-2xl font-black text-slate-900 mb-3 group-hover:text-green-600 transition-colors">
                  Community Ready
                </h3>
                <p className="text-slate-600 font-medium leading-relaxed mb-6">
                  Share info, stay informed, and keep everyone safe with community-driven flood reporting.
                </p>

                <div className="flex items-center text-green-600 font-bold text-sm group-hover:gap-3 gap-2 transition-all">
                  <span>Learn more</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </div>
          </div>

          <div className="text-center">
            <button
              onClick={() => onRoleSelect('citizen')}
              className="group inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-blue-600 via-cyan-600 to-teal-600 text-white rounded-xl font-black text-lg shadow-2xl hover:shadow-3xl transition-all duration-300 hover:scale-105"
            >
              <span>Get Started Now</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-2 transition-transform" />
            </button>
            <p className="text-sm text-slate-500 mt-4 font-medium">
              Join thousands of Nigerians staying safe from floods
            </p>
          </div>
        </div>

        <div className="w-full max-w-5xl mb-16">
          <AlertRegistration />
        </div>

        <div className="w-full max-w-5xl mb-12">
          <h2 className="text-3xl font-bold text-center mb-10 text-slate-900">
            Choose Your Access Level
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <button
              onClick={() => onRoleSelect('citizen')}
              className="group relative text-left bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 border-2 border-transparent hover:border-blue-500 overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

              <div className="relative">
                <div className="flex items-center gap-4 mb-6">
                  <div className="p-4 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <Users className="w-10 h-10 text-white" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-slate-900 mb-1">
                      Citizen Portal
                    </h3>
                    <div className="text-sm text-blue-600 font-semibold">For Community Members</div>
                  </div>
                </div>

                <ul className="space-y-3 mb-6 text-slate-600">
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-2 flex-shrink-0"></div>
                    <span>Report flood emergencies and request assistance</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-2 flex-shrink-0"></div>
                    <span>Monitor flood risks in your area with live updates</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-2 flex-shrink-0"></div>
                    <span>Receive instant Email alerts for nearby floods</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-2 flex-shrink-0"></div>
                    <span>Locate nearby emergency centers and shelters</span>
                  </li>
                </ul>

                <div className="flex items-center justify-between">
                  <div className="text-sm font-bold text-blue-600 group-hover:translate-x-2 transition-transform duration-300">
                    Enter Citizen Portal →
                  </div>
                  <div className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-bold">
                    Public Access
                  </div>
                </div>
              </div>
            </button>

            <button
              onClick={() => onRoleSelect('authority')}
              className="group relative text-left bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 border-2 border-transparent hover:border-orange-500 overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-orange-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

              <div className="relative">
                <div className="flex items-center gap-4 mb-6">
                  <div className="p-4 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <Shield className="w-10 h-10 text-white" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-slate-900 mb-1">
                      Authority Dashboard
                    </h3>
                    <div className="text-sm text-orange-600 font-semibold">For Emergency Response</div>
                  </div>
                </div>

                <ul className="space-y-3 mb-6 text-slate-600">
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-2 flex-shrink-0"></div>
                    <span>Monitor all flood events across Nigeria in real-time</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-2 flex-shrink-0"></div>
                    <span>Manage emergency reports and coordinate responses</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-2 flex-shrink-0"></div>
                    <span>Broadcast Email alerts to affected communities</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-2 flex-shrink-0"></div>
                    <span>Access weather data and flood risk analytics</span>
                  </li>
                </ul>

                <div className="flex items-center justify-between">
                  <div className="text-sm font-bold text-orange-600 group-hover:translate-x-2 transition-transform duration-300">
                    Enter Authority Dashboard →
                  </div>
                  <div className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-bold">
                    Admin Access
                  </div>
                </div>
              </div>
            </button>
          </div>
        </div>

        <div className="text-center max-w-3xl">
          <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-slate-200">
            <p className="text-sm text-slate-600 font-medium mb-2">Powered by cutting-edge technology</p>
            <div className="flex flex-wrap items-center justify-center gap-3 text-xs text-slate-500">
              <span className="px-3 py-1 bg-white rounded-full font-semibold">OpenWeatherMap API</span>
              <span className="px-3 py-1 bg-white rounded-full font-semibold">Open-Meteo Flood Data</span>
              <span className="px-3 py-1 bg-white rounded-full font-semibold">Email Support</span>
              <span className="px-3 py-1 bg-white rounded-full font-semibold">Supabase Backend</span>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes blob {
          0%, 100% { transform: translate(0, 0) scale(1); }
          25% { transform: translate(20px, -50px) scale(1.1); }
          50% { transform: translate(-20px, 20px) scale(0.9); }
          75% { transform: translate(50px, 50px) scale(1.05); }
        }
        .animate-blob {
          animation: blob 20s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
}
