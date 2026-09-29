import json, re

with open('signin.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
if m:
    data = json.loads(m.group(1))
    print('NEXT_DATA keys:', data.keys())
    print('props:', json.dumps(data.get('props', {}), indent=2)[:500])
    # search for supabase url or gotrue or api in the whole json string
    s = m.group(1)
    for url in set(re.findall(r'https?://[a-zA-Z0-9.-]+', s)):
        print('Found host:', url)
