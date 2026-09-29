import urllib.request, re

req = urllib.request.Request('https://supabase.com/dashboard/sign-in', headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print('Status:', resp.status)
        scripts = re.findall(r'<script[^>]+src="([^">]+)"', html)
        print('Scripts:', scripts[:5])
        with open('signin.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Wrote signin.html')
except Exception as e:
    print('Error:', e)
