import React, { useState, useEffect, useRef, useCallback, useMemo, Suspense, lazy } from 'react';
import Header from './components/Header';
import TransitMap from './components/TransitMap';
import BottomNav from './components/BottomNav';

const PassengerBroadcastModal = lazy(() => import('./components/PassengerBroadcastModal'));
const CrowdReportModal = lazy(() => import('./components/CrowdReportModal'));
const LineScheduleDrawer = lazy(() => import('./components/LineScheduleDrawer'));
const StationArrivalModal = lazy(() => import('./components/StationArrivalModal'));
const LinesListView = lazy(() => import('./components/LinesListView'));
const SmartTripPlannerModal = lazy(() => import('./components/SmartTripPlannerModal'));
import { 
  fetchLiveVehicles,
  fetchLiveLocations, 
  fetchCrowdReports, 
  subscribeToRealtimeUpdates,
  broadcastLeave,
  removeLiveLocation,
  SUPABASE_URL,
  SUPABASE_ANON_KEY
} from './supabase';
import { STATIC_LINES } from './data/staticTransit';
import { isNativeAndroid, isBackgroundBroadcastRunning } from './native/backgroundBroadcast';
import { Radio, AlertTriangle, Layers, Navigation, Search } from 'lucide-react';
import { getStationName, getLineName, getLineShortName, t } from './utils/i18n';
import { getSavedTheme, applyTheme } from './utils/theme';

