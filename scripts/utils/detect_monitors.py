import ctypes
from ctypes import wintypes


def get_monitor_info():
    user32 = ctypes.windll.user32
    monitors = []

    # Callback
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

    # Define callback type
    MonitorEnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
    cb = MonitorEnumProc(_cb)

    user32.EnumDisplayMonitors(None, None, cb, 0)
    return monitors

def get_system_metrics():
    user32 = ctypes.windll.user32
    return {
        "CMONITORS": user32.GetSystemMetrics(80),
        "CXVIRTUALSCREEN": user32.GetSystemMetrics(78),
        "CYVIRTUALSCREEN": user32.GetSystemMetrics(79),
    }

if __name__ == "__main__":
    metrics = get_system_metrics()
    print("System Metrics:")
    print(f"  Count according to GetSystemMetrics(80): {metrics['CMONITORS']}")
    print(f"  Virtual Screen Size: {metrics['CXVIRTUALSCREEN']}x{metrics['CYVIRTUALSCREEN']}")

    mons = get_monitor_info()
    print("\nDetailed Monitor Info (EnumDisplayMonitors):")
    for i, m in enumerate(mons):
        print(f"  [{i}] {m['width']}x{m['height']} at ({m['left']}, {m['top']})")
