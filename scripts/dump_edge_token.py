import ctypes, re, json
from ctypes import wintypes

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("PartitionId", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]

MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04
PAGE_READONLY = 0x02

import subprocess
out = subprocess.check_output('powershell -Command "(Get-Process -Name msedge).Id"', shell=True)
pids = [int(p.strip()) for p in out.decode().split() if p.strip().isdigit()]

print("Found msedge PIDs:", pids)

found_tokens = set()

for pid in pids:
    h_proc = ctypes.windll.kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not h_proc:
        continue
    
    addr = 0
    mbi = MEMORY_BASIC_INFORMATION()
    
    while ctypes.windll.kernel32.VirtualQueryEx(h_proc, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        if mbi.State == MEM_COMMIT and (mbi.Protect & (PAGE_READWRITE | PAGE_READONLY)):
            size = min(mbi.RegionSize, 10 * 1024 * 1024) # max 10MB per region
            buf = ctypes.create_string_buffer(size)
            bytes_read = ctypes.c_size_t()
            if ctypes.windll.kernel32.ReadProcessMemory(h_proc, ctypes.c_void_p(addr), buf, size, ctypes.byref(bytes_read)):
                chunk = buf.raw[:bytes_read.value]
                # Look for token
                matches = re.findall(rb'Bearer (eyJ[a-zA-Z0-9_-]{20,}\.eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,})', chunk)
                for m in matches:
                    found_tokens.add(m.decode('utf-8'))
        addr += mbi.RegionSize
        if addr >= 0x7FFFFFFF0000:
            break
            
    ctypes.windll.kernel32.CloseHandle(h_proc)

print(f"Total tokens found in Edge memory: {len(found_tokens)}")
import base64
for tok in found_tokens:
    try:
        parts = tok.split('.')
        payload = parts[1] + '=' * (-len(parts[1]) % 4)
        p = json.loads(base64.urlsafe_b64decode(payload))
        print("Token:", p.get('iss'), p.get('email'), p.get('exp'))
        if p.get('email') == 'upcudup@gmail.com':
            print("MATCH FOUND! Saving...")
            with open('scripts/supabase_user_session.json', 'w') as f:
                json.dump({"access_token": tok}, f, indent=2)
            break
    except Exception as e:
        pass
