import React, { useState, useEffect, useRef, useMemo, memo } from 'react';
import L from 'leaflet';
import { STATIC_LINES } from '../data/staticTransit';
import { Users, Navigation, Clock, ShieldCheck, AlertCircle, X, LocateFixed, Layers, Search, Compass, MapPin, Radio, Footprints, ArrowRight, Target } from 'lucide-react';
import { getStationName, getLineName, getLineShortName, getDirectionLabel } from '../utils/i18n';
import { getWalkingRoute, getTransitRideSegment } from '../utils/itineraryRouter';

export const GOOGLE_MAPS_API_KEY = 'AIzaSyD5AZ-rNY0NGtkFDZUyB3cwPKH3CiUit6I';

/**
 * Distance in meters between two lat/lon coordinates
 */
export function getDistanceMeters(lat1, lon1, lat2, lon2) {
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
}

/**
 * Offsets a polyline perpendicularly to the RIGHT-HAND side of its travel heading.
 * This spaces the "Aller" (going) and "Retour" (backing) tracks into separate driving lanes
 * so they are never drawn directly on top of each other.
 */
export function offsetPolylineRight(points, offsetMeters = 2.5) {
  if (!points || points.length < 2) return points || [];
  const len = points.length;
  let sumLat = 0;
  for (let i = 0; i < len; i++) sumLat += points[i][0];
  const meanLat = (sumLat / len) * (Math.PI / 180.0);
  const cosLat = Math.cos(meanLat);
  const lat0 = points[0][0];
  const lon0 = points[0][1];

  const ptsM = new Array(len);
  for (let i = 0; i < len; i++) {
    ptsM[i] = [
      (points[i][1] - lon0) * cosLat * 111320.0,
      (points[i][0] - lat0) * 111320.0
    ];
  }

  const result = new Array(len);
  for (let i = 0; i < len; i++) {
    let dx, dy;
    if (i === 0) {
      dx = ptsM[1][0] - ptsM[0][0];
      dy = ptsM[1][1] - ptsM[0][1];
    } else if (i === len - 1) {
      dx = ptsM[len - 1][0] - ptsM[len - 2][0];
      dy = ptsM[len - 1][1] - ptsM[len - 2][1];
    } else {
      const dx1 = ptsM[i][0] - ptsM[i - 1][0];
      const dy1 = ptsM[i][1] - ptsM[i - 1][1];
      const l1 = Math.hypot(dx1, dy1) || 1.0;
      const dx2 = ptsM[i + 1][0] - ptsM[i][0];
      const dy2 = ptsM[i + 1][1] - ptsM[i][1];
      const l2 = Math.hypot(dx2, dy2) || 1.0;
      dx = (dx1 / l1) + (dx2 / l2);
      dy = (dy1 / l1) + (dy2 / l2);
    }
    const hyp = Math.hypot(dx, dy) || 1.0;
    const tx = dx / hyp;
    const ty = dy / hyp;
    const nx = ty;
    const ny = -tx;

    const ox = ptsM[i][0] + nx * offsetMeters;
    const oy = ptsM[i][1] + ny * offsetMeters;

    const oLat = lat0 + (oy / 111320.0);
    const oLon = lon0 + (ox / (111320.0 * cosLat));
    result[i] = [parseFloat(oLat.toFixed(6)), parseFloat(oLon.toFixed(6))];
  }
  return result;
}

