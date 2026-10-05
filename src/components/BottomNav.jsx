import React from 'react';
import { Map, List, Radio, AlertTriangle, Compass } from 'lucide-react';

export default function BottomNav({
  activeTab,
  setActiveTab,
  onOpenBroadcast,
  isBroadcasting,
  onOpenReport,
  reportCount,
  onOpenTripPlanner,
  language = 'fr',
  theme = 'dark'
}) {
  const isLight = theme === 'light';

  return (
    <nav className={`fixed bottom-0 inset-x-0 z-[1010] md:hidden glass-panel safe-bottom-padding px-1.5 py-1.5 flex items-center justify-around pointer-events-auto transition-colors ${
      isLight ? 'border-t border-slate-200/90 shadow-lg' : 'border-t border-slate-800/80'
    }`}>
      
      {/* Map Tab */}
      <button
        onClick={() => setActiveTab('map')}
        className={`flex flex-col items-center gap-1 py-1 px-2.5 rounded-xl transition-all ${
          activeTab === 'map'
            ? (isLight ? 'text-blue-600 font-bold' : 'text-blue-400 font-bold')
            : (isLight ? 'text-slate-500 hover:text-slate-800' : 'text-slate-400 hover:text-slate-200')
        }`}
      >
        <Map className="w-5 h-5" />
        <span className="text-[10px]">{language === 'ar' ? 'الخريطة' : 'Carte'}</span>
      </button>

      {/* Guide Trajet (Smart Trip Planner) */}
      <button
        onClick={onOpenTripPlanner}
        className={`flex flex-col items-center gap-1 py-1 px-2.5 rounded-xl transition-all group ${
          isLight ? 'text-slate-500 hover:text-indigo-600' : 'text-slate-400 hover:text-blue-300'
        }`}
      >
        <Compass className={`w-5 h-5 group-hover:scale-110 transition-transform ${isLight ? 'text-indigo-600' : 'text-indigo-400'}`} />
        <span className={`text-[10px] font-semibold ${isLight ? 'text-indigo-600' : 'text-indigo-300'}`}>{language === 'ar' ? 'مسار' : 'Trajet'}</span>
      </button>

      {/* Passenger Broadcast (Prominent Center Button) */}
      <button
        onClick={onOpenBroadcast}
        className={`flex flex-col items-center gap-1 py-0.5 px-2 rounded-xl transition-all -mt-3 ${
          isBroadcasting
            ? (isLight ? 'text-emerald-600 font-bold animate-pulse' : 'text-emerald-400 font-bold animate-pulse')
            : (isLight ? 'text-blue-600 font-bold' : 'text-blue-400 font-bold')
        }`}
      >
        <div className={`p-2.5 rounded-full ring-4 shadow-xl ${
          isLight ? 'ring-slate-100 shadow-md' : 'ring-slate-950 shadow-xl'
        } ${
          isBroadcasting 
            ? 'bg-emerald-500 text-slate-950 shadow-emerald-500/50' 
            : 'bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-blue-500/40'
        }`}>
          <Radio className="w-5 h-5" />
        </div>
        <span className="text-[10px] font-bold">
          {isBroadcasting ? (language === 'ar' ? 'على المتن' : 'À bord') : (language === 'ar' ? 'بث GPS' : 'Diffuser')}
        </span>
      </button>

      {/* Lines Tab */}
      <button
        onClick={() => setActiveTab('lines')}
        className={`flex flex-col items-center gap-1 py-1 px-2.5 rounded-xl transition-all ${
          activeTab === 'lines'
            ? (isLight ? 'text-blue-600 font-bold' : 'text-blue-400 font-bold')
            : (isLight ? 'text-slate-500 hover:text-slate-800' : 'text-slate-400 hover:text-slate-200')
        }`}
      >
        <List className="w-5 h-5" />
        <span className="text-[10px]">{language === 'ar' ? 'الخطوط' : 'Lignes'}</span>
      </button>

      {/* Report Tab */}
      <button
        onClick={onOpenReport}
        className={`flex flex-col items-center gap-1 py-1 px-2.5 rounded-xl relative transition-all ${
          isLight ? 'text-slate-500 hover:text-slate-800' : 'text-slate-400 hover:text-slate-200'
        }`}
      >
        <AlertTriangle className={`w-5 h-5 ${isLight ? 'text-amber-500' : 'text-amber-400'}`} />
        <span className="text-[10px]">{language === 'ar' ? 'إبلاغ' : 'Signaler'}</span>
        {reportCount > 0 && (
          <span className="absolute top-0 right-1.5 w-4 h-4 bg-amber-500 text-slate-950 font-bold text-[9px] rounded-full flex items-center justify-center">
            {reportCount}
          </span>
        )}
      </button>

    </nav>
  );
}