export default function App() {
  const [language, setLanguage] = useState(() => localStorage.getItem('app_lang') || 'fr');
  const [theme, setTheme] = useState(getSavedTheme);

  const toggleTheme = useCallback(() => {
    setTheme(prev => {
      const next = prev === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      return next;
    });
  }, []);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const toggleLanguage = useCallback(() => {
    setLanguage(prev => {
      const next = prev === 'fr' ? 'ar' : 'fr';
      localStorage.setItem('app_lang', next);
      return next;
    });
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
  }, [language]);

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
  
  // Radar Proximity Scale (0.5 km to 2.5 km, default: 1.5 km, 0 = disabled)
  const [radarRadiusKm, setRadarRadiusKm] = useState(() => {
    try {
      const saved = localStorage.getItem('transit_radar_radius');
      if (saved === '0' || saved === 'off') return 0;
      return saved ? Math.min(2.5, Math.max(0.5, Number(saved))) : 1.5;
    } catch (e) {
      return 1.5;
    }
  });

  const handleUpdateRadarRadius = useCallback((radius) => {
    let val;
    if (radius === 0 || radius === '0' || radius === 'off') {
      val = 0;
    } else {
      val = Math.min(2.5, Math.max(0.5, Number(radius) || 1.5));
    }
    setRadarRadiusKm(val);
    try {
      localStorage.setItem('transit_radar_radius', val.toString());
    } catch (e) {}
  }, []);

  // Real-time Viewers Count (concurrent users on the app)
  const [liveViewersCount, setLiveViewersCount] = useState(1);

  // Active Broadcasters (vehicles with live GPS)
  const broadcastersCount = useMemo(() => {
    const cutoff = Date.now() - 30 * 1000;
    return (liveLocations || []).filter(v => {
      const t = new Date(v.updated_at).getTime();
      return !isNaN(t) && t >= cutoff;
    }).length;
  }, [liveLocations]);

  // Hold Users / Passengers on board
  const totalPassengersOnBoard = useMemo(() => {
    const cutoff = Date.now() - 30 * 1000;
    return (liveLocations || []).reduce((acc, v) => {
      const t = new Date(v.updated_at).getTime();
      if (!isNaN(t) && t < cutoff) return acc;
      return acc + (Number(v.passenger_count) || 1);
    }, 0);
  }, [liveLocations]);

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
    fetchLiveLocations((viewers) => {
      if (viewers > 0) setLiveViewersCount(viewers);
    }).then(setLiveLocations);
    fetchCrowdReports().then(setCrowdReports);

    // 2. Realtime WebSocket subscription with presence viewers tracking
    const unsubscribe = subscribeToRealtimeUpdates(
      (updatedLocations) => {
        setLiveLocations(updatedLocations);
      },
      (updatedReports) => {
        setCrowdReports(updatedReports);
      },
      (updatedViewers) => {
        setLiveViewersCount(updatedViewers);
      }
    );

    // 3. Start watching real GPS location
    requestUserGps();

    // 4. Client-side Real-time Liveness Pruner (30-second ghost eviction)
    const livenessTimer = setInterval(() => {
      const cutoff = Date.now() - 30 * 1000;
      setLiveLocations(prev => prev.filter(loc => {
        const t = new Date(loc.updated_at).getTime();
        return !isNaN(t) && t > cutoff;
      }));
    }, 4000);

    // 5. Global Unload Listener: remove or release any active vehicle when user closes window/tab
    const handleUnload = () => {
      try {
        const activeId = localStorage.getItem('transit_broadcast_id');
        const devId = localStorage.getItem('transit_device_id');
        if (activeId) {
          localStorage.removeItem('transit_broadcast_id');
          if (devId) {
            broadcastLeave(activeId, devId);
          } else {
            removeLiveLocation(activeId);
          }
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
    <div className={`flex flex-col h-[100dvh] w-screen overflow-hidden font-sans ${theme === 'light' ? 'bg-slate-50 text-slate-900' : 'bg-slate-950 text-slate-100'}`}>
      
      {/* Top Navigation Bar */}
      <Header
        activeNetwork={activeNetwork}
        setActiveNetwork={setActiveNetwork}
        liveCount={broadcastersCount}
        broadcastersCount={broadcastersCount}
        passengersCount={totalPassengersOnBoard}
        viewersCount={liveViewersCount}
        onOpenBroadcast={() => handleOpenBroadcast()}
        isBroadcasting={isBroadcasting}
        onOpenReport={() => setIsReportOpen(true)}
        recentReportCount={crowdReports.length}
        userLocation={userLocation}
        onRequestGps={requestUserGps}
        gpsStatus={gpsStatus}
        onOpenTripPlanner={() => setIsTripPlannerOpen(true)}
        language={language}
        onToggleLanguage={toggleLanguage}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {/* Main View Area */}
      <main className="flex-1 relative overflow-hidden flex flex-col md:flex-row">
        
        {/* Desktop Sidebar: Line Quick Selector */}
        <aside className={`hidden lg:flex flex-col w-80 z-[1005] backdrop-blur-md pointer-events-auto transition-colors ${
          theme === 'light'
            ? 'border-r border-slate-200 bg-white/95 text-slate-800'
            : 'border-r border-slate-800 bg-slate-900/90 text-slate-200'
        }`}>
          <div className={`p-3 border-b flex items-center justify-between ${
            theme === 'light' ? 'border-slate-200 bg-slate-100/70' : 'border-slate-800 bg-slate-800/40'
          }`}>
            <span className={`text-xs font-bold uppercase tracking-wider ${
              theme === 'light' ? 'text-slate-700' : 'text-slate-300'
            }`}>
              {language === 'ar' ? 'الخطوط العاملة' : 'Lignes en service'}
            </span>
            <span className="text-[11px] bg-blue-500/20 text-blue-500 font-semibold px-2 py-0.5 rounded-full">
              {STATIC_LINES.length} {language === 'ar' ? 'خط' : 'Lignes'}
            </span>
          </div>

          {/* Sidebar Search */}
          <div className={`p-2 border-b ${
            theme === 'light' ? 'border-slate-200/80 bg-slate-50' : 'border-slate-800/60 bg-slate-800/20'
          }`}>
            <div className="relative">
              <Search className={`absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 ${
                theme === 'light' ? 'text-slate-400' : 'text-slate-500'
              }`} />
              <input
                type="text"
                value={sidebarSearch}
                onChange={(e) => setSidebarSearch(e.target.value)}
                placeholder={language === 'ar' ? 'بحث عن خط (مثال: 36، 1، TGM...)' : 'Chercher ligne (ex : 35, 1, TGM...)'}
                className={`w-full rounded-lg pl-8 pr-3 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 border ${
                  theme === 'light'
                    ? 'bg-white border-slate-200 text-slate-900 placeholder:text-slate-400 shadow-sm'
                    : 'bg-slate-800/80 border-slate-700/80 text-white placeholder:text-slate-500'
                }`}
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
            {STATIC_LINES
              .filter(l => activeNetwork === 'all' || l.type_id === activeNetwork)
              .filter(l => {
                if (!sidebarSearch.trim()) return true;
                const q = sidebarSearch.toLowerCase().trim();
                const sn = (l.short_name || '').toLowerCase();
                const sna = (l.short_name_ar || '').toLowerCase();
                const ln = (l.long_name || '').toLowerCase();
                const lnf = (l.long_name_fr || '').toLowerCase();
                const lna = (l.long_name_ar || '').toLowerCase();
                return sn.includes(q) || sna.includes(q) || ln.includes(q) || lnf.includes(q) || lna.includes(q);
              })
              .map(line => {
              const liveCount = liveLocations.filter(loc => loc.line_id === line.id).length;
              const isSelected = selectedLine?.id === line.id;
              const dispShort = getLineShortName(line, language);
              const dispLong = getLineName(line, language);

              return (
                <div
                  key={line.id}
                  onClick={() => handleSelectLine(isSelected ? null : line)}
                  className={`p-2.5 rounded-xl border cursor-pointer transition-all flex items-center justify-between group ${
                    isSelected
                      ? 'bg-blue-600/15 border-blue-500 text-blue-600 shadow-sm ring-1 ring-blue-500/30'
                      : theme === 'light'
                        ? 'bg-slate-50/80 border-slate-200/90 text-slate-700 hover:bg-slate-100 hover:text-slate-900'
                        : 'bg-slate-800/40 border-slate-700/50 text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span
                      className="w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs text-white flex-shrink-0 shadow"
                      style={{ backgroundColor: line.color }}
                    >
                      {dispShort}
                    </span>
                    <div className="min-w-0">
                      <div className="font-semibold text-xs truncate">{dispLong}</div>
                      <div className={`text-[10px] ${theme === 'light' ? 'text-slate-500' : 'text-slate-400'}`}>
                        {line.stops.length} {language === 'ar' ? 'محطة' : 'stations'}
                      </div>
                    </div>
                  </div>

                  {liveCount > 0 && (
                    <span className="flex-shrink-0 bg-emerald-500/20 text-emerald-500 font-bold text-[10px] px-1.5 py-0.5 rounded-full flex items-center gap-1 border border-emerald-500/30">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                      {liveCount}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Quick Active Broadcast Footer */}
          {isBroadcasting && (
            <div className={`p-3 border-t flex items-center justify-between text-xs ${
              theme === 'light'
                ? 'bg-emerald-50/90 border-emerald-200 text-emerald-700'
                : 'bg-emerald-950/40 border-emerald-800/40 text-emerald-400'
            }`}>
              <span className="flex items-center gap-1.5 font-semibold">
                <Radio className="w-3.5 h-3.5 animate-pulse" />
                {language === 'ar' ? 'GPS نشط على المتن' : 'GPS Actif à bord'}
              </span>
              <button
                onClick={() => setIsBroadcastOpen(true)}
                className="text-[11px] underline hover:opacity-80"
              >
                {language === 'ar' ? 'إدارة' : 'Gérer'}
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
              radarRadiusKm={radarRadiusKm}
              onUpdateRadarRadius={handleUpdateRadarRadius}
              language={language}
              theme={theme}
            />
          ) : (
            <div className="h-full overflow-y-auto pb-24">
              <Suspense fallback={<div className="p-8 text-center text-slate-400 text-xs">Chargement des lignes...</div>}>
                <LinesListView
                  activeNetwork={activeNetwork}
                  liveLocations={liveLocations}
                  onSelectLine={(l) => {
                    handleSelectLine(l);
                    setIsScheduleDrawerOpen(false);
                    setActiveTab('map');
                  }}
                  language={language}
                  theme={theme}
                />
              </Suspense>
            </div>
          )}
        </div>

      </main>

      {/* Lazy Suspense Boundary for Drawers & Modals */}
      <Suspense fallback={null}>
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
            language={language}
            theme={theme}
          />
        )}

        {/* Station Arrivals Modal */}
        {selectedStation && (
          <StationArrivalModal
            station={selectedStation}
            line={stationContextLine}
            onClose={() => setSelectedStation(null)}
            liveLocations={liveLocations}
            onOpenBroadcast={handleOpenBroadcast}
            language={language}
            theme={theme}
          />
        )}

        {/* Smart Trip Planner Modal ("Guide Trajet / Où aller ?") */}
        {isTripPlannerOpen && (
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
            language={language}
            theme={theme}
          />
        )}

        {/* Passenger Broadcast Modal ("Je suis à bord") */}
        {isBroadcastOpen && (
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
            language={language}
            theme={theme}
          />
        )}

        {/* Community Report Modal */}
        {isReportOpen && (
          <CrowdReportModal
            isOpen={isReportOpen}
            onClose={() => setIsReportOpen(false)}
            onReportSuccess={() => fetchCrowdReports().then(setCrowdReports)}
            language={language}
            theme={theme}
          />
        )}
      </Suspense>

      {/* Mobile Bottom Navigation */}
      <BottomNav
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenBroadcast={() => handleOpenBroadcast()}
        isBroadcasting={isBroadcasting}
        onOpenReport={() => setIsReportOpen(true)}
        reportCount={crowdReports.length}
        onOpenTripPlanner={() => setIsTripPlannerOpen(true)}
        language={language}
        theme={theme}
      />

    </div>
  );
}
