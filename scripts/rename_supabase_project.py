import json, urllib.request, urllib.error

with open('scripts/supabase_user_session.json', 'r') as f:
    session = json.load(f)

access_token = session['access_token']
headers = {
    'Authorization': f'Bearer {access_token}',
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/json'
}

# 1. Get Project Details
req = urllib.request.Request(
    'https://api.supabase.com/v1/projects/rqwpafatgsyncvretjym',
    headers=headers
)
try:
    with urllib.request.urlopen(req) as resp:
        proj = json.loads(resp.read())
        print("Current Project Info:", proj.get('name'), proj.get('ref'), proj.get('status'))
except Exception as e:
    print("Error getting project:", e)
    if hasattr(e, 'read'): print(e.read().decode())

# 2. Rename Project to 'transit'
# Supabase Management API endpoint for updating a project name is PATCH /v1/projects/{ref} with {"name": "transit"}
patch_data = json.dumps({"name": "transit"}).encode('utf-8')
req_patch = urllib.request.Request(
    'https://api.supabase.com/v1/projects/rqwpafatgsyncvretjym',
    data=patch_data,
    headers=headers,
    method='PATCH'
)

try:
    with urllib.request.urlopen(req_patch) as resp:
        res = json.loads(resp.read())
        print("Rename result:", res)
except Exception as e:
    print("Error renaming project:", e)
    if hasattr(e, 'read'): print(e.read().decode())
    # Try PUT if PATCH didn't work
    req_put = urllib.request.Request(
        'https://api.supabase.com/v1/projects/rqwpafatgsyncvretjym',
        data=patch_data,
        headers=headers,
        method='PUT'
    )
    try:
        with urllib.request.urlopen(req_put) as resp:
            print("PUT Rename result:", json.loads(resp.read()))
    except Exception as e2:
        print("Error with PUT:", e2)
        if hasattr(e2, 'read'): print(e2.read().decode())
