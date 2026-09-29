import urllib.request, re

with open('signin.html', 'r', encoding='utf-8') as f:
    html = f.read()

scripts = re.findall(r'<script[^>]+src="([^">]+)"', html)
for s in scripts:
    try:
        req = urllib.request.Request(s, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            if 'signInWithPassword' in content or 'api.supabase.com' in content:
                print('Found in', s)
                # find endpoints
                matches = re.findall(r'https://api\.supabase\.com[^\s"\'`)]*', content)
                if matches:
                    print('api.supabase.com matches:', matches[:5])
                gotrue = re.findall(r'/auth/v1/[^\s"\'`)]*', content)
                if gotrue:
                    print('gotrue matches:', gotrue[:5])
    except Exception as e:
        pass
