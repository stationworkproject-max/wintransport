/**
 * WinTransport Tunisia — Dynamic Transit Data Manager
 * Handles Offline-First Local Storage (IndexedDB) + Over-The-Air (OTA) Supabase Sync
 * Seamless across Web PWA and Android Capacitor WebView
 */

import { STATIC_LINES, TRANSIT_NETWORKS } from '../data/staticTransit';
import TRANSIT_SHAPES_STATIC from '../data/transitShapes.json';
import { supabase, CUSTOM_DOMAIN_URL } from '../supabase';

const DB_NAME = 'wintransport_transit_db';
const DB_VERSION = 1;
const STORE_NAME = 'transit_store';

const KEY_VERSION = 'dataset_version';
const KEY_LINES = 'dataset_lines';
const KEY_SHAPES = 'dataset_shapes';
const KEY_LAST_CHECK = 'dataset_last_check';

// In-Memory Active State (initialized with static fallback)
let inMemoryLines = [...STATIC_LINES];
let inMemoryShapes = { ...TRANSIT_SHAPES_STATIC };
let inMemoryVersion = 1;
let isInitialized = false;
const listeners = new Set();

/**
 * Open or create IndexedDB
 */
function openDB() {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.indexedDB) {
      return reject(new Error('IndexedDB not supported'));
    }
    const req = window.indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

/**
 * Get item from IndexedDB
 */
async function idbGet(key) {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const req = store.get(key);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  } catch (err) {
    console.warn('[TransitDataManager] idbGet error:', err);
    return null;
  }
}

/**
 * Set item in IndexedDB
 */
async function idbSet(key, value) {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const req = store.put(value, key);
      req.onsuccess = () => resolve(true);
      req.onerror = () => reject(req.error);
    });
  } catch (err) {
    console.warn('[TransitDataManager] idbSet error:', err);
    return false;
  }
}

/**
 * Initialize Transit Data (Local-First 0ms Startup)
 */
export async function initTransitData() {
  if (isInitialized) {
    return { lines: inMemoryLines, shapes: inMemoryShapes, version: inMemoryVersion };
  }

  try {
    const [cachedVer, cachedLines, cachedShapes] = await Promise.all([
      idbGet(KEY_VERSION),
      idbGet(KEY_LINES),
      idbGet(KEY_SHAPES)
    ]);

    if (cachedVer && Array.isArray(cachedLines) && cachedLines.length > 0 && cachedShapes) {
      inMemoryVersion = cachedVer;
      inMemoryLines = cachedLines;
      inMemoryShapes = cachedShapes;
      console.log(`[TransitDataManager] Loaded v${inMemoryVersion} from IndexedDB (${cachedLines.length} lines)`);
    } else {
      // First boot: Seed IndexedDB with bundled assets
      inMemoryVersion = 1;
      inMemoryLines = [...STATIC_LINES];
      inMemoryShapes = { ...TRANSIT_SHAPES_STATIC };
      
      // Async seed without blocking UI
      Promise.all([
        idbSet(KEY_VERSION, 1),
        idbSet(KEY_LINES, inMemoryLines),
        idbSet(KEY_SHAPES, inMemoryShapes)
      ]).catch(e => console.warn('[TransitDataManager] Failed to seed IndexedDB:', e));
      
      console.log(`[TransitDataManager] Seeded initial bundled assets (${inMemoryLines.length} lines)`);
    }
  } catch (e) {
    console.warn('[TransitDataManager] IndexedDB init error, using static fallback:', e);
  }

  isInitialized = true;
  notifyListeners();
  return { lines: inMemoryLines, shapes: inMemoryShapes, version: inMemoryVersion };
}

/**
 * Check for Remote Updates from Supabase (OTA)
 */
export async function checkForRemoteUpdates(force = false) {
  try {
    const now = Date.now();
    const lastCheck = await idbGet(KEY_LAST_CHECK) || 0;
    
    // Avoid spamming check if checked less than 1 minute ago unless forced
    if (!force && (now - lastCheck < 60000)) {
      return { updated: false, version: inMemoryVersion };
    }
    await idbSet(KEY_LAST_CHECK, now);

    // 1. Fetch latest metadata record
    const { data, error } = await supabase
      .from('transit_dataset_meta')
      .select('*')
      .order('version', { ascending: false })
      .limit(1);

    if (error || !data || data.length === 0) {
      return { updated: false, version: inMemoryVersion };
    }

    const remoteMeta = data[0];
    if (remoteMeta.version <= inMemoryVersion) {
      return { updated: false, version: inMemoryVersion };
    }

    console.log(`[TransitDataManager] New remote version detected: v${remoteMeta.version} (current: v${inMemoryVersion}). Syncing OTA...`);

    // 2. Fetch remote lines and shapes JSON
    const linesUrl = remoteMeta.lines_url;
    const shapesUrl = remoteMeta.shapes_url;

    if (!linesUrl || !shapesUrl) {
      console.warn('[TransitDataManager] Missing lines_url or shapes_url in meta record');
      return { updated: false, version: inMemoryVersion };
    }

    const [linesRes, shapesRes] = await Promise.all([
      fetch(linesUrl, { cache: 'no-cache' }),
      fetch(shapesUrl, { cache: 'no-cache' })
    ]);

    if (!linesRes.ok || !shapesRes.ok) {
      throw new Error(`Failed to download OTA assets: lines ${linesRes.status}, shapes ${shapesRes.status}`);
    }

    const newLines = await linesRes.json();
    const newShapes = await shapesRes.json();

    if (!Array.isArray(newLines) || typeof newShapes !== 'object') {
      throw new Error('Invalid JSON structure downloaded from OTA storage');
    }

    // 3. Persist to IndexedDB
    await Promise.all([
      idbSet(KEY_VERSION, remoteMeta.version),
      idbSet(KEY_LINES, newLines),
      idbSet(KEY_SHAPES, newShapes)
    ]);

    // 4. Update in-memory state
    inMemoryVersion = remoteMeta.version;
    inMemoryLines = newLines;
    inMemoryShapes = newShapes;

    console.log(`[TransitDataManager] ✅ Successfully applied OTA dataset v${inMemoryVersion}! (${newLines.length} lines)`);
    
    notifyListeners();

    // Dispatch global DOM event for any outside subscriber
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('transit:ota_updated', {
        detail: { version: inMemoryVersion, linesCount: newLines.length }
      }));
    }

    return { updated: true, version: inMemoryVersion, linesCount: newLines.length };
  } catch (err) {
    console.error('[TransitDataManager] OTA update check failed:', err);
    return { updated: false, error: err.message, version: inMemoryVersion };
  }
}

/**
 * Get active in-memory lines
 */
export function getActiveLines() {
  return inMemoryLines;
}

/**
 * Get active in-memory shapes
 */
export function getActiveShapes() {
  return inMemoryShapes;
}

/**
 * Get active dataset version
 */
export function getActiveVersion() {
  return inMemoryVersion;
}

/**
 * Subscribe to live dataset updates
 */
export function subscribeToTransitData(callback) {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

function notifyListeners() {
  for (const listener of listeners) {
    try {
      listener({
        lines: inMemoryLines,
        shapes: inMemoryShapes,
        version: inMemoryVersion
      });
    } catch (e) {
      console.error('[TransitDataManager] Error in listener:', e);
    }
  }
}
