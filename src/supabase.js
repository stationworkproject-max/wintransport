import { createClient } from '@supabase/supabase-js';

export const SUPABASE_URL = 'https://rqwpafatgsyncvretjym.supabase.co';
export const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJxd3BhZmF0Z3N5bmN2cmV0anltIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMwMTc2MzksImV4cCI6MjA5ODU5MzYzOX0.fjhdr_H_BeuCdLusEwojfhl8wNVraNDzZgwr76m6dQU';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
  },
});

/**
 * Fetch all transit lines
 */
export async function fetchLines() {
  const { data, error } = await supabase
    .from('transit_lines')
    .select('*, transit_types(*)');
  if (error) {
    console.error('Error fetching lines:', error);
    return [];
  }
  return data || [];
}

/**
 * Fetch all stations with their associated lines
 */
export async function fetchStations() {
  const { data, error } = await supabase
    .from('transit_stations')
    .select(`
      *,
      transit_line_stops(
        line_id,
        stop_sequence,
        direction,
        transit_lines(short_name, long_name, color, type_id)
      )
    `);
  if (error) {
    console.error('Error fetching stations:', error);
    return [];
  }
  return data || [];
}

/**
 * Fetch active crowd-sourced live vehicles (strictly updated in the last 45 seconds)
 */
export async function fetchLiveLocations() {
  const staleThreshold = new Date(Date.now() - 45 * 1000).toISOString();

  // Asynchronously purge obsolete or expired vehicles from DB
  supabase
    .from('transit_live_locations')
    .delete()
    .lt('updated_at', staleThreshold)
    .then(() => {})
    .catch(() => {});

  const { data, error } = await supabase
    .from('transit_live_locations')
    .select('*, transit_lines(*)')
    .gt('updated_at', staleThreshold);

  if (error) {
    console.error('Error fetching live locations:', error);
    return [];
  }
  return data || [];
}

/**
 * Upsert live location from passenger device with a 45-second heartbeat TTL
 */
export async function publishLiveLocation(locData) {
  const payload = {
    ...locData,
    updated_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + 45 * 1000).toISOString(), // 45s heartbeat TTL
  };
  const { data, error } = await supabase
    .from('transit_live_locations')
    .upsert(payload, { onConflict: 'id' });
  if (error) {
    console.error('Error publishing location:', error);
    throw error;
  }
  return data;
}

/**
 * Remove vehicle when passenger stops sharing, arrives, or closes app
 */
export async function removeLiveLocation(id) {
  if (!id) return;
  const { error } = await supabase
    .from('transit_live_locations')
    .delete()
    .eq('id', id);
  if (error) {
    console.error('Error removing live location:', error);
  }
}

/**
 * Fetch recent community reports
 */
export async function fetchCrowdReports() {
  const { data, error } = await supabase
    .from('transit_crowd_reports')
    .select('*, transit_lines(*)')
    .order('created_at', { ascending: false })
    .limit(20);
  if (error) {
    console.error('Error fetching reports:', error);
    return [];
  }
  return data || [];
}

/**
 * Publish community report
 */
export async function submitCrowdReport(report) {
  const { data, error } = await supabase
    .from('transit_crowd_reports')
    .insert([report])
    .select();
  if (error) {
    console.error('Error submitting report:', error);
    throw error;
  }
  return data;
}

/**
 * Realtime subscription to vehicles and reports
 */
export function subscribeToRealtimeUpdates(onLocationsChange, onReportsChange) {
  const channel = supabase
    .channel('transit-live-stream')
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: 'transit_live_locations' },
      () => {
        fetchLiveLocations().then(onLocationsChange);
      }
    )
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: 'transit_crowd_reports' },
      () => {
        fetchCrowdReports().then(onReportsChange);
      }
    )
    .subscribe();

  return () => {
    supabase.removeChannel(channel);
  };
}
