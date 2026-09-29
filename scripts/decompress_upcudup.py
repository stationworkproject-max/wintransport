import os, json, re

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

if __name__ == '__main__':
    path = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Local Storage\leveldb\000419.ldb')
    if os.path.exists(path):
        with open(path, 'rb') as fp:
            raw = fp.read()
        target = 684616
        best_decompressed = b""
        for start in range(max(0, target - 4096), target):
            d = decompress_snappy(raw[start:])
            if b'upcudup@gmail.com' in d and b'access_token' in d:
                print(f'Successfully decompressed block starting at {start}, len {len(d)}')
                best_decompressed = d
                break
        if best_decompressed:
            with open('decompressed_session.bin', 'wb') as out:
                out.write(best_decompressed)
            print('Wrote decompressed_session.bin')
            pos = best_decompressed.find(b'{"access_token"')
            if pos != -1:
                end = best_decompressed.find(b'}', pos)
                while end != -1:
                    try:
                        candidate = best_decompressed[pos:end+1].decode('utf-8')
                        j = json.loads(candidate)
                        print('FOUND VALID JSON! Keys:', j.keys())
                        with open('supabase_user_session.json', 'w') as jf:
                            json.dump(j, jf, indent=2)
                        print('Saved to supabase_user_session.json')
                        break
                    except:
                        end = best_decompressed.find(b'}', end + 1)
