import os, glob, re, json
from decompress_upcudup import decompress_snappy

edge_ldb = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Local Storage\leveldb')
files = sorted(glob.glob(os.path.join(edge_ldb, '*.*')), key=os.path.getmtime, reverse=True)

print(f"Scanning {len(files)} files in {edge_ldb}...")
found_tokens = []

for f in files:
    if not (f.endswith('.ldb') or f.endswith('.log')): continue
    try:
        with open(f, 'rb') as fp:
            data = fp.read()
    except Exception as e:
        continue

    # 1. Search for raw JWT in uncompressed
    matches = re.findall(rb'eyJ[a-zA-Z0-9_-]{20,}\.eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}', data)
    for m in matches:
        found_tokens.append(('raw', f, m))

    # 2. Search for snappy blocks containing "access_token" or "supabase"
    pos = 0
    while True:
        pos = data.find(b'access_token', pos)
        if pos == -1: break
        for start in range(max(0, pos - 2000), pos, 16):
            d = decompress_snappy(data[start:])
            if b'access_token' in d and (b'upcudup' in d or b'supabase' in d):
                m_sub = re.findall(rb'eyJ[a-zA-Z0-9_-]{20,}\.eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}', d)
                for m in m_sub:
                    found_tokens.append(('snappy', f, m))
                if m_sub: break
        pos += 12

print(f"Total tokens found: {len(found_tokens)}")
import base64
valid_dashboard_tokens = []
for typ, f, tok in found_tokens:
    try:
        parts = tok.split(b'.')
        payload = parts[1] + b'=' * (-len(parts[1]) % 4)
        p = json.loads(base64.urlsafe_b64decode(payload))
        email = p.get('email')
        exp = p.get('exp')
        iss = p.get('iss')
        print(f"Type: {typ}, File: {os.path.basename(f)}, Email: {email}, Exp: {exp}, Iss: {iss}")
        if email == 'upcudup@gmail.com':
            valid_dashboard_tokens.append((exp, tok.decode('utf-8')))
    except Exception as e:
        pass

if valid_dashboard_tokens:
    valid_dashboard_tokens.sort(key=lambda x: x[0], reverse=True)
    best_exp, best_tok = valid_dashboard_tokens[0]
    print(f"\nBest token expires at {best_exp}")
    with open('scripts/supabase_dashboard_token.txt', 'w') as out:
        out.write(best_tok)
    with open('scripts/supabase_user_session.json', 'w') as out:
        json.dump({"access_token": best_tok}, out)
    print("Saved to scripts/supabase_user_session.json")
