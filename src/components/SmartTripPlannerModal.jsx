import React, { useState, useMemo } from 'react';
import { 
  Compass, 
  MapPin, 
  X, 
  Search, 
  ArrowRight, 
  Radio, 
  Navigation, 
  Clock, 
  Footprints,
  CheckCircle2,
  ChevronRight,
  Sparkles,
  Building,
  Target
} from 'lucide-react';
import { STATIC_LINES } from '../data/staticTransit';
import { getStationName, getLineName, getLineShortName } from '../utils/i18n';

function getDistanceMeters(lat1, lon1, lat2, lon2) {
  if (!lat1 || !lon1 || !lat2 || !lon2) return 999999;
  const R = 6371e3; // Earth radius in meters
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

// Popular destinations, key districts, and landmarks across Greater Tunis
export const POPULAR_LANDMARKS = [
  { name: "Avenue Habib Bourguiba", detail: "Centre-Ville Tunis", category: "Centre-Ville", lat: 36.7997, lon: 10.1800, icon: "🏙️" },
  { name: "Place de Barcelone", detail: "Gare Centrale & Métros", category: "Gares", lat: 36.7950, lon: 10.1800, icon: "🚉" },
  { name: "Tunis Marine", detail: "Terminus TGM & Bus Banlieue", category: "Gares", lat: 36.8010, lon: 10.1920, icon: "🚆" },
  { name: "Les Berges du Lac 1", detail: "Zone d'Affaires", category: "Affaires", lat: 36.8320, lon: 10.2350, icon: "🌊" },
  { name: "Les Berges du Lac 2", detail: "Ambassades & Bureaux", category: "Affaires", lat: 36.8450, lon: 10.2750, icon: "🏢" },
  { name: "Aéroport Tunis-Carthage", detail: "Terminal Principal", category: "Transport", lat: 36.8510, lon: 10.2272, icon: "✈️" },
  { name: "La Marsa Plage", detail: "Corniche & Plage", category: "Banlieue Nord", lat: 36.8785, lon: 10.3235, icon: "🏖️" },
  { name: "Sidi Bou Saïd", detail: "Village & Café des Délices", category: "Banlieue Nord", lat: 36.8710, lon: 10.3415, icon: "🏛️" },
  { name: "Carthage Amphi & Musée", detail: "Site Archéologique", category: "Banlieue Nord", lat: 36.8540, lon: 10.3290, icon: "🏛️" },
  { name: "Le Bardo & Musée National", detail: "Musée & Parlement", category: "Culture", lat: 36.8090, lon: 10.1340, icon: "🏛️" },
  { name: "Campus Univ. El Manar", detail: "Facultés des Sciences & Médecine", category: "Universités", lat: 36.8335, lon: 10.1470, icon: "🎓" },
  { name: "Campus Univ. La Manouba", detail: "Lettres, FLAHM & ISCAE", category: "Universités", lat: 36.8120, lon: 10.0880, icon: "🎓" },
  { name: "Ariana Centre", detail: "Centre-Ville Ariana", category: "Banlieue", lat: 36.8620, lon: 10.1950, icon: "📍" },
  { name: "Ben Arous Centre", detail: "Centre Gouvernorat", category: "Banlieue Sud", lat: 36.7530, lon: 10.2220, icon: "📍" },
  { name: "Radès Ville & Stade", detail: "Cité Sportive", category: "Banlieue Sud", lat: 36.7680, lon: 10.2800, icon: "🏟️" },
  { name: "Hammam-Lif", detail: "Banlieue Sud & Plage", category: "Banlieue Sud", lat: 36.7290, lon: 10.3390, icon: "📍" },
];

export default function SmartTripPlannerModal({
  isOpen,
  onClose,
  userLocation,
  onRequestGps,
  onSelectLineAndStation,
  onShowItinerary,
  liveLocations,
  language = 'fr'
}) {
  const [destinationQuery, setDestinationQuery] = useState('');
  const [targetDestination, setTargetDestination] = useState(null);

  // Extract all unique stations with their associated lines
  const allStations = useMemo(() => {
    const stationMap = new Map();
    STATIC_LINES.forEach(line => {
      line.stops.forEach((stop, index) => {
        if (!stationMap.has(stop.name)) {
          stationMap.set(stop.name, {
            name: stop.name,
            name_fr: stop.name_fr || stop.name,
            name_ar: stop.name_ar || stop.name,
            lat: stop.lat,
            lon: stop.lon,
            lines: []
          });
        }
        const st = stationMap.get(stop.name);
        if (!st.lines.some(l => l.id === line.id)) {
          st.lines.push({
            id: line.id,
            short_name: line.short_name,
            short_name_ar: line.short_name_ar,
            long_name: line.long_name,
            long_name_fr: line.long_name_fr,
            long_name_ar: line.long_name_ar,
            color: line.color,
            type_id: line.type_id,
            stopIndex: index,
            stops: line.stops
          });
        }
      });
    });
    return Array.from(stationMap.values());
  }, []);

  // Nearest stations to user GPS
  const nearestStations = useMemo(() => {
    if (!userLocation) return [];
    return allStations
      .map(st => ({
        ...st,
        distanceMeters: getDistanceMeters(userLocation.lat, userLocation.lon, st.lat, st.lon)
      }))
      .sort((a, b) => a.distanceMeters - b.distanceMeters)
      .slice(0, 5);
  }, [userLocation, allStations]);

  // Autocomplete destination results (Matches both stations and popular places)
  const destinationResults = useMemo(() => {
    if (!destinationQuery.trim()) return [];
    const q = destinationQuery.toLowerCase().trim();

    // 1. Matching Landmarks
    const matchingLandmarks = POPULAR_LANDMARKS
      .filter(l => l.name.toLowerCase().includes(q) || l.detail.toLowerCase().includes(q) || l.category.toLowerCase().includes(q))
      .map(l => ({
        ...l,
        isStation: false,
        type: 'Lieu / Quartier'
      }));

    // 2. Matching Transit Stations
    const matchingStations = allStations
      .filter(st => st.name.toLowerCase().includes(q))
      .slice(0, 10)
      .map(st => ({
        name: st.name,
        detail: `Station desservie par ${st.lines.length} ligne(s)`,
        lat: st.lat,
        lon: st.lon,
        isStation: true,
        type: 'Station de transport'
      }));

    return [...matchingLandmarks, ...matchingStations].slice(0, 10);
  }, [destinationQuery, allStations]);

  // SMART ROUTING ENGINE:
  // Evaluates which lines bring the user CLOSEST to the target destination
  const routeSolutions = useMemo(() => {
    if (!targetDestination) return [];

    const solutions = [];
    const destLat = targetDestination.lat;
    const destLon = targetDestination.lon;

    // Determine candidate boarding stations near the user
    // If user has GPS: take stations within 1500m (or top 10 closest)
    // If no GPS: take major transit hub stations
    const candidateOrigins = userLocation
      ? allStations
          .map(st => ({
            ...st,
            walkToOriginMeters: getDistanceMeters(userLocation.lat, userLocation.lon, st.lat, st.lon)
          }))
          .filter(st => st.walkToOriginMeters <= 1800)
          .sort((a, b) => a.walkToOriginMeters - b.walkToOriginMeters)
          .slice(0, 10)
      : allStations
          .filter(st => ["Place de Barcelone", "Tunis Marine", "Passage", "Bab Saadoun", "Bab Alioua", "Ariana"].includes(st.name))
          .map(st => ({ ...st, walkToOriginMeters: 0 }));

    // Fallback if no stations within 1800m of user: take top 6 closest anyway
    const activeOrigins = candidateOrigins.length > 0 
      ? candidateOrigins 
      : allStations
          .map(st => ({
            ...st,
            walkToOriginMeters: userLocation ? getDistanceMeters(userLocation.lat, userLocation.lon, st.lat, st.lon) : 0
          }))
          .sort((a, b) => a.walkToOriginMeters - b.walkToOriginMeters)
          .slice(0, 6);

    const evaluatedLineMap = new Map();

    activeOrigins.forEach(originSt => {
      originSt.lines.forEach(originLineInfo => {
        const lineObj = STATIC_LINES.find(l => l.id === originLineInfo.id);
        if (!lineObj) return;

        const originIndex = originLineInfo.stopIndex;

        // Scan all other stops on this line to find the one that gets CLOSEST to the target destination
        let bestDropoffStop = null;
        let minDropoffDist = Infinity;
        let bestDropoffIndex = -1;

        lineObj.stops.forEach((stop, sIndex) => {
          if (sIndex === originIndex) return; // Must actually ride the vehicle
          const dToTarget = getDistanceMeters(stop.lat, stop.lon, destLat, destLon);
          if (dToTarget < minDropoffDist) {
            minDropoffDist = dToTarget;
            bestDropoffStop = stop;
            bestDropoffIndex = sIndex;
          }
        });

        // Maximum allowed walk from drop-off to destination: 2500m (2.5 km)
        if (bestDropoffStop && minDropoffDist <= 2500) {
          const stopsDiff = bestDropoffIndex - originIndex;
          const stopsCount = Math.abs(stopsDiff);

          // Determine direction
          const isForward = stopsDiff > 0;
          const directionName = isForward 
            ? lineObj.directions[0] || lineObj.long_name 
            : lineObj.directions[1] || lineObj.directions[0] || lineObj.long_name;

          // Check live vehicles on this line
          const liveVehicles = (liveLocations || []).filter(loc => loc.line_id === lineObj.id);

          const walkToOriginMeters = originSt.walkToOriginMeters;
          const walkFromDropoffMeters = minDropoffDist;
          const totalWalkMeters = walkToOriginMeters + walkFromDropoffMeters;

          // Estimated time: ~80m/min walk, ~2 min per transit stop
          const walkToOriginMins = Math.max(1, Math.round(walkToOriginMeters / 80));
          const rideMins = Math.max(2, stopsCount * 2);
          const walkFromDropoffMins = Math.max(1, Math.round(walkFromDropoffMeters / 80));
          const estimatedTotalMins = walkToOriginMins + rideMins + walkFromDropoffMins;

          // Score: live vehicles get high priority (deduct 15 min equivalent wait)
          const liveBonus = liveVehicles.length > 0 ? 15 : 0;
          const score = estimatedTotalMins - liveBonus;

          const key = lineObj.id;
          if (!evaluatedLineMap.has(key) || evaluatedLineMap.get(key).score > score) {
            evaluatedLineMap.set(key, {
              line: lineObj,
              originStation: originSt,
              dropoffStation: bestDropoffStop,
              walkToOriginMeters,
              walkToOriginMins,
              stopsCount,
              direction: directionName,
              directionIndex: isForward ? 0 : 1,
              walkFromDropoffMeters,
              walkFromDropoffMins,
              totalWalkMeters,
              estimatedTotalMins,
              isDirectStop: walkFromDropoffMeters < 80,
              liveVehiclesCount: liveVehicles.length,
              closestVehicle: liveVehicles[0] || null,
              score
            });
          }
        }
      });
    });

    const sorted = Array.from(evaluatedLineMap.values()).sort((a, b) => a.score - b.score);
    return sorted.slice(0, 6);
  }, [targetDestination, userLocation, allStations, liveLocations]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-[1060] flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in pointer-events-auto"
      onClick={onClose}
    >
      <div 
        className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden text-slate-100 flex flex-col max-h-[92vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800/80 bg-slate-800/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
              <Compass className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-base text-white">Guide Trajet Intelligent</h2>
                <span className="text-[10px] bg-blue-500/20 text-blue-400 font-extrabold px-2 py-0.5 rounded-full flex items-center gap-1 border border-blue-500/30">
                  <Sparkles className="w-3 h-3" /> Assistant Multi-Lignes
                </span>
              </div>
              <p className="text-xs text-slate-400">Trouve les lignes qui vous amènent au plus près de votre destination</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
          
          {/* Destination Search Box */}
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5 text-blue-400" />
              Où souhaitez-vous vous rendre ?
            </label>
            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={destinationQuery}
                onChange={(e) => {
                  setDestinationQuery(e.target.value);
                  setTargetDestination(null);
                }}
                placeholder="Tapez un lieu ou une station (ex: Marsa, Bourguiba, Lac 1, El Manar...)"
                className="w-full bg-slate-800/90 border border-slate-700 rounded-2xl pl-10 pr-4 py-3 text-xs sm:text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
              />
              {destinationQuery && (
                <button
                  onClick={() => {
                    setDestinationQuery('');
                    setTargetDestination(null);
                  }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Quick Popular Landmarks Chips */}
            {!targetDestination && (
              <div>
                <div className="text-[11px] text-slate-400 font-semibold mb-1.5 flex items-center gap-1">
                  <span>Destinations populaires :</span>
                </div>
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                  {POPULAR_LANDMARKS.slice(0, 8).map(place => (
                    <button
                      key={place.name}
                      onClick={() => {
                        setTargetDestination(place);
                        setDestinationQuery(place.name);
                      }}
                      className="px-2.5 py-1 bg-slate-800/60 hover:bg-slate-700/80 border border-slate-700 rounded-xl text-[11px] text-slate-300 hover:text-white whitespace-nowrap transition flex items-center gap-1"
                    >
                      <span>{place.icon}</span>
                      <span>{place.short}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Destination Autocomplete Suggestions */}
            {!targetDestination && destinationResults.length > 0 && (
              <div className="bg-slate-800/95 border border-slate-700/80 rounded-2xl shadow-xl overflow-hidden divide-y divide-slate-700/40">
                {destinationResults.map((item) => (
                  <button
                    key={`${item.name}-${item.lat}`}
                    onClick={() => {
                      setTargetDestination(item);
                      setDestinationQuery(item.name);
                    }}
                    className="w-full p-3 text-left hover:bg-slate-700/60 transition flex items-center justify-between group"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="p-1.5 rounded-lg bg-blue-600/20 text-blue-400 flex-shrink-0">
                        {item.isStation ? <MapPin className="w-4 h-4" /> : <Building className="w-4 h-4" />}
                      </div>
                      <div className="min-w-0">
                        <div className="font-semibold text-xs text-white group-hover:text-blue-300 transition truncate">
                          {item.name}
                        </div>
                        <div className="text-[10px] text-slate-400 truncate">
                          {item.detail} • <span className="text-slate-500">{item.type}</span>
                        </div>
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-blue-400 group-hover:translate-x-0.5 transition flex-shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Solutions for Target Destination */}
          {targetDestination && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Meilleures lignes pour {targetDestination.name}
                  </span>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    Classées par proximité et véhicules en direct
                  </div>
                </div>
                <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2.5 py-0.5 rounded-full font-bold border border-emerald-500/30">
                  {routeSolutions.length} solution(s)
                </span>
              </div>

              {routeSolutions.length === 0 ? (
                <div className="p-5 bg-slate-800/40 border border-slate-700/60 rounded-2xl text-center space-y-2">
                  <p className="text-xs text-slate-300 font-semibold">
                    Aucune ligne de transport ne passe à moins de 2.5 km de ce lieu depuis votre position.
                  </p>
                  <p className="text-[11px] text-slate-400">
                    Astuce : Rapprochez-vous d'un grand pôle d'échange comme <strong>Place de Barcelone</strong>, <strong>Tunis Marine</strong> ou <strong>Passage</strong>.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {routeSolutions.map((sol, index) => (
                    <div
                      key={`${sol.line.id}-${sol.originStation.name}-${index}`}
                      className="p-4 bg-slate-800/60 hover:bg-slate-800/90 border border-slate-700/70 hover:border-blue-500/80 rounded-2xl transition-all shadow-md group space-y-3"
                    >
                      {/* Line Badge & Live Signal */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2.5 min-w-0">
                          <span
                            className="px-2.5 py-1 rounded-xl text-white font-black text-xs shadow flex-shrink-0"
                            style={{ backgroundColor: sol.line.color }}
                          >
                            {getLineShortName(sol.line, language)}
                          </span>
                          <div className="min-w-0">
                            <div className="font-bold text-xs text-white truncate">
                              {getLineName(sol.line, language)}
                            </div>
                            <div className="text-[10px] text-slate-400 truncate">
                              {language === 'ar' ? 'الاتجاه : ' : 'Direction : '}<span className="text-slate-200 font-semibold">{sol.direction}</span>
                            </div>
                          </div>
                        </div>

                        {sol.liveVehiclesCount > 0 ? (
                          <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 flex-shrink-0">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                            {sol.liveVehiclesCount} {language === 'ar' ? 'مباشرة' : 'en direct'}
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-400 bg-slate-900/60 px-2 py-0.5 rounded-full flex-shrink-0">
                            ~{sol.estimatedTotalMins} {language === 'ar' ? 'دقيقة إجمالاً' : 'min au total'}
                          </span>
                        )}
                      </div>

                      {/* Step-by-Step Guidance */}
                      <div className="bg-slate-900/80 rounded-2xl p-3 text-xs space-y-2 border border-slate-800 text-slate-300">
                        {/* Step 1: Walk to Boarding */}
                        <div className="flex items-start gap-2.5">
                          <Footprints className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                          <div>
                            <span>{language === 'ar' ? 'الركوب من محطة ' : 'Prendre à l\'arrêt '}</span>
                            <strong className="text-white">{getStationName(sol.originStation, language)}</strong>
                            {sol.walkToOriginMeters > 0 && (
                              <span className="text-slate-400"> ({sol.walkToOriginMeters}m - ~{sol.walkToOriginMins} {language === 'ar' ? 'دقيقة سيراً' : 'min à pied'})</span>
                            )}
                          </div>
                        </div>

                        {/* Step 2: Transit Ride */}
                        <div className="flex items-start gap-2.5">
                          <div className="w-4 h-4 rounded-full flex items-center justify-center font-bold text-[9px] text-white flex-shrink-0 mt-0.5" style={{ backgroundColor: sol.line.color }}>
                            {sol.line.type_id === 'bus' ? '🚌' : '🚇'}
                          </div>
                          <div>
                            <span>{language === 'ar' ? 'السفر عبر الخط ' : 'Voyager sur la ligne '}</span>
                            <strong className="text-white">{getLineShortName(sol.line, language)}</strong>
                            <span className="text-slate-400"> {language === 'ar' ? `لمدة ${sol.stopsCount} محطات` : `pendant ${sol.stopsCount} arrêt(s)`}</span>
                            {sol.liveVehiclesCount > 0 && (
                              <div className="text-[11px] text-emerald-400 font-semibold mt-0.5">
                                {language === 'ar' ? '🟢 مركبة مباشرة متابعة بالـ GPS على هذا الخط' : '🟢 Véhicule en direct suivi par GPS sur cette ligne'}
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Step 3: Drop-off */}
                        <div className="flex items-start gap-2.5">
                          <MapPin className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                          <div>
                            <span>{language === 'ar' ? 'النزول في محطة ' : 'Descendre à l\'arrêt '}</span>
                            <strong className="text-white">{getStationName(sol.dropoffStation, language)}</strong>
                          </div>
                        </div>

                        {/* Step 4: Final Walk to Target Place */}
                        <div className="flex items-start gap-2.5">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                          <div>
                            {sol.isDirectStop ? (
                              <span className="text-emerald-400 font-bold">
                                🎯 Vous arrivez directement à votre destination !
                              </span>
                            ) : (
                              <span>
                                Marcher <strong className="text-white">{sol.walkFromDropoffMeters} mètres</strong> (~{sol.walkFromDropoffMins} min) jusqu'à <strong className="text-white">{targetDestination.name}</strong>
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Action Button */}
                      <button
                        onClick={() => {
                          if (onShowItinerary) {
                            onShowItinerary({
                              ...sol,
                              targetDestination,
                              userLocation
                            });
                          } else if (onSelectLineAndStation) {
                            onSelectLineAndStation(sol.line, sol.originStation);
                          }
                          onClose();
                        }}
                        className="w-full py-2.5 px-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-md shadow-blue-500/20 active:scale-[0.99]"
                      >
                        <span>Afficher cet itinéraire sur la carte</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Nearby Stations from GPS (Quick Overview) */}
          <div className="space-y-2.5 pt-2 border-t border-slate-800/60">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Navigation className="w-3.5 h-3.5 text-blue-400" />
                Arrêts autour de vous
              </span>
              {!userLocation && onRequestGps && (
                <button
                  onClick={onRequestGps}
                  className="text-[11px] text-blue-400 hover:underline font-bold"
                >
                  Activer GPS
                </button>
              )}
            </div>

            {userLocation ? (
              <div className="grid grid-cols-1 gap-2">
                {nearestStations.map((st) => (
                  <div
                    key={st.name}
                    className="p-3 bg-slate-800/40 hover:bg-slate-800/80 border border-slate-700/50 rounded-2xl transition flex items-center justify-between"
                  >
                    <div>
                      <div className="font-bold text-xs text-white">{st.name}</div>
                      <div className="text-[10px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                        <Footprints className="w-3 h-3 text-emerald-400" />
                        <span className="text-emerald-400 font-semibold">{st.distanceMeters} mètres</span>
                        <span>(~{Math.max(1, Math.round(st.distanceMeters / 80))} min à pied)</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 overflow-x-auto max-w-[150px]">
                      {st.lines.slice(0, 3).map((l) => (
                        <span
                          key={l.id}
                          className="px-1.5 py-0.5 rounded text-[10px] font-bold text-white shadow"
                          style={{ backgroundColor: l.color }}
                          title={`${l.short_name} : ${l.long_name}`}
                        >
                          {l.short_name}
                        </span>
                      ))}
                      {st.lines.length > 3 && (
                        <span className="text-[10px] text-slate-400 font-bold">
                          +{st.lines.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-slate-800/30 border border-slate-700/40 rounded-2xl text-center">
                <p className="text-xs text-slate-400 mb-2">
                  Activez votre localisation GPS pour que le guide calcule votre marche exacte jusqu'aux arrêts.
                </p>
                {onRequestGps && (
                  <button
                    onClick={onRequestGps}
                    className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition"
                  >
                    Activer mon GPS
                  </button>
                )}
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
