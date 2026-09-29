import React from 'react';
import { Map, List, Radio, AlertTriangle, Compass } from 'lucide-react';

export default function BottomNav({
  activeTab,
  setActiveTab,
  onOpenBroadcast,
  isBroadcasting,
  onOpenReport,
  reportCount,
  onOpenTripPlanner
}) {
  return (
    <nav className="fixed bottom-0 inset-x-0 z-[1010] md:hidden glass-panel border-t border-slate-800/80 px-1.5 py-1.5 flex items-center justify-around safe-bottom-padding pointer-events-auto">
      
      {/* Map Tab */}
      <button
        onClick={() => setActiveTab('map')}
        className={`flex flex-col items-center gap-1 py-1 px-2.5 rounded-xl transition-all ${
          activeTab === 'map' ? 'text-blue-400 font-bold' : 'text-slate-400 hover:text-slate-200'
        }`}
      >
        <Map className="w-5 h-5" />
        <span className="text-[10px]">Carte</span>
      </button>

      {/* Guide Trajet (Smart Trip Planner) */}
      <button
        onClick={onOpenTripPlanner}
        className="flex flex-col items-center gap-1 py-1 px-2.5 rounded-xl text-slate-400 hover:text-blue-300 transition-all group"
      >
        <Compass className="w-5 h-5 text-indigo-400 group-hover:scale-110 transition-transform" />
        <span className="text-[10px] text-indigo-300 font-semibold">Trajet</span>
      </button>

      {/* Passenger Broadcast (Prominent Center Button) */}
      <button
        onClick={onOpenBroadcast}
        className={`flex flex-col items-center gap-1 py-0.5 px-2 rounded-xl transition-all -mt-3 ${
          isBroadcasting
            ? 'text-emerald-400 font-bold animate-pulse'
            : 'text-blue-400 font-bold'
        }`}
      >
        <div className={`p-2.5 rounded-full ring-4 ring-slate-950 shadow-xl ${
          isBroadcasting 
            ? 'bg-emerald-500 text-slate-950 shadow-emerald-500/50' 
            : 'bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-blue-500/40'
        }`}>
          <Radio className="w-5 h-5" />
        </div>
        <span className="text-[10px] font-bold">{isBroadcasting ? 'À bord' : 'Diffuser'}</span>
      </button>

      {/* Lines Tab */}
      <button
        onClick={() => setActiveTab('lines')}
        className={`flex flex-col items-center gap-1 py-1 px-2.5 rounded-xl transition-all ${
          activeTab === 'lines' ? 'text-blue-400 font-bold' : 'text-slate-400 hover:text-slate-200'
        }`}
      >
        <List className="w-5 h-5" />
        <span className="text-[10px]">Lignes</span>
      </button>

      {/* Report Tab */}
      <button
        onClick={onOpenReport}
        className="flex flex-col items-center gap-1 py-1 px-2.5 rounded-xl text-slate-400 hover:text-slate-200 relative"
      >
        <AlertTriangle className="w-5 h-5 text-amber-400" />
        <span className="text-[10px]">Signaler</span>
        {reportCount > 0 && (
          <span className="absolute top-0 right-1.5 w-4 h-4 bg-amber-500 text-slate-950 font-bold text-[9px] rounded-full flex items-center justify-center">
            {reportCount}
          </span>
        )}
      </button>

    </nav>
  );
}
