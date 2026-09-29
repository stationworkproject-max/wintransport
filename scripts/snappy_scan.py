import os, re, json, base64

def decompress_snappy(data):
    try:
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
    except:
        return b""

ldb_path = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Local Storage\leveldb\000419.ldb')
with open(ldb_path, 'rb') as fp:
    raw = fp.read()

print('Raw ldb size:', len(raw))

# Scan raw for snappy compressed block markers or decompress sliding windows
# In LevelDB table format, blocks are: [block_data] [compression_type (1 byte: 0=none, 1=snappy)] [crc32 (4 bytes)]
decompressed_chunks = []
for i in range(len(raw) - 5):
    # compression_type == 1
    if raw[i] == 1:
        # check if prev bytes decompress cleanly
        # try various block start positions
        pass

# Even simpler: scan for any snappy stream or inspect uncompressed tokens
# Let's search raw for tokens again or search all decoded text
found = set()
for m in re.finditer(rb'\{[^{}]{20,}\}', raw):
    s = m.group(0)
    if b'supabase' in s or b'token' in s or b'rqwpafat' in s:
        print('JSON block in raw:', s[:200])

# Let's also check if we can scan 4KB blocks in raw and snappy decompress
for offset in range(0, len(raw), 512):
    dec = decompress_snappy(raw[offset:])
    if len(dec) > 200:
        if b'supabase' in dec or b'rqwpafat' in dec or b'eyJ' in dec:
            # search for jwts
            jwts = re.findall(rb'eyJ[a-zA-Z0-9_-]{15,}\.eyJ[a-zA-Z0-9_-]{15,}\.[a-zA-Z0-9_-]{15,}', dec)
            for j in jwts:
                try:
                    parts = j.split(b'.')
                    p = json.loads(base64.urlsafe_b64decode(parts[1] + b'=' * (-len(parts[1]) % 4)))
                    if j not in found:
                        found.add(j)
                        print('DECOMPRESSED JWT:', p)
                        with open('extracted_jwts.txt', 'ab') as out:
                            out.write(j + b'\n')
                except:
                    pass
print('Done. Total found:', len(found))
