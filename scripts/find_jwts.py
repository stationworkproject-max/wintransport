import glob, os, re

files = glob.glob(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Local Storage\leveldb\*.*'))

for f in files:
    try:
        with open(f, 'rb') as fp:
            data = fp.read()
            # find all JWTs
            jwts = re.findall(rb'eyJ[a-zA-Z0-9_-]{15,}\.eyJ[a-zA-Z0-9_-]{15,}\.[a-zA-Z0-9_-]{15,}', data)
            if jwts:
                print(f'{f}: {len(jwts)} JWTs')
                for j in set(jwts):
                    import base64, json
                    parts = j.split(b'.')
                    payload = parts[1] + b'=' * (-len(parts[1]) % 4)
                    try:
                        p = json.loads(base64.urlsafe_b64decode(payload))
                        print('   iss:', p.get('iss'), 'email:', p.get('email'), 'role:', p.get('role'), 'ref:', p.get('ref'))
                        if p.get('email') == 'upcudup@gmail.com' or 'rqwpafatgsyncvretjym' in str(p) or p.get('role') in ['anon', 'service_role']:
                            print('   *** MATCH FOUND ***')
                            with open('matched_supabase_jwt.txt', 'wb') as mfp:
                                mfp.write(j)
                    except:
                        pass
    except Exception as e:
        pass
