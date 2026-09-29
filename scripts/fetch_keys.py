import json, urllib.request

with open('supabase_user_session.json', 'r') as f:
    session = json.load(f)

access_token = session['access_token']

headers = {
    'Authorization': f'Bearer {access_token}',
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/json'
}

endpoints = [
    'https://api.supabase.com/v1/projects/rqwpafatgsyncvretjym/api-keys',
    'https://api.supabase.com/v1/projects/rqwpafatgsyncvretjym',
    'https://api.supabase.com/v1/projects/rqwpafatgsyncvretjym/postgrest'
]

results = {}
for ep in endpoints:
    try:
        req = urllib.request.Request(ep, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            print(f'SUCCESS for {ep}:')
            print(json.dumps(data, indent=2)[:500])
            results[ep] = data
    except Exception as e:
        print(f'FAILED for {ep}:', e)
        if hasattr(e, 'read'):
            print(e.read().decode())

with open('project_api_keys.json', 'w') as out:
    json.dump(results, out, indent=2)
print('Wrote project_api_keys.json')
