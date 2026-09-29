import os, glob, json

def decompress_snappy(data):
    pos = 0
    length = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        length |= (b & 0x7f) << shift
        if not (b & 0x80):
            break
        shift += 7
    if length <= 0 or length > 50000000:
        return b""
    out = bytearray()
    while pos < len(data) and len(out) < length:
        tag = data[pos]
        pos += 1
        elem_type = tag & 0x03
        if elem_type == 0:
            lit_len = tag >> 2
            if lit_len < 60:
                lit_len += 1
            elif lit_len == 60:
                if pos >= len(data): break
                lit_len = data[pos] + 1; pos += 1
            elif lit_len == 61:
                if pos + 1 >= len(data): break
                lit_len = (data[pos] | (data[pos+1] << 8)) + 1; pos += 2
            elif lit_len == 62:
                if pos + 2 >= len(data): break
                lit_len = (data[pos] | (data[pos+1] << 8) | (data[pos+2] << 16)) + 1; pos += 3
            elif lit_len == 63:
                if pos + 3 >= len(data): break
                lit_len = (data[pos] | (data[pos+1] << 8) | (data[pos+2] << 16) | (data[pos+3] << 24)) + 1; pos += 4
            out.extend(data[pos:pos+lit_len])
            pos += lit_len
        elif elem_type == 1:
            if pos >= len(data): break
            copy_len = ((tag >> 2) & 0x07) + 4
            offset = ((tag >> 5) << 8) | data[pos]
            pos += 1
            if offset == 0 or offset > len(out): break
            for _ in range(copy_len):
                out.append(out[-offset])
        elif elem_type == 2:
            if pos + 1 >= len(data): break
            copy_len = (tag >> 2) + 1
            offset = data[pos] | (data[pos+1] << 8)
            pos += 2
            if offset == 0 or offset > len(out): break
            for _ in range(copy_len):
                out.append(out[-offset])
        elif elem_type == 3:
            if pos + 3 >= len(data): break
            copy_len = (tag >> 2) + 1
            offset = data[pos] | (data[pos+1] << 8) | (data[pos+2] << 16) | (data[pos+3] << 24)
            pos += 4
            if offset == 0 or offset > len(out): break
            for _ in range(copy_len):
                out.append(out[-offset])
    return bytes(out)

edge_ldb = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Local Storage\leveldb')
files = sorted(glob.glob(os.path.join(edge_ldb, '*.ldb')) + glob.glob(os.path.join(edge_ldb, '*.log')), key=os.path.getmtime, reverse=True)

found = False
for f in files[:5]:
    print('Checking', f)
    with open(f, 'rb') as fp:
        raw = fp.read()
    
    # scan for snappy compressed blocks containing upcudup
    idx = 0
    while True:
        pos = raw.find(b'upcudup@gmail.com', idx)
        if pos == -1:
            break
        for start in range(max(0, pos - 4000), pos, 8):
            d = decompress_snappy(raw[start:])
            if b'access_token' in d and b'upcudup@gmail.com' in d:
                t_pos = d.find(b'{"access_token"')
                if t_pos != -1:
                    t_end = d.find(b'}', t_pos)
                    while t_end != -1 and t_end - t_pos < 5000:
                        try:
                            cand = d[t_pos:t_end+1].decode('utf-8')
                            j = json.loads(cand)
                            print('Found in decompressed block! expires_at:', j.get('expires_at'))
                            with open('scripts/supabase_user_session.json', 'w') as out:
                                json.dump(j, out, indent=2)
                            found = True
                            break
                        except:
                            t_end = d.find(b'}', t_end+1)
                if found: break
        if found: break
        idx = pos + 1
    if found: break

print('Session extraction finished. Found:', found)
