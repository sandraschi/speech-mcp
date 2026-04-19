import ctypes
import json
import subprocess
from ctypes import wintypes


def get_monitors():
    user32 = ctypes.windll.user32
    monitors = []

    def _cb(hMonitor, hdcMonitor, lprcMonitor, dwData):
        rect = lprcMonitor.contents
        monitors.append({
            "left": rect.left,
            "top": rect.top,
            "right": rect.right,
            "bottom": rect.bottom,
            "width": rect.right - rect.left,
            "height": rect.bottom - rect.top
        })
        return True

    MonitorEnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
    cb = MonitorEnumProc(_cb)
    user32.EnumDisplayMonitors(None, None, cb, 0)
    return monitors

def get_microphones():
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        mics = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info.get('maxInputChannels') > 0:
                mics.append({
                    "index": i,
                    "name": info.get('name'),
                    "channels": info.get('maxInputChannels'),
                    "rate": int(info.get('defaultSampleRate'))
                })
        p.terminate()
        return mics
    except ImportError:
        return []

def get_cameras():
    # Use native PowerShell to avoid OpenCV/DirectShow complexity in raw ctypes
    cmd = "Get-CimInstance -ClassName Win32_PnPEntity | Where-Object { $_.Service -eq 'usbvideo' } | Select-Object Name | ConvertTo-Json"
    try:
        result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
        if not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        if isinstance(data, dict):
            return [data['Name']]
        elif isinstance(data, list):
            return [d['Name'] for d in data]
        return []
    except Exception:
        return []

def main():
    probe = {
        "monitors": get_monitors(),
        "microphones": get_microphones(),
        "cameras": get_cameras()
    }
    print(json.dumps(probe, indent=2))

if __name__ == "__main__":
    main()
