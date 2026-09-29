import json
import urllib.request
import urllib.error

with open('scripts/supabase_user_session.json', 'r') as f:
    session = json.load(f)

access_token = session['access_token']
headers = {
    'Authorization': f'Bearer {access_token}',
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/json'
}

def run_query(sql):
    data = json.dumps({"query": sql}).encode('utf-8')
    req = urllib.request.Request(
        'https://api.supabase.com/v1/projects/rqwpafatgsyncvretjym/database/query',
        data=data,
        headers=headers
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code, e.read().decode())
        return None
    except Exception as e:
        print("Error:", e)
        return None

# Check current tables
tables = run_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
print("Current public tables:", tables)
