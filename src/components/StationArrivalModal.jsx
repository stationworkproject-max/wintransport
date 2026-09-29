import React from 'react';
import { X, MapPin, Clock, Radio, Navigation, Users, AlertCircle, Compass } from 'lucide-react';

function getDistanceKm(lat1, lon1, lat2, lon2) {
  if (!lat1 || !lon1 || !lat2 || !lon2) return 999;
  const R = 6371; // Earth radius km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export default function StationArrivalModal({
  station,
  line,
  onClose,
  liveLocations,
  onOpenBroadcast
}) {
  if (!station) return null;

  // Filter ONLY real vehicles currently broadcasting on this line
  const vehiclesOnLine = (liveLocations || []).filter(loc => {
    if (line) return loc.line_id === line.id;
    return true;
  });

  // Calculate real ETAs based on actual GPS distance and speed
  const realArrivals = vehiclesOnLine
    .map(v => {
      const distKm = getDistanceKm(v.latitude, v.longitude, station.lat, station.lon);
      const speedKmh = Math.max(v.speed_kmh || 25, 10);
      const etaMins = Math.max(1, Math.round((distKm / speedKmh) * 60));

      return {
        id: v.id,
        lineShort: line?.short_name || 'Direct',
        lineColor: line?.color || '#0071e3',
        direction: v.direction || line?.directions?.[0] || 'En route',
        distanceKm: distKm.toFixed(1),
        etaMins: etaMins,
        isLive: true,
        passengers: v.passenger_count || 1,
        speedKmh: v.speed_kmh || 25,
        vehicleLabel: v.vehicle_label || 'Véhicule en direct'
      };
    })
    .sort((a, b) => a.etaMins - b.etaMins);

  return (
    <div 
      className="fixed inset-0 z-[1060] flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fade-in pointer-events-auto"
      onClick={onClose}
    >
      <div 
        className="w-full max-w-sm bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden text-slate-100"
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* Header */}
        <div className="p-4 border-b border-slate-800 bg-slate-800/40 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center text-white font-bold text-xs shadow-md"
              style={{ backgroundColor: line?.color || '#0071e3' }}
            >
              {line?.short_name || <MapPin className="w-4 h-4" />}
            </div>
            <div>
              <h3 className="font-bold text-sm text-white">{station.name}</h3>
              <p className="text-[11px] text-slate-400">
                {line ? `${line.short_name} • ${line.long_name}` : 'Arrêt de transport'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Departures Content */}
        <div className="p-4 space-y-3">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
            <span>Passages en temps réel</span>
            <span className="text-emerald-400 font-medium text-[10px] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
              GPS Direct
            </span>
          </div>

          {realArrivals.length > 0 ? (
            <div className="space-y-2">
              {realArrivals.map((arr) => (
                <div
                  key={arr.id}
                  className="bg-slate-800/60 border border-emerald-500/40 rounded-xl p-3 flex items-center justify-between"
                >
                  <div className="flex items-center gap-2.5">
                    <span
                      className="px-2 py-0.5 rounded text-xs font-bold text-white shadow-sm"
                      style={{ backgroundColor: arr.lineColor }}
                    >
                      {arr.lineShort}
                    </span>
                    <div>
                      <div className="font-semibold text-xs text-white">Vers {arr.direction}</div>
                      <div className="text-[10px] text-emerald-400 font-bold flex items-center gap-1.5 mt-0.5">
                        <span>🟢 GPS Actif</span>
                        <span>•</span>
                        <span>{arr.distanceKm} km ({arr.speedKmh} km/h)</span>
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="font-black text-sm text-emerald-400">
                      ~{arr.etaMins} min
                    </div>
                    <div className="text-[10px] text-slate-400">
                      {arr.etaMins <= 2 ? 'En approche immédiate' : 'Temps réel'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-slate-800/30 border border-slate-800 rounded-xl p-4 text-center space-y-2.5">
              <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-slate-400">
                <Radio className="w-4 h-4 text-slate-500" />
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-300">
                  Aucun véhicule ne transmet en ce moment
                </p>
                <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                  Le suivi en direct repose sur les passagers à bord. Dès qu'un usager monte et active son GPS, sa position réelle s'affiche ici.
                </p>
              </div>
            </div>
          )}

          {/* Quick CTA to Broadcast */}
          <button
            onClick={() => {
              onClose();
              if (onOpenBroadcast && line) onOpenBroadcast(line.id);
            }}
            className="w-full mt-2 py-2.5 px-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl shadow-lg flex items-center justify-center gap-2"
          >
            <Radio className="w-3.5 h-3.5" />
            <span>Je suis dans ce véhicule (Diffuser ma position)</span>
          </button>
        </div>

      </div>
    </div>
  );
}
