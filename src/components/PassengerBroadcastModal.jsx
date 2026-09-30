import React, { useState, useEffect, useRef, useMemo } from 'react';
import { 
  Radio, 
  X, 
  MapPin, 
  Navigation, 
  CheckCircle2, 
  AlertCircle, 
  Gauge, 
  ShieldCheck,
  Zap,
  LocateFixed
} from 'lucide-react';
import { STATIC_LINES } from '../data/staticTransit';
import TRANSIT_SHAPES from '../data/transitShapes.json';
import { publishLiveLocation, removeLiveLocation, SUPABASE_URL, SUPABASE_ANON_KEY } from '../supabase';
import { isNativeAndroid, startBackgroundBroadcast, stopBackgroundBroadcast, isBackgroundBroadcastRunning } from '../native/backgroundBroadcast';
import { getLineName, getLineShortName } from '../utils/i18n';

const RAIL_LINE_TYPES = new Set(['metro', 'tgm', 'rfr', 'train']);
const HUB_SHARED_STOP_RADIUS_METERS = 95;

export default function PassengerBroadcastModal({
  isOpen,
  onClose,
  isBroadcasting,
  setIsBroadcasting,
  userLocation,
  broadcastSession,
  setBroadcastSession,
  onRequestGps,
  gpsStatus,
  language = 'fr'
}) {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedLineId, setSelectedLineId] = useState(broadcastSession?.lineId || '');
  const [direction, setDirection] = useState(broadcastSession?.direction || '');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [currentSpeed, setCurrentSpeed] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [backgroundLocationEnabled, setBackgroundLocationEnabled] = useState(false);
  const watchIdRef = useRef(null);
  const lastPosRef = useRef(null);

  // Helper: Distance in meters between two lat/lon points
  const getDistanceMeters = (lat1, lon1, lat2, lon2) => {
    if (!lat1 || !lon1 || !lat2 || !lon2) return 999999;
    const R = 6371e3;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return Math.round(R * c);
  };

  // Helper: Distance in meters from point P to line segment AB
  const getDistanceToSegment = (pLat, pLon, aLat, aLon, bLat, bLon) => {
    const cosLat = Math.cos((aLat * Math.PI) / 180);
    const mPerDegLat = 111132;
    const mPerDegLon = 111132 * cosLat;
    const dx = (bLon - aLon) * mPerDegLon;
    const dy = (bLat - aLat) * mPerDegLat;
    const lenSq = dx * dx + dy * dy;
    if (lenSq === 0) return getDistanceMeters(pLat, pLon, aLat, aLon);
    const px = (pLon - aLon) * mPerDegLon;
    const py = (pLat - aLat) * mPerDegLat;
    let t = (px * dx + py * dy) / lenSq;
    t = Math.max(0, Math.min(1, t));
    const distX = px - (t * dx);
    const distY = py - (t * dy);
    return Math.round(Math.sqrt(distX * distX + distY * distY));
  };

  // Helper: Exact distance from user GPS to a transit line (checks both high-def OSM track shapes & stops)
  const getDistanceToLine = (userLat, userLon, line) => {
    if (!line) return { minD: 999999, closestStop: null };
    let minD = Infinity;
    let closestStop = null;

    // 1. High-definition real physical route geometry (from OSM / QGIS)
    const shape = TRANSIT_SHAPES[line.id];
    if (shape && shape.length > 1) {
      for (let i = 0; i < shape.length - 1; i++) {
        const ptA = shape[i];
        const ptB = shape[i + 1];
        const dSeg = getDistanceToSegment(userLat, userLon, ptA[0], ptA[1], ptB[0], ptB[1]);
        if (dSeg < minD) {
          minD = dSeg;
        }
      }
    }

    // 2. Individual stops
    if (line.stops) {
      for (let i = 0; i < line.stops.length; i++) {
        const s = line.stops[i];
        const d = getDistanceMeters(userLat, userLon, s.lat, s.lon);
        if (d < minD) {
          minD = d;
          closestStop = s;
        }
      }

      // 3. Fallback segments between stops if line does not have a dedicated shape polyline
      if (!shape) {
        for (let i = 0; i < line.stops.length - 1; i++) {
          const sA = line.stops[i];
          const sB = line.stops[i + 1];
          const dSeg = getDistanceToSegment(userLat, userLon, sA.lat, sA.lon, sB.lat, sB.lon);
          if (dSeg < minD) {
            minD = dSeg;
          }
        }
      }
    }

    return { minD, closestStop };
  };

  const getRailHubContext = (userLat, userLon) => {
    const railLines = STATIC_LINES.filter(line => RAIL_LINE_TYPES.has(line.type_id));
    if (!railLines.length) return null;

    const hubDetectionRadius = Math.max(65, Math.min(95, maxAllowedDistance + 20));
    const nearbyStops = [];

    railLines.forEach(line => {
      (line.stops || []).forEach(stop => {
        const d = getDistanceMeters(userLat, userLon, stop.lat, stop.lon);
        if (d <= hubDetectionRadius) {
          nearbyStops.push({ stop, distance: d });
        }
      });
    });

    if (!nearbyStops.length) return null;

    let bestHub = null;

    nearbyStops.forEach(({ stop, distance }) => {
      const lineIds = new Set();

      railLines.forEach(line => {
        const servesHub = (line.stops || []).some(otherStop =>
          getDistanceMeters(stop.lat, stop.lon, otherStop.lat, otherStop.lon) <= HUB_SHARED_STOP_RADIUS_METERS
        );
        if (servesHub) lineIds.add(line.id);
      });

      if (lineIds.size < 2) return;

      if (
        !bestHub ||
        lineIds.size > bestHub.lineIds.size ||
        (lineIds.size === bestHub.lineIds.size && distance < bestHub.nearestStopDistance)
      ) {
        bestHub = {
          nearestStopName: stop.name,
          nearestStopDistance: distance,
          lineIds,
        };
      }
    });

    return bestHub;
  };

  const canUseLineFromPosition = (userLat, userLon, line) => {
    if (!line) return { allowed: false, minD: 999999, viaHub: false, hubName: null };

    const { minD } = getDistanceToLine(userLat, userLon, line);
    if (minD <= maxAllowedDistance) {
      return { allowed: true, minD, viaHub: false, hubName: null };
    }

    const hubContext = getRailHubContext(userLat, userLon);
    if (hubContext && hubContext.lineIds.has(line.id)) {
      return { allowed: true, minD, viaHub: true, hubName: hubContext.nearestStopName };
    }

    return {
      allowed: false,
      minD,
      viaHub: false,
      hubName: hubContext?.nearestStopName || null
    };
  };

  // Distance helper in KM
  const getDistanceKm = (lat1, lon1, lat2, lon2) => {
    return getDistanceMeters(lat1, lon1, lat2, lon2) / 1000;
  };

  // SMART ANTI-SCAM THRESHOLD:
  // Base proximity: 45 meters (accommodates wide boulevards, multi-track stations, bus platforms, and vehicle interior)
  // Scales up slightly if GPS has high uncertainty (±15m), capped at 55 meters maximum.
  // Anyone at home or 60m+ away is strictly BLOCKED from diffusing.
  const gpsAccuracy = Math.round(userLocation?.accuracy || 10);
  const maxAllowedDistance = Math.min(55, Math.max(45, Math.round(gpsAccuracy * 1.4)));

  // Compute exact physical distance to all lines, sorted by proximity
  const allLinesDistances = useMemo(() => {
    if (!userLocation) return [];
    const list = [];
    STATIC_LINES.forEach(line => {
      const { minD, closestStop } = getDistanceToLine(userLocation.lat, userLocation.lon, line);
      list.push({
        ...line,
        distanceMeters: minD,
        closestStopName: closestStop?.name || 'Arrêt'
      });
    });
    return list.sort((a, b) => a.distanceMeters - b.distanceMeters);
  }, [userLocation]);

  const nearestLine = allLinesDistances[0] || null;
  const isAtTransitLine = nearestLine && nearestLine.distanceMeters <= maxAllowedDistance;

  const railHubContext = useMemo(() => {
    if (!userLocation) return null;
    return getRailHubContext(userLocation.lat, userLocation.lon);
  }, [userLocation, maxAllowedDistance]);

  const isAtRailHub = !!railHubContext;
  const isAtTransitContext = !!(isAtTransitLine || isAtRailHub);

  // Nearest-track rule + shared rail-hub rule (major stations with parallel tracks)
  const eligibleLines = useMemo(() => {
    if (!isAtTransitContext || !nearestLine) return [];

    const nearestDist = nearestLine.distanceMeters;
    const hubLineIds = railHubContext?.lineIds || new Set();

    return allLinesDistances.filter(line => {
      const sameNearestTrack =
        line.distanceMeters <= maxAllowedDistance &&
        Math.abs(line.distanceMeters - nearestDist) <= 10;

      const sharedRailHubTrack = hubLineIds.has(line.id);
      return sameNearestTrack || sharedRailHubTrack;
    });
  }, [allLinesDistances, isAtTransitContext, nearestLine, maxAllowedDistance, railHubContext]);

  // Backward compatible alias
  const nearbyLines = eligibleLines;

  // Auto-select nearest line
  useEffect(() => {
    if (eligibleLines.length > 0) {
      if (!selectedLineId || !eligibleLines.some(l => l.id === selectedLineId)) {
        setSelectedLineId(eligibleLines[0].id);
        setDirection(eligibleLines[0].directions[0] || '');
      }
    } else {
      setSelectedLineId('');
      setDirection('');
    }
  }, [eligibleLines]);

  const selectedLine = STATIC_LINES.find(l => l.id === selectedLineId);
  const selectedLineDistance = allLinesDistances.find(line => line.id === selectedLineId)?.distanceMeters;

  // Set default direction when line changes
  useEffect(() => {
    if (selectedLine && (!direction || !selectedLine.directions.includes(direction))) {
      setDirection(selectedLine.directions[0] || '');
    }
  }, [selectedLineId]);

  // Filter nearby lines by category & search
  const filteredNearbyLines = eligibleLines.filter(line => {
    if (selectedCategory !== 'all' && line.type_id !== selectedCategory) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      return line.short_name.toLowerCase().includes(q) || line.long_name.toLowerCase().includes(q);
    }
    return true;
  });

  // Check if a searched line is far away (scam warning)
  const distantSearchedLine = useMemo(() => {
    if (!searchQuery.trim() || !userLocation) return null;
    const q = searchQuery.toLowerCase().trim();
    const candidate = STATIC_LINES.find(l => 
      l.short_name.toLowerCase() === q || l.long_name.toLowerCase().includes(q)
    );
    if (!candidate) return null;

    const { minD } = getDistanceToLine(userLocation.lat, userLocation.lon, candidate);
    if (minD > maxAllowedDistance) {
      return {
        ...candidate,
        distanceMeters: minD,
        distanceDisplay: minD >= 1000 ? `${(minD / 1000).toFixed(1)} km` : `${minD} m`
      };
    }
    return null;
  }, [searchQuery, userLocation, maxAllowedDistance]);

  // Timer for active broadcast session
  useEffect(() => {
    let interval;
    if (isBroadcasting) {
      interval = setInterval(() => {
        setElapsedSeconds(prev => prev + 1);
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => clearInterval(interval);
  }, [isBroadcasting]);


  useEffect(() => {
    if (!isOpen || !isNativeAndroid()) return;
    let active = true;

    isBackgroundBroadcastRunning()
      .then((status) => {
        if (active) {
          setBackgroundLocationEnabled(!!status?.running);
        }
      })
      .catch(() => {
        if (active) {
          setBackgroundLocationEnabled(false);
        }
      });

    return () => {
      active = false;
    };
  }, [isOpen]);

  // Instant Unload Cleanup: if user closes tab/browser/app, immediately DELETE the vehicle
  useEffect(() => {
    if (!isBroadcasting || !broadcastSession?.sessionId || isNativeAndroid()) return;

    const cleanupOnExit = () => {
      const sessId = broadcastSession.sessionId;
      try {
        localStorage.removeItem('transit_broadcast_id');
      } catch (e) {}

      const url = `${SUPABASE_URL}/rest/v1/transit_live_locations?id=eq.${sessId}`;
      try {
        fetch(url, {
          method: 'DELETE',
          headers: {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          },
          keepalive: true,
        }).catch(() => {});
      } catch (e) {}
    };

    window.addEventListener('beforeunload', cleanupOnExit);
    window.addEventListener('pagehide', cleanupOnExit);

    return () => {
      window.removeEventListener('beforeunload', cleanupOnExit);
      window.removeEventListener('pagehide', cleanupOnExit);
    };
  }, [isBroadcasting, broadcastSession]);

  // Periodic Heartbeat (every 10s): keeps TTL fresh while broadcasting
  useEffect(() => {
    if (!isBroadcasting || !broadcastSession?.sessionId || backgroundLocationEnabled) return;

    const heartbeat = setInterval(() => {
      if (lastPosRef.current && selectedLine) {
        publishLiveLocation({
          id: broadcastSession.sessionId,
          line_id: selectedLineId,
          direction: direction,
          vehicle_label: `${selectedLine.short_name || 'Ligne'} (Signal direct)`,
          latitude: lastPosRef.current.lat,
          longitude: lastPosRef.current.lon,
          heading: 0,
          speed_kmh: currentSpeed,
          passenger_count: 1,
          is_simulated: false,
        }).catch(() => {});
      }
    }, 10000);

    return () => clearInterval(heartbeat);
  }, [isBroadcasting, broadcastSession, selectedLine, selectedLineId, direction, currentSpeed, backgroundLocationEnabled]);

  // Handle GPS location streaming to Supabase
  const startBroadcasting = async () => {
    if (!userLocation) {
      alert("Votre position GPS est obligatoire pour diffuser.");
      return;
    }

    if (!selectedLine) {
      alert("Veuillez sélectionner une ligne proche de vous.");
      return;
    }

    // Geofence validation: line itself OR shared multi-track rail hub (e.g. Barcelone / Tunis Marine / Tunis Ville)
    const lineAccess = canUseLineFromPosition(userLocation.lat, userLocation.lon, selectedLine);
    if (!lineAccess.allowed) {
      const hubHint = lineAccess.hubName
        ? ` (hub détecté: ${lineAccess.hubName}, mais cette ligne n'y passe pas)`
        : '';
      alert(`Diffusion bloquée (Sécurité anti-fraude) : Vous êtes à ${lineAccess.minD}m de cette ligne. Distance autorisée: ${maxAllowedDistance}m (GPS ±${gpsAccuracy}m)${hubHint}. Placez-vous sur la ligne ou dans une station commune de cette ligne.`);
      return;
    }

    const sessionId = `veh-${selectedLineId}-${Math.floor(1000 + Math.random() * 9000)}`;

    try {
      localStorage.setItem('transit_broadcast_id', sessionId);
    } catch (e) {}

    setIsBroadcasting(true);
    setBroadcastSession({
      sessionId,
      lineId: selectedLineId,
      direction,
      lineName: selectedLine.short_name,
      startedAt: new Date(),
    });
    setStatusMessage("Signal GPS verrouillé. Diffusion en direct active.");

    lastPosRef.current = { lat: userLocation.lat, lon: userLocation.lon, time: Date.now() };
    publishLiveLocation({
      id: sessionId,
      line_id: selectedLineId,
      direction: direction,
      vehicle_label: `${selectedLine.short_name || 'Ligne'} (Signal direct)`,
      latitude: userLocation.lat,
      longitude: userLocation.lon,
      heading: userLocation.heading || 0,
      speed_kmh: userLocation.speed || 0,
      passenger_count: 1,
      is_simulated: false,
    }).catch(console.error);

    if (isNativeAndroid()) {
      try {
        const nativeStart = await startBackgroundBroadcast({
          sessionId,
          lineId: selectedLineId,
          direction,
          lineShortName: selectedLine.short_name || 'Ligne',
          supabaseUrl: SUPABASE_URL,
          supabaseAnonKey: SUPABASE_ANON_KEY,
        });

        if (nativeStart?.started) {
          setBackgroundLocationEnabled(true);
          setStatusMessage('Diffusion en direct active (avant-plan + arrière-plan).');
        }
      } catch (error) {
        console.error('Background location start failed:', error);
        setBackgroundLocationEnabled(false);
        setStatusMessage('Diffusion active au premier plan. Autorisez la localisation en arrière-plan dans les paramètres Android.');
      }
    } else {
      setBackgroundLocationEnabled(false);
    }

    // High accuracy watchPosition loop
    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        let speedKmh = 0;
        if (pos.coords.speed !== null && pos.coords.speed !== undefined && !isNaN(pos.coords.speed)) {
          speedKmh = Math.max(0, Math.round(pos.coords.speed * 3.6));
        } else if (lastPosRef.current) {
          const dKm = getDistanceKm(lastPosRef.current.lat, lastPosRef.current.lon, pos.coords.latitude, pos.coords.longitude);
          const dtHours = (pos.timestamp - lastPosRef.current.time) / (1000 * 3600);
          if (dtHours > 0 && dtHours < 0.01) {
            speedKmh = Math.min(Math.round(dKm / dtHours), 120);
          }
        }
        lastPosRef.current = { lat: pos.coords.latitude, lon: pos.coords.longitude, time: pos.timestamp };
        setCurrentSpeed(speedKmh);

        publishLiveLocation({
          id: sessionId,
          line_id: selectedLineId,
          direction: direction,
          vehicle_label: `${selectedLine.short_name || 'Ligne'} (Signal direct)`,
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          heading: pos.coords.heading || 0,
          speed_kmh: speedKmh,
          passenger_count: 1,
          is_simulated: false,
        })
          .then(() => {
            const acc = pos.coords.accuracy ? `±${Math.round(pos.coords.accuracy)}m` : '';
            setStatusMessage(`Position GPS transmise en direct (${acc}) 🟢`);

            // Auto-cutoff: allow shared multi-track rail hubs before stopping
            const { minD: currentLineDist } = getDistanceToLine(pos.coords.latitude, pos.coords.longitude, selectedLine);
            const currentHub = getRailHubContext(pos.coords.latitude, pos.coords.longitude);
            const isOnSharedRailHubTrack = !!(currentHub && currentHub.lineIds.has(selectedLine.id));
            if (currentLineDist > Math.max(90, maxAllowedDistance * 3) && !isOnSharedRailHubTrack) {
              stopBroadcasting();
              alert(`Diffusion arrêtée : vous vous êtes éloigné du tracé de la ligne (${currentLineDist}m).`);
            }
          })
          .catch((err) => {
            console.error("Erreur mise à jour position:", err);
            setStatusMessage("Erreur de synchronisation réseau.");
          });
      },
      (error) => {
        console.warn("Erreur GPS:", error);
        setStatusMessage("Signal GPS momentanément indisponible.");
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 1000,
      }
    );
  };

  const stopBroadcasting = () => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }

    if (isNativeAndroid()) {
      stopBackgroundBroadcast().catch((error) => {
        console.error('Background location stop failed:', error);
      });
    }

    try {
      localStorage.removeItem('transit_broadcast_id');
    } catch (e) {}

    if (broadcastSession?.sessionId) {
      removeLiveLocation(broadcastSession.sessionId).catch(console.error);
    }

    setBackgroundLocationEnabled(false);
    setIsBroadcasting(false);
    setBroadcastSession(null);
    setStatusMessage("Partage de position arrêté.");
  };

  // Auto detect closest line within the chosen category
  const handleAutoDetectLine = () => {
    if (!userLocation) {
      setStatusMessage("⚠️ Activez votre GPS pour la détection automatique.");
      return;
    }

    const candidateLines = STATIC_LINES.filter(l => 
      selectedCategory === 'all' || l.type_id === selectedCategory
    );

    let nearestLine = null;
    let nearestStopName = '';
    let minDistance = Infinity;

    candidateLines.forEach(line => {
      line.stops.forEach(stop => {
        const d = Math.hypot(stop.lat - userLocation.lat, stop.lon - userLocation.lon);
        if (d < minDistance) {
          minDistance = d;
          nearestLine = line;
          nearestStopName = stop.name;
        }
      });
    });

    if (nearestLine) {
      setSelectedLineId(nearestLine.id);
      setDirection(nearestLine.directions[0] || '');
      setStatusMessage(`✅ Ligne détectée : ${nearestLine.short_name} (${nearestStopName})`);
    } else {
      setStatusMessage("Aucune ligne trouvée à proximité. Choisissez votre ligne ci-dessous.");
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-[1070] flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in pointer-events-auto"
      onClick={onClose}
    >
      <div 
        className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden text-slate-100 flex flex-col max-h-[92vh]"
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-5 border-b border-slate-800 bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-2xl ${isBroadcasting ? 'bg-emerald-500/20 text-emerald-400 animate-pulse' : 'bg-blue-600/20 text-blue-400'}`}>
              <Radio className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-base text-white">Je suis à bord</h2>
              <p className="text-xs text-slate-400">Diffusez la position de votre véhicule pour aider les voyageurs</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 sm:p-5 space-y-4 overflow-y-auto flex-1">
          
          {/* Active Broadcast Banner */}
          {isBroadcasting ? (
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-2xl p-4 text-center space-y-4">
              <div className="inline-flex items-center gap-2 bg-emerald-500/20 text-emerald-300 font-bold px-3 py-1 rounded-full text-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                Diffusion GPS en direct active
              </div>
              
              <div className="flex items-center justify-around py-2 bg-slate-900/60 rounded-xl border border-emerald-500/20">
                <div>
                  <div className="text-[11px] text-slate-400">Ligne active</div>
                  <div className="font-extrabold text-base text-white">{selectedLine?.short_name}</div>
                </div>
                <div className="w-px h-8 bg-slate-800"></div>
                <div>
                  <div className="text-[11px] text-slate-400">Vitesse</div>
                  <div className="font-extrabold text-base text-emerald-400">{currentSpeed} km/h</div>
                </div>
                <div className="w-px h-8 bg-slate-800"></div>
                <div>
                  <div className="text-[11px] text-slate-400">Durée</div>
                  <div className="font-extrabold text-base text-white">
                    {Math.floor(elapsedSeconds / 60)}m {elapsedSeconds % 60}s
                  </div>
                </div>
              </div>

              <div className="text-xs text-slate-300">
                Direction : <strong className="text-white">{direction}</strong>
              </div>

              <div className="space-y-1">
                <p className="text-xs text-emerald-300/90 font-medium">
                  {statusMessage || "Votre véhicule est maintenant visible sur la carte pour tous les voyageurs !"}
                </p>
                {backgroundLocationEnabled && (
                  <p className="text-[11px] text-emerald-400 font-semibold">Mode arrière-plan actif sur Android</p>
                )}
              </div>

              <button
                onClick={stopBroadcasting}
                className="w-full py-3 px-4 bg-red-600 hover:bg-red-500 text-white font-bold text-xs rounded-xl shadow-lg transition-all"
              >
                Arrêter la diffusion (Je suis descendu)
              </button>
            </div>
          ) : !userLocation ? (
            /* ANTI-SCAM GATEKEEPER 1: GPS Required */
            <div className="p-4 sm:p-6 text-center space-y-4">
              <div className="w-16 h-16 rounded-3xl bg-amber-500/20 text-amber-400 mx-auto flex items-center justify-center border border-amber-500/30">
                <LocateFixed className="w-8 h-8 animate-pulse" />
              </div>
              <div>
                <h3 className="font-extrabold text-base text-white">Localisation GPS Obligatoire</h3>
                <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto leading-relaxed">
                  Pour garantir l'exactitude des positions et <strong>empêcher les fausses diffusions à distance</strong>, vous devez activer votre GPS.
                </p>
              </div>
              
              <div className="p-3 bg-slate-800/60 rounded-2xl border border-slate-700 text-xs text-slate-300 flex items-start gap-2.5 max-w-sm mx-auto text-left">
                <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                <p>
                  <strong>Protection anti-fraude stricte :</strong> Seule la ligne sur laquelle vous êtes physiquement présent (à moins de 10 à 35 mètres) est sélectionnable.
                </p>
              </div>

              {onRequestGps ? (
                <button
                  type="button"
                  onClick={onRequestGps}
                  className="py-3 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm rounded-2xl shadow-xl shadow-blue-500/30 transition active:scale-95 flex items-center gap-2 mx-auto"
                >
                  <Navigation className="w-4 h-4" />
                  <span>Activer et autoriser mon GPS</span>
                </button>
              ) : (
                <p className="text-xs text-amber-300">Veuillez autoriser l'accès GPS dans votre navigateur.</p>
              )}
            </div>
          ) : !isAtTransitContext ? (
            /* ANTI-SCAM GATEKEEPER 2: User is not physically within strict ~10-35m of any transit line */
            <div className="p-4 sm:p-6 text-center space-y-4">
              <div className="w-16 h-16 rounded-3xl bg-amber-500/10 text-amber-400 mx-auto flex items-center justify-center border border-amber-500/30">
                <MapPin className="w-8 h-8 animate-bounce" />
              </div>
              <div>
                <h3 className="font-extrabold text-base text-white">Aucun transport à portée immédiate</h3>
                <p className="text-xs text-slate-300 mt-1 max-w-sm mx-auto leading-relaxed">
                  Votre position GPS indique que vous n'êtes pas sur le tracé ou à l'arrêt d'une ligne de transport en commun.
                </p>
              </div>

              {nearestLine && (
                <div className="p-3.5 bg-slate-800/80 rounded-2xl border border-slate-700 max-w-sm mx-auto text-left space-y-2">
                  <div className="text-[11px] uppercase tracking-wider font-bold text-slate-400 flex items-center justify-between">
                    <span>Ligne la plus proche détectée</span>
                    <span className="text-amber-400 font-extrabold">à {nearestLine.distanceMeters} m</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <span
                      className="px-2.5 py-1 rounded-xl text-white font-extrabold text-xs shadow flex-shrink-0"
                      style={{ backgroundColor: nearestLine.color }}
                    >
                      {nearestLine.short_name}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="font-bold text-xs text-white truncate">{nearestLine.long_name}</div>
                      <div className="text-[10px] text-slate-400">Arrêt proche : {nearestLine.closestStopName}</div>
                    </div>
                  </div>
                  <div className="pt-2 border-t border-slate-700/60 flex items-center justify-between text-[11px] text-slate-400">
                    <span>Distance autorisée (anti-fraude) :</span>
                    <span className="font-bold text-slate-200">Max {maxAllowedDistance}m (GPS ±{gpsAccuracy}m)</span>
                  </div>
                </div>
              )}

              <div className="p-3 bg-red-950/40 rounded-2xl border border-red-500/40 text-xs text-red-200 max-w-sm mx-auto text-left flex items-start gap-2.5">
                <ShieldCheck className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="leading-relaxed">
                  <strong>Sécurité anti-triche :</strong> Pour empêcher toute fausse diffusion à distance (depuis chez soi ou à 50m/100m), la diffusion est <strong>strictement réservée</strong> aux voyageurs physiquement à bord ou à l'arrêt (distance ≤ {maxAllowedDistance}m).
                </p>
              </div>

              {onRequestGps && (
                <button
                  type="button"
                  onClick={onRequestGps}
                  className="py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl border border-slate-700 transition flex items-center gap-2 mx-auto"
                >
                  <Navigation className="w-3.5 h-3.5 text-blue-400" />
                  <span>Actualiser ma position GPS</span>
                </button>
              )}
            </div>
          ) : (
            <>
              {/* Proximity GPS Badge - Certified onboard/at station */}
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex items-center justify-between text-xs">
                <div className="flex items-center gap-2.5 text-emerald-300 font-bold">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
                  <span>Position certifiée sur la ligne (à {selectedLineDistance ?? nearestLine?.distanceMeters}m)</span>
                </div>
                <span className="text-[10px] bg-emerald-950/80 px-2 py-0.5 rounded-full text-emerald-300 border border-emerald-500/40 font-mono">
                  GPS ±{gpsAccuracy}m
                </span>
              </div>

              {/* Ligne(s) détectée(s) sous vos pieds */}
              <div>
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                  Ligne détectée à votre emplacement
                </label>
                <div className="space-y-2">
                  {eligibleLines.map(line => (
                    <button
                      key={line.id}
                      type="button"
                      onClick={() => {
                        setSelectedLineId(line.id);
                        setDirection(line.directions[0] || '');
                      }}
                      className={`w-full p-3.5 rounded-2xl text-left flex items-center justify-between transition border ${
                        selectedLineId === line.id
                          ? 'bg-blue-600/30 border-blue-500 text-white shadow-lg ring-1 ring-blue-500'
                          : 'bg-slate-800/40 border-slate-800 text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <span
                          className="px-3 py-1.5 rounded-xl font-extrabold text-sm text-white flex-shrink-0 shadow"
                          style={{ backgroundColor: line.color }}
                        >
                          {getLineShortName(line, language)}
                        </span>
                        <div className="min-w-0">
                          <div className="font-bold text-xs truncate text-white">{getLineName(line, language)}</div>
                          <div className="text-[10px] text-slate-400 mt-0.5">
                            {language === 'ar' ? 'محطة : ' : 'Arrêt : '}<strong className="text-slate-300">{line.closestStopName}</strong>
                          </div>
                        </div>
                      </div>
                      <span className="text-[10px] bg-emerald-500/20 text-emerald-400 font-bold px-2.5 py-1 rounded-full border border-emerald-500/30 flex-shrink-0 ml-2">
                        à {line.distanceMeters}m
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Direction Selector */}
              {selectedLine && (
                <div className="p-3.5 bg-slate-800/50 border border-slate-700/80 rounded-2xl space-y-2.5">
                  <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    Direction du véhicule
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {selectedLine.directions.map(dir => (
                      <button
                        key={dir}
                        type="button"
                        onClick={() => setDirection(dir)}
                        className={`p-3 rounded-xl border text-xs font-bold text-center transition-all ${
                          direction === dir
                            ? 'bg-blue-600 border-blue-400 text-white shadow-md'
                            : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700/70'
                        }`}
                      >
                        Vers {dir}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Privacy Notice */}
              <div className="bg-slate-800/30 border border-slate-800 rounded-xl p-3 flex items-start gap-2.5 text-xs text-slate-400">
                <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <p>
                  <strong>100% Anonyme :</strong> Seule la position GPS en temps réel du véhicule est partagée avec les usagers attendant sur cette ligne.
                </p>
              </div>

              {/* Action Button */}
              <button
                onClick={startBroadcasting}
                disabled={!selectedLine || !direction}
                className="w-full py-3.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-sm rounded-2xl shadow-xl shadow-blue-500/25 flex items-center justify-center gap-2 transition-all active:scale-[0.99]"
              >
                <Radio className="w-4 h-4" />
                <span>Diffuser ma position en direct</span>
              </button>
            </>
          )}

        </div>

      </div>
    </div>
  );
}

