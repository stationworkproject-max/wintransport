import json, urllib.request

with open('supabase_user_session.json', 'r') as f:
    session = json.load(f)

access_token = session['access_token']

headers = {
    'Authorization': f'Bearer {access_token}',
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/json'
}

query = "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
data = json.dumps({"query": query}).encode('utf-8')

req = urllib.request.Request(
    'https://api.supabase.com/v1/projects/rqwpafatgsyncvretjym/database/query',
    data=data,
    headers=headers
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read())
        print('Existing tables in public schema:', res)
except Exception as e:
    print('Query error:', e)
    if hasattr(e, 'read'):
        print(e.read().decode())
