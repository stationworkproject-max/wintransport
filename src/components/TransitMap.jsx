import React, { useState, useEffect, useRef, useMemo, memo } from 'react';
import L from 'leaflet';
import { STATIC_LINES } from '../data/staticTransit';
import TRANSIT_SHAPES from '../data/transitShapes.json';
import { Users, Navigation, Clock, ShieldCheck, AlertCircle, X, LocateFixed, Layers, Search, Compass, MapPin } from 'lucide-react';
import { getStationName, getLineName, getLineShortName, getDirectionLabel } from '../utils/i18n';

export const GOOGLE_MAPS_API_KEY = 'AIzaSyD5AZ-rNY0NGtkFDZUyB3cwPKH3CiUit6I';

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
  language = 'fr'
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const tileLayerRef = useRef(null);
  const lineLayersRef = useRef({});
  const stationLayersRef = useRef({});
  const vehicleMarkersRef = useRef({});
  const userMarkerRef = useRef(null);
  const userAccuracyCircleRef = useRef(null);
  // Keep latest liveLocations in a ref so the vehicle interval can read it
  // without needing a re-render of the component
  const liveLocationsRef = useRef(liveLocations);
  const activeNetworkRef = useRef(activeNetwork);
  const selectedLineRef = useRef(selectedLine);
  useEffect(() => { liveLocationsRef.current = liveLocations; }, [liveLocations]);
  useEffect(() => { activeNetworkRef.current = activeNetwork; }, [activeNetwork]);
  useEffect(() => { selectedLineRef.current = selectedLine; }, [selectedLine]);


  // Map layer style: Google Streets (default) with API key, Google Satellite, Google Traffic, or Dark
  const [mapStyle, setMapStyle] = useState('google_streets');
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

    // Clicking on empty map area deselects active line/station
    map.on('click', () => {
      if (Date.now() < ignoreMapClickUntilRef.current) return;
      setIsSearchDropdownOpen(false);
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
      crossOrigin: true
    };

    if (mapStyle === 'google_streets') {
      url = `https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&key=${GOOGLE_MAPS_API_KEY}`;
      options = {
        attribution: '&copy; Google Maps',
        subdomains: ['0', '1', '2', '3'],
        ...commonTileOptions
      };
    } else if (mapStyle === 'google_satellite') {
      url = `https://mt{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}&key=${GOOGLE_MAPS_API_KEY}`;
      options = {
        attribution: '&copy; Google Maps Satellite',
        subdomains: ['0', '1', '2', '3'],
        ...commonTileOptions
      };
    } else if (mapStyle === 'google_traffic') {
      url = `https://mt{s}.google.com/vt/lyrs=m,traffic&x={x}&y={y}&z={z}&key=${GOOGLE_MAPS_API_KEY}`;
      options = {
        attribution: '&copy; Google Maps Trafic',
        subdomains: ['0', '1', '2', '3'],
        ...commonTileOptions
      };
    } else {
      url = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
      options = {
        attribution: '&copy; CARTO | &copy; OpenStreetMap',
        subdomains: 'abcd',
        maxZoom: 19,
        keepBuffer: 8,
        updateWhenIdle: false,
        updateWhenZooming: false
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
    if (selectedLine) {
      const activeDir = typeof selectedDirection === 'number' ? selectedDirection : 0;
      const dirShapeKey = `${selectedLine.id}_${activeDir}`;

      let latlngs = null;
      if (TRANSIT_SHAPES[dirShapeKey] && TRANSIT_SHAPES[dirShapeKey].length > 1) {
        latlngs = TRANSIT_SHAPES[dirShapeKey];
      } else if (TRANSIT_SHAPES[selectedLine.id] && TRANSIT_SHAPES[selectedLine.id].length > 1) {
        latlngs = activeDir === 1
          ? [...TRANSIT_SHAPES[selectedLine.id]].reverse()
          : TRANSIT_SHAPES[selectedLine.id];
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
      
      // 1. Draw glowing background casing + crisp colored route line
      if (latlngs && latlngs.length >= 2) {
        // Draw complementary return/going rail so both rails are clearly visible line by line
        const otherDir = activeDir === 0 ? 1 : 0;
        const otherDirShapeKey = `${selectedLine.id}_${otherDir}`;
        const otherLatlngs = TRANSIT_SHAPES[otherDirShapeKey];
        if (otherLatlngs && otherLatlngs.length >= 2 && otherLatlngs !== latlngs) {
          const companionPolyline = L.polyline(otherLatlngs, {
            color: selectedLine.color,
            weight: 3.5,
            opacity: 0.8,
            lineJoin: 'round',
            lineCap: 'round',
          }).addTo(map);

          lineLayersRef.current[`${selectedLine.id}-companion`] = companionPolyline;
        }

        const casing = L.polyline(latlngs, {
          color: '#ffffff',
          weight: 8,
          opacity: 0.65,
          lineJoin: 'round',
          lineCap: 'round',
        }).addTo(map);

        const mainPolyline = L.polyline(latlngs, {
          color: selectedLine.color,
          weight: 5,
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

      // Fit map bounds smoothly to the isolated line
      if (lineLayersRef.current[selectedLine.id]) {
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
    // Heavy rail lines (Metro 1-6, TGM, RFR, Trains) are drawn as the clean city backbone.
    // Bus lines are drawn when selected by user ("see just one line like bus 104 only not all the map").
    const linesToProcess = STATIC_LINES.filter(line => {
      if (line.type_id === 'bus') return false;
      if (activeNetwork === 'all') return true;
      return line.type_id === activeNetwork;
    });

    linesToProcess.forEach(line => {
      const shape0 = TRANSIT_SHAPES[`${line.id}_0`];
      const shape1 = TRANSIT_SHAPES[`${line.id}_1`];
      const hasDualRails = shape0 && shape1 && shape0.length > 1 && shape1.length > 1;
      const hasShape = TRANSIT_SHAPES[line.id] && TRANSIT_SHAPES[line.id].length > 1;
      const latlngs = hasDualRails
        ? [shape0, shape1]
        : (hasShape ? TRANSIT_SHAPES[line.id] : line.stops.map(s => [s.lat, s.lon]));

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
  }, [activeNetwork, selectedLine, selectedDirection, language]);

  // ── Vehicle marker updater — runs on interval, reads from refs (NO re-render) ──
  useEffect(() => {
    function updateVehicleMarkers() {
      const map = mapInstanceRef.current;
      if (!map) return;

      const liveLocations = liveLocationsRef.current || [];
      const activeNetwork = activeNetworkRef.current;
      const selectedLine = selectedLineRef.current;

      const currentVehicleIds = new Set();

      const activeVehicles = liveLocations.filter(loc => {
        if (selectedLine) return loc.line_id === selectedLine.id;
        if (activeNetwork === 'all') return true;
        const matchingLine = STATIC_LINES.find(l => l.id === loc.line_id);
        return matchingLine?.type_id === activeNetwork;
      });

      activeVehicles.forEach(loc => {
        currentVehicleIds.add(loc.id);
        const line = STATIC_LINES.find(l => l.id === loc.line_id) || loc.transit_lines;
        const lineColor = line?.color || '#0071e3';
        const lineShort = line?.short_name || 'Direct';
        const passengerCount = loc.passenger_count || 1;

        const iconHtml = `
          <div class="relative flex items-center justify-center cursor-pointer group" style="width: 44px; height: 44px;">
            <div class="radar-ring absolute w-10 h-10 rounded-full" style="background-color: ${lineColor};"></div>
            <div class="relative flex items-center justify-center w-8 h-8 rounded-full shadow-lg border-2 border-white text-white font-extrabold text-[11px] transition-transform duration-300 group-hover:scale-110" style="background-color: ${lineColor};">
              ${lineShort}
              <div class="absolute -top-1 right-0 w-2.5 h-2.5 rounded-full bg-emerald-400 border border-slate-900 shadow"></div>
            </div>
            <div class="absolute -bottom-1 bg-slate-900/90 text-emerald-400 font-bold text-[9px] px-1.5 py-0.2 rounded-full border border-slate-700 shadow flex items-center gap-0.5">
              👤${passengerCount}
            </div>
          </div>
        `;

        const popupContent = `
          <div class="p-3 min-w-[210px] text-slate-100">
            <div class="flex items-center justify-between border-b border-slate-700/60 pb-2 mb-2">
              <div class="flex items-center gap-2">
                <span class="px-2 py-0.5 rounded font-bold text-xs text-white" style="background-color: ${lineColor};">${lineShort}</span>
                <span class="font-bold text-sm text-white">${loc.vehicle_label || 'Véhicule en direct'}</span>
              </div>
              <span class="text-[10px] bg-emerald-500/20 text-emerald-400 font-bold px-1.5 py-0.5 rounded border border-emerald-500/40">GPS Direct</span>
            </div>
            <div class="space-y-1.5 text-xs">
              <div class="flex items-center justify-between text-slate-300">
                <span class="text-slate-400">Direction :</span>
                <span class="font-semibold text-white truncate max-w-[120px]">${loc.direction || 'En service'}</span>
              </div>
              <div class="flex items-center justify-between text-slate-300">
                <span class="text-slate-400">Vitesse réelle :</span>
                <span class="font-bold text-emerald-400">${loc.speed_kmh || 0} km/h</span>
              </div>
              <div class="flex items-center justify-between text-slate-300">
                <span class="text-slate-400">Voyageurs à bord :</span>
                <span class="font-semibold">${passengerCount} personne(s)</span>
              </div>
            </div>
          </div>
        `;

        if (vehicleMarkersRef.current[loc.id]) {
          // Smooth position update — no DOM flicker
          const marker = vehicleMarkersRef.current[loc.id];
          marker.setLatLng([loc.latitude, loc.longitude]);
          marker.setPopupContent(popupContent);
        } else {
          const vehicleIcon = L.divIcon({
            html: iconHtml,
            className: 'vehicle-marker',
            iconSize: [44, 44],
            iconAnchor: [22, 22],
            popupAnchor: [0, -22],
          });
          const marker = L.marker([loc.latitude, loc.longitude], {
            icon: vehicleIcon,
            zIndexOffset: 1000,
          }).bindPopup(popupContent, { className: 'custom-popup' });
          marker.addTo(map);
          vehicleMarkersRef.current[loc.id] = marker;
        }
      });

      // Remove stale vehicles
      Object.keys(vehicleMarkersRef.current).forEach(id => {
        if (!currentVehicleIds.has(id)) {
          map.removeLayer(vehicleMarkersRef.current[id]);
          delete vehicleMarkersRef.current[id];
        }
      });
    }

    // Run immediately, then every 5 seconds — no React re-render needed
    updateVehicleMarkers();
    const interval = setInterval(updateVehicleMarkers, 5000);
    return () => clearInterval(interval);
  }, []); // empty deps: reads from refs, never causes re-render


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
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Floating Top Bar: Single Line Isolation & Quick Line Search & Guide Trajet */}
      <div className="absolute top-4 left-4 right-4 z-[1003] flex items-center justify-between gap-2 pointer-events-auto">
        
        {/* Single Line Isolation Badge or Quick Line Search */}
        {/* Single Line Isolation Badge & Directional Switcher */}
        {selectedLine ? (
          <div className="flex flex-col bg-slate-900/95 border border-slate-700/90 rounded-2xl shadow-2xl p-2.5 backdrop-blur-xl max-w-sm sm:max-w-md animate-fade-in">
            <div className="flex items-center gap-2.5">
              <span
                className="w-8 h-8 rounded-xl flex items-center justify-center font-extrabold text-xs text-white shadow flex-shrink-0"
                style={{ backgroundColor: selectedLine.color }}
              >
                {getLineShortName(selectedLine, language)}
              </span>
              <div className="min-w-0 flex-1 pr-1">
                <div className="font-bold text-xs text-white truncate max-w-[140px] sm:max-w-xs">
                  {getLineName(selectedLine, language)}
                </div>
                <div className="text-[10px] text-slate-400 flex items-center gap-1">
                  <span>
                    {((selectedDirection === 1 && selectedLine.stops_retour?.length)
                      ? selectedLine.stops_retour.length
                      : (selectedLine.stops_aller?.length || selectedLine.stops.length))} {language === 'ar' ? 'محطة' : 'arrêts'}
                  </span>
                  <span>•</span>
                  <span className="text-emerald-400 font-semibold">{language === 'ar' ? 'مسار معزول' : 'Ligne isolée'}</span>
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
                  className="p-1.5 px-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-bold flex items-center gap-1 transition shadow border border-slate-600/60"
                  title={language === 'ar' ? 'إلغاء وعرض كامل الشبكة' : 'Afficher tout le réseau'}
                >
                  <X className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">{language === 'ar' ? 'إلغاء' : 'Effacer'}</span>
                </button>
              </div>
            </div>

            {/* Direction Switcher (Sens Aller / Sens Retour) */}
            {selectedLine.directions && selectedLine.directions.length > 1 && (
              <div className="flex items-center gap-1.5 mt-2 pt-2 border-t border-slate-800/80">
                {selectedLine.directions.map((dir, idx) => {
                  const dirText = getDirectionLabel(selectedLine, idx, language);
                  return (
                    <button
                      key={idx}
                      onClick={() => onDirectionChange && onDirectionChange(idx)}
                      className={`flex-1 py-1 px-2 rounded-xl text-[11px] font-bold transition flex items-center justify-center gap-1 truncate ${
                        (selectedDirection || 0) === idx
                          ? 'bg-blue-600 text-white shadow-md ring-1 ring-blue-400'
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
          </div>
        ) : (
          <div className="flex flex-col gap-1.5 flex-1 max-w-xs sm:max-w-md">
            <div className="relative">
              <div className="flex items-center gap-2 bg-slate-900/95 border border-slate-700/80 rounded-2xl shadow-2xl p-2 px-3 backdrop-blur-xl">
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
                  className="bg-transparent text-xs text-white placeholder:text-slate-500 focus:outline-none w-full font-medium"
                />
                {lineFilterSearch && (
                  <button
                    onClick={() => {
                      setLineFilterSearch('');
                      setIsSearchDropdownOpen(false);
                    }}
                    className="text-slate-400 hover:text-white text-xs p-0.5"
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
                  className="absolute top-full left-0 right-0 mt-1.5 max-h-60 overflow-y-auto bg-slate-900/95 border border-slate-700/90 rounded-2xl shadow-2xl divide-y divide-slate-800/80 backdrop-blur-xl z-[1030]"
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
                      className="w-full p-2.5 text-left flex items-center justify-between text-xs hover:bg-slate-800/80 active:bg-slate-700 transition"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span
                          className="px-2 py-0.5 rounded font-extrabold text-[11px] text-white flex-shrink-0"
                          style={{ backgroundColor: line.color }}
                        >
                          {getLineShortName(line, language)}
                        </span>
                        <span className="text-white font-medium truncate">{getLineName(line, language)}</span>
                      </div>
                      <span className="text-[10px] text-slate-400 flex-shrink-0 ml-1">
                        {line.stops.length} {language === 'ar' ? 'محطة' : 'arrêts'}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Floating Guide Trajet Assistant Button */}
        {onOpenTripPlanner && (
          <button
            onClick={onOpenTripPlanner}
            className="flex items-center gap-1.5 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs p-2 px-3 sm:px-4 rounded-2xl shadow-xl shadow-blue-500/25 transition active:scale-95 border border-white/20 whitespace-nowrap"
          >
            <Compass className="w-4 h-4 text-white" />
            <span className="hidden sm:inline">{language === 'ar' ? 'تخطيط المسار' : 'Guide Trajet'}</span>
            <span className="sm:hidden">{language === 'ar' ? 'مسار' : 'Trajet'}</span>
          </button>
        )}

      </div>

      {/* Floating Controls: GPS Center & Google Maps Layer Selector */}
      <div className="absolute bottom-20 sm:bottom-8 right-3 sm:right-6 z-[1002] flex flex-col items-end gap-2.5 pointer-events-auto">
        {/* Layer Selector Dropdown */}
        {isLayerSelectorOpen && (
          <div className="bg-slate-900/95 border border-slate-700/80 rounded-2xl shadow-2xl p-2 flex flex-col gap-1 backdrop-blur-xl animate-fade-in text-xs min-w-[170px] mb-1">
            <span className="text-[10px] uppercase font-bold text-slate-400 px-2 py-1">
              {language === 'ar' ? 'نمط الخريطة' : 'Fond de Carte'}
            </span>
            <button
              onClick={() => { setMapStyle('google_streets'); setIsLayerSelectorOpen(false); }}
              className={`px-3 py-1.5 rounded-xl text-left flex items-center justify-between transition-all ${
                mapStyle === 'google_streets' ? 'bg-blue-600 text-white font-bold' : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <span>{language === 'ar' ? '🗺️ خريطة عادية' : '🗺️ Google Plan'}</span>
              {mapStyle === 'google_streets' && <span className="text-[10px]">✓</span>}
            </button>
            <button
              onClick={() => { setMapStyle('google_satellite'); setIsLayerSelectorOpen(false); }}
              className={`px-3 py-1.5 rounded-xl text-left flex items-center justify-between transition-all ${
                mapStyle === 'google_satellite' ? 'bg-blue-600 text-white font-bold' : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <span>{language === 'ar' ? '🛰️ قمر صناعي' : '🛰️ Google Satellite'}</span>
              {mapStyle === 'google_satellite' && <span className="text-[10px]">✓</span>}
            </button>
            <button
              onClick={() => { setMapStyle('google_traffic'); setIsLayerSelectorOpen(false); }}
              className={`px-3 py-1.5 rounded-xl text-left flex items-center justify-between transition-all ${
                mapStyle === 'google_traffic' ? 'bg-blue-600 text-white font-bold' : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <span>{language === 'ar' ? '🚦 حركة المرور' : '🚦 Google Trafic'}</span>
              {mapStyle === 'google_traffic' && <span className="text-[10px]">✓</span>}
            </button>
            <button
              onClick={() => { setMapStyle('dark'); setIsLayerSelectorOpen(false); }}
              className={`px-3 py-1.5 rounded-xl text-left flex items-center justify-between transition-all ${
                mapStyle === 'dark' ? 'bg-blue-600 text-white font-bold' : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <span>{language === 'ar' ? '🌙 الوضع الليلي' : '🌙 Mode Sombre'}</span>
              {mapStyle === 'dark' && <span className="text-[10px]">✓</span>}
            </button>
          </div>
        )}

        {/* Toggle Layer Button */}
        <button
          onClick={() => setIsLayerSelectorOpen(!isLayerSelectorOpen)}
          className="p-3 sm:p-3.5 rounded-2xl shadow-xl border bg-slate-900/95 border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 transition-all flex items-center justify-center active:scale-95"
          title={language === 'ar' ? 'تغيير نمط الخريطة' : 'Changer le style de carte'}
        >
          <Layers className="w-5 h-5 text-blue-400" />
        </button>

        {/* Center on GPS Target Button */}
        <button
          onClick={() => {
            if (!userLocation) {
              if (onRequestGps) onRequestGps();
            } else if (mapInstanceRef.current) {
              mapInstanceRef.current.flyTo([userLocation.lat, userLocation.lon], 16, { animate: true, duration: 1 });
            }
          }}
          className={`p-3 sm:p-3.5 rounded-2xl shadow-2xl border flex items-center justify-center transition-all active:scale-95 ${
            userLocation
              ? 'bg-slate-900/95 border-blue-500/80 text-blue-400 hover:bg-slate-800 hover:scale-105 ring-2 ring-blue-500/20'
              : 'bg-blue-600 border-blue-400 text-white shadow-blue-500/30 animate-pulse hover:bg-blue-500'
          }`}
          title={userLocation ? (language === 'ar' ? `موقعي الحالي (±${Math.round(userLocation.accuracy || 10)}م)` : `Ma position GPS (±${Math.round(userLocation.accuracy || 10)}m)`) : (language === 'ar' ? 'تحديد موقعي' : 'Activer mon GPS')}
        >
          <LocateFixed className={`w-5 h-5 ${userLocation ? 'text-blue-400' : 'text-white'}`} />
        </button>
      </div>

      {/* GPS Status & Satellite Search Pill */}
      {gpsErrorMsg && gpsStatus !== 'insecure' && (
        <div className="absolute top-20 sm:top-20 left-1/2 -translate-x-1/2 z-[1050] max-w-md w-[calc(100%-2rem)] sm:w-auto p-2 px-3.5 rounded-2xl bg-slate-900/95 border border-blue-500/50 shadow-2xl backdrop-blur-xl flex items-center justify-between gap-3 text-xs text-slate-100 pointer-events-auto animate-fade-in">
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
    prev.gpsStatus === next.gpsStatus &&
    prev.gpsErrorMsg === next.gpsErrorMsg &&
    prev.userLocation?.lat === next.userLocation?.lat &&
    prev.userLocation?.lon === next.userLocation?.lon &&
    prev.liveLocations === next.liveLocations
  );
}

export default memo(TransitMap, _areMapPropsEqual);
