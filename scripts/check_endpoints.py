import urllib.request, re

url = 'https://frontend-assets.supabase.com/studio/36371de15127/_next/static/chunks/0gufr3dkmt0c2.js?dpl=dpl_C5Skd6eAJ1jHD6hjb2gzj641BXWU'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    data = resp.read().decode('utf-8', errors='ignore')

matches = set(re.findall(r'"(/[a-zA-Z0-9_\-/]+)"', data))
for m in sorted(matches):
    if any(k in m for k in ['auth', 'login', 'token', 'user', 'sign', 'project']):
        print(m)
