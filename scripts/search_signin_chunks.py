import urllib.request, re

with open('signin.html', 'r', encoding='utf-8') as f:
    html = f.read()

scripts = re.findall(r'<script[^>]+src="([^">]+)"', html)
for s in scripts:
    try:
        req = urllib.request.Request(s, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            if 'signInWithPassword' in content:
                print('Found signInWithPassword in', s)
                pos = content.find('signInWithPassword')
                print(content[pos-100:pos+200])
            if 'auth.signIn' in content or 'login' in content.lower():
                matches = re.findall(r'https?://[^\s"\'`)]+', content)
                for m in matches:
                    if 'api' in m or 'auth' in m:
                        print('URL in chunk:', m)
    except Exception as e:
        pass
