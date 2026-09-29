import React, { useState } from 'react';
import { Search, ChevronRight, Clock, MapPin, Radio } from 'lucide-react';
import { STATIC_LINES } from '../data/staticTransit';

export default function LinesListView({
  activeNetwork,
  liveLocations,
  onSelectLine
}) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredLines = STATIC_LINES.filter(line => {
    if (activeNetwork !== 'all' && line.type_id !== activeNetwork) return false;
    if (!searchQuery.trim()) return true;

    const q = searchQuery.toLowerCase();
    const matchName = line.short_name.toLowerCase().includes(q) || line.long_name.toLowerCase().includes(q);
    const matchStop = line.stops.some(s => s.name.toLowerCase().includes(q));
    return matchName || matchStop;
  });

  return (
    <div className="w-full max-w-xl mx-auto p-4 space-y-3">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Rechercher une ligne ou un arrêt (ex : 1, TGM, Barcelone...)"
          className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Lines Grid */}
      <div className="space-y-2">
        {filteredLines.map(line => {
          const liveVehiclesCount = liveLocations.filter(loc => loc.line_id === line.id).length;

          return (
            <div
              key={line.id}
              onClick={() => onSelectLine(line)}
              className="bg-slate-800/40 hover:bg-slate-800/80 border border-slate-700/60 rounded-xl p-3 cursor-pointer transition-all flex items-center justify-between group"
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-black text-sm shadow-md flex-shrink-0"
                  style={{ backgroundColor: line.color }}
                >
                  {line.short_name}
                </div>
                <div>
                  <div className="font-bold text-xs text-white group-hover:text-blue-400 transition-colors">
                    {line.long_name}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-2">
                    <span>{line.stops.length} arrêts</span>
                    <span>•</span>
                    <span>Toutes les ~{line.frequency_mins || 10} min</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {liveVehiclesCount > 0 && (
                  <div className="flex items-center gap-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span>{liveVehiclesCount} en direct</span>
                  </div>
                )}
                <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-blue-400 transition-colors" />
              </div>
            </div>
          );
        })}

        {filteredLines.length === 0 && (
          <div className="text-center py-10 text-slate-400 text-xs">
            Aucune ligne ne correspond à votre recherche.
          </div>
        )}
      </div>
    </div>
  );
}
