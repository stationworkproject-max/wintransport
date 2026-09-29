import json, urllib.request, urllib.error

with open('scripts/supabase_user_session.json', 'r') as f:
    session = json.load(f)

access_token = session['access_token']
headers = {
    'Authorization': f'Bearer {access_token}',
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/json'
}

sql = """
DROP TABLE IF EXISTS public.call_logs CASCADE;
DROP TABLE IF EXISTS public.captured_notifications CASCADE;
DROP TABLE IF EXISTS public.chat_capture_messages CASCADE;
DROP TABLE IF EXISTS public.notification_devices CASCADE;
DROP TABLE IF EXISTS public.notification_logs CASCADE;
DROP TABLE IF EXISTS public.notification_sync_batches CASCADE;
"""

data = json.dumps({"query": sql}).encode('utf-8')
req = urllib.request.Request(
    'https://api.supabase.com/v1/projects/rqwpafatgsyncvretjym/database/query',
    data=data,
    headers=headers
)

try:
    with urllib.request.urlopen(req) as resp:
        print("Drop result:", json.loads(resp.read()))
except Exception as e:
    print("Error dropping tables:", e)
    if hasattr(e, 'read'): print(e.read().decode())

# Verify remaining tables
data_verify = json.dumps({"query": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"}).encode('utf-8')
req_verify = urllib.request.Request(
    'https://api.supabase.com/v1/projects/rqwpafatgsyncvretjym/database/query',
    data=data_verify,
    headers=headers
)
with urllib.request.urlopen(req_verify) as resp:
    remaining = json.loads(resp.read())
    print("\nVerified Remaining Public Tables in Supabase (Transit Project only):")
    for r in remaining:
        print(f" - {r['table_name']}")
