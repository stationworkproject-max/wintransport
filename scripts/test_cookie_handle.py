import os, ctypes
from ctypes import wintypes

cookie_src = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies')

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80

handle = ctypes.windll.kernel32.CreateFileW(
    cookie_src, 
    GENERIC_READ, 
    FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, 
    None, 
    OPEN_EXISTING, 
    FILE_ATTRIBUTE_NORMAL, 
    None
)

err = ctypes.windll.kernel32.GetLastError()
print(f"Handle: {handle}, LastError: {err}")
if handle != -1 and handle != 0xFFFFFFFFFFFFFFFF:
    size = ctypes.windll.kernel32.GetFileSize(handle, None)
    print("Cookie file size:", size)
    ctypes.windll.kernel32.CloseHandle(handle)