function TransitMap({
  activeNetwork,
  liveLocations,
  selectedLine,
  onSelectLine,
  selectedDirection = 0,
  onDirectionChange,
  userLocation,
  onSelectStation,
  onOpenSchedule,
  onRequestGps,
  gpsStatus,
  gpsErrorMsg,
  onDismissGpsError,
  onOpenTripPlanner,
  activeItinerary = null,
  onClearItinerary,
  radarRadiusKm = 1.5,
  onUpdateRadarRadius,
  language = 'fr',
  theme = 'dark'
}) {
  const isAr = language === 'ar';
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const tileLayerRef = useRef(null);
  const lineLayersRef = useRef({});
  const stationLayersRef = useRef({});
  const itineraryLayersRef = useRef([]);
  const activeItineraryRef = useRef(activeItinerary);
  activeItineraryRef.current = activeItinerary;
  const itineraryFittedRef = useRef(null);
  const vehicleMarkersRef = useRef({});
  const vehicleAnimRef = useRef({});
  const animFrameIdRef = useRef(null);
  const userMarkerRef = useRef(null);
  const userAccuracyCircleRef = useRef(null);
  const radarCircleRef = useRef(null);

  // Dropdown Refs for outside click handling
  const radarDropdownRef = useRef(null);
  const radarButtonRef = useRef(null);
  const layerDropdownRef = useRef(null);
  const layerButtonRef = useRef(null);
  const searchDropdownRef = useRef(null);

  // Excess vehicles count (when > 15 vehicles near user)
  const [excessVehiclesCount, setExcessVehiclesCount] = useState(0);

  // Asynchronously load high-density route geometries to keep main JS bundle tiny and load fast
  const [transitShapes, setTransitShapes] = useState({});
  useEffect(() => {
    import('../data/transitShapes.json')
      .then((mod) => {
        setTransitShapes(mod.default || mod);
      })
      .catch((err) => {
        console.warn('Transit shapes deferred load warning:', err);
      });
  }, []);

  // Keep latest liveLocations, userLocation and radarRadius in refs for high-frequency render interval
  const liveLocationsRef = useRef(liveLocations);
  const activeNetworkRef = useRef(activeNetwork);
  const selectedLineRef = useRef(selectedLine);
  const userLocationRef = useRef(userLocation);
  const radarRadiusKmRef = useRef(radarRadiusKm);

  useEffect(() => { liveLocationsRef.current = liveLocations; }, [liveLocations]);
  useEffect(() => { activeNetworkRef.current = activeNetwork; }, [activeNetwork]);
  useEffect(() => { selectedLineRef.current = selectedLine; }, [selectedLine]);
  useEffect(() => { userLocationRef.current = userLocation; }, [userLocation]);
  useEffect(() => { radarRadiusKmRef.current = radarRadiusKm; }, [radarRadiusKm]);

  // Radar Proximity Settings Dropdown State
  const [isRadarSettingsOpen, setIsRadarSettingsOpen] = useState(false);

  // Global Outside Click Listener: closes dropdowns when clicking anywhere outside
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (
        radarDropdownRef.current &&
        !radarDropdownRef.current.contains(e.target) &&
        (!radarButtonRef.current || !radarButtonRef.current.contains(e.target))
      ) {
        setIsRadarSettingsOpen(false);
      }
      if (
        layerDropdownRef.current &&
        !layerDropdownRef.current.contains(e.target) &&
        (!layerButtonRef.current || !layerButtonRef.current.contains(e.target))
      ) {
        setIsLayerSelectorOpen(false);
      }
      if (
        searchDropdownRef.current &&
        !searchDropdownRef.current.contains(e.target)
      ) {
        setIsSearchDropdownOpen(false);
      }
    };

    document.addEventListener('pointerdown', handleOutsideClick);
    return () => {
      document.removeEventListener('pointerdown', handleOutsideClick);
    };
  }, []);

  // Direction filter for selected line: 'all' | '0' (Aller) | '1' (Retour)
  const [selectedDirectionFilter, setSelectedDirectionFilter] = useState('all');
  const selectedDirectionFilterRef = useRef(selectedDirectionFilter);
  useEffect(() => { selectedDirectionFilterRef.current = selectedDirectionFilter; }, [selectedDirectionFilter]);
  useEffect(() => { setSelectedDirectionFilter('all'); }, [selectedLine]);

  // Compute live vehicles for selected line (broken down into Aller & Retour)
  const selectedLineVehicles = useMemo(() => {
    if (!selectedLine) return [];
    const cutoffTime = Date.now() - 30 * 1000;
    return (liveLocations || []).filter(v => {
      const t = new Date(v.updated_at).getTime();
      if (!isNaN(t) && t < cutoffTime) return false;
      return v.line_id === selectedLine.id;
    });
  }, [selectedLine, liveLocations]);

  const selectedLineLiveCount = selectedLineVehicles.length;
  const selectedLineAllerCount = selectedLineVehicles.filter(v => Number(v.direction) === 0).length;
  const selectedLineRetourCount = selectedLineVehicles.filter(v => Number(v.direction) === 1).length;

  // Compute total active vehicles within the radar radius (when no line is selected)
  const nearbyVehiclesCount = useMemo(() => {
    const cutoffTime = Date.now() - 30 * 1000;
    const center = userLocation || null;
    const isRadarActive = Number(radarRadiusKm) > 0;
    const radiusM = (Number(radarRadiusKm) || 1.5) * 1000;

    return (liveLocations || []).filter(v => {
      const t = new Date(v.updated_at).getTime();
      if (!isNaN(t) && t < cutoffTime) return false;
      if (activeNetwork !== 'all') {
        const matchingLine = STATIC_LINES.find(l => l.id === v.line_id);
        const netType = v.network_type || matchingLine?.type_id;
        if (netType !== activeNetwork) return false;
      }
      if (isRadarActive && center && center.lat && center.lon) {
        return getDistanceMeters(center.lat, center.lon, v.latitude, v.longitude) <= radiusM;
      }
      return true;
    }).length;
  }, [liveLocations, userLocation, activeNetwork, radarRadiusKm]);

  // Map layer style: Strictly Official Google Maps (google_streets, google_satellite, google_traffic)
  const [mapStyle, setMapStyle] = useState(() => {
    try {
      const saved = localStorage.getItem('transit_map_style');
      if (['google_streets', 'google_satellite', 'google_traffic'].includes(saved)) {
        return saved;
      }
    } catch (e) {}
    return 'google_streets';
  });

  const handleSelectMapStyle = (style) => {
    setMapStyle(style);
    try {
      localStorage.setItem('transit_map_style', style);
    } catch (e) {}
    setIsLayerSelectorOpen(false);
  };

  const [isLayerSelectorOpen, setIsLayerSelectorOpen] = useState(false);
  
  // Floating line search bar on the map
  const [lineFilterSearch, setLineFilterSearch] = useState('');
  const [isSearchDropdownOpen, setIsSearchDropdownOpen] = useState(false);

  const onSelectLineRef = useRef(onSelectLine);
  onSelectLineRef.current = onSelectLine;
  const onSelectStationRef = useRef(onSelectStation);
  onSelectStationRef.current = onSelectStation;
  const ignoreMapClickUntilRef = useRef(0);

  // Filtered lines for the floating search bar
  const searchResults = STATIC_LINES.filter(line => {
    if (!lineFilterSearch.trim()) return false;
    const q = lineFilterSearch.toLowerCase().trim();
    const sn = (line.short_name || '').toLowerCase();
    const sna = (line.short_name_ar || '').toLowerCase();
    const ln = (line.long_name || '').toLowerCase();
    const lnf = (line.long_name_fr || '').toLowerCase();
    const lna = (line.long_name_ar || '').toLowerCase();
    return sn.includes(q) || sna.includes(q) || ln.includes(q) || lnf.includes(q) || lna.includes(q);
  });

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Tunis center coordinates
    const map = L.map(mapContainerRef.current, {
      center: [36.8065, 10.1815],
      zoom: 12,
      zoomControl: false,
      tap: false, // Ensures standard pointer/click events are not intercepted on mobile
    });

    L.control.zoom({ position: 'bottomleft' }).addTo(map);

    // Clicking on empty map area deselects active line/station and closes popups
    map.on('click', () => {
      setIsRadarSettingsOpen(false);
      setIsLayerSelectorOpen(false);
      setIsSearchDropdownOpen(false);
      if (Date.now() < ignoreMapClickUntilRef.current) return;
      if (activeItineraryRef.current) return;
      if (onSelectLineRef.current) onSelectLineRef.current(null);
      if (onSelectStationRef.current) onSelectStationRef.current(null, null);
    });

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Handle Tile Layer Switching with Google Maps API Key
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (tileLayerRef.current) {
      map.removeLayer(tileLayerRef.current);
      tileLayerRef.current = null;
    }

    let url = '';
    let options = {};

    const commonTileOptions = {
      maxZoom: 20,
      keepBuffer: 8,
      updateWhenIdle: false,
      updateWhenZooming: false,
      crossOrigin: true,
      subdomains: ['0', '1', '2', '3']
    };

    if (mapStyle === 'google_satellite') {
      url = `https://mt{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}&key=${GOOGLE_MAPS_API_KEY}`;
      options = {
        attribution: '&copy; Google Maps Satellite',
        ...commonTileOptions
      };
    } else if (mapStyle === 'google_traffic') {
      url = `https://mt{s}.google.com/vt/lyrs=m,traffic&x={x}&y={y}&z={z}&key=${GOOGLE_MAPS_API_KEY}`;
      options = {
        attribution: '&copy; Google Maps Trafic',
        ...commonTileOptions
      };
    } else {
      // Default: Official Google Maps Plan (Streets)
      url = `https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&key=${GOOGLE_MAPS_API_KEY}`;
      options = {
        attribution: '&copy; Google Maps',
        ...commonTileOptions
      };
    }

    const newLayer = L.tileLayer(url, options).addTo(map);
    tileLayerRef.current = newLayer;
  }, [mapStyle]);

  // Draw Transit Lines & Stations (Single Line Isolation or Clean Overview)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clear previous line layers
    Object.values(lineLayersRef.current).forEach(layer => map.removeLayer(layer));
    lineLayersRef.current = {};

    // Clear previous station layers
    Object.values(stationLayersRef.current).forEach(layer => map.removeLayer(layer));
    stationLayersRef.current = {};

    // SCENARIO 1: Single Line is Selected (ISOLATION MODE)
    if (selectedLine && !activeItinerary) {
      const activeDir = typeof selectedDirection === 'number' ? selectedDirection : 0;
      const dirShapeKey = `${selectedLine.id}_${activeDir}`;

      let latlngs = null;
      if (transitShapes[dirShapeKey] && transitShapes[dirShapeKey].length > 1) {
        latlngs = transitShapes[dirShapeKey];
      } else if (transitShapes[selectedLine.id] && transitShapes[selectedLine.id].length > 1) {
        latlngs = activeDir === 1
          ? [...transitShapes[selectedLine.id]].reverse()
          : transitShapes[selectedLine.id];
      } else {
        const retourStops = (selectedLine.stops_retour && selectedLine.stops_retour.length > 0)
          ? selectedLine.stops_retour
          : [...selectedLine.stops].reverse();
        const fallbackStops = activeDir === 1 ? retourStops : (selectedLine.stops_aller || selectedLine.stops);
        latlngs = fallbackStops.map(s => [s.lat, s.lon]);
      }

      // Directional stops sequence (1 to N)
      const directionalStops = activeDir === 1
        ? ((selectedLine.stops_retour && selectedLine.stops_retour.length > 0)
            ? selectedLine.stops_retour
            : [...selectedLine.stops].reverse())
        : (selectedLine.stops_aller || selectedLine.stops);
      const activeDirLabel = getDirectionLabel(selectedLine, activeDir, language);
      
      // 1. Draw glowing background casing + crisp colored route line directly on road
      if (latlngs && latlngs.length >= 2) {

        const casing = L.polyline(latlngs, {
          color: '#ffffff',
          weight: 12.5,
          opacity: 0.85,
          lineJoin: 'round',
          lineCap: 'round',
        }).addTo(map);

        const mainPolyline = L.polyline(latlngs, {
          color: selectedLine.color,
          weight: 8.5,
          opacity: 1,
          lineJoin: 'round',
          lineCap: 'round',
        }).addTo(map);

        lineLayersRef.current[selectedLine.id] = mainPolyline;
        lineLayersRef.current[`${selectedLine.id}-casing`] = casing;
      }

      // 2. Draw numbered sequence stops for the isolated line
      directionalStops.forEach((stop, index) => {
        const isStart = index === 0;
        const isEnd = index === directionalStops.length - 1;
        const stopNum = index + 1;
        const stopName = getStationName(stop, language);
        const lineShort = getLineShortName(selectedLine, language);
        const isAr = language === 'ar';

        const stopIcon = L.divIcon({
          html: `
            <div class="relative flex items-center justify-center" style="width: 28px; height: 28px;">
              ${(isStart || isEnd) ? `<div class="absolute w-7 h-7 rounded-full opacity-40 ring-2 ring-white" style="background-color: ${selectedLine.color};"></div>` : ''}
              <div class="flex items-center justify-center w-6 h-6 rounded-full border-2 border-white shadow-xl text-[10px] font-black text-white" style="background-color: ${selectedLine.color};">
                ${stopNum}
              </div>
            </div>
          `,
          className: 'isolated-station-marker',
          iconSize: [28, 28],
          iconAnchor: [14, 14],
        });

        const marker = L.marker([stop.lat, stop.lon], {
          icon: stopIcon,
          zIndexOffset: 1500 + index,
        });

        marker.bindTooltip(`
          <div class="font-bold text-xs text-white" dir="${isAr ? 'rtl' : 'ltr'}">${isAr ? 'المحطة' : 'Arrêt'} ${stopNum} : ${stopName}</div>
          <div class="text-[10px] text-slate-300" dir="${isAr ? 'rtl' : 'ltr'}">
            ${isStart ? (isAr ? '🏁 انطلاق' : '🏁 Départ') : isEnd ? (isAr ? '🛑 نهاية الخط' : '🛑 Terminus') : (isAr ? 'محطة' : 'Arrêt')} • ${lineShort} (${isAr ? 'إلى' : 'vers'} ${activeDirLabel})
          </div>
        `, {
          direction: 'top',
          offset: [0, -10],
          className: 'station-label',
        });

        marker.on('click', (e) => {
          if (e && e.originalEvent) L.DomEvent.stopPropagation(e);
          onSelectStation(stop, selectedLine);
        });

        marker.addTo(map);
        stationLayersRef.current[`${selectedLine.id}-${stop.id}`] = marker;
      });

      // Fit map bounds smoothly to the isolated line (if not in active itinerary mode)
      if (!activeItinerary && lineLayersRef.current[selectedLine.id]) {
        const bounds = lineLayersRef.current[selectedLine.id].getBounds();
        if (bounds && bounds.isValid()) {
          map.fitBounds(bounds, { 
            paddingTopLeft: [40, 130], 
            paddingBottomRight: [40, 90], 
            maxZoom: 15,
            animate: true
          });
        }
      }

      return;
    }

    // SCENARIO 2: Overview Mode (NO single line selected)
    // By default, ONLY draw the rapid transit backbone: RFR, Trains SNCFT, Métro Léger (1-6), and TGM.
    // All other lines (including all buses) are drawn strictly when selected by the user!
    const linesToProcess = STATIC_LINES.filter(line => {
      return ['rfr', 'train', 'metro', 'tgm'].includes(line.type_id);
    });

    linesToProcess.forEach(line => {
      const shape0 = transitShapes[`${line.id}_0`];
      const shape1 = transitShapes[`${line.id}_1`];
      const hasDualRails = shape0 && shape1 && shape0.length > 1 && shape1.length > 1;
      const hasShape = transitShapes[line.id] && transitShapes[line.id].length > 1;
      const latlngs = hasDualRails
        ? [shape0, shape1]
        : (hasShape ? transitShapes[line.id] : line.stops.map(s => [s.lat, s.lon]));

      const lineShort = getLineShortName(line, language);
      const lineName = getLineName(line, language);
      const isAr = language === 'ar';

      // 1. Draw route polylines
      if (latlngs.length >= 2) {
        const polyWeight = 3.5;
        const polyOpacity = 0.85;

        const polyline = L.polyline(latlngs, {
          color: line.color || '#10b981',
          weight: polyWeight,
          opacity: polyOpacity,
          lineJoin: 'round',
          lineCap: 'round',
        });

        polyline.bindTooltip(`
          <div class="font-bold text-xs" dir="${isAr ? 'rtl' : 'ltr'}">${lineShort} : ${lineName}</div>
          <div class="text-[10px] text-slate-300" dir="${isAr ? 'rtl' : 'ltr'}">${line.stops.length} ${isAr ? 'محطة • اضغط لعرض المسار' : 'arrêts • Cliquez pour isoler la ligne'}</div>
        `, {
          sticky: true,
          className: 'station-label',
        });

        polyline.on('click', (e) => {
          if (e && e.originalEvent) L.DomEvent.stopPropagation(e);
          onSelectLine(line);
        });

        polyline.addTo(map);
        lineLayersRef.current[line.id] = polyline;
      }

      // 2. Draw station dots for rail
      line.stops.forEach((stop, index) => {
        const key = `${line.id}-${stop.id}`;
        const isTerminus = index === 0 || index === line.stops.length - 1;
        const radius = isTerminus ? 5 : 3.5;
        const sName = getStationName(stop, language);

        const stationMarker = L.circleMarker([stop.lat, stop.lon], {
          radius: radius,
          fillColor: line.color,
          fillOpacity: 0.9,
          color: '#ffffff',
          weight: 1.5,
        });

        stationMarker.bindTooltip(`
          <div class="font-bold text-xs" dir="${isAr ? 'rtl' : 'ltr'}">${sName}</div>
          <div class="text-[10px] text-slate-300" dir="${isAr ? 'rtl' : 'ltr'}">${lineShort} • ${lineName}</div>
        `, {
          direction: 'top',
          offset: [0, -6],
          className: 'station-label',
        });

        stationMarker.on('click', (e) => {
          if (e && e.originalEvent) L.DomEvent.stopPropagation(e);
          onSelectStation(stop, line);
        });

        stationMarker.addTo(map);
        stationLayersRef.current[key] = stationMarker;
      });
    });
  }, [activeNetwork, selectedLine, selectedDirection, language, transitShapes, activeItinerary]);

  // ── Render Active Itinerary (Pedestrian Legs + Sliced Transit Ride + Target Destination) ──
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clean up previous itinerary layers
    itineraryLayersRef.current.forEach(layer => map.removeLayer(layer));
    itineraryLayersRef.current = [];

    if (!activeItinerary) {
      itineraryFittedRef.current = null;
      return;
    }

    let isCancelled = false;

    async function loadAndDrawItinerary() {
      const {
        line,
        originStation,
        dropoffStation,
        targetDestination,
        directionIndex = 0
      } = activeItinerary;

      const userLoc = activeItinerary.userLocation || userLocationRef.current;
      const startPt = userLoc && userLoc.lat && userLoc.lon ? userLoc : null;

      // 1. Sliced transit ride segment along line (high-density shape)
      const transitCoords = getTransitRideSegment(line, originStation, dropoffStation, directionIndex, transitShapes);

      // 2. Fetch walking legs asynchronously (with OSRM foot routing and fallback)
      let walkLeg1Coords = [];
      if (startPt && originStation) {
        walkLeg1Coords = await getWalkingRoute(startPt, originStation);
      }

      let walkLeg2Coords = [];
      if (dropoffStation && targetDestination) {
        walkLeg2Coords = await getWalkingRoute(dropoffStation, targetDestination);
      }

      if (isCancelled || !mapInstanceRef.current) return;
      const currentMap = mapInstanceRef.current;

      // Clear any layers if re-rendered during fetch
      itineraryLayersRef.current.forEach(layer => currentMap.removeLayer(layer));
      itineraryLayersRef.current = [];

      const newLayers = [];
      const allCoords = [];

      // A) Leg 1: Walk to origin station (À pied)
      if (walkLeg1Coords.length >= 2) {
        allCoords.push(...walkLeg1Coords);
        const glow = L.polyline(walkLeg1Coords, {
          color: '#0284c7',
          weight: 9,
          opacity: 0.35,
          lineCap: 'round',
          lineJoin: 'round'
        }).addTo(currentMap);

        const lineDash = L.polyline(walkLeg1Coords, {
          color: '#38bdf8',
          weight: 4.5,
          dashArray: '6, 8',
          opacity: 0.95,
          lineCap: 'round',
          lineJoin: 'round'
        }).addTo(currentMap);

        newLayers.push(glow, lineDash);
      }

      // B) Leg 2: Transit Ride along line (from originStation to dropoffStation)
      if (transitCoords.length >= 2) {
        allCoords.push(...transitCoords);
        // Outer dark casing
        const casing = L.polyline(transitCoords, {
          color: '#020617',
          weight: 10,
          opacity: 0.85,
          lineCap: 'round',
          lineJoin: 'round'
        }).addTo(currentMap);

        // Core line in route color
        const mainLine = L.polyline(transitCoords, {
          color: line?.color || '#2563eb',
          weight: 6.5,
          opacity: 1.0,
          lineCap: 'round',
          lineJoin: 'round'
        }).addTo(currentMap);

        // Direction dash pattern
        const dashOverlay = L.polyline(transitCoords, {
          color: '#ffffff',
          weight: 2.5,
          opacity: 0.55,
          dashArray: '10, 15',
          lineCap: 'round',
          lineJoin: 'round'
        }).addTo(currentMap);

        newLayers.push(casing, mainLine, dashOverlay);
      }

      // C) Leg 3: Walk to final destination (À pied vers destination)
      if (walkLeg2Coords.length >= 2) {
        allCoords.push(...walkLeg2Coords);
        const glow = L.polyline(walkLeg2Coords, {
          color: '#059669',
          weight: 9,
          opacity: 0.35,
          lineCap: 'round',
          lineJoin: 'round'
        }).addTo(currentMap);

        const lineDash = L.polyline(walkLeg2Coords, {
          color: '#10b981',
          weight: 4.5,
          dashArray: '6, 8',
          opacity: 0.95,
          lineCap: 'round',
          lineJoin: 'round'
        }).addTo(currentMap);

        newLayers.push(glow, lineDash);
      }

      // D) Markers for Itinerary Points:
      // 1. Start / User point
      if (startPt) {
        allCoords.push([startPt.lat, startPt.lon]);
        const startIcon = L.divIcon({
          html: `
            <div class="relative flex items-center justify-center" style="transform: translate(-50%, -50%);">
              <div class="w-9 h-9 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm shadow-2xl border-2 border-white ring-4 ring-blue-500/40">
                🚶
              </div>
            </div>
          `,
          className: 'itinerary-marker-start',
          iconSize: [0, 0]
        });
        const m = L.marker([startPt.lat, startPt.lon], { icon: startIcon, zIndexOffset: 2500 }).addTo(currentMap);
        m.bindTooltip(language === 'ar' ? 'نقطة الانطلاق (أنت هنا)' : 'Point de départ (Vous)', {
          direction: 'top',
          offset: [0, -18]
        });
        newLayers.push(m);
      }

      // 2. Boarding Station (Station A)
      if (originStation) {
        allCoords.push([originStation.lat, originStation.lon]);
        const oName = getStationName(originStation, language);
        const lShort = getLineShortName(line, language);
        const boardIcon = L.divIcon({
          html: `
            <div class="flex flex-col items-center pointer-events-auto" style="transform: translate(-50%, -100%);">
              <div class="px-2 py-0.5 rounded-lg text-[10px] font-black text-white shadow-2xl flex items-center gap-1 whitespace-nowrap mb-1 ring-2 ring-white" style="background-color: ${line?.color || '#2563eb'};">
                <span>${language === 'ar' ? '1. الركوب هنا' : '1. Monter ici'}</span>
                <span class="bg-black/40 px-1 rounded text-[9px]">${lShort}</span>
              </div>
              <div class="w-8 h-8 rounded-full bg-white border-2 flex items-center justify-center shadow-2xl font-bold text-sm" style="border-color: ${line?.color || '#2563eb'}; color: ${line?.color || '#2563eb'};">
                🚏
              </div>
            </div>
          `,
          className: 'itinerary-marker-board',
          iconSize: [0, 0]
        });
        const m = L.marker([originStation.lat, originStation.lon], { icon: boardIcon, zIndexOffset: 2600 }).addTo(currentMap);
        m.bindTooltip(`<b>${language === 'ar' ? 'محطة الركوب :' : 'Station de montée :'}</b> ${oName}`, {
          direction: 'top',
          offset: [0, -36]
        });
        newLayers.push(m);
      }

      // 3. Drop-off Station (Station B)
      if (dropoffStation) {
        allCoords.push([dropoffStation.lat, dropoffStation.lon]);
        const dName = getStationName(dropoffStation, language);
        const dropIcon = L.divIcon({
          html: `
            <div class="flex flex-col items-center pointer-events-auto" style="transform: translate(-50%, -100%);">
              <div class="px-2 py-0.5 rounded-lg text-[10px] font-black text-white shadow-2xl flex items-center gap-1 whitespace-nowrap mb-1 bg-amber-500 ring-2 ring-white">
                <span>${language === 'ar' ? '2. النزول هنا' : '2. Descendre ici'}</span>
              </div>
              <div class="w-8 h-8 rounded-full bg-white border-2 border-amber-500 flex items-center justify-center shadow-2xl font-bold text-sm text-amber-600">
                🏁
              </div>
            </div>
          `,
          className: 'itinerary-marker-drop',
          iconSize: [0, 0]
        });
        const m = L.marker([dropoffStation.lat, dropoffStation.lon], { icon: dropIcon, zIndexOffset: 2600 }).addTo(currentMap);
        m.bindTooltip(`<b>${language === 'ar' ? 'محطة النزول :' : 'Station de descente :'}</b> ${dName}`, {
          direction: 'top',
          offset: [0, -36]
        });
        newLayers.push(m);
      }

      // 4. Target Destination (Point B)
      if (targetDestination) {
        allCoords.push([targetDestination.lat, targetDestination.lon]);
        const destIcon = L.divIcon({
          html: `
            <div class="flex flex-col items-center pointer-events-auto" style="transform: translate(-50%, -100%);">
              <div class="px-2.5 py-0.5 rounded-lg text-[10px] font-black text-white shadow-2xl flex items-center gap-1 whitespace-nowrap mb-1 bg-emerald-600 ring-2 ring-white">
                <span>${language === 'ar' ? 'الوجهة المقصودة' : 'Destination finale'}</span>
              </div>
              <div class="w-9 h-9 rounded-full bg-emerald-500 text-white border-2 border-white flex items-center justify-center shadow-2xl text-base font-bold ring-4 ring-emerald-500/40">
                🎯
              </div>
            </div>
          `,
          className: 'itinerary-marker-dest',
          iconSize: [0, 0]
        });
        const m = L.marker([targetDestination.lat, targetDestination.lon], { icon: destIcon, zIndexOffset: 2700 }).addTo(currentMap);
        m.bindTooltip(`<b>${targetDestination.name}</b>`, {
          direction: 'top',
          offset: [0, -40]
        });
        newLayers.push(m);
      }

      itineraryLayersRef.current = newLayers;

      // Fit map bounds to view all legs with comfortable padding (ONLY ONCE upon itinerary load)
      if (allCoords.length >= 2 && itineraryFittedRef.current !== activeItinerary) {
        itineraryFittedRef.current = activeItinerary;
        const bounds = L.latLngBounds(allCoords);
        if (bounds.isValid()) {
          currentMap.fitBounds(bounds, {
            paddingTopLeft: [50, 50],
            paddingBottomRight: [50, 160], // Clearance for bottom navigation card
            maxZoom: 16,
            animate: true
          });
        }
      }
    }

    loadAndDrawItinerary();

    return () => {
      isCancelled = true;
      if (mapInstanceRef.current) {
        itineraryLayersRef.current.forEach(layer => mapInstanceRef.current.removeLayer(layer));
        itineraryLayersRef.current = [];
      }
    };
  }, [activeItinerary, transitShapes, language]);

  // ── High-Scale 60 FPS Lerp (Linear Interpolation) Animation Loop ──
  // Glides vehicle markers continuously across animation frames without snapping or jumps
  useEffect(() => {
    const animateVehicles = (now) => {
      // Pause completely when tab or phone screen is inactive/hidden to save battery and CPU
      if (document.hidden) {
        animFrameIdRef.current = requestAnimationFrame(animateVehicles);
        return;
      }

      const markers = vehicleMarkersRef.current;
      const anims = vehicleAnimRef.current;

      Object.keys(anims).forEach(id => {
        const anim = anims[id];
        const marker = markers[id];
        if (!anim || !marker || anim.completed) return;

        const elapsed = now - anim.startTime;
        const progress = Math.min(1, Math.max(0, elapsed / anim.duration));

        // Smooth linear progression
        const curLat = anim.startLat + (anim.targetLat - anim.startLat) * progress;
        const curLon = anim.startLon + (anim.targetLon - anim.startLon) * progress;

        marker.setLatLng([curLat, curLon]);

        if (progress >= 1) {
          anim.completed = true;
        }

        // Smooth angular bearing rotation
        if (anim.startBearing !== undefined && anim.targetBearing !== undefined) {
          let diff = (anim.targetBearing - anim.startBearing) % 360;
          if (diff > 180) diff -= 360;
          if (diff < -180) diff += 360;
          const curBearing = anim.startBearing + diff * progress;
          const el = marker.getElement();
          if (el) {
            const rotEl = el.querySelector('.vehicle-bearing-rotate');
            if (rotEl) {
              rotEl.style.transform = `rotate(${Math.round(curBearing)}deg)`;
            }
          }
        }
      });

      animFrameIdRef.current = requestAnimationFrame(animateVehicles);
    };

    animFrameIdRef.current = requestAnimationFrame(animateVehicles);

    return () => {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
    };
  }, []);

  // ── Vehicle marker updater — syncs edge data and establishes 4000ms Lerp targets ──
  useEffect(() => {
    function updateVehicleMarkers() {
      const map = mapInstanceRef.current;
      if (!map) return;

      const liveLocations = liveLocationsRef.current || [];
      const activeNetwork = activeNetworkRef.current;
      const selectedLine = selectedLineRef.current;
      const now = performance.now();
      const cutoffTime = Date.now() - 30 * 1000; // 30-second ghost eviction

      const currentVehicleIds = new Set();

      const userLoc = userLocationRef.current;
      const radarRadius = Number(radarRadiusKmRef.current) || 0;
      const isRadarActive = radarRadius > 0;
      const dirFilter = selectedDirectionFilterRef.current;
      const center = userLoc || (map ? { lat: map.getCenter().lat, lon: map.getCenter().lng } : null);

      const candidates = liveLocations.filter(loc => {
        // Ghost check (30-second eviction)
        const t = new Date(loc.updated_at).getTime();
        if (!isNaN(t) && t < cutoffTime) return false;

        // RULE 1: If user selected a specific line -> SHOW ALL VEHICLES OF THIS LINE ACROSS THE WHOLE MAP!
        // No proximity boundary restriction!
        if (selectedLine) {
          if (loc.line_id !== selectedLine.id) return false;
          if (dirFilter !== 'all') {
            return Number(loc.direction) === Number(dirFilter);
          }
          return true;
        }

        // Network filter ('all', 'bus', 'metro', 'train', 'tgm', 'rfr')
        if (activeNetwork !== 'all') {
          const matchingLine = STATIC_LINES.find(l => l.id === loc.line_id);
          const netType = loc.network_type || matchingLine?.type_id;
          if (netType !== activeNetwork) return false;
        }

        // RULE 2: Proximity Radar Filter (0.5 km to 2.5 km) around user position
        if (isRadarActive && center && center.lat && center.lon) {
          const distM = getDistanceMeters(center.lat, center.lon, loc.latitude, loc.longitude);
          if (distM > radarRadius * 1000) return false;
        }

        return true;
      });

      // Single Source of Truth / Deduplication:
      // 1. Map by vehicle ID (keep latest updated_at)
      const uniqueMap = new Map();
      candidates.forEach(v => {
        const existing = uniqueMap.get(v.id);
        if (!existing || new Date(v.updated_at).getTime() > new Date(existing.updated_at).getTime()) {
          uniqueMap.set(v.id, v);
        }
      });
      const uniqueCandidates = Array.from(uniqueMap.values());

      // 2. Spatial Deduplication: If two records on the same line and same direction are within 25m, keep the freshest
      const dedupedCandidates = [];
      for (const v of uniqueCandidates) {
        const duplicate = dedupedCandidates.find(other => 
          other.line_id === v.line_id &&
          Number(other.direction) === Number(v.direction) &&
          getDistanceMeters(other.latitude, other.longitude, v.latitude, v.longitude) < 25
        );
        if (!duplicate) {
          dedupedCandidates.push(v);
        } else if (new Date(v.updated_at).getTime() > new Date(duplicate.updated_at).getTime()) {
          const idx = dedupedCandidates.indexOf(duplicate);
          dedupedCandidates[idx] = v;
        }
      }

      let activeVehicles = dedupedCandidates;
      if (!selectedLine) {
        // Sort closest to user / center
        if (center && center.lat && center.lon) {
          activeVehicles.sort((a, b) => {
            const distA = getDistanceMeters(center.lat, center.lon, a.latitude, a.longitude);
            const distB = getDistanceMeters(center.lat, center.lon, b.latitude, b.longitude);
            return distA - distB;
          });
        }
        // Cap to max 15 closest vehicles for optimal mobile performance
        const excess = Math.max(0, activeVehicles.length - 15);
        setExcessVehiclesCount(excess);
        activeVehicles = activeVehicles.slice(0, 15);
      } else {
        setExcessVehiclesCount(0);
      }

      activeVehicles.forEach(loc => {
        currentVehicleIds.add(loc.id);
        const line = STATIC_LINES.find(l => l.id === loc.line_id) || loc.transit_lines;
        const lineColor = line?.color || '#0071e3';
        const lineShort = line?.short_name || 'Direct';
        const networkType = loc.network_type || line?.type_id || 'bus';
        const passengerCount = loc.passenger_count || 1;
        const isAr = language === 'ar';

        // Multi-modal transit icon emoji
        let typeEmoji = '🚌';
        let typeLabel = 'Bus Transtu';
        if (networkType === 'metro') { typeEmoji = '🚇'; typeLabel = 'Métro Léger'; }
        else if (networkType === 'train') { typeEmoji = '🚆'; typeLabel = 'Train SNCFT'; }
        else if (networkType === 'rfr') { typeEmoji = '🚄'; typeLabel = 'RFR Rapide'; }
        else if (networkType === 'tgm') { typeEmoji = '🚊'; typeLabel = 'TGM'; }

        // Direction display: Aller (0) vs Retour (1)
        const isRetour = Number(loc.direction) === 1;
        const dirName = loc.direction_name || (line?.directions ? (line.directions[isRetour ? 1 : 0] || '') : '');
        const dirBadge = isRetour ? 'Retour ⬅️' : 'Aller ➡️';

        const iconHtml = `
          <div class="relative flex items-center justify-center cursor-pointer group" style="width: 46px; height: 46px;">
            <div class="vehicle-bearing-rotate absolute inset-0 flex items-center justify-center pointer-events-none transition-transform duration-300" style="transform: rotate(${loc.heading || 0}deg);">
              <div class="absolute -top-1 w-0 h-0 border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-b-[7px] border-b-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)]"></div>
            </div>
            <div class="radar-ring absolute w-11 h-11 rounded-full opacity-60" style="background-color: ${lineColor};"></div>
            <div class="relative flex items-center justify-center w-8 h-8 rounded-full shadow-lg border-2 border-white text-white font-black text-[11px] transition-transform duration-300 group-hover:scale-110" style="background-color: ${lineColor};">
              ${lineShort}
              <div class="absolute -top-1 -right-1 text-[10px] bg-slate-900 rounded-full w-4 h-4 flex items-center justify-center border border-slate-700 shadow">${typeEmoji}</div>
            </div>
            <div class="absolute -bottom-1 bg-slate-900/95 text-emerald-400 font-bold text-[9px] px-1.5 py-0.2 rounded-full border border-slate-700 shadow flex items-center gap-0.5">
              <span class="veh-speed-val">${loc.speed_kmh || 0} km/h</span>
            </div>
          </div>
        `;

        const popupContent = `
          <div class="p-3 min-w-[220px] text-slate-100">
            <div class="flex items-center justify-between border-b border-slate-700/60 pb-2 mb-2">
              <div class="flex items-center gap-2">
                <span class="px-2 py-0.5 rounded font-extrabold text-xs text-white" style="background-color: ${lineColor};">${lineShort}</span>
                <span class="font-bold text-sm text-white">${typeLabel}</span>
              </div>
              <span class="text-[10px] bg-emerald-500/20 text-emerald-400 font-bold px-1.5 py-0.5 rounded border border-emerald-500/40">GPS Direct</span>
            </div>
            <div class="space-y-1.5 text-xs">
              <div class="flex items-center justify-between text-slate-300">
                <span class="text-slate-400">Direction :</span>
                <span class="font-semibold text-white truncate max-w-[130px]">${dirName || 'En service'} <span class="text-[10px] text-blue-400">(${dirBadge})</span></span>
              </div>
              <div class="flex items-center justify-between text-slate-300">
                <span class="text-slate-400">Vitesse réelle :</span>
                <span class="font-bold text-emerald-400">${loc.speed_kmh || 0} km/h</span>
              </div>
              <div class="flex items-center justify-between text-slate-300">
                <span class="text-slate-400">${isAr ? 'على المتن :' : 'Voyageurs à bord :'}</span>
                <span class="font-semibold text-slate-200">👤 ${passengerCount > 1 ? `${passengerCount} (${isAr ? '1 يبث + ' + (passengerCount - 1) + ' في الانتظار' : '1 diffuseur + ' + (passengerCount - 1) + ' en attente'})` : (isAr ? '1 (يبث)' : '1 (diffuseur)')}</span>
              </div>
            </div>
          </div>
        `;

        const vehicleIcon = L.divIcon({
          html: iconHtml,
          className: 'vehicle-marker',
          iconSize: [46, 46],
          iconAnchor: [23, 23],
          popupAnchor: [0, -23],
        });

        const speedKmh = loc.speed_kmh || 0;
        const isStationary = speedKmh < 2;

        if (vehicleMarkersRef.current[loc.id]) {
          // Existing marker: update target position and reset Lerp
          const marker = vehicleMarkersRef.current[loc.id];
          const curPos = marker.getLatLng();
          const prevAnim = vehicleAnimRef.current[loc.id];
          const prevBearing = prevAnim ? (prevAnim.targetBearing ?? prevAnim.startBearing ?? 0) : (loc.heading || 0);

          const distMoved = getDistanceMeters(curPos.lat, curPos.lng, loc.latitude, loc.longitude);
          const rawBearing = (loc.heading !== null && loc.heading !== undefined && !isNaN(loc.heading)) ? loc.heading : prevBearing;

          // Deadband Threshold check:
          // If speed < 2 km/h:
          // 1. Lock coordinates to current position if small drift (< 6m)
          // 2. Freeze bearing/rotation angle to prevBearing (do not rotate at 0 km/h)
          let targetLat = loc.latitude;
          let targetLon = loc.longitude;
          let targetBearing = rawBearing;

          if (isStationary) {
            targetBearing = prevBearing; // Freeze heading
            if (distMoved < 6) {
              targetLat = curPos.lat;
              targetLon = curPos.lng;
            }
          }

          const bearingMoved = Math.abs((prevBearing || 0) - targetBearing);
          const effectiveDistMoved = getDistanceMeters(curPos.lat, curPos.lng, targetLat, targetLon);

          if (effectiveDistMoved > 0.5 || bearingMoved > 1 || !prevAnim) {
            vehicleAnimRef.current[loc.id] = {
              startLat: curPos.lat,
              startLon: curPos.lng,
              targetLat: targetLat,
              targetLon: targetLon,
              startBearing: prevBearing,
              targetBearing: targetBearing,
              startTime: now,
              duration: 4000,
              completed: false,
            };
          }

          // Dynamically update speed badge and direction on existing marker
          const el = marker.getElement();
          if (el) {
            const speedEl = el.querySelector('.veh-speed-val');
            if (speedEl) {
              speedEl.textContent = `${speedKmh} km/h`;
            }
          }

          // If direction or line changed, refresh icon
          if (marker._lastDirection !== loc.direction) {
            marker.setIcon(vehicleIcon);
            marker._lastDirection = loc.direction;
          }

          marker.setPopupContent(popupContent);
        } else {
          // New vehicle marker
          const initialBearing = loc.heading || 0;
          const marker = L.marker([loc.latitude, loc.longitude], {
            icon: vehicleIcon,
            zIndexOffset: 1000,
          }).bindPopup(popupContent, { className: 'custom-popup' });
          marker._lastDirection = loc.direction;
          marker.addTo(map);
          vehicleMarkersRef.current[loc.id] = marker;

          vehicleAnimRef.current[loc.id] = {
            startLat: loc.latitude,
            startLon: loc.longitude,
            targetLat: loc.latitude,
            targetLon: loc.longitude,
            startBearing: initialBearing,
            targetBearing: initialBearing,
            startTime: now,
            duration: 4000,
            completed: true,
          };
        }
      });

      // 30s Ghost Eviction: Remove stale or disappeared vehicles
      Object.keys(vehicleMarkersRef.current).forEach(id => {
        if (!currentVehicleIds.has(id)) {
          map.removeLayer(vehicleMarkersRef.current[id]);
          delete vehicleMarkersRef.current[id];
          delete vehicleAnimRef.current[id];
        }
      });

      // Update or clear Radar Visual Perimeter Circle
      if (!selectedLine && isRadarActive && userLoc && userLoc.lat && userLoc.lon && map) {
        const radiusM = radarRadius * 1000;
        if (!radarCircleRef.current) {
          radarCircleRef.current = L.circle([userLoc.lat, userLoc.lon], {
            radius: radiusM,
            color: '#10b981',
            weight: 1.5,
            dashArray: '5, 8',
            fillColor: '#10b981',
            fillOpacity: 0.02,
            interactive: false,
          }).addTo(map);
        } else {
          radarCircleRef.current.setLatLng([userLoc.lat, userLoc.lon]);
          radarCircleRef.current.setRadius(radiusM);
        }
      } else if (radarCircleRef.current && map) {
        map.removeLayer(radarCircleRef.current);
        radarCircleRef.current = null;
      }
    }

    // Run whenever liveLocations updates, and every 4s fallback
    updateVehicleMarkers();
    const interval = setInterval(updateVehicleMarkers, 4000);
    return () => {
      clearInterval(interval);
      if (radarCircleRef.current && mapInstanceRef.current) {
        mapInstanceRef.current.removeLayer(radarCircleRef.current);
        radarCircleRef.current = null;
      }
    };
  }, [liveLocations, activeNetwork, selectedLine, selectedDirectionFilter, radarRadiusKm, userLocation]);


  // User Real GPS Location Marker & Accuracy Circle
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (!userLocation) {
      if (userMarkerRef.current) {
        map.removeLayer(userMarkerRef.current);
        userMarkerRef.current = null;
      }
      if (userAccuracyCircleRef.current) {
        map.removeLayer(userAccuracyCircleRef.current);
        userAccuracyCircleRef.current = null;
      }
      return;
    }

    const { lat, lon, accuracy } = userLocation;

    // 1. Accuracy Circle
    if (!userAccuracyCircleRef.current) {
      const circle = L.circle([lat, lon], {
        radius: Math.max(accuracy || 15, 10),
        color: '#3b82f6',
        fillColor: '#3b82f6',
        fillOpacity: 0.15,
        weight: 1.5
      }).addTo(map);
      userAccuracyCircleRef.current = circle;
    } else {
      userAccuracyCircleRef.current.setLatLng([lat, lon]);
      userAccuracyCircleRef.current.setRadius(Math.max(accuracy || 15, 10));
    }

    // 2. User Center Pin
    if (!userMarkerRef.current) {
      const userIcon = L.divIcon({
        html: `
          <div class="relative flex items-center justify-center w-8 h-8 cursor-pointer">
            <div class="absolute w-7 h-7 rounded-full bg-blue-500 opacity-25 ring-2 ring-blue-400"></div>
            <div class="w-4 h-4 rounded-full bg-blue-500 border-2 border-white shadow-xl ring-2 ring-blue-400/40"></div>
          </div>
        `,
        className: 'user-gps-marker',
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });

      const accText = accuracy ? `±${Math.round(accuracy)}m` : '';
      const marker = L.marker([lat, lon], {
        icon: userIcon,
        zIndexOffset: 3000,
      }).bindTooltip(`Vous êtes ici (${accText})`, { direction: 'top', offset: [0, -12] });

      marker.addTo(map);
      userMarkerRef.current = marker;
    } else {
      userMarkerRef.current.setLatLng([lat, lon]);
    }
  }, [userLocation]);

  return (
    <div className="relative w-full h-full min-h-[500px]">
      <div ref={mapContainerRef} className="w-full h-full bg-[#e5e3df]" />

      {/* Floating Top Bar: Single Line Isolation & Quick Line Search & Guide Trajet */}
      <div className="absolute top-3.5 left-3 sm:left-4 right-3 sm:right-4 z-[1003] flex items-center justify-between gap-2 pointer-events-auto">
        
        {/* Single Line Isolation Badge or Quick Line Search */}
        {selectedLine ? (
          <div className={`flex flex-col border rounded-2xl shadow-xl p-2.5 backdrop-blur-xl max-w-sm sm:max-w-md animate-fade-in transition-colors ${
            theme === 'light'
              ? 'bg-white/95 border-slate-200/90 text-slate-800'
              : 'bg-slate-900/95 border-slate-700/90 text-white shadow-2xl'
          }`}>
            <div className="flex items-center gap-2.5">
              <span
                className="w-8 h-8 rounded-xl flex items-center justify-center font-extrabold text-xs text-white shadow flex-shrink-0"
                style={{ backgroundColor: selectedLine.color }}
              >
                {getLineShortName(selectedLine, language)}
              </span>
              <div className="min-w-0 flex-1 pr-1">
                <div className={`font-bold text-xs truncate max-w-[140px] sm:max-w-xs ${
                  theme === 'light' ? 'text-slate-900' : 'text-white'
                }`}>
                  {getLineName(selectedLine, language)}
                </div>
                <div className={`text-[10px] flex items-center gap-1.5 flex-wrap ${
                  theme === 'light' ? 'text-slate-500' : 'text-slate-400'
                }`}>
                  <span>
                    {((selectedDirection === 1 && selectedLine.stops_retour?.length)
                      ? selectedLine.stops_retour.length
                      : (selectedLine.stops_aller?.length || selectedLine.stops.length))} {language === 'ar' ? 'محطة' : 'arrêts'}
                  </span>
                  <span>•</span>
                  <span className="text-emerald-500 font-bold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    {selectedLineLiveCount > 0 ? (
                      language === 'ar'
                        ? `${selectedLineLiveCount} مركبة مباشرة على كامل المسار`
                        : `${selectedLineLiveCount} en direct sur toute la carte`
                    ) : (
                      language === 'ar' ? 'مسار كامل معزول' : 'Ligne isolée (toute la carte)'
                    )}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-1.5 flex-shrink-0">
                {onOpenSchedule && (
                  <button
                    onClick={onOpenSchedule}
                    className="p-1.5 px-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold flex items-center gap-1 transition shadow border border-blue-400/40"
                    title={language === 'ar' ? 'عرض المحطات والتوقيت' : 'Voir la liste des arrêts et horaires'}
                  >
                    <Clock className="w-3.5 h-3.5" />
                    <span>{language === 'ar' ? 'المحطات' : 'Arrêts'}</span>
                  </button>
                )}
                <button
                  onClick={() => onSelectLine(null)}
                  className={`p-1.5 px-2 rounded-xl text-xs font-bold flex items-center gap-1 transition shadow border ${
                    theme === 'light'
                      ? 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'
                      : 'bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border-slate-600/60'
                  }`}
                  title={language === 'ar' ? 'إلغاء وعرض كامل الشبكة' : 'Afficher tout le réseau'}
                >
                  <X className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">{language === 'ar' ? 'إلغاء' : 'Effacer'}</span>
                </button>
              </div>
            </div>

            {/* Direction Switcher (Sens Aller / Sens Retour) */}
            {selectedLine.directions && selectedLine.directions.length > 1 && (
              <div className={`flex items-center gap-1.5 mt-2 pt-2 border-t ${
                theme === 'light' ? 'border-slate-200' : 'border-slate-800/80'
              }`}>
                {selectedLine.directions.map((dir, idx) => {
                  const dirText = getDirectionLabel(selectedLine, idx, language);
                  return (
                    <button
                      key={idx}
                      onClick={() => onDirectionChange && onDirectionChange(idx)}
                      className={`flex-1 py-1 px-2 rounded-xl text-[11px] font-bold transition flex items-center justify-center gap-1 truncate ${
                        (selectedDirection || 0) === idx
                          ? 'bg-blue-600 text-white shadow-md ring-1 ring-blue-400'
                          : theme === 'light'
                            ? 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                            : 'bg-slate-800/80 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                      }`}
                    >
                      <span className="text-[9px] uppercase tracking-wider opacity-75">
                        {idx === 0 ? (language === 'ar' ? 'ذهاب :' : 'Aller :') : (language === 'ar' ? 'إياب :' : 'Retour :')}
                      </span>
                      <span className="truncate max-w-[120px]">{dirText}</span>
                    </button>
                  );
                })}
              </div>
            )}

            {/* Live Vehicles Breakdown & Filter on this line */}
            {selectedLineLiveCount > 0 && (
              <div className={`flex items-center gap-1.5 mt-2 pt-2 border-t flex-wrap ${
                theme === 'light' ? 'border-slate-200' : 'border-slate-800/80'
              }`}>
                <span className={`text-[10px] font-bold uppercase tracking-wider pl-0.5 ${
                  theme === 'light' ? 'text-slate-500' : 'text-slate-400'
                }`}>
                  {language === 'ar' ? 'المركبات :' : 'Véhicules :'}
                </span>
                <button
                  onClick={() => setSelectedDirectionFilter('all')}
                  className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition ${
                    selectedDirectionFilter === 'all'
                      ? 'bg-blue-600 text-white shadow'
                      : theme === 'light'
                        ? 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {language === 'ar' ? 'الكل' : 'Tous'} ({selectedLineLiveCount})
                </button>
                <button
                  onClick={() => setSelectedDirectionFilter('0')}
                  className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition flex items-center gap-0.5 ${
                    selectedDirectionFilter === '0'
                      ? 'bg-blue-600 text-white shadow'
                      : theme === 'light'
                        ? 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  <span>Aller ➡️</span>
                  <span>({selectedLineAllerCount})</span>
                </button>
                <button
                  onClick={() => setSelectedDirectionFilter('1')}
                  className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition flex items-center gap-0.5 ${
                    selectedDirectionFilter === '1'
                      ? 'bg-blue-600 text-white shadow'
                      : theme === 'light'
                        ? 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  <span>Retour ⬅️</span>
                  <span>({selectedLineRetourCount})</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-1.5 flex-1 max-w-xs sm:max-w-md">
            <div ref={searchDropdownRef} className="relative">
              <div className={`flex items-center gap-2 border rounded-2xl shadow-xl p-2 px-3 backdrop-blur-xl transition-colors ${
                theme === 'light'
                  ? 'bg-white/95 border-slate-200/90 text-slate-900 shadow-slate-200/50'
                  : 'bg-slate-900/95 border-slate-700/80 text-white shadow-2xl'
              }`}>
                <Search className="w-4 h-4 text-slate-400 flex-shrink-0" />
                <input
                  type="text"
                  value={lineFilterSearch}
                  onChange={(e) => {
                    setLineFilterSearch(e.target.value);
                    setIsSearchDropdownOpen(true);
                  }}
                  onFocus={() => setIsSearchDropdownOpen(true)}
                  placeholder={language === 'ar' ? 'ابحث عن خط أو حافلة أو قطار...' : 'Isoler une ligne (ex: Bus 36B, Métro 1...)'}
                  className={`bg-transparent text-xs focus:outline-none w-full font-medium ${
                    theme === 'light' ? 'text-slate-900 placeholder:text-slate-400' : 'text-white placeholder:text-slate-500'
                  }`}
                />
                {lineFilterSearch && (
                  <button
                    onClick={() => {
                      setLineFilterSearch('');
                      setIsSearchDropdownOpen(false);
                    }}
                    className={`text-xs p-0.5 ${theme === 'light' ? 'text-slate-400 hover:text-slate-700' : 'text-slate-400 hover:text-white'}`}
                  >
                    ✕
                  </button>
                )}
              </div>

              {/* Dropdown of search results */}
              {isSearchDropdownOpen && searchResults.length > 0 && (
                <div 
                  onMouseDown={(e) => e.stopPropagation()}
                  onTouchStart={(e) => e.stopPropagation()}
                  onClick={(e) => e.stopPropagation()}
                  className={`absolute top-full left-0 right-0 mt-1.5 max-h-60 overflow-y-auto border rounded-2xl shadow-2xl backdrop-blur-xl z-[1030] ${
                    theme === 'light'
                      ? 'bg-white/95 border-slate-200 divide-y divide-slate-100 text-slate-800'
                      : 'bg-slate-900/95 border-slate-700/90 divide-y divide-slate-800/80 text-white'
                  }`}
                >
                  {searchResults.slice(0, 25).map(line => (
                    <button
                      key={line.id}
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        ignoreMapClickUntilRef.current = Date.now() + 500;
                        onSelectLine(line);
                        setIsSearchDropdownOpen(false);
                        setLineFilterSearch('');
                      }}
                      className={`w-full p-2.5 text-left flex items-center justify-between text-xs transition ${
                        theme === 'light' ? 'hover:bg-slate-100 active:bg-slate-200' : 'hover:bg-slate-800/80 active:bg-slate-700'
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span
                          className="px-2 py-0.5 rounded font-extrabold text-[11px] text-white flex-shrink-0"
                          style={{ backgroundColor: line.color }}
                        >
                          {getLineShortName(line, language)}
                        </span>
                        <span className={`font-medium truncate ${theme === 'light' ? 'text-slate-900' : 'text-white'}`}>
                          {getLineName(line, language)}
                        </span>
                      </div>
                      <span className={`text-[10px] flex-shrink-0 ml-1 ${theme === 'light' ? 'text-slate-400' : 'text-slate-500'}`}>
                        {line.stops.length} {language === 'ar' ? 'محطة' : 'arrêts'}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Nearby vehicles within radar indicator */}
            <div className={`flex flex-col gap-1 backdrop-blur-xl shadow-lg border rounded-2xl p-2 px-3 text-[11px] self-start transition-colors max-w-xs ${
              theme === 'light'
                ? 'bg-white/95 border-slate-200 text-slate-700'
                : 'bg-slate-900/90 border-slate-700/80 text-slate-300'
            }`}>
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="font-semibold">
                  {radarRadiusKm === 0 ? (
                    language === 'ar' ? 'الرادار معطل' : 'Radar désactivé'
                  ) : (
                    language === 'ar'
                      ? `رادار ${radarRadiusKm} كم : ${Math.min(nearbyVehiclesCount, 15)} معروضة`
                      : `Radar ${radarRadiusKm} km : ${Math.min(nearbyVehiclesCount, 15)} affiché(s)`
                  )}
                </span>
                {excessVehiclesCount > 0 && (
                  <span className="text-[10px] font-bold text-amber-500">
                    (+{excessVehiclesCount} {language === 'ar' ? 'أخرى' : 'autres'})
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => setIsRadarSettingsOpen(true)}
                  className="text-emerald-500 underline font-semibold ml-auto hover:opacity-80"
                >
                  {language === 'ar' ? 'تعديل' : 'Modifier'}
                </button>
              </div>

              {excessVehiclesCount > 0 && (
                <div className="text-[10px] text-amber-600 dark:text-amber-400 font-medium leading-tight pt-0.5 border-t border-slate-200/60 dark:border-slate-800/60">
                  {language === 'ar'
                    ? `⚠️ أكثر من 15 مركبة قريبة — ابحث عن خطك لعزله ورؤية موقعه.`
                    : `⚠️ Plus de 15 véhicules proches — recherchez une ligne pour l'isoler.`}
                </div>
              )}
            </div>
          </div>
        )}



      </div>

      {/* Floating Controls: GPS Center & Google Maps Layer Selector (Guaranteed Safe Area Clearance) */}
      <div className="absolute bottom-[calc(env(safe-area-inset-bottom,0px)+5.2rem)] sm:bottom-8 right-3 sm:right-6 z-[1002] flex flex-col items-end gap-2.5 pointer-events-auto">
        {/* Radar Settings Dropdown */}
        {isRadarSettingsOpen && (
          <div ref={radarDropdownRef} className={`border rounded-2xl shadow-2xl p-3 flex flex-col gap-2.5 backdrop-blur-xl animate-fade-in text-xs w-64 sm:w-72 mb-1 ${
            theme === 'light'
              ? 'bg-white/95 border-slate-200 text-slate-800 shadow-slate-300/50'
              : 'bg-slate-900/95 border-slate-700/80 text-white'
          }`}>
            <div className={`flex items-center justify-between border-b pb-2 ${
              theme === 'light' ? 'border-slate-200' : 'border-slate-800'
            }`}>
              <div className={`flex items-center gap-1.5 font-bold ${theme === 'light' ? 'text-slate-900' : 'text-white'}`}>
                <Radio className="w-4 h-4 text-emerald-500" />
                <span>{language === 'ar' ? 'نطاق الرادار' : 'Rayon du Radar'}</span>
              </div>
              <span className={`px-2 py-0.5 rounded-full font-extrabold text-[11px] border ${
                radarRadiusKm === 0
                  ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                  : 'bg-emerald-500/20 text-emerald-500 border-emerald-500/30'
              }`}>
                {radarRadiusKm === 0 ? (language === 'ar' ? 'معطل' : 'Désactivé') : `${radarRadiusKm} km`}
              </span>
            </div>

            <p className={`text-[11px] leading-tight ${theme === 'light' ? 'text-slate-500' : 'text-slate-400'}`}>
              {language === 'ar'
                ? 'عرض المركبات القريبة منك فقط (حد أقصى 15 مركبة لضمان خفة التطبيق).'
                : 'Affiche les véhicules proches (max 15 véhicules pour une fluidité maximale).'}
            </p>

            {/* Slider 0.5 to 2.5 km */}
            <div className="flex flex-col gap-1">
              <input
                type="range"
                min="0.5"
                max="2.5"
                step="0.25"
                value={radarRadiusKm === 0 ? 0.5 : radarRadiusKm}
                onChange={(e) => onUpdateRadarRadius && onUpdateRadarRadius(Number(e.target.value))}
                className={`w-full accent-emerald-500 cursor-pointer h-1.5 rounded-lg appearance-none ${
                  theme === 'light' ? 'bg-slate-200' : 'bg-slate-800'
                }`}
              />
              <div className={`flex justify-between text-[10px] font-semibold px-0.5 ${
                theme === 'light' ? 'text-slate-400' : 'text-slate-500'
              }`}>
                <span>0.5 km</span>
                <span>1.0 km</span>
                <span>1.5 km</span>
                <span>2.0 km</span>
                <span>2.5 km</span>
              </div>
            </div>

            {/* Quick Presets */}
            <div className="grid grid-cols-5 gap-1 pt-1">
              {[0.5, 1, 1.5, 2.5].map(val => (
                <button
                  key={val}
                  type="button"
                  onClick={() => onUpdateRadarRadius && onUpdateRadarRadius(val)}
                  className={`py-1 rounded-xl text-[10px] font-bold transition text-center ${
                    radarRadiusKm === val
                      ? 'bg-emerald-600 text-white shadow-md'
                      : theme === 'light'
                        ? 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  {val} km
                </button>
              ))}
              <button
                type="button"
                onClick={() => onUpdateRadarRadius && onUpdateRadarRadius(0)}
                className={`py-1 rounded-xl text-[10px] font-bold transition text-center ${
                  radarRadiusKm === 0
                    ? 'bg-rose-600 text-white shadow-md'
                    : theme === 'light'
                      ? 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
                title={language === 'ar' ? 'تعطيل الرادار' : 'Désactiver le radar'}
              >
                {language === 'ar' ? 'تعطيل' : 'Off'}
              </button>
            </div>

            <div className={`text-[10px] p-2 rounded-xl border leading-normal ${
              theme === 'light'
                ? 'bg-slate-50 text-slate-600 border-slate-200'
                : 'bg-slate-950/60 text-slate-400 border-slate-800/80'
            }`}>
              💡 <span className={theme === 'light' ? 'text-slate-700 font-medium' : 'text-slate-300 font-medium'}>
                {language === 'ar'
                  ? 'عند اختيار خط محدد (مثل حافلة 104)، يتم إظهار جميع مركباته على كامل الخريطة تلقائياً.'
                  : 'Sélectionner une ligne isolée affiche tous ses véhicules sur toute la carte, sans limite de distance.'}
              </span>
            </div>
          </div>
        )}

        {/* Layer Selector Dropdown */}
        {isLayerSelectorOpen && (
          <div ref={layerDropdownRef} className={`border rounded-2xl shadow-2xl p-2 flex flex-col gap-1 backdrop-blur-xl animate-fade-in text-xs min-w-[170px] mb-1 ${
            theme === 'light'
              ? 'bg-white/95 border-slate-200 text-slate-800 shadow-slate-300/50'
              : 'bg-slate-900/95 border-slate-700/80 text-white'
          }`}>
            <span className={`text-[10px] uppercase font-bold px-2 py-1 ${
              theme === 'light' ? 'text-slate-500' : 'text-slate-400'
            }`}>
              {language === 'ar' ? 'نمط الخريطة' : 'Fond de Carte'}
            </span>
            <button
              onClick={() => handleSelectMapStyle('google_streets')}
              className={`px-3 py-1.5 rounded-xl text-left flex items-center justify-between transition-all ${
                mapStyle === 'google_streets'
                  ? 'bg-blue-600 text-white font-bold'
                  : theme === 'light' ? 'text-slate-700 hover:bg-slate-100' : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <span>{language === 'ar' ? '🗺️ خريطة عادية' : '🗺️ Google Plan'}</span>
              {mapStyle === 'google_streets' && <span className="text-[10px]">✓</span>}
            </button>
            <button
              onClick={() => handleSelectMapStyle('google_satellite')}
              className={`px-3 py-1.5 rounded-xl text-left flex items-center justify-between transition-all ${
                mapStyle === 'google_satellite'
                  ? 'bg-blue-600 text-white font-bold'
                  : theme === 'light' ? 'text-slate-700 hover:bg-slate-100' : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <span>{language === 'ar' ? '🛰️ قمر صناعي' : '🛰️ Google Satellite'}</span>
              {mapStyle === 'google_satellite' && <span className="text-[10px]">✓</span>}
            </button>
            <button
              onClick={() => handleSelectMapStyle('google_traffic')}
              className={`px-3 py-1.5 rounded-xl text-left flex items-center justify-between transition-all ${
                mapStyle === 'google_traffic'
                  ? 'bg-blue-600 text-white font-bold'
                  : theme === 'light' ? 'text-slate-700 hover:bg-slate-100' : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <span>{language === 'ar' ? '🚦 حركة المرور' : '🚦 Google Trafic'}</span>
              {mapStyle === 'google_traffic' && <span className="text-[10px]">✓</span>}
            </button>
          </div>
        )}

        {/* Toggle Radar Settings Button */}
        <button
          ref={radarButtonRef}
          onClick={(e) => {
            e.stopPropagation();
            setIsRadarSettingsOpen(prev => !prev);
            setIsLayerSelectorOpen(false);
          }}
          className={`p-3 sm:p-3.5 rounded-2xl shadow-xl border transition-all flex items-center justify-center active:scale-95 ${
            isRadarSettingsOpen
              ? 'bg-emerald-600 border-emerald-400 text-white shadow-emerald-500/30'
              : theme === 'light'
                ? 'bg-white/95 border-slate-200 text-slate-700 hover:bg-slate-100 shadow-md'
                : 'bg-slate-900/95 border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800'
          }`}
          title={language === 'ar' ? 'ضبط نطاق الرادار' : 'Régler le rayon du radar (0.5 - 2.5 km)'}
        >
          <Radio className="w-5 h-5 text-emerald-500" />
        </button>

        {/* Toggle Layer Button */}
        <button
          ref={layerButtonRef}
          onClick={(e) => {
            e.stopPropagation();
            setIsLayerSelectorOpen(prev => !prev);
            setIsRadarSettingsOpen(false);
          }}
          className={`p-3 sm:p-3.5 rounded-2xl shadow-xl border transition-all flex items-center justify-center active:scale-95 ${
            isLayerSelectorOpen
              ? 'bg-blue-600 border-blue-400 text-white shadow-blue-500/30'
              : theme === 'light'
                ? 'bg-white/95 border-slate-200 text-slate-700 hover:bg-slate-100 shadow-md'
                : 'bg-slate-900/95 border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800'
          }`}
          title={language === 'ar' ? 'تغيير نمط الخريطة' : 'Changer le style de carte'}
        >
          <Layers className="w-5 h-5 text-blue-500" />
        </button>

        {/* Center on GPS Target Button */}
        <button
          onClick={() => {
            if (!userLocation) {
              if (onRequestGps) onRequestGps(true);
            } else if (mapInstanceRef.current) {
              mapInstanceRef.current.flyTo([userLocation.lat, userLocation.lon], 16, { animate: true, duration: 1 });
            }
          }}
          className={`p-3 sm:p-3.5 rounded-2xl shadow-2xl border flex items-center justify-center transition-all active:scale-95 ${
            userLocation
              ? theme === 'light'
                ? 'bg-white/95 border-blue-500/80 text-blue-600 hover:bg-slate-100 ring-2 ring-blue-500/20 shadow-md'
                : 'bg-slate-900/95 border-blue-500/80 text-blue-400 hover:bg-slate-800 ring-2 ring-blue-500/20'
              : 'bg-blue-600 border-blue-400 text-white shadow-blue-500/30 animate-pulse hover:bg-blue-500'
          }`}
          title={userLocation ? (language === 'ar' ? `موقعي الحالي (±${Math.round(userLocation.accuracy || 10)}م)` : `Ma position GPS (±${Math.round(userLocation.accuracy || 10)}m)`) : (language === 'ar' ? 'تحديد موقعي' : 'Activer mon GPS')}
        >
          <LocateFixed className={`w-5 h-5 ${userLocation ? (theme === 'light' ? 'text-blue-600' : 'text-blue-400') : 'text-white'}`} />
        </button>
      </div>

      {/* GPS Status & Satellite Search Pill */}
      {gpsErrorMsg && gpsStatus !== 'insecure' && (
        <div className={`absolute top-20 sm:top-20 left-1/2 -translate-x-1/2 z-[1050] max-w-md w-[calc(100%-2rem)] sm:w-auto p-2 px-3.5 rounded-2xl border shadow-2xl backdrop-blur-xl flex items-center justify-between gap-3 text-xs pointer-events-auto animate-fade-in ${
          theme === 'light'
            ? 'bg-white/95 border-blue-300 text-slate-800'
            : 'bg-slate-900/95 border-blue-500/50 text-slate-100'
        }`}>
          <div className="flex items-center gap-2.5 min-w-0">
            <span className="relative flex h-2.5 w-2.5 flex-shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-500"></span>
            </span>
            <span className="text-[11px] font-medium truncate">
              {language === 'ar'
                ? (gpsErrorMsg.includes('satellite') ? 'جاري البحث عن إشارة GPS...' : gpsErrorMsg)
                : gpsErrorMsg}
            </span>
          </div>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {onRequestGps && gpsStatus !== 'acquiring' && (
              <button
                onClick={onRequestGps}
                className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-[10px] font-bold transition shadow"
              >
                {language === 'ar' ? 'تفعيل' : 'Autoriser'}
              </button>
            )}
            {onDismissGpsError && (
              <button
                onClick={onDismissGpsError}
                className="p-1 text-slate-400 hover:text-white rounded-lg transition"
                title={language === 'ar' ? 'إغلاق' : 'Fermer'}
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Mobile HTTPS Insecure Guidance Notice */}
      {gpsStatus === 'insecure' && (
        <div className="absolute top-20 left-4 right-4 sm:left-auto sm:right-4 z-[1050] max-w-md p-3.5 rounded-2xl bg-amber-950/95 border border-amber-500/50 shadow-2xl backdrop-blur-md flex items-start gap-3 text-xs text-amber-100">
          <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-bold text-white text-sm">
              {language === 'ar' ? 'إذن الـ GPS على الهاتف' : 'Autorisation GPS sur mobile'}
            </p>
            <p className="mt-1 text-[11px] leading-relaxed text-amber-200">
              {language === 'ar'
                ? 'لأسباب أمنية، تمنع المتصفحات إذن GPS على روابط غير مشفرة. يرجى استخدام HTTPS أو التطبيق المثبت.'
                : "Pour des raisons de sécurité, les navigateurs mobiles bloquent le GPS sur HTTP. Utilisez l'adresse sécurisée HTTPS ou l'application Android installée."}
            </p>
            <a
              href={`https://${window.location.hostname}:3000/`}
              className="inline-block mt-2 px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-xs transition-colors"
            >
              {language === 'ar' ? 'التحويل إلى رابط HTTPS' : "Passer sur l'URL HTTPS sécurisée"}
            </a>
          </div>
        </div>
      )}

      {/* ── Active Itinerary Navigation Guidance Card ── */}
      {activeItinerary && (
        <div className="absolute bottom-[calc(env(safe-area-inset-bottom,0px)+5rem)] left-3 right-3 sm:left-6 sm:max-w-lg sm:right-auto z-[1040] pointer-events-auto animate-fade-in">
          <div className={`p-3.5 sm:p-4 rounded-3xl shadow-2xl border backdrop-blur-2xl transition-all ${
            theme === 'light'
              ? 'bg-white/95 border-slate-200/90 text-slate-800 shadow-slate-300/60 ring-1 ring-slate-900/5'
              : 'bg-slate-900/95 border-slate-700/80 text-white shadow-2xl ring-1 ring-white/10'
          }`}>
            {/* Header: Destination & Total Duration */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-200/60 dark:border-slate-800/80">
              <div className="flex items-center gap-2.5 min-w-0">
                <span
                  className="w-8 h-8 rounded-xl flex items-center justify-center font-black text-xs text-white shadow-md flex-shrink-0"
                  style={{ backgroundColor: activeItinerary.line?.color || '#2563eb' }}
                >
                  {getLineShortName(activeItinerary.line, language)}
                </span>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-500">
                      {language === 'ar' ? '🎯 الوجهة' : '🎯 Destination'}
                    </span>
                    <span className="text-[11px] font-bold text-slate-400">•</span>
                    <span className="text-[11px] font-bold text-emerald-400">
                      ~{activeItinerary.estimatedTotalMins} min
                    </span>
                  </div>
                  <h4 className="font-extrabold text-sm truncate text-white">
                    {activeItinerary.targetDestination?.name}
                  </h4>
                </div>
              </div>

              {onClearItinerary && (
                <button
                  onClick={onClearItinerary}
                  className="p-1.5 px-2.5 rounded-xl bg-slate-100 hover:bg-rose-600 hover:text-white dark:bg-slate-800 text-slate-400 transition-all shadow flex items-center gap-1 text-[11px] font-bold active:scale-95"
                  title={language === 'ar' ? 'إنهاء المسار' : 'Quitter l\'itinéraire'}
                >
                  <X className="w-3.5 h-3.5" />
                  <span>{language === 'ar' ? 'إنهاء' : 'Quitter'}</span>
                </button>
              )}
            </div>

            {/* Stepped Journey Timeline */}
            <div className="pt-3 space-y-2.5">
              {/* Leg 1: Walk to station */}
              <div className="flex items-start gap-2.5">
                <div className="flex flex-col items-center">
                  <span className="w-5 h-5 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center text-[10px] font-extrabold flex-shrink-0">
                    🚶
                  </span>
                  <div className="w-0.5 h-4 bg-sky-500/40 my-0.5"></div>
                </div>
                <div className="text-[11px] leading-tight pt-0.5">
                  <span className="text-slate-400">{language === 'ar' ? 'المشي' : 'Marcher'} </span>
                  <span className="font-bold text-sky-400">{activeItinerary.walkToOriginMeters}m</span> (~{activeItinerary.walkToOriginMins} min)
                  <span className="text-slate-400"> {language === 'ar' ? 'إلى محطة' : 'jusqu\'à'} </span>
                  <span className="font-bold text-white">{getStationName(activeItinerary.originStation, language)}</span>
                </div>
              </div>

              {/* Leg 2: Transit Ride */}
              <div className="flex items-start gap-2.5">
                <div className="flex flex-col items-center">
                  <span
                    className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-black text-white flex-shrink-0 shadow-sm"
                    style={{ backgroundColor: activeItinerary.line?.color || '#2563eb' }}
                  >
                    {getLineShortName(activeItinerary.line, language)}
                  </span>
                  <div className="w-0.5 h-4 bg-slate-600/40 my-0.5"></div>
                </div>
                <div className="text-[11px] leading-tight pt-0.5">
                  <span className="text-slate-400">{language === 'ar' ? 'ركوب' : 'Prendre'} </span>
                  <span className="font-bold" style={{ color: activeItinerary.line?.color || '#3b82f6' }}>
                    {getLineName(activeItinerary.line, language)}
                  </span>
                  <span className="text-slate-400"> ({activeItinerary.stopsCount} {language === 'ar' ? 'محطات' : 'arrêts'}) {language === 'ar' ? 'حتى' : 'jusqu\'à'} </span>
                  <span className="font-bold text-white">{getStationName(activeItinerary.dropoffStation, language)}</span>
                </div>
              </div>

              {/* Leg 3: Walk to target */}
              <div className="flex items-start gap-2.5">
                <div className="flex flex-col items-center">
                  <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-extrabold flex-shrink-0">
                    🎯
                  </span>
                </div>
                <div className="text-[11px] leading-tight pt-0.5">
                  <span className="text-slate-400">{language === 'ar' ? 'المشي' : 'Marcher'} </span>
                  <span className="font-bold text-emerald-400">{activeItinerary.walkFromDropoffMeters}m</span> (~{activeItinerary.walkFromDropoffMins} min)
                  <span className="text-slate-400"> {language === 'ar' ? 'للوصول إلى' : 'pour arriver à'} </span>
                  <span className="font-bold text-white">{activeItinerary.targetDestination?.name}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Prevent map blinking — memo skips re-render only when truly nothing changed ─
// The map LAYER drawing useEffect only depends on [activeNetwork, selectedLine, selectedDirection]
// so even when liveLocations triggers a re-render, line layers are NOT cleared/redrawn.
// The vehicles useEffect handles vehicle markers independently.
function _areMapPropsEqual(prev, next) {
  return (
    prev.activeNetwork === next.activeNetwork &&
    prev.selectedLine?.id === next.selectedLine?.id &&
    prev.selectedDirection === next.selectedDirection &&
    prev.activeItinerary === next.activeItinerary &&
    prev.gpsStatus === next.gpsStatus &&
    prev.gpsErrorMsg === next.gpsErrorMsg &&
    prev.userLocation?.lat === next.userLocation?.lat &&
    prev.userLocation?.lon === next.userLocation?.lon &&
    prev.liveLocations === next.liveLocations
  );
}

export default memo(TransitMap, _areMapPropsEqual);
