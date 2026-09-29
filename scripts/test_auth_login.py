import json, urllib.request, urllib.error

email = "upcudup@gmail.com"
password = "14150393Asas/"

candidates = [
    ("https://alt.supabase.io/auth/v1/token?grant_type=password", {
        "email": email,
        "password": password
    }),
    ("https://api.supabase.com/v1/auth/login", {
        "email": email,
        "password": password
    }),
    ("https://supabase.com/dashboard/api/auth/sign-in", {
        "email": email,
        "password": password
    }),
    ("https://api.supabase.com/v1/auth/token?grant_type=password", {
        "email": email,
        "password": password
    })
]

for url, payload in candidates:
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        with urllib.request.urlopen(req) as resp:
            print("SUCCESS:", url, resp.status)
            res = json.loads(resp.read())
            print("Keys:", list(res.keys()))
            with open("scripts/supabase_user_session.json", "w") as out:
                json.dump(res, out, indent=2)
            break
    except urllib.error.HTTPError as e:
        print("Failed", url, e.code, e.read().decode())
    except Exception as e:
        print("Error", url, e)
