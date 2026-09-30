import React, { useState } from 'react';
import { 
  X, 
  Clock, 
  MapPin, 
  ArrowRight, 
  Radio, 
  Users, 
  CheckCircle, 
  AlertTriangle,
  ChevronRight,
  Navigation
} from 'lucide-react';
import { getStationName, getLineName, getLineShortName, getDirectionLabel } from '../utils/i18n';

function getDistanceKm(lat1, lon1, lat2, lon2) {
  if (!lat1 || !lon1 || !lat2 || !lon2) return 999;
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export default function LineScheduleDrawer({
  line,
  onClose,
  liveLocations,
  onOpenBroadcast,
  onSelectStation,
  crowdReports,
  selectedDirection = 0,
  onDirectionChange,
  language = 'fr'
}) {
  if (!line) return null;

  const activeDir = typeof selectedDirection === 'number' ? selectedDirection : 0;
  const displayedStops = activeDir === 1
    ? ((line.stops_retour && line.stops_retour.length > 0) ? line.stops_retour : [...line.stops].reverse())
    : (line.stops_aller || line.stops);
  const activeDirectionName = getDirectionLabel(line, activeDir, language);

  // Filter ONLY real vehicles currently broadcasting on this line
  const vehiclesOnLine = (liveLocations || []).filter(loc => loc.line_id === line.id);
  const reportsOnLine = (crowdReports || []).filter(r => r.line_id === line.id);

  return (
    <>
      <div 
        className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-[1040] transition-opacity animate-fade-in" 
        onClick={onClose} 
      />
      <div className="fixed inset-y-0 right-0 z-[1050] w-full max-w-md bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col text-slate-100 safe-top-padding safe-bottom-padding pointer-events-auto">
      
      {/* Drawer Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-800/40 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center font-black text-sm text-white shadow-lg"
            style={{ backgroundColor: line.color }}
          >
            {getLineShortName(line, language)}
          </div>
          <div>
            <h2 className="font-bold text-sm text-white leading-tight">{getLineName(line, language)}</h2>
            <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
              <span>{displayedStops.length} {language === 'ar' ? 'محطة' : 'arrêts'}</span>
              <span>•</span>
              {vehiclesOnLine.length > 0 ? (
                <span className="text-emerald-400 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  {vehiclesOnLine.length} {language === 'ar' ? 'مركبة مباشرة' : 'véhicule(s) en direct'}
                </span>
              ) : (
                <span className="text-slate-400">{language === 'ar' ? 'لا توجد إشارة مباشرة' : 'Aucun signal direct'}</span>
              )}
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Direction Switcher */}
      <div className="p-3 bg-slate-950/60 border-b border-slate-800/80">
        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center justify-between">
          <span>{language === 'ar' ? 'اتجاه الخط' : 'Direction du trajet'}</span>
          <span className="text-[11px] font-semibold text-blue-400">
            {language === 'ar' ? (activeDir === 0 ? 'ذهاب' : 'إياب') : (activeDir === 0 ? 'Aller' : 'Retour')}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {line.directions.map((dir, idx) => (
            <button
              key={dir}
              onClick={() => {
                if (onDirectionChange) onDirectionChange(idx);
              }}
              className={`px-3 py-2 rounded-xl text-xs font-bold text-center transition-all flex flex-col items-center justify-center gap-0.5 ${
                activeDir === idx
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30 ring-1 ring-blue-400'
                  : 'bg-slate-800/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <span className="text-[9px] uppercase tracking-wider opacity-75">
                {language === 'ar' ? (idx === 0 ? 'اتجاه الذهاب' : 'اتجاه الإياب') : (idx === 0 ? 'Sens Aller' : 'Sens Retour')}
              </span>
              <span className="truncate max-w-full">{getDirectionLabel(line, idx, language)}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Community Status Banner */}
      {vehiclesOnLine.length === 0 ? (
        <div className="p-3 bg-blue-500/10 border-b border-blue-500/20 flex items-center justify-between text-xs">
          <div className="text-slate-300">
            <strong>{language === 'ar' ? 'لا توجد إشارة مباشرة حالياً' : 'Pas de signal direct en ce moment'}</strong>
            <p className="text-[11px] text-slate-400">
              {language === 'ar' ? 'شارك موقعك إذا كنت على متن وسيلة النقل' : 'Partagez votre position si vous êtes à bord'}
            </p>
          </div>
          <button
            onClick={() => onOpenBroadcast(line.id)}
            className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-bold px-3 py-1.5 rounded-lg shadow flex items-center gap-1.5 whitespace-nowrap"
          >
            <Radio className="w-3.5 h-3.5" />
            {language === 'ar' ? 'أنا على المتن' : 'Je suis à bord'}
          </button>
        </div>
      ) : (
        <div className="p-3 bg-emerald-500/10 border-b border-emerald-500/20 flex items-center justify-between text-xs text-emerald-300">
          <span className="font-semibold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            {language === 'ar'
              ? `${vehiclesOnLine.length} مسافر ينقلون الموقع الفعلي الآن`
              : `${vehiclesOnLine.length} voyageur(s) transmettent la position réelle`}
          </span>
          <span className="text-[10px] bg-emerald-500/20 px-2 py-0.5 rounded-full font-bold">
            GPS Live
          </span>
        </div>
      )}

      {/* Live Community Reports on this line */}
      {reportsOnLine.length > 0 && (
        <div className="p-3 bg-amber-500/10 border-b border-amber-500/20 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs">
            <strong className="text-amber-300">
              {language === 'ar' ? 'تنبيهات المسافرين الحديثة :' : 'Infos voyageurs récentes :'}
            </strong>
            <p className="text-slate-300 mt-0.5">
              {reportsOnLine[0].message || (language === 'ar' ? 'إبلاغ مسافرين بالقرب من الخط' : `Signalement ${reportsOnLine[0].report_type} près de la ligne`)}
            </p>
          </div>
        </div>
      )}

      {/* Vertical Station Progression Timeline */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
          {language === 'ar' ? 'المحطات والمسار' : 'Arrêts et passages'}
        </div>

        <div className="relative pl-6 space-y-3">
          {/* Vertical Connecting Track Line */}
          <div
            className="absolute left-2.5 top-3 bottom-3 w-1 rounded-full opacity-60"
            style={{ backgroundColor: line.color }}
          ></div>

          {displayedStops.map((stop, index) => {
            const isFirst = index === 0;
            const isLast = index === displayedStops.length - 1;
            const stopName = getStationName(stop, language);

            // Find nearest REAL live vehicle to this stop
            const nearest = vehiclesOnLine.reduce((closest, v) => {
              const d = getDistanceKm(v.latitude, v.longitude, stop.lat, stop.lon);
              if (!closest || d < closest.dist) {
                return { vehicle: v, dist: d };
              }
              return closest;
            }, null);

            let liveEtaText = null;
            if (nearest && nearest.dist < 15) {
              const speed = Math.max(nearest.vehicle.speed_kmh || 25, 10);
              const etaMins = Math.max(1, Math.round((nearest.dist / speed) * 60));
              liveEtaText = language === 'ar' 
                ? `🟢 مركبة على بعد ${nearest.dist.toFixed(1)} كم (~${etaMins} دقيقة)`
                : `🟢 Véhicule à ${nearest.dist.toFixed(1)} km (~${etaMins} min)`;
            }

            return (
              <div key={stop.id} className="relative group">
                {/* Station Node Marker */}
                <div
                  className={`absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full border-2 border-slate-900 z-10 transition-transform group-hover:scale-125 ${
                    isFirst || isLast ? 'ring-2 ring-white' : ''
                  }`}
                  style={{ backgroundColor: line.color }}
                ></div>

                {/* Station Card */}
                <div
                  onClick={() => onSelectStation(stop, line)}
                  className="bg-slate-800/40 hover:bg-slate-800/80 border border-slate-700/50 rounded-xl p-3 cursor-pointer transition-all flex items-center justify-between"
                >
                  <div>
                    <div className="font-semibold text-xs text-white group-hover:text-blue-400 transition-colors">
                      {stopName}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1.5">
                      <Clock className="w-3 h-3 text-slate-500" />
                      {liveEtaText ? (
                        <span className="text-emerald-400 font-bold">
                          {liveEtaText}
                        </span>
                      ) : (
                        <span>{language === 'ar' ? 'في انتظار إشارة الـ GPS' : 'En attente de transmission GPS'}</span>
                      )}
                    </div>
                  </div>

                  {liveEtaText && (
                    <div className="flex items-center gap-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold">
                      <span>Live</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer CTA */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/90">
        <button
          onClick={() => onOpenBroadcast(line.id)}
          className="w-full py-2.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl shadow-lg flex items-center justify-center gap-2"
        >
          <Radio className="w-4 h-4" />
          <span>Je monte dans ce bus / métro (Partager mon GPS)</span>
        </button>
      </div>

    </div>
  </>
);
}
