import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import Header from './components/Header';
import TransitMap from './components/TransitMap';
import PassengerBroadcastModal from './components/PassengerBroadcastModal';
import CrowdReportModal from './components/CrowdReportModal';
import LineScheduleDrawer from './components/LineScheduleDrawer';
import StationArrivalModal from './components/StationArrivalModal';
import LinesListView from './components/LinesListView';
import BottomNav from './components/BottomNav';
import SmartTripPlannerModal from './components/SmartTripPlannerModal';
import { 
  fetchLiveLocations, 
  fetchCrowdReports, 
  subscribeToRealtimeUpdates,
  removeLiveLocation,
  SUPABASE_URL,
  SUPABASE_ANON_KEY
} from './supabase';
import { STATIC_LINES } from './data/staticTransit';
import { isNativeAndroid, isBackgroundBroadcastRunning } from './native/backgroundBroadcast';
import { Radio, AlertTriangle, Layers, Navigation, Search } from 'lucide-react';

export default function App() {
  const [activeNetwork, setActiveNetwork] = useState('all');
  const [liveLocations, setLiveLocations] = useState([]);
  const [crowdReports, setCrowdReports] = useState([]);
  const [selectedLine, setSelectedLine] = useState(null);
  const [selectedDirection, setSelectedDirection] = useState(0);
  const [isScheduleDrawerOpen, setIsScheduleDrawerOpen] = useState(false);
  const [selectedStation, setSelectedStation] = useState(null);
  const [stationContextLine, setStationContextLine] = useState(null);
  const [sidebarSearch, setSidebarSearch] = useState('');

  const handleSelectLine = useCallback((line) => {
    setSelectedLine(line);
    setSelectedDirection(0);
  }, []);
  
  // Modals & Drawers
  const [isBroadcastOpen, setIsBroadcastOpen] = useState(false);
  const [isBroadcasting, setIsBroadcasting] = useState(false);
  const [broadcastSession, setBroadcastSession] = useState(null);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [isTripPlannerOpen, setIsTripPlannerOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('map'); // 'map' | 'lines'

  // User Real GPS State
  const [userLocation, setUserLocation] = useState(null);
  const [gpsStatus, setGpsStatus] = useState('idle'); // 'idle' | 'acquiring' | 'granted' | 'denied' | 'insecure'
  const [gpsErrorMsg, setGpsErrorMsg] = useState('');
  const watchIdRef = useRef(null);

  // Request & Watch Real GPS Location
  const requestUserGps = () => {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (!window.isSecureContext && !isLocal && window.location.protocol !== 'https:') {
      setGpsStatus('insecure');
      setGpsErrorMsg(`Sur mobile, le GPS exige HTTPS. Ouvrez https://${window.location.hostname}:3000/`);
      return;
    }

    if (!navigator.geolocation) {
      setGpsStatus('denied');
      setGpsErrorMsg("La géolocalisation n'est pas supportée par cet appareil.");
      return;
    }

    setGpsStatus('acquiring');
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
    }

    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        setGpsStatus('granted');
        setGpsErrorMsg('');
        setUserLocation({
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          speed: pos.coords.speed ? Math.round(pos.coords.speed * 3.6) : 0,
          heading: pos.coords.heading || 0,
          timestamp: pos.timestamp
        });
      },
      (err) => {
        console.warn('GPS error:', err);
        if (err.code === 1) {
          setGpsStatus('denied');
          setGpsErrorMsg("Permission GPS refusée. Veuillez autoriser la localisation dans les paramètres du navigateur.");
        } else if (err.code === 2) {
          setGpsStatus('denied');
          setGpsErrorMsg("Position GPS introuvable. Vérifiez que la localisation GPS de votre téléphone est activée.");
        } else {
          setGpsStatus('acquiring');
          setGpsErrorMsg("Recherche des satellites GPS en cours...");
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 1000
      }
    );
  };

  // Initial Data Fetch & Supabase Realtime Subscription + Auto-cleanup
  useEffect(() => {
    // 0. Clean up abandoned session only when no native background broadcast is active
    const cleanAbandonedSession = async () => {
      try {
        const abandonedId = localStorage.getItem('transit_broadcast_id');
        if (!abandonedId) return;

        let shouldCleanup = true;
        if (isNativeAndroid()) {
          const nativeStatus = await isBackgroundBroadcastRunning().catch(() => ({ running: false }));
          shouldCleanup = !nativeStatus?.running;
        }

        if (shouldCleanup) {
          removeLiveLocation(abandonedId).catch(() => {});
          localStorage.removeItem('transit_broadcast_id');
        }
      } catch (e) {}
    };
    cleanAbandonedSession();

    // 1. Initial fetch
    fetchLiveLocations().then(setLiveLocations);
    fetchCrowdReports().then(setCrowdReports);

    // 2. Realtime WebSocket subscription
    const unsubscribe = subscribeToRealtimeUpdates(
      (updatedLocations) => {
        setLiveLocations(updatedLocations);
      },
      (updatedReports) => {
        setCrowdReports(updatedReports);
      }
    );

    // 3. Start watching real GPS location
    requestUserGps();

    // 4. Client-side Real-time Liveness Pruner (runs every 8s)
    // Drops any vehicle whose last ping is older than 45 seconds immediately
    const livenessTimer = setInterval(() => {
      const cutoff = Date.now() - 45 * 1000;
      setLiveLocations(prev => prev.filter(loc => {
        const t = new Date(loc.updated_at).getTime();
        return !isNaN(t) && t > cutoff;
      }));
    }, 8000);

    // 5. Periodic background re-sync (every 20s)
    const syncTimer = setInterval(() => {
      fetchLiveLocations().then(setLiveLocations);
    }, 20000);

    // 6. Global Unload Listener: remove any active vehicle when user closes window/tab
    const handleUnload = () => {
      try {
        const activeId = localStorage.getItem('transit_broadcast_id');
        if (activeId) {
          localStorage.removeItem('transit_broadcast_id');
          const url = `${SUPABASE_URL}/rest/v1/transit_live_locations?id=eq.${activeId}`;
          fetch(url, {
            method: 'DELETE',
            headers: {
              'apikey': SUPABASE_ANON_KEY,
              'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
            },
            keepalive: true,
          }).catch(() => {});
        }
      } catch (e) {}
    };

    const useUnloadCleanup = !isNativeAndroid();
    if (useUnloadCleanup) {
      window.addEventListener('beforeunload', handleUnload);
      window.addEventListener('pagehide', handleUnload);
    }

    return () => {
      unsubscribe();
      clearInterval(livenessTimer);
      clearInterval(syncTimer);
      if (useUnloadCleanup) {
        window.removeEventListener('beforeunload', handleUnload);
        window.removeEventListener('pagehide', handleUnload);
      }
      if (watchIdRef.current !== null && navigator.geolocation) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  const handleOpenBroadcast = useCallback((preselectedLineId) => {
    if (preselectedLineId && typeof preselectedLineId === 'string') {
      const line = STATIC_LINES.find(l => l.id === preselectedLineId);
      if (line) {
        setBroadcastSession(prev => ({
          ...prev,
          lineId: line.id,
          direction: line.directions[0],
          lineName: line.short_name
        }));
      }
    }
    setIsBroadcastOpen(true);
  }, []);

  const handleSelectStation = useCallback((station, line) => {
    setSelectedStation(station);
    setStationContextLine(line);
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-950 overflow-hidden font-sans">
      
      {/* Top Navigation Bar */}
      <Header
        activeNetwork={activeNetwork}
        setActiveNetwork={setActiveNetwork}
        liveCount={liveLocations.length}
        onOpenBroadcast={() => handleOpenBroadcast()}
        isBroadcasting={isBroadcasting}
        onOpenReport={() => setIsReportOpen(true)}
        recentReportCount={crowdReports.length}
        userLocation={userLocation}
        onRequestGps={requestUserGps}
        gpsStatus={gpsStatus}
        onOpenTripPlanner={() => setIsTripPlannerOpen(true)}
      />

      {/* Main View Area */}
      <main className="flex-1 relative overflow-hidden flex flex-col md:flex-row">
        
        {/* Desktop Sidebar: Line Quick Selector */}
        <aside className="hidden lg:flex flex-col w-80 border-r border-slate-800 bg-slate-900/90 z-[1005] backdrop-blur-md pointer-events-auto">
          <div className="p-3 border-b border-slate-800 bg-slate-800/40 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Lignes en service
            </span>
            <span className="text-[11px] bg-blue-500/20 text-blue-400 font-semibold px-2 py-0.5 rounded-full">
              229 Lignes
            </span>
          </div>

          {/* Sidebar Search */}
          <div className="p-2 border-b border-slate-800/60 bg-slate-800/20">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input
                type="text"
                value={sidebarSearch}
                onChange={(e) => setSidebarSearch(e.target.value)}
                placeholder="Chercher ligne (ex : 35, 1, TGM...)"
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
            {STATIC_LINES
              .filter(l => activeNetwork === 'all' || l.type_id === activeNetwork)
              .filter(l => {
                if (!sidebarSearch.trim()) return true;
                const q = sidebarSearch.toLowerCase();
                return l.short_name.toLowerCase().includes(q) || l.long_name.toLowerCase().includes(q);
              })
              .map(line => {
              const liveCount = liveLocations.filter(loc => loc.line_id === line.id).length;
              const isSelected = selectedLine?.id === line.id;

              return (
                <div
                  key={line.id}
                  onClick={() => handleSelectLine(isSelected ? null : line)}
                  className={`p-2.5 rounded-xl border cursor-pointer transition-all flex items-center justify-between group ${
                    isSelected
                      ? 'bg-blue-600/20 border-blue-500/80 text-white shadow-md ring-1 ring-blue-500/30'
                      : 'bg-slate-800/40 border-slate-700/50 text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span
                      className="w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs text-white flex-shrink-0 shadow"
                      style={{ backgroundColor: line.color }}
                    >
                      {line.short_name}
                    </span>
                    <div className="min-w-0">
                      <div className="font-semibold text-xs truncate">{line.long_name}</div>
                      <div className="text-[10px] text-slate-400">{line.stops.length} stations</div>
                    </div>
                  </div>

                  {liveCount > 0 && (
                    <span className="flex-shrink-0 bg-emerald-500/20 text-emerald-400 text-[10px] font-bold px-1.5 py-0.5 rounded-full flex items-center gap-1 border border-emerald-500/30">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                      {liveCount}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Quick Active Broadcast Footer */}
          {isBroadcasting && (
            <div className="p-3 bg-emerald-950/40 border-t border-emerald-800/40 flex items-center justify-between text-xs text-emerald-400">
              <span className="flex items-center gap-1.5 font-semibold">
                <Radio className="w-3.5 h-3.5 animate-pulse" />
                GPS Actif à bord
              </span>
              <button
                onClick={() => setIsBroadcastOpen(true)}
                className="text-[11px] underline hover:text-white"
              >
                Gérer
              </button>
            </div>
          )}
        </aside>

        {/* Center / Full Map or Mobile Tab Content */}
        <div className="flex-1 relative w-full h-full">
          {activeTab === 'map' ? (
            <TransitMap
              activeNetwork={activeNetwork}
              liveLocations={liveLocations}
              selectedLine={selectedLine}
              onSelectLine={handleSelectLine}
              selectedDirection={selectedDirection}
              onDirectionChange={setSelectedDirection}
              onOpenSchedule={() => setIsScheduleDrawerOpen(true)}
              userLocation={userLocation}
              onSelectStation={handleSelectStation}
              onRequestGps={requestUserGps}
              gpsStatus={gpsStatus}
              gpsErrorMsg={gpsErrorMsg}
              onDismissGpsError={() => setGpsErrorMsg('')}
              onOpenTripPlanner={() => setIsTripPlannerOpen(true)}
            />
          ) : (
            <div className="h-full overflow-y-auto pb-20">
              <LinesListView
                activeNetwork={activeNetwork}
                liveLocations={liveLocations}
                onSelectLine={(l) => {
                  handleSelectLine(l);
                  setIsScheduleDrawerOpen(false);
                  setActiveTab('map');
                }}
              />
            </div>
          )}
        </div>

      </main>

      {/* Line Progression & Schedule Drawer */}
      {isScheduleDrawerOpen && selectedLine && (
        <LineScheduleDrawer
          line={selectedLine}
          onClose={() => setIsScheduleDrawerOpen(false)}
          liveLocations={liveLocations}
          onOpenBroadcast={handleOpenBroadcast}
          onSelectStation={handleSelectStation}
          crowdReports={crowdReports}
          selectedDirection={selectedDirection}
          onDirectionChange={setSelectedDirection}
        />
      )}

      {/* Station Arrivals Modal */}
      <StationArrivalModal
        station={selectedStation}
        line={stationContextLine}
        onClose={() => setSelectedStation(null)}
        liveLocations={liveLocations}
        onOpenBroadcast={handleOpenBroadcast}
      />

      {/* Smart Trip Planner Modal ("Guide Trajet / Où aller ?") */}
      <SmartTripPlannerModal
        isOpen={isTripPlannerOpen}
        onClose={() => setIsTripPlannerOpen(false)}
        userLocation={userLocation}
        onRequestGps={requestUserGps}
        onSelectLineAndStation={(line, station) => {
          handleSelectLine(line);
          setSelectedStation(station);
          setStationContextLine(line);
          setActiveTab('map');
        }}
        liveLocations={liveLocations}
      />

      {/* Passenger Broadcast Modal ("Je suis à bord") */}
      <PassengerBroadcastModal
        isOpen={isBroadcastOpen}
        onClose={() => setIsBroadcastOpen(false)}
        isBroadcasting={isBroadcasting}
        setIsBroadcasting={setIsBroadcasting}
        userLocation={userLocation}
        broadcastSession={broadcastSession}
        setBroadcastSession={setBroadcastSession}
        onRequestGps={requestUserGps}
        gpsStatus={gpsStatus}
      />

      {/* Community Report Modal */}
      <CrowdReportModal
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
        onReportSuccess={() => fetchCrowdReports().then(setCrowdReports)}
      />

      {/* Mobile Bottom Navigation */}
      <BottomNav
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenBroadcast={() => handleOpenBroadcast()}
        isBroadcasting={isBroadcasting}
        onOpenReport={() => setIsReportOpen(true)}
        reportCount={crowdReports.length}
        onOpenTripPlanner={() => setIsTripPlannerOpen(true)}
      />

    </div>
  );
}
