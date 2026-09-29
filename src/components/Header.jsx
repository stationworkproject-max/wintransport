import React from 'react';
import { 
  Radio, 
  MapPin, 
  AlertTriangle, 
  Train, 
  Bus, 
  Layers,
  Compass,
  Navigation
} from 'lucide-react';
import { TRANSIT_NETWORKS } from '../data/staticTransit';

export default function Header({
  activeNetwork,
  setActiveNetwork,
  liveCount,
  onOpenBroadcast,
  isBroadcasting,
  onOpenReport,
  recentReportCount,
  userLocation,
  onRequestGps,
  gpsStatus,
  onOpenTripPlanner
}) {
  return (
    <header className="sticky top-0 z-[1010] w-full glass-panel border-b border-slate-800/80 px-4 py-3 safe-top-padding pointer-events-auto">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        
        {/* Brand & Live Counter */}
        <div className="flex items-center justify-between w-full md:w-auto gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-red-600 flex items-center justify-center shadow-lg shadow-blue-500/20 text-white font-bold text-lg ring-1 ring-white/20">
              TN
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-bold text-lg tracking-tight text-white flex items-center gap-1.5">
                  WinTransport <span className="text-blue-400 font-extrabold">TN</span>
                </h1>
                <span className="text-xs bg-slate-800/80 text-slate-400 px-2 py-0.5 rounded-full border border-slate-700/60 font-medium">
                  وين الترنسبور
                </span>
              </div>
              <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="text-emerald-400 font-medium">{liveCount} véhicules</span> en direct par la communauté
              </p>
            </div>
          </div>

          {/* Mobile Action Buttons */}
          <div className="flex items-center gap-2 md:hidden">
            <button
              onClick={onOpenBroadcast}
              className={`p-2.5 rounded-xl border flex items-center justify-center transition-all ${
                isBroadcasting
                  ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400 animate-pulse'
                  : 'bg-blue-600 border-blue-500 text-white shadow-md shadow-blue-600/30'
              }`}
              title="Je suis à bord"
            >
              <Radio className="w-4 h-4" />
            </button>
            <button
              onClick={onOpenReport}
              className="p-2.5 rounded-xl bg-slate-800/90 border border-slate-700 text-amber-400 relative"
              title="Signaler un problème"
            >
              <AlertTriangle className="w-4 h-4" />
              {recentReportCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-amber-500 text-slate-950 text-[10px] font-bold rounded-full flex items-center justify-center">
                  {recentReportCount}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Network Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto max-w-full pb-1 md:pb-0 scrollbar-none w-full md:w-auto justify-start md:justify-center">
          {TRANSIT_NETWORKS.map((net) => {
            const isActive = activeNetwork === net.id;
            return (
              <button
                key={net.id}
                onClick={() => setActiveNetwork(net.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 border ${
                  isActive
                    ? 'bg-blue-600 border-blue-500 text-white shadow-md shadow-blue-600/25'
                    : 'bg-slate-800/50 border-slate-700/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <span>{net.name}</span>
              </button>
            );
          })}
        </div>

        {/* Desktop Action Buttons */}
        <div className="hidden md:flex items-center gap-2.5">
          {/* Real Live Community Tracking Status / GPS Indicator */}
          {userLocation ? (
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/60 border border-emerald-500/40 text-xs text-slate-300">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="font-semibold text-white">GPS Précis</span>
              <span className="text-slate-500">•</span>
              <span className="text-emerald-400 font-medium">±{Math.round(userLocation.accuracy || 10)}m</span>
            </div>
          ) : (
            <button
              onClick={onRequestGps}
              className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/50 text-xs text-blue-300 font-semibold transition-all"
              title="Activer la géolocalisation GPS"
            >
              <Navigation className="w-3.5 h-3.5 text-blue-400" />
              <span>Activer mon GPS</span>
            </button>
          )}

          {/* Guide Trajet Button */}
          {onOpenTripPlanner && (
            <button
              onClick={onOpenTripPlanner}
              className="px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-xs font-semibold text-indigo-300 flex items-center gap-1.5 transition-all"
            >
              <Compass className="w-3.5 h-3.5 text-indigo-400" />
              <span>Guide Trajet</span>
            </button>
          )}

          {/* Report Button */}
          <button
            onClick={onOpenReport}
            className="px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-xs font-semibold text-amber-400 flex items-center gap-1.5 transition-all"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Signaler</span>
            {recentReportCount > 0 && (
              <span className="ml-0.5 bg-amber-500 text-slate-950 px-1.5 py-0.2 rounded-full text-[10px] font-bold">
                {recentReportCount}
              </span>
            )}
          </button>

          {/* Passenger On-Board Broadcast Button */}
          <button
            onClick={onOpenBroadcast}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-md ${
              isBroadcasting
                ? 'bg-emerald-500 text-slate-950 shadow-emerald-500/30 animate-pulse'
                : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-blue-500/25 ring-1 ring-white/10'
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            <span>{isBroadcasting ? 'À bord (GPS Actif)' : 'Je suis à bord'}</span>
          </button>
        </div>

      </div>
    </header>
  );
}
