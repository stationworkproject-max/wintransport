import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { 
  initTransitData, 
  checkForRemoteUpdates, 
  subscribeToTransitData, 
  getActiveLines, 
  getActiveShapes, 
  getActiveVersion 
} from '../services/transitDataManager';

const TransitDataContext = createContext({
  lines: getActiveLines(),
  shapes: getActiveShapes(),
  version: getActiveVersion(),
  checkForUpdates: () => Promise.resolve({ updated: false }),
  lastUpdateBanner: null,
  dismissUpdateBanner: () => {}
});

export function TransitDataProvider({ children }) {
  const [lines, setLines] = useState(getActiveLines);
  const [shapes, setShapes] = useState(getActiveShapes);
  const [version, setVersion] = useState(getActiveVersion);
  const [lastUpdateBanner, setLastUpdateBanner] = useState(null);

  useEffect(() => {
    // 1. Initial fast local boot (from IndexedDB or fallback)
    initTransitData().then(({ lines: l, shapes: s, version: v }) => {
      setLines(l);
      setShapes(s);
      setVersion(v);

      // 2. Non-blocking OTA check after 3 seconds of app launch
      const timer = setTimeout(() => {
        checkForRemoteUpdates().then(res => {
          if (res && res.updated) {
            setLastUpdateBanner(`Réseau de transport mis à jour (v${res.version})`);
          }
        });
      }, 3000);

      return () => clearTimeout(timer);
    });

    // 3. Subscribe to any runtime dataset updates
    const unsubscribe = subscribeToTransitData(({ lines: l, shapes: s, version: v }) => {
      setLines(l);
      setShapes(s);
      setVersion(v);
    });

    return unsubscribe;
  }, []);

  const manualCheck = useCallback((force = true) => {
    return checkForRemoteUpdates(force).then(res => {
      if (res && res.updated) {
        setLastUpdateBanner(`Réseau de transport mis à jour (v${res.version})`);
      }
      return res;
    });
  }, []);

  const dismissUpdateBanner = useCallback(() => {
    setLastUpdateBanner(null);
  }, []);

  return (
    <TransitDataContext.Provider value={{ 
      lines, 
      shapes, 
      version, 
      checkForUpdates: manualCheck,
      lastUpdateBanner,
      dismissUpdateBanner
    }}>
      {children}
    </TransitDataContext.Provider>
  );
}

export function useTransitData() {
  return useContext(TransitDataContext);
}
