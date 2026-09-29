import json, urllib.request

with open('supabase_user_session.json', 'r') as f:
    session = json.load(f)

access_token = session['access_token']

headers = {
    'Authorization': f'Bearer {access_token}',
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/json'
}

sql = """
-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Transit Types
CREATE TABLE IF NOT EXISTS public.transit_types (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT NOT NULL,
    color TEXT NOT NULL
);

-- 2. Transit Lines
CREATE TABLE IF NOT EXISTS public.transit_lines (
    id TEXT PRIMARY KEY,
    type_id TEXT REFERENCES public.transit_types(id) ON DELETE CASCADE,
    short_name TEXT NOT NULL,
    long_name TEXT NOT NULL,
    color TEXT NOT NULL,
    text_color TEXT DEFAULT '#FFFFFF',
    route_id INTEGER
);

-- 3. Transit Stations
CREATE TABLE IF NOT EXISTS public.transit_stations (
    id TEXT PRIMARY KEY,
    stop_id INTEGER,
    name TEXT NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    route_type INTEGER DEFAULT 1
);

-- 4. Line Stops Link Table
CREATE TABLE IF NOT EXISTS public.transit_line_stops (
    id SERIAL PRIMARY KEY,
    line_id TEXT REFERENCES public.transit_lines(id) ON DELETE CASCADE,
    station_id TEXT REFERENCES public.transit_stations(id) ON DELETE CASCADE,
    stop_sequence INTEGER NOT NULL,
    direction TEXT NOT NULL
);

-- 5. Real-Time Crowd-Sourced Vehicle Locations
CREATE TABLE IF NOT EXISTS public.transit_live_locations (
    id TEXT PRIMARY KEY,
    line_id TEXT REFERENCES public.transit_lines(id) ON DELETE CASCADE,
    direction TEXT NOT NULL,
    vehicle_label TEXT,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    heading DOUBLE PRECISION DEFAULT 0,
    speed_kmh DOUBLE PRECISION DEFAULT 0,
    passenger_count INTEGER DEFAULT 1,
    is_simulated BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '5 minutes')
);

-- 6. Crowd Reports (Delays, Crowding, Accidents)
CREATE TABLE IF NOT EXISTS public.transit_crowd_reports (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    line_id TEXT REFERENCES public.transit_lines(id) ON DELETE CASCADE,
    stop_name TEXT,
    report_type TEXT NOT NULL,
    severity TEXT DEFAULT 'medium',
    message TEXT,
    upvotes INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for ultra fast spatial and line queries
CREATE INDEX IF NOT EXISTS idx_live_loc_line ON public.transit_live_locations(line_id);
CREATE INDEX IF NOT EXISTS idx_live_loc_expires ON public.transit_live_locations(expires_at);
CREATE INDEX IF NOT EXISTS idx_reports_line ON public.transit_crowd_reports(line_id);
CREATE INDEX IF NOT EXISTS idx_line_stops_line ON public.transit_line_stops(line_id);

-- Enable Row Level Security (RLS)
ALTER TABLE public.transit_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transit_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transit_stations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transit_line_stops ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transit_live_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transit_crowd_reports ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "Public read transit_types" ON public.transit_types;
DROP POLICY IF EXISTS "Public read transit_lines" ON public.transit_lines;
DROP POLICY IF EXISTS "Public read transit_stations" ON public.transit_stations;
DROP POLICY IF EXISTS "Public read transit_line_stops" ON public.transit_line_stops;
DROP POLICY IF EXISTS "Public read transit_live_locations" ON public.transit_live_locations;
DROP POLICY IF EXISTS "Public upsert transit_live_locations" ON public.transit_live_locations;
DROP POLICY IF EXISTS "Public delete transit_live_locations" ON public.transit_live_locations;
DROP POLICY IF EXISTS "Public read transit_crowd_reports" ON public.transit_crowd_reports;
DROP POLICY IF EXISTS "Public insert transit_crowd_reports" ON public.transit_crowd_reports;

-- Create Open Policies for Client App (Anon)
CREATE POLICY "Public read transit_types" ON public.transit_types FOR SELECT USING (true);
CREATE POLICY "Public read transit_lines" ON public.transit_lines FOR SELECT USING (true);
CREATE POLICY "Public read transit_stations" ON public.transit_stations FOR SELECT USING (true);
CREATE POLICY "Public read transit_line_stops" ON public.transit_line_stops FOR SELECT USING (true);

CREATE POLICY "Public read transit_live_locations" ON public.transit_live_locations FOR SELECT USING (true);
CREATE POLICY "Public upsert transit_live_locations" ON public.transit_live_locations FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Public read transit_crowd_reports" ON public.transit_crowd_reports FOR SELECT USING (true);
CREATE POLICY "Public insert transit_crowd_reports" ON public.transit_crowd_reports FOR INSERT WITH CHECK (true);

-- Enable Realtime for Live Locations and Reports
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables 
        WHERE pubname = 'supabase_realtime' AND tablename = 'transit_live_locations'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.transit_live_locations;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables 
        WHERE pubname = 'supabase_realtime' AND tablename = 'transit_crowd_reports'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.transit_crowd_reports;
    END IF;
END $$;
"""

data = json.dumps({"query": sql}).encode('utf-8')
req = urllib.request.Request(
    'https://api.supabase.com/v1/projects/rqwpafatgsyncvretjym/database/query',
    data=data,
    headers=headers
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read())
        print('Database schema created successfully!')
        print(res)
except Exception as e:
    print('Setup error:', e)
    if hasattr(e, 'read'):
        print(e.read().decode())
