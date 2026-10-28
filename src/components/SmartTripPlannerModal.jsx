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
  Target,
  Zap
} from 'lucide-react';
import { STATIC_LINES as DEFAULT_STATIC_LINES } from '../data/staticTransit';
import { useTransitData } from '../context/TransitDataContext';
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
  { name: "Faculté 9 Avril", short: "9 Avril", detail: "Campus Universitaire 9 Avril & Hôpitaux", category: "Universités", lat: 36.7938, lon: 10.1624, icon: "🎓" },
  { name: "Station Le Bardo", short: "Le Bardo", detail: "Gare RFR D, Métro 4 & Bus", category: "Gares", lat: 36.8074, lon: 10.1345, icon: "🚉" },
  { name: "Bab Saadoun", short: "Bab Saadoun", detail: "Pôle d'Échange Métros 3, 4, 5 & Hôpitaux", category: "Gares", lat: 36.8099, lon: 10.1621, icon: "🚉" },
  { name: "Place de Barcelone", short: "Barcelone", detail: "Gare Centrale & Métros", category: "Gares", lat: 36.7950, lon: 10.1800, icon: "🚉" },
  { name: "Passage / République", short: "Passage", detail: "Pôle Central Métros 2, 3, 4, 5 & Bus", category: "Gares", lat: 36.8065, lon: 10.1808, icon: "🚉" },
  { name: "Avenue Habib Bourguiba", short: "Centre-Ville", detail: "Centre-Ville Tunis", category: "Centre-Ville", lat: 36.7997, lon: 10.1800, icon: "🏙️" },
  { name: "Tunis Marine", short: "Tunis Marine", detail: "Terminus TGM & Bus Banlieue", category: "Gares", lat: 36.8010, lon: 10.1920, icon: "🚆" },
  { name: "Les Berges du Lac 1", short: "Lac 1", detail: "Zone d'Affaires", category: "Affaires", lat: 36.8320, lon: 10.2350, icon: "🌊" },
  { name: "Les Berges du Lac 2", short: "Lac 2", detail: "Ambassades & Bureaux", category: "Affaires", lat: 36.8450, lon: 10.2750, icon: "🏢" },
  { name: "Aéroport Tunis-Carthage", short: "Aéroport", detail: "Terminal Principal", category: "Transport", lat: 36.8510, lon: 10.2272, icon: "✈️" },
  { name: "La Marsa Plage", short: "La Marsa", detail: "Corniche & Plage", category: "Banlieue Nord", lat: 36.8785, lon: 10.3235, icon: "🏖️" },
  { name: "Sidi Bou Saïd", short: "Sidi Bou Saïd", detail: "Village & Café des Délices", category: "Banlieue Nord", lat: 36.8710, lon: 10.3415, icon: "🏛️" },
  { name: "Carthage Amphi & Musée", short: "Carthage", detail: "Site Archéologique", category: "Banlieue Nord", lat: 36.8540, lon: 10.3290, icon: "🏛️" },
  { name: "Campus Univ. El Manar", short: "El Manar", detail: "Facultés des Sciences & Médecine", category: "Universités", lat: 36.8335, lon: 10.1470, icon: "🎓" },
  { name: "Campus Univ. La Manouba", short: "Manouba Univ", detail: "Lettres, FLAHM & ISCAE", category: "Universités", lat: 36.8120, lon: 10.0880, icon: "🎓" },
  { name: "Ariana Centre", short: "Ariana", detail: "Centre-Ville Ariana", category: "Banlieue", lat: 36.8620, lon: 10.1950, icon: "📍" },
  { name: "Ben Arous Centre", short: "Ben Arous", detail: "Centre Gouvernorat", category: "Banlieue Sud", lat: 36.7530, lon: 10.2220, icon: "📍" },
  { name: "Radès Ville & Stade", short: "Radès", detail: "Cité Sportive", category: "Banlieue Sud", lat: 36.7680, lon: 10.2800, icon: "🏟️" },
  { name: "Hammam-Lif", short: "Hammam-Lif", detail: "Banlieue Sud & Plage", category: "Banlieue Sud", lat: 36.7290, lon: 10.3390, icon: "📍" },
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
  const { lines: dynamicLines } = useTransitData();
  const STATIC_LINES = dynamicLines || DEFAULT_STATIC_LINES;
  const [destinationQuery, setDestinationQuery] = useState('');
  const [targetDestination, setTargetDestination] = useState(null);
  const [filterMode, setFilterMode] = useState('fastest'); // 'fastest' | 'soonest' | 'least_walk' | 'all'

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

  // SMART ROUTING ENGINE (Direct Network Scan & Strict Nearest-Station Guarantee):
  // Evaluates which lines bring the user CLOSEST to the target destination.
  // STRICT RULE: For any candidate line, the boarding station MUST be the closest possible stop to the user's location.
  // Never directs a user to walk past a station or trek to a distant stop when a close stop exists!
  const routeSolutions = useMemo(() => {
    if (!targetDestination) return [];

    const destLat = targetDestination.lat;
    const destLon = targetDestination.lon;

    // User start point: either user's GPS position, or fallback to central hub (Place de Barcelone)
    const startLoc = (userLocation && userLocation.lat && userLocation.lon)
      ? { lat: userLocation.lat, lon: userLocation.lon }
      : { lat: 36.7950, lon: 10.1800, isFallback: true };

    const rawSolutions = [];

    // Evaluate each line across both directions with its exact directional stops
    STATIC_LINES.forEach(line => {
      const dirConfigs = [];

      // Direction 0 (Aller)
      const dir0Stops = (line.stops_aller && line.stops_aller.length > 0) ? line.stops_aller : line.stops;
      if (dir0Stops && dir0Stops.length > 1) {
        dirConfigs.push({
          dirIndex: 0,
          dirName: line.directions?.[0] || line.long_name,
          stops: dir0Stops
        });
      }

      // Direction 1 (Retour)
      let dir1Stops = null;
      if (line.stops_retour && line.stops_retour.length > 1) {
        dir1Stops = line.stops_retour;
      } else if (line.stops_aller && line.stops_aller.length > 1) {
        dir1Stops = [...line.stops_aller].reverse();
      } else if (line.stops && line.stops.length > 1) {
        dir1Stops = [...line.stops].reverse();
      }

      if (dir1Stops) {
        dirConfigs.push({
          dirIndex: 1,
          dirName: line.directions?.[1] || line.directions?.[0] || line.long_name,
          stops: dir1Stops
        });
      }

      dirConfigs.forEach(cfg => {
        const stops = cfg.stops;

        // 1. Find the stop on this line sequence strictly NEAREST to the user's start point
        let bestOriginIdx = -1;
        let minOriginDist = Infinity;

        // 2. Find the stop on this line sequence strictly NEAREST to the destination
        let bestDropoffIdx = -1;
        let minDropoffDist = Infinity;

        stops.forEach((s, idx) => {
          if (!s || !s.lat || !s.lon) return;
          const dO = getDistanceMeters(startLoc.lat, startLoc.lon, s.lat, s.lon);
          if (dO < minOriginDist) {
            minOriginDist = dO;
            bestOriginIdx = idx;
          }

          const dD = getDistanceMeters(destLat, destLon, s.lat, s.lon);
          if (dD < minDropoffDist) {
            minDropoffDist = dD;
            bestDropoffIdx = idx;
          }
        });

        // 3. Forward progression check:
        // - Boarding stop must strictly precede dropoff stop in travel sequence!
        // - User must be within reasonable walk of boarding stop (max 1800m)
        // - Dropoff within reasonable distance of target (max 2000m)
        if (
          bestOriginIdx !== -1 &&
          bestDropoffIdx !== -1 &&
          bestOriginIdx < bestDropoffIdx &&
          minOriginDist <= 1800 &&
          minDropoffDist <= 2000
        ) {
          const originStop = stops[bestOriginIdx];
          const dropoffStop = stops[bestDropoffIdx];
          const stopsCount = bestDropoffIdx - bestOriginIdx;

          // Check physical progress: dropoff must bring user significantly closer to destination than where they boarded!
          const dOriginToDest = getDistanceMeters(originStop.lat, originStop.lon, destLat, destLon);
          if (minDropoffDist >= dOriginToDest) return;

          // 1. Live Vehicles on this line & ETA calculation to originStop
          const lineVehicles = (liveLocations || []).filter(loc => loc.line_id === line.id);
          let approachingVehicle = null;
          let minVehicleEtaMins = Infinity;

          lineVehicles.forEach(v => {
            if (!v.latitude || !v.longitude) return;
            // Find which stop on cfg.stops this vehicle is closest to
            let closestStopIdx = -1;
            let minVDist = Infinity;
            stops.forEach((s, idx) => {
              const dist = getDistanceMeters(v.latitude, v.longitude, s.lat, s.lon);
              if (dist < minVDist) {
                minVDist = dist;
                closestStopIdx = idx;
              }
            });

            // If the vehicle is upstream of the boarding stop (or within 150m of it)
            if (closestStopIdx !== -1 && closestStopIdx <= bestOriginIdx) {
              const distToOrigin = getDistanceMeters(v.latitude, v.longitude, originStop.lat, originStop.lon);
              // Average speed in urban traffic ~18 km/h = ~300 m/min
              const etaMins = Math.max(0, Math.round(distToOrigin / 300));
              if (etaMins < minVehicleEtaMins) {
                minVehicleEtaMins = etaMins;
                approachingVehicle = { ...v, etaMins, distMeters: distToOrigin };
              }
            }
          });

          // Wait time to board (waitMins)
          let waitMins = 0;
          let hasLiveApproaching = false;
          if (approachingVehicle && minVehicleEtaMins <= 45) {
            waitMins = minVehicleEtaMins;
            hasLiveApproaching = true;
          } else {
            // Standard frequency / expected wait time per mode
            if (line.type_id === 'subway') waitMins = 5;
            else if (line.type_id === 'tgm') waitMins = 8;
            else if (line.type_id === 'train' || line.type_id === 'rfr') waitMins = 12;
            else waitMins = 8; // Bus
          }

          // 2. In-vehicle ride duration (commercial speed)
          let rideMins = 0;
          if (line.type_id === 'train' || line.type_id === 'rfr') {
            rideMins = Math.max(3, Math.round(stopsCount * 1.6));
          } else if (line.type_id === 'subway' || line.type_id === 'tgm') {
            rideMins = Math.max(3, Math.round(stopsCount * 2.0));
          } else {
            rideMins = Math.max(3, Math.round(stopsCount * 2.4));
          }

          const walkToOriginMeters = minOriginDist;
          const walkFromDropoffMeters = minDropoffDist;
          const totalWalkMeters = walkToOriginMeters + walkFromDropoffMeters;

          const walkToOriginMins = Math.max(1, Math.round(walkToOriginMeters / 75));
          const walkFromDropoffMins = Math.round(walkFromDropoffMeters / 75);

          // Total door-to-door arrival time
          const totalArrivalMins = walkToOriginMins + waitMins + rideMins + walkFromDropoffMins;

          // SCORING:
          // Heavy penalty on walking to origin (x3.0) and wait time so fastest incoming options rank highest
          const isRail = line.type_id === 'subway' || line.type_id === 'train' || line.type_id === 'rfr' || line.type_id === 'tgm';
          const railBonus = isRail ? 150 : 0;
          const liveBonus = hasLiveApproaching ? 250 : (lineVehicles.length > 0 ? 100 : 0);
          const score = (walkToOriginMeters * 3.0) + (walkFromDropoffMeters * 1.5) + (waitMins * 80) + (rideMins * 50) - railBonus - liveBonus;

          rawSolutions.push({
            line,
            originStation: originStop,
            dropoffStation: dropoffStop,
            walkToOriginMeters,
            walkToOriginMins,
            stopsCount,
            direction: cfg.dirName,
            directionIndex: cfg.dirIndex,
            walkFromDropoffMeters,
            walkFromDropoffMins,
            totalWalkMeters,
            waitMins,
            rideMins,
            totalArrivalMins,
            estimatedTotalMins: totalArrivalMins,
            hasLiveApproaching,
            approachingVehicle,
            isDirectStop: walkFromDropoffMeters < 80,
            liveVehiclesCount: lineVehicles.length,
            closestVehicle: approachingVehicle || lineVehicles[0] || null,
            score
          });
        }
      });
    });

    // Deduplicate by line ID: keep the best direction/solution for each line
    const byLine = new Map();
    rawSolutions.forEach(sol => {
      if (!byLine.has(sol.line.id) || byLine.get(sol.line.id).totalArrivalMins > sol.totalArrivalMins) {
        byLine.set(sol.line.id, sol);
      }
    });

    const solutionsList = Array.from(byLine.values());
    if (solutionsList.length === 0) return [];

    // Identify minimum metrics across all solutions for pinned badges
    let minTotal = Infinity;
    let minWait = Infinity;
    let minWalk = Infinity;

    solutionsList.forEach(s => {
      if (s.totalArrivalMins < minTotal) minTotal = s.totalArrivalMins;
      if (s.waitMins < minWait) minWait = s.waitMins;
      if (s.totalWalkMeters < minWalk) minWalk = s.totalWalkMeters;
    });

    // Tag each solution with pinned attributes
    const taggedSolutions = solutionsList.map(s => ({
      ...s,
      isFastestTotal: s.totalArrivalMins === minTotal,
      isSoonestDeparture: s.waitMins === minWait,
      isLeastWalk: s.totalWalkMeters === minWalk || s.isDirectStop
    }));

    // Sort according to active filterMode
    let sorted = [...taggedSolutions];
    if (filterMode === 'fastest') {
      sorted.sort((a, b) => a.totalArrivalMins - b.totalArrivalMins);
    } else if (filterMode === 'soonest') {
      sorted.sort((a, b) => a.waitMins - b.waitMins || a.totalArrivalMins - b.totalArrivalMins);
    } else if (filterMode === 'least_walk') {
      sorted.sort((a, b) => a.totalWalkMeters - b.totalWalkMeters || a.totalArrivalMins - b.totalArrivalMins);
    } else {
      sorted.sort((a, b) => a.score - b.score);
    }

    return sorted.slice(0, 8);
  }, [targetDestination, userLocation, STATIC_LINES, liveLocations, filterMode]);

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
                  {POPULAR_LANDMARKS.slice(0, 10).map(place => (
                    <button
                      key={place.name}
                      onClick={() => {
                        setTargetDestination(place);
                        setDestinationQuery(place.name);
                      }}
                      className="px-2.5 py-1 bg-slate-800/60 hover:bg-slate-700/80 border border-slate-700 rounded-xl text-[11px] text-slate-300 hover:text-white whitespace-nowrap transition flex items-center gap-1 shadow-sm"
                    >
                      <span>{place.icon}</span>
                      <span>{place.short || place.name}</span>
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
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    {language === 'ar' ? `أفضل مسارات للوصول إلى ${targetDestination.name}` : `Meilleures lignes pour ${targetDestination.name}`}
                  </span>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    {language === 'ar' ? 'مصنفة حسب سرعة الوصول، توقيت المركبة القادمة ومسافة المشي' : 'Classées selon rapidité d\'arrivée, proximité de départ et marche'}
                  </div>
                </div>
                <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2.5 py-0.5 rounded-full font-bold border border-emerald-500/30 self-start sm:self-auto">
                  {routeSolutions.length} {language === 'ar' ? 'حلول متاحة' : 'solution(s)'}
                </span>
              </div>

              {/* Quick Filter / Sort Pills for Decision Making */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                <button
                  type="button"
                  onClick={() => setFilterMode('fastest')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap flex items-center gap-1.5 shadow-sm active:scale-95 ${
                    filterMode === 'fastest'
                      ? 'bg-emerald-600 text-white shadow-emerald-500/25 ring-2 ring-emerald-400/40'
                      : 'bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700/70'
                  }`}
                >
                  <Zap className="w-3.5 h-3.5 text-amber-300" />
                  <span>{language === 'ar' ? 'الأسرع وصولاً' : '⚡ Le plus rapide'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => setFilterMode('soonest')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap flex items-center gap-1.5 shadow-sm active:scale-95 ${
                    filterMode === 'soonest'
                      ? 'bg-amber-600 text-white shadow-amber-500/25 ring-2 ring-amber-400/40'
                      : 'bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700/70'
                  }`}
                >
                  <Clock className="w-3.5 h-3.5 text-amber-200" />
                  <span>{language === 'ar' ? 'أقرب انطلاق' : '⏱️ Départ imminent'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => setFilterMode('least_walk')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap flex items-center gap-1.5 shadow-sm active:scale-95 ${
                    filterMode === 'least_walk'
                      ? 'bg-sky-600 text-white shadow-sky-500/25 ring-2 ring-sky-400/40'
                      : 'bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700/70'
                  }`}
                >
                  <Footprints className="w-3.5 h-3.5 text-sky-200" />
                  <span>{language === 'ar' ? 'أقل مشي' : '🚶 Moins de marche'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => setFilterMode('all')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap flex items-center gap-1.5 shadow-sm active:scale-95 ${
                    filterMode === 'all'
                      ? 'bg-indigo-600 text-white shadow-indigo-500/25 ring-2 ring-indigo-400/40'
                      : 'bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700/70'
                  }`}
                >
                  <span>📋</span>
                  <span>{language === 'ar' ? 'جميع الخيارات' : 'Toutes les options'}</span>
                </button>
              </div>

              {routeSolutions.length === 0 ? (
                <div className="p-5 bg-slate-800/40 border border-slate-700/60 rounded-2xl text-center space-y-2">
                  <p className="text-xs text-slate-300 font-semibold">
                    {language === 'ar'
                      ? 'لا توجد خطوط نقل مباشرة تمر قريباً من هذه الوجهة انطلاقاً من موقعك.'
                      : 'Aucune ligne de transport ne passe à moins de 2.5 km de ce lieu depuis votre position.'}
                  </p>
                  <p className="text-[11px] text-slate-400">
                    {language === 'ar'
                      ? 'نصيحة : اقترب من محطة رئيسية مثل ساحة برشلونة، تونس البحرية أو الباساج.'
                      : 'Astuce : Rapprochez-vous d\'un grand pôle d\'échange comme Place de Barcelone, Tunis Marine ou Passage.'}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {routeSolutions.map((sol, index) => (
                    <div
                      key={`${sol.line.id}-${sol.originStation.name}-${index}`}
                      className="p-4 bg-slate-800/60 hover:bg-slate-800/90 border border-slate-700/70 hover:border-blue-500/80 rounded-2xl transition-all shadow-md group space-y-3"
                    >
                      {/* Pinned Badges for Instant Comparison */}
                      <div className="flex flex-wrap items-center gap-1.5">
                        {sol.isFastestTotal && (
                          <span className="px-2.5 py-1 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-black text-[10px] shadow-sm flex items-center gap-1 border border-emerald-400/30">
                            <span>⚡</span>
                            <span>{language === 'ar' ? `الأسرع وصولاً (~${sol.totalArrivalMins} دق إجمالاً)` : `LE PLUS RAPIDE (~${sol.totalArrivalMins} min au total)`}</span>
                          </span>
                        )}

                        {sol.isSoonestDeparture && (
                          <span className="px-2.5 py-1 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 text-white font-black text-[10px] shadow-sm flex items-center gap-1 border border-amber-400/30">
                            <span>⏱️</span>
                            <span>{language === 'ar' ? `أقرب انطلاق (~${sol.waitMins} دق)` : `DÉPART IMMINENT (~${sol.waitMins} min d'attente)`}</span>
                          </span>
                        )}

                        {sol.isLeastWalk && (
                          <span className="px-2.5 py-1 rounded-xl bg-gradient-to-r from-sky-600 to-blue-600 text-white font-black text-[10px] shadow-sm flex items-center gap-1 border border-sky-400/30">
                            <span>🚶</span>
                            <span>{language === 'ar' ? `أقرب نزول (${sol.walkFromDropoffMeters}م مشي)` : `DÉPOSE AU PLUS PRÈS (${sol.walkFromDropoffMeters}m de marche)`}</span>
                          </span>
                        )}

                        {sol.hasLiveApproaching && (
                          <span className="px-2 py-0.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] font-bold flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                            <span>{language === 'ar' ? `مباشر GPS: خلال ~${sol.waitMins} دق` : `GPS Live : dans ~${sol.waitMins} min`}</span>
                          </span>
                        )}
                      </div>

                      {/* Line Header */}
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

                        <div className="text-right flex-shrink-0">
                          <div className="text-xs font-black text-emerald-400">
                            ~{sol.totalArrivalMins} {language === 'ar' ? 'دق' : 'min'}
                          </div>
                          <div className="text-[10px] text-slate-400">
                            {language === 'ar' ? 'الوقت الإجمالي' : 'porte-à-porte'}
                          </div>
                        </div>
                      </div>

                      {/* Journey Step-by-Step Breakdown Strip */}
                      <div className="flex items-center gap-1.5 text-[10.5px] font-semibold text-slate-300 bg-slate-950/70 p-2.5 rounded-xl border border-slate-800/90 overflow-x-auto scrollbar-none">
                        <span className="flex items-center gap-1 text-sky-400 whitespace-nowrap">
                          <Footprints className="w-3 h-3" />
                          <span>{sol.walkToOriginMins}m à pied</span>
                        </span>
                        <span className="text-slate-600">→</span>
                        <span className="flex items-center gap-1 text-amber-400 whitespace-nowrap">
                          <Clock className="w-3 h-3" />
                          <span>Attente ~{sol.waitMins}m</span>
                        </span>
                        <span className="text-slate-600">→</span>
                        <span className="flex items-center gap-1 font-bold whitespace-nowrap" style={{ color: sol.line.color }}>
                          <span>{sol.line.type_id === 'bus' ? '🚌' : '🚇'}</span>
                          <span>Trajet ~{sol.rideMins}m</span>
                        </span>
                        <span className="text-slate-600">→</span>
                        <span className="flex items-center gap-1 text-emerald-400 whitespace-nowrap">
                          <Footprints className="w-3 h-3" />
                          <span>{sol.walkFromDropoffMins}m à pied</span>
                        </span>
                      </div>

                      {/* Step-by-Step Guidance */}
                      <div className="bg-slate-900/80 rounded-2xl p-3 text-xs space-y-2.5 border border-slate-800 text-slate-300">
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

                        {/* Step 2: Waiting time */}
                        <div className="flex items-start gap-2.5">
                          <Clock className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                          <div>
                            {sol.hasLiveApproaching ? (
                              <span className="text-emerald-400 font-bold">
                                {language === 'ar'
                                  ? `🟢 مركبة مباشرة قادمة نحو المحطة (تصل خلال ~${sol.waitMins} دق)`
                                  : `🟢 Véhicule direct en approche (arrive dans ~${sol.waitMins} min)`}
                              </span>
                            ) : (
                              <span className="text-slate-300">
                                {language === 'ar'
                                  ? `⏱️ وقت الانتظار التقديري : ~${sol.waitMins} دقيقة`
                                  : `⏱️ Temps d'attente estimé : ~${sol.waitMins} min`}
                                <span className="text-slate-500 text-[10px]"> ({sol.line.type_id === 'bus' ? 'Bus' : 'Train/Métro'})</span>
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Step 3: Transit Ride */}
                        <div className="flex items-start gap-2.5">
                          <div className="w-4 h-4 rounded-full flex items-center justify-center font-bold text-[9px] text-white flex-shrink-0 mt-0.5" style={{ backgroundColor: sol.line.color }}>
                            {sol.line.type_id === 'bus' ? '🚌' : '🚇'}
                          </div>
                          <div>
                            <span>{language === 'ar' ? 'السفر عبر الخط ' : 'Voyager sur la ligne '}</span>
                            <strong className="text-white">{getLineShortName(sol.line, language)}</strong>
                            <span className="text-slate-400"> {language === 'ar' ? `لمدة ~${sol.rideMins} دق (${sol.stopsCount} محطات)` : `pendant ~${sol.rideMins} min (${sol.stopsCount} arrêts)`}</span>
                          </div>
                        </div>

                        {/* Step 4: Drop-off */}
                        <div className="flex items-start gap-2.5">
                          <MapPin className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                          <div>
                            <span>{language === 'ar' ? 'النزول في محطة ' : 'Descendre à l\'arrêt '}</span>
                            <strong className="text-white">{getStationName(sol.dropoffStation, language)}</strong>
                          </div>
                        </div>

                        {/* Step 5: Final Walk to Target Place */}
                        <div className="flex items-start gap-2.5">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                          <div>
                            {sol.isDirectStop ? (
                              <span className="text-emerald-400 font-bold">
                                {language === 'ar' ? '🎯 وصول مباشر أمام وجهتك بالتمام !' : '🎯 Dépose directe devant votre destination !'}
                              </span>
                            ) : (
                              <span>
                                {language === 'ar'
                                  ? `المشي ${sol.walkFromDropoffMeters} متراً (~${sol.walkFromDropoffMins} دق) للوصول إلى `
                                  : `Marcher `}
                                <strong className="text-white">{sol.walkFromDropoffMeters} mètres</strong> (~{sol.walkFromDropoffMins} min) {language === 'ar' ? '' : 'jusqu\'à '}
                                <strong className="text-white">{targetDestination.name}</strong>
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
                        <span>{language === 'ar' ? 'عرض هذا المسار على الخريطة' : 'Afficher cet itinéraire sur la carte'}</span>
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
