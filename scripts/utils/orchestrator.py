import argparse
import json
import os
import subprocess
import time


def get_hardware_map():
    script_dir = os.path.dirname(__file__)
    probe_path = os.path.join(script_dir, "hardware_probe.py")
    try:
        result = subprocess.run(["py", probe_path], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception:
        return {"monitors": [], "microphones": [], "cameras": []}


def move_window_to_monitor(process_name: str, monitor_index: int, monitors: list):
    if monitor_index >= len(monitors):
        return

    target_mon = monitors[monitor_index]
    # Simple PowerShell snippet to find window by name and move it
    # note: this is a heuristic, real implementation might need a small C# wrapper for robustness
    ps_cmd = f"""
    Add-Type @"
      using System;
      using System.Runtime.InteropServices;
      public class User32 {{
        [DllImport("user32.dll")]
        public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
        [DllImport("user32.dll")]
        public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
        [DllImport("user32.dll")]
        public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
        public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
        [DllImport("user32.dll")]
        public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
      }}
"@
    $targetProc = Get-Process -Name "{process_name}" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($targetProc) {{
      $hwnd = $targetProc.MainWindowHandle
      if ($hwnd -ne 0) {{
        [User32]::SetWindowPos($hwnd, 0, {target_mon["left"]}, {target_mon["top"]}, {target_mon["width"]}, {target_mon["height"]}, 0x0040)
      }}
    }}
    """
    subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)


def main():
    parser = argparse.ArgumentParser(description="Professional MCP Orchestrator")
    parser.add_argument("--app", type=str, help="Target application command (e.g. blender)")
    parser.add_argument("--monitor", type=int, default=1, help="Monitor index for the webapp (0-indexed)")
    parser.add_argument("--virtual-desktop", type=int, help="Optional Virtual Desktop index")
    args = parser.parse_args()

    hw = get_hardware_map()
    monitors = hw.get("monitors", [])

    print(f"[*] Detected {len(monitors)} monitors.")

    # 1. Start the target app on primary (Monitor 0)
    if args.app:
        print(f"[*] Launching target application: {args.app}")
        subprocess.Popen(args.app, shell=True)

    # 2. Start the Speech-MCP webapp
    print("[*] Launching Speech-MCP backend...")
    webapp_proc = subprocess.Popen(["py", "-m", "speech_mcp.webapp"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    print("[*] Waiting for UI to initialize...")
    time.sleep(5)  # Give it time to spawn windows

    # 3. Position the webapp
    target_mon_idx = args.monitor
    if len(monitors) > 1:
        print(f"[*] Dual screen detected. Moving webapp to Monitor {target_mon_idx}...")
        # Note: We move the browser window if it's open, or wait for it.
        # This is a bit tricky without knowing exactly which browser opened.
        # Typically the user opens the browser.
    else:
        print("[*] Single screen detected.")
        if args.virtual_desktop:
            print(f"[*] Attempting move to Virtual Desktop {args.virtual_desktop}...")
            # Virtual desktop logic would go here

    print("[*] Orchestration complete. Press Ctrl+C to shutdown both.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[*] Shutting down...")
        webapp_proc.terminate()
        # Kill the target app if possible (process group management would be better here)


if __name__ == "__main__":
    main()
