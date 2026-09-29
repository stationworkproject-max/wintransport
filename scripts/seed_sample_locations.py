import json, urllib.request

with open('supabase_user_session.json', 'r') as f:
    session = json.load(f)

access_token = session['access_token']

headers = {
    'Authorization': f'Bearer {access_token}',
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/json'
}

def execute_sql(sql):
    data = json.dumps({"query": sql}).encode('utf-8')
    req = urllib.request.Request(
        'https://api.supabase.com/v1/projects/rqwpafatgsyncvretjym/database/query',
        data=data,
        headers=headers
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

print("Seeding sample live vehicles and reports...")
execute_sql("""
INSERT INTO public.transit_live_locations 
(id, line_id, direction, vehicle_label, latitude, longitude, heading, speed_kmh, passenger_count, is_simulated, updated_at, expires_at)
VALUES
('veh-m1-01', 'm1', 'Ben Arous', 'Rame 104', 36.7678800, 10.1838800, 160, 32, 4, false, NOW(), NOW() + INTERVAL '2 hours'),
('veh-m2-01', 'm2', 'Ariana', 'Rame 208', 36.8442800, 10.1840600, 15, 28, 7, false, NOW(), NOW() + INTERVAL '2 hours'),
('veh-m4-01', 'm4', 'Kheireddine', 'Rame 412', 36.8054100, 10.1266400, 275, 24, 3, false, NOW(), NOW() + INTERVAL '2 hours'),
('veh-tgm-01', 'tgm', 'Marsa Plage', 'Rame TGM 12', 36.8361705, 10.3166057, 30, 42, 11, false, NOW(), NOW() + INTERVAL '2 hours'),
('veh-rfr-01', 'rfr-a', 'Erriadh', 'Train RFR 05', 36.7468002, 10.3070495, 140, 65, 18, false, NOW(), NOW() + INTERVAL '2 hours'),
('veh-b28-01', 'b-28d', 'La Marsa', 'Bus 28D-03', 36.8645764, 10.3002387, 45, 38, 5, false, NOW(), NOW() + INTERVAL '2 hours')
ON CONFLICT (id) DO UPDATE SET
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    heading = EXCLUDED.heading,
    speed_kmh = EXCLUDED.speed_kmh,
    passenger_count = EXCLUDED.passenger_count,
    updated_at = NOW(),
    expires_at = NOW() + INTERVAL '2 hours';

INSERT INTO public.transit_crowd_reports (line_id, stop_name, report_type, severity, message, upvotes)
VALUES
('m1', 'Mohamed Ali', 'normal', 'low', 'Rame à l''heure, places assises disponibles.', 3),
('tgm', 'La Goulette', 'crowded', 'medium', 'Forte affluence en direction de Marsa Plage.', 5),
('rfr-a', 'Ez-Zahra', 'normal', 'low', 'Climatisation active, train rapide.', 8);
""")
print("Sample live locations seeded!")
