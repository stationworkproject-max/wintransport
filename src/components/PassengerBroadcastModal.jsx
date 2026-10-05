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
import { 
  broadcastPing, 
  broadcastLeave, 
  fetchLiveVehicles, 
  publishLiveLocation, 
  removeLiveLocation, 
  SUPABASE_URL, 
  SUPABASE_ANON_KEY 
} from '../supabase';
import { isNativeAndroid, startBackgroundBroadcast, stopBackgroundBroadcast, isBackgroundBroadcastRunning } from '../native/backgroundBroadcast';
import { getLineName, getLineShortName } from '../utils/i18n';
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
  const [broadcasterRole, setBroadcasterRole] = useState(broadcastSession?.role || 'OFF'); // 'OFF' | 'LEADER' | 'STANDBY'
  const [currentVehicleId, setCurrentVehicleId] = useState(broadcastSession?.sessionId || '');
  
  const watchIdRef = useRef(null);
  const lastPosRef = useRef(null);
  const latestPosRef = useRef(null);
  const broadcasterIdRef = useRef(null);
  const transmissionTimerRef = useRef(null);
  const standbyCheckTimerRef = useRef(null);
  const directionAnchorRef = useRef(null);
  const directionStreakRef = useRef(0);

  // Initialize or restore persistent unique client device identifier
  useEffect(() => {
    let devId = null;
    try {
      devId = localStorage.getItem('transit_device_id');
      if (!devId) {
        devId = 'dev_' + Math.random().toString(36).substring(2, 10);
        localStorage.setItem('transit_device_id', devId);
      }
    } catch (e) {
      devId = 'dev_' + Math.random().toString(36).substring(2, 10);
    }
    broadcasterIdRef.current = devId;
  }, []);

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

  const canUseLineFromPosition = (userLat, userLon, line) => {
    if (!line) return { allowed: false, minD: 999999 };

    const { minD } = getDistanceToLine(userLat, userLon, line);
    if (minD <= maxAllowedDistance) {
      return { allowed: true, minD };
    }

    return {
      allowed: false,
      minD
    };
  };

  // Distance helper in KM
  const getDistanceKm = (lat1, lon1, lat2, lon2) => {
    return getDistanceMeters(lat1, lon1, lat2, lon2) / 1000;
  };

  // Inferred Direction Engine: computes whether physical movement aligns with Aller (0) or Retour (1)
  const inferTransitDirection = (line, currentLat, currentLon, prevLat, prevLon, heading) => {
    if (!line || !line.directions || line.directions.length < 2) return null;
    if (!currentLat || !currentLon || !prevLat || !prevLon) return null;

    const dTravel = getDistanceMeters(prevLat, prevLon, currentLat, currentLon);
    if (dTravel < 25) return null; // Need at least 25m of physical displacement

    const stopsAller = (line.stops_aller && line.stops_aller.length >= 2)
      ? line.stops_aller
      : (line.stops && line.stops.length >= 2 ? line.stops : null);

    const stopsRetour = (line.stops_retour && line.stops_retour.length >= 2)
      ? line.stops_retour
      : (stopsAller ? [...stopsAller].reverse() : null);

    if (!stopsAller || stopsAller.length < 2) return null;

    // Terminus destinations
    const destAller = stopsAller[stopsAller.length - 1];
    const destRetour = stopsRetour ? stopsRetour[stopsRetour.length - 1] : stopsAller[0];

    // Distance deltas to each terminus
    const distToAllerDestCurr = getDistanceMeters(currentLat, currentLon, destAller.lat, destAller.lon);
    const distToAllerDestPrev = getDistanceMeters(prevLat, prevLon, destAller.lat, destAller.lon);

    const distToRetourDestCurr = getDistanceMeters(currentLat, currentLon, destRetour.lat, destRetour.lon);
    const distToRetourDestPrev = getDistanceMeters(prevLat, prevLon, destRetour.lat, destRetour.lon);

    const dDeltaAller = distToAllerDestCurr - distToAllerDestPrev; // Negative = approaching Aller terminus
    const dDeltaRetour = distToRetourDestCurr - distToRetourDestPrev; // Negative = approaching Retour terminus

    // Shape track bearing alignment
    const shape = TRANSIT_SHAPES[line.id + '_aller'] || TRANSIT_SHAPES[line.id];
    let headingAlignment = 0; // +1 = Aller, -1 = Retour

    if (heading !== null && heading !== undefined && !isNaN(heading) && shape && shape.length >= 2) {
      let minSegD = Infinity;
      let segIdx = 0;
      for (let i = 0; i < shape.length - 1; i++) {
        const pA = shape[i];
        const pB = shape[i + 1];
        const d = getDistanceToSegment(currentLat, currentLon, pA[0], pA[1], pB[0], pB[1]);
        if (d < minSegD) {
          minSegD = d;
          segIdx = i;
        }
      }

      if (minSegD <= 60) {
        const pA = shape[segIdx];
        const pB = shape[segIdx + 1];
        const y = Math.sin((pB[1] - pA[1]) * Math.PI / 180) * Math.cos(pB[0] * Math.PI / 180);
        const x = Math.cos(pA[0] * Math.PI / 180) * Math.sin(pB[0] * Math.PI / 180) -
                  Math.sin(pA[0] * Math.PI / 180) * Math.cos(pB[0] * Math.PI / 180) * Math.cos((pB[1] - pA[1]) * Math.PI / 180);
        const segBearingDeg = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;

        const diffAngle = Math.abs(((heading - segBearingDeg) + 180) % 360 - 180);
        if (diffAngle < 55) {
          headingAlignment = 1; // strongly Aller
        } else if (diffAngle > 125) {
          headingAlignment = -1; // strongly Retour
        }
      }
    }

    let scoreAller = 0;
    let scoreRetour = 0;

    if (dDeltaAller < -8 && dDeltaRetour > 8) {
      scoreAller += 2;
    } else if (dDeltaRetour < -8 && dDeltaAller > 8) {
      scoreRetour += 2;
    }

    if (headingAlignment === 1) scoreAller += 2;
    if (headingAlignment === -1) scoreRetour += 2;

    if (scoreAller >= 2 && scoreAller > scoreRetour) return 0;
    if (scoreRetour >= 2 && scoreRetour > scoreAller) return 1;

    return null;
  };

  // SMART ANTI-SCAM THRESHOLD:
  // Strictly no more than 10 meters based on GPS accuracy.
  // Anyone further than 10 meters is strictly BLOCKED from diffusing.
  const gpsAccuracy = Math.round(userLocation?.accuracy || 10);
  const maxAllowedDistance = Math.min(10, Math.max(6, Math.round(gpsAccuracy)));

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
  const isAtTransitContext = Boolean(isAtTransitLine);

  // Strictly lines where user is physically within <= maxAllowedDistance (never exceeds 10m)
  const eligibleLines = useMemo(() => {
    if (!isAtTransitContext || !nearestLine) return [];

    return allLinesDistances.filter(line => {
      return line.distanceMeters <= maxAllowedDistance;
    });
  }, [allLinesDistances, isAtTransitContext, nearestLine, maxAllowedDistance]);

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

  // Instant Unload Cleanup: if user closes tab/browser/app, immediately leave broadcast lease
  useEffect(() => {
    if (!isBroadcasting || !currentVehicleId || isNativeAndroid()) return;

    const cleanupOnExit = () => {
      const sessId = currentVehicleId;
      const bId = broadcasterIdRef.current;
      try {
        localStorage.removeItem('transit_broadcast_id');
      } catch (e) {}

      if (sessId && bId) {
        broadcastLeave(sessId, bId);
      }
    };

    window.addEventListener('beforeunload', cleanupOnExit);
    window.addEventListener('pagehide', cleanupOnExit);

    return () => {
      window.removeEventListener('beforeunload', cleanupOnExit);
      window.removeEventListener('pagehide', cleanupOnExit);
    };
  }, [isBroadcasting, currentVehicleId]);

  // ── 1. LEADER Dynamic Transmission Loop ──
  // Dynamic GPS sampling: stopped (<= 5 km/h) = 20s; moving (> 5 km/h) = 8s + jitter (±1.5s)
  // Writes connectionless PostgREST RPC pings, zero WAL overhead
  useEffect(() => {
    if (!isBroadcasting || broadcasterRole !== 'LEADER' || !currentVehicleId) {
      if (transmissionTimerRef.current) {
        clearTimeout(transmissionTimerRef.current);
        transmissionTimerRef.current = null;
      }
      return;
    }

    let isCancelled = false;

    const scheduleNextTransmission = () => {
      const spd = latestPosRef.current?.speed || 0;
      // Stopped: 20s. Moving: 8s + jitter (6.5s to 9.5s)
      const delay = spd <= 5 
        ? 20000 
        : Math.max(6000, 8000 + Math.round((Math.random() * 3000 - 1500)));

      transmissionTimerRef.current = setTimeout(async () => {
        if (isCancelled || !latestPosRef.current || !selectedLine) return;

        try {
          const directionIndex = (selectedLine.directions && selectedLine.directions.indexOf(direction) === 1) ? 1 : 0;
          const res = await broadcastPing({
            vehicleId: currentVehicleId,
            routeId: selectedLineId,
            lineName: selectedLine.short_name || 'Ligne',
            networkType: selectedLine.type_id || 'bus',
            direction: directionIndex,
            directionName: direction || '',
            latitude: latestPosRef.current.lat,
            longitude: latestPosRef.current.lon,
            speed: latestPosRef.current.speed || 0,
            bearing: latestPosRef.current.heading || 0,
            broadcasterId: broadcasterIdRef.current,
          });

          if (res?.is_leader === false) {
            // Relinquished or another broadcaster superseded
            setBroadcasterRole('STANDBY');
            setStatusMessage("En Veille Active : un autre voyageur diffuse ce véhicule 🟡");
            return;
          }

          const acc = latestPosRef.current.accuracy ? `±${Math.round(latestPosRef.current.accuracy)}m` : '';
          setStatusMessage(`Émetteur Principal : Signal direct synchronisé (${acc}) 🟢`);
        } catch (e) {
          console.error("Leader transmission ping failed:", e);
        }

        if (!isCancelled) {
          scheduleNextTransmission();
        }
      }, delay);
    };

    scheduleNextTransmission();

    return () => {
      isCancelled = true;
      if (transmissionTimerRef.current) {
        clearTimeout(transmissionTimerRef.current);
        transmissionTimerRef.current = null;
      }
    };
  }, [isBroadcasting, broadcasterRole, currentVehicleId, selectedLine, selectedLineId, direction]);

  // ── 2. STANDBY Failover & Auto-Divergence Promotion Engine ──
  // Checks every 4 seconds:
  // A) If leader silent > 15 seconds: takes over immediately!
  // B) Divergence Split: If leader has moved away (> 22m), we are on a DIFFERENT vehicle
  //    (e.g., two buses queued 7-10m apart at a stop; the front bus left while this one stayed).
  //    Auto-splits and immediately creates an independent vehicle!
  useEffect(() => {
    if (!isBroadcasting || broadcasterRole !== 'STANDBY' || !currentVehicleId) {
      if (standbyCheckTimerRef.current) {
        clearInterval(standbyCheckTimerRef.current);
        standbyCheckTimerRef.current = null;
      }
      return;
    }

    standbyCheckTimerRef.current = setInterval(async () => {
      try {
        const vehicles = await fetchLiveVehicles();
        const cur = vehicles.find(v => v.id === currentVehicleId);

        let shouldPromote = false;
        let shouldSplit = false;

        if (!cur) {
          // Vehicle evicted or silent > 30s
          shouldPromote = true;
        } else {
          const ageMs = Date.now() - new Date(cur.updated_at).getTime();
          if (ageMs > 15000) {
            // Leader timed out (> 15s lease expiry)
            shouldPromote = true;
          } else if (latestPosRef.current) {
            // Divergence Check: If distance to leader > 22m, vehicles have separated!
            const distToLeader = getDistanceMeters(
              latestPosRef.current.lat,
              latestPosRef.current.lon,
              cur.latitude,
              cur.longitude
            );
            if (distToLeader > 22) {
              shouldSplit = true;
            }
          }
        }

        if ((shouldPromote || shouldSplit) && latestPosRef.current && selectedLine) {
          const directionIndex = (selectedLine.directions && selectedLine.directions.indexOf(direction) === 1) ? 1 : 0;
          const targetId = shouldSplit
            ? `veh_${selectedLineId}_d${directionIndex}_${Math.random().toString(36).substring(2, 8)}`
            : currentVehicleId;

          if (shouldSplit) {
            setCurrentVehicleId(targetId);
            try {
              localStorage.setItem('transit_broadcast_id', targetId);
            } catch (e) {}
          }

          const res = await broadcastPing({
            vehicleId: targetId,
            routeId: selectedLineId,
            lineName: selectedLine.short_name || 'Ligne',
            networkType: selectedLine.type_id || 'bus',
            direction: directionIndex,
            directionName: direction || '',
            latitude: latestPosRef.current.lat,
            longitude: latestPosRef.current.lon,
            speed: latestPosRef.current.speed || 0,
            bearing: latestPosRef.current.heading || 0,
            broadcasterId: broadcasterIdRef.current,
          });

          if (res?.is_leader === true) {
            setBroadcasterRole('LEADER');
            setStatusMessage(
              shouldSplit
                ? "Séparation automatique : Véhicule distinct créé et diffusé en direct 🟢"
                : "Relais GPS pris en direct ! Vous êtes désormais l'Émetteur Principal 🟢"
            );
          }
        }
      } catch (e) {
        console.warn("Standby failover/split check error:", e);
      }
    }, 4000);

    return () => {
      if (standbyCheckTimerRef.current) {
        clearInterval(standbyCheckTimerRef.current);
        standbyCheckTimerRef.current = null;
      }
    };
  }, [isBroadcasting, broadcasterRole, currentVehicleId, selectedLine, selectedLineId, direction]);

  // Manual split trigger if user knows they are in a different queued vehicle
  const handleForceSplitVehicle = async () => {
    if (!latestPosRef.current || !selectedLine) return;
    const directionIndex = (selectedLine.directions && selectedLine.directions.indexOf(direction) === 1) ? 1 : 0;
    const newVehicleId = `veh_${selectedLineId}_d${directionIndex}_${Math.random().toString(36).substring(2, 8)}`;
    setCurrentVehicleId(newVehicleId);
    try {
      localStorage.setItem('transit_broadcast_id', newVehicleId);
    } catch (e) {}

    try {
      const res = await broadcastPing({
        vehicleId: newVehicleId,
        routeId: selectedLineId,
        lineName: selectedLine.short_name || 'Ligne',
        networkType: selectedLine.type_id || 'bus',
        direction: directionIndex,
        directionName: direction || '',
        latitude: latestPosRef.current.lat,
        longitude: latestPosRef.current.lon,
        speed: latestPosRef.current.speed || 0,
        bearing: latestPosRef.current.heading || 0,
        broadcasterId: broadcasterIdRef.current,
      });
      if (res?.is_leader === true) {
        setBroadcasterRole('LEADER');
        setStatusMessage("Véhicule séparé avec succès ! Vous êtes désormais l'Émetteur Principal 🟢");
      }
    } catch (err) {
      console.error("Manual vehicle split error:", err);
    }
  };

  // Handle GPS location streaming with Spatial Clustering & Leader Election
  const startBroadcasting = async () => {
    if (!userLocation) {
      alert("Votre position GPS est obligatoire pour diffuser.");
      return;
    }

    if (!selectedLine) {
      alert("Veuillez sélectionner une ligne proche de vous.");
      return;
    }

    // Geofence validation: strict physical proximity check (<= 10m)
    const lineAccess = canUseLineFromPosition(userLocation.lat, userLocation.lon, selectedLine);
    if (!lineAccess.allowed) {
      alert(`Diffusion bloquée (Sécurité anti-fraude) : Vous êtes à ${lineAccess.minD}m de cette ligne. Distance autorisée: ${maxAllowedDistance}m (GPS ±${gpsAccuracy}m). Vous devez être à 10m maximum de la ligne pour diffuser.`);
      return;
    }

    const directionIndex = (selectedLine.directions && selectedLine.directions.indexOf(direction) === 1) ? 1 : 0;
    const bId = broadcasterIdRef.current || ('dev_' + Math.random().toString(36).substring(2, 10));

    // Spatial clustering: detect if an active vehicle on this line & direction already exists nearby.
    // Tight 18m threshold (max vehicle length 12m + GPS buffer) + kinematic motion check.
    let targetVehicleId = null;
    const clusteringThresholdMeters = Math.min(22, Math.max(12, (userLocation.accuracy || 10) + 4));
    const userSpdKmh = userLocation.speed ? Math.round(userLocation.speed * 3.6) : 0;

    try {
      const activeList = await fetchLiveVehicles();
      const sameLineSameDir = activeList.filter(v => 
        v.line_id === selectedLineId && Number(v.direction) === directionIndex
      );
      for (const veh of sameLineSameDir) {
        const d = getDistanceMeters(userLocation.lat, userLocation.lon, veh.latitude, veh.longitude);
        if (d <= clusteringThresholdMeters) {
          // Kinematic check: If candidate vehicle is moving fast (> 15 km/h) and user is stationary (<= 4 km/h),
          // it's an overtaking/passing vehicle on the same street, NOT our vehicle!
          const vehSpd = veh.speed || 0;
          if (vehSpd > 15 && userSpdKmh <= 4) {
            continue;
          }
          // If both moving, speeds must be somewhat correlated
          if (vehSpd > 10 && userSpdKmh > 10 && Math.abs(vehSpd - userSpdKmh) > 18) {
            continue;
          }
          targetVehicleId = veh.id;
          break;
        }
      }
    } catch (e) {
      console.warn("Clustering lookup error:", e);
    }

    if (!targetVehicleId) {
      targetVehicleId = `veh_${selectedLineId}_d${directionIndex}_${Math.random().toString(36).substring(2, 8)}`;
    }

    setCurrentVehicleId(targetVehicleId);
    try {
      localStorage.setItem('transit_broadcast_id', targetVehicleId);
    } catch (e) {}

    latestPosRef.current = {
      lat: userLocation.lat,
      lon: userLocation.lon,
      speed: userLocation.speed || 0,
      heading: userLocation.heading || 0,
      accuracy: userLocation.accuracy || 10,
      time: Date.now()
    };
    lastPosRef.current = latestPosRef.current;
    directionAnchorRef.current = { lat: userLocation.lat, lon: userLocation.lon };
    directionStreakRef.current = 0;

    // Initial ping to claim lease or enter standby
    let isLeader = false;
    try {
      const pingResult = await broadcastPing({
        vehicleId: targetVehicleId,
        routeId: selectedLineId,
        lineName: selectedLine.short_name || 'Ligne',
        networkType: selectedLine.type_id || 'bus',
        direction: directionIndex,
        directionName: direction || '',
        latitude: userLocation.lat,
        longitude: userLocation.lon,
        speed: userLocation.speed || 0,
        bearing: userLocation.heading || 0,
        broadcasterId: bId,
      });
      isLeader = pingResult?.is_leader === true;
    } catch (err) {
      console.error("Initial broadcast ping error:", err);
      isLeader = true;
    }

    setIsBroadcasting(true);
    setBroadcasterRole(isLeader ? 'LEADER' : 'STANDBY');
    setBroadcastSession({
      sessionId: targetVehicleId,
      lineId: selectedLineId,
      direction,
      directionIndex,
      lineName: selectedLine.short_name,
      networkType: selectedLine.type_id,
      startedAt: new Date(),
      role: isLeader ? 'LEADER' : 'STANDBY',
    });

    if (isLeader) {
      setStatusMessage("Émetteur Principal actif. Signal direct synchronisé 🟢");
    } else {
      setStatusMessage("En Veille Active : un passager diffuse déjà ce véhicule. Relais prêt 🟡");
    }

    if (isNativeAndroid()) {
      try {
        const nativeStart = await startBackgroundBroadcast({
          sessionId: targetVehicleId,
          lineId: selectedLineId,
          direction,
          directionIndex,
          networkType: selectedLine.type_id,
          lineShortName: selectedLine.short_name || 'Ligne',
          supabaseUrl: SUPABASE_URL,
          supabaseAnonKey: SUPABASE_ANON_KEY,
        });

        if (nativeStart?.started) {
          setBackgroundLocationEnabled(true);
        }
      } catch (error) {
        console.error('Background location start failed:', error);
        setBackgroundLocationEnabled(false);
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
        } else if (latestPosRef.current) {
          const dKm = getDistanceKm(latestPosRef.current.lat, latestPosRef.current.lon, pos.coords.latitude, pos.coords.longitude);
          const dtHours = (pos.timestamp - latestPosRef.current.time) / (1000 * 3600);
          if (dtHours > 0 && dtHours < 0.01) {
            speedKmh = Math.min(Math.round(dKm / dtHours), 120);
          }
        }

        latestPosRef.current = {
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          speed: speedKmh,
          heading: pos.coords.heading || 0,
          accuracy: pos.coords.accuracy || 10,
          time: pos.timestamp
        };
        lastPosRef.current = latestPosRef.current;
        setCurrentSpeed(speedKmh);

        // Auto-Direction Correction: detect if the user selected Retour instead of Aller (or vice versa) by mistake
        if (speedKmh >= 10 && selectedLine && selectedLine.directions?.length > 1) {
          if (!directionAnchorRef.current) {
            directionAnchorRef.current = { lat: pos.coords.latitude, lon: pos.coords.longitude };
          } else {
            const dFromAnchor = getDistanceMeters(
              directionAnchorRef.current.lat,
              directionAnchorRef.current.lon,
              pos.coords.latitude,
              pos.coords.longitude
            );

            if (dFromAnchor >= 40) {
              const currentDirIdx = (selectedLine.directions && selectedLine.directions.indexOf(direction) === 1) ? 1 : 0;
              const inferredDir = inferTransitDirection(
                selectedLine,
                pos.coords.latitude,
                pos.coords.longitude,
                directionAnchorRef.current.lat,
                directionAnchorRef.current.lon,
                pos.coords.heading
              );

              if (inferredDir !== null && inferredDir !== currentDirIdx) {
                directionStreakRef.current = (directionStreakRef.current || 0) + 1;
                if (directionStreakRef.current >= 2) {
                  // Confirmed direction error! Reverse / auto-correct direction
                  const correctedDirName = selectedLine.directions[inferredDir];
                  setDirection(correctedDirName);
                  directionStreakRef.current = 0;

                  const oldId = currentVehicleId;
                  const newId = `veh_${selectedLineId}_d${inferredDir}_${Math.random().toString(36).substring(2, 8)}`;
                  setCurrentVehicleId(newId);
                  try { localStorage.setItem('transit_broadcast_id', newId); } catch (e) {}

                  if (broadcasterRole === 'LEADER') {
                    broadcastPing({
                      vehicleId: newId,
                      routeId: selectedLineId,
                      lineName: selectedLine.short_name || 'Ligne',
                      networkType: selectedLine.type_id || 'bus',
                      direction: inferredDir,
                      directionName: correctedDirName,
                      latitude: pos.coords.latitude,
                      longitude: pos.coords.longitude,
                      speed: speedKmh,
                      bearing: pos.coords.heading || 0,
                      broadcasterId: broadcasterIdRef.current,
                    }).catch(console.error);

                    if (oldId) {
                      broadcastLeave(oldId, broadcasterIdRef.current).catch(console.error);
                    }
                  }

                  setStatusMessage(
                    `🧭 Direction inversée automatiquement : Déplacement détecté vers ${correctedDirName} (${inferredDir === 0 ? 'Sens Aller ➡️' : 'Sens Retour ⬅️'})`
                  );
                }
              } else {
                directionStreakRef.current = 0;
              }

              // Advance anchor
              directionAnchorRef.current = { lat: pos.coords.latitude, lon: pos.coords.longitude };
            }
          }
        }

        // Auto-cutoff: user must remain on the transit line (within 25m accounting for vehicle turn / GPS drift)
        const { minD: currentLineDist } = getDistanceToLine(pos.coords.latitude, pos.coords.longitude, selectedLine);
        if (currentLineDist > Math.max(25, maxAllowedDistance * 2.5)) {
          stopBroadcasting();
          alert(`Diffusion arrêtée : vous vous êtes éloigné du tracé de la ligne (${currentLineDist}m).`);
        }
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
    if (transmissionTimerRef.current !== null) {
      clearTimeout(transmissionTimerRef.current);
      transmissionTimerRef.current = null;
    }
    if (standbyCheckTimerRef.current !== null) {
      clearInterval(standbyCheckTimerRef.current);
      standbyCheckTimerRef.current = null;
    }

    if (isNativeAndroid()) {
      stopBackgroundBroadcast().catch((error) => {
        console.error('Background location stop failed:', error);
      });
    }

    const sessId = currentVehicleId || broadcastSession?.sessionId;
    const bId = broadcasterIdRef.current;
    if (sessId && bId) {
      broadcastLeave(sessId, bId).catch(console.error);
    }

    try {
      localStorage.removeItem('transit_broadcast_id');
    } catch (e) {}

    setBackgroundLocationEnabled(false);
    setIsBroadcasting(false);
    setBroadcasterRole('OFF');
    setCurrentVehicleId('');
    setBroadcastSession(null);
    directionAnchorRef.current = null;
    directionStreakRef.current = 0;
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
            <div className={`border rounded-2xl p-4 text-center space-y-4 ${
              broadcasterRole === 'LEADER'
                ? 'bg-emerald-500/10 border-emerald-500/30'
                : 'bg-amber-500/10 border-amber-500/30'
            }`}>
              {broadcasterRole === 'LEADER' ? (
                <div className="inline-flex items-center gap-2 bg-emerald-500/20 text-emerald-300 font-bold px-3 py-1 rounded-full text-xs">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                  🟢 Émetteur Principal (Direct GPS actif)
                </div>
              ) : (
                <div className="inline-flex items-center gap-2 bg-amber-500/20 text-amber-300 font-bold px-3 py-1 rounded-full text-xs">
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                  🟡 En Veille Active (Relais automatique prêt)
                </div>
              )}
              
              <div className="flex items-center justify-around py-2 bg-slate-900/60 rounded-xl border border-slate-700/60">
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

              <div className="space-y-1.5">
                <p className={`text-xs font-medium ${broadcasterRole === 'LEADER' ? 'text-emerald-300/90' : 'text-amber-300/90'}`}>
                  {statusMessage || (broadcasterRole === 'LEADER' ? "Signal GPS diffusé en direct pour tous les voyageurs !" : "En veille active : prêt à prendre le relais")}
                </p>

                {broadcasterRole === 'LEADER' ? (
                  <div className="p-2.5 bg-emerald-950/40 border border-emerald-500/20 rounded-xl text-[11px] text-emerald-200/90 text-left flex items-start gap-2">
                    <Zap className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                    <span>Cadence adaptative : émission toutes les 8s en route (&gt; 5 km/h) et 20s à l'arrêt pour économiser la batterie.</span>
                  </div>
                ) : (
                  <div className="p-2.5 bg-amber-950/40 border border-amber-500/20 rounded-xl text-[11px] text-amber-200/90 text-left flex items-start gap-2">
                    <ShieldCheck className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                    <span>Un autre voyageur émet déjà le signal sur ce véhicule. Vos données sont préservées ; en cas d'interruption, vous prendrez le relais immédiatement.</span>
                  </div>
                )}

                {broadcasterRole === 'STANDBY' && (
                  <div className="pt-2 border-t border-amber-500/20">
                    <button
                      type="button"
                      onClick={handleForceSplitVehicle}
                      className="w-full py-2.5 px-3 bg-amber-600/30 hover:bg-amber-600/50 border border-amber-500/40 text-amber-200 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-sm active:scale-95"
                    >
                      <span>🚌</span>
                      <span>Vous êtes dans un autre bus juste derrière ? Cliquez pour séparer</span>
                    </button>
                  </div>
                )}

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
                  <strong>Sécurité anti-triche :</strong> Pour empêcher toute fausse diffusion à distance (depuis chez soi ou à plus de 10m), la diffusion est <strong>strictement réservée</strong> aux voyageurs physiquement à bord ou sur la ligne (distance ≤ {maxAllowedDistance}m).
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

