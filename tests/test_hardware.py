import ctypes
import sys
from ctypes import wintypes
from unittest.mock import patch

import pytest

from scripts.utils.hardware_probe import get_cameras, get_microphones, get_monitors


@pytest.mark.skipif(sys.platform != "win32", reason="Windows monitor APIs only")
def test_monitor_enumeration_logic():
    """Verify that monitor enumeration handles the ctypes callback logic."""
    with patch("ctypes.windll.user32.EnumDisplayMonitors") as mock_enum:

        def fake_enum(hdc, rect, callback, data):
            monitor_rect = wintypes.RECT()
            monitor_rect.left = 0
            monitor_rect.top = 0
            monitor_rect.right = 1920
            monitor_rect.bottom = 1080
            callback(0, 0, ctypes.pointer(monitor_rect), 0)
            return True

        mock_enum.side_effect = fake_enum
        monitors = get_monitors()
        assert len(monitors) == 1
        assert monitors[0]["width"] == 1920


@pytest.mark.skipif(sys.platform != "win32", reason="Windows PowerShell camera probe only")
def test_camera_detection_powershell_mock():
    """Verify that camera detection correctly parses PowerShell JSON output."""
    mock_ps_output = '[{"Name":"c922 Pro Stream Webcam"}]'
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = mock_ps_output
        cams = get_cameras()
        assert len(cams) == 1
        assert cams[0] == "c922 Pro Stream Webcam"


def test_microphone_enumeration_import_fallback():
    """Verify that microphone detection handles missing pyaudio gracefully."""
    with patch("builtins.__import__", side_effect=ImportError):
        mics = get_microphones()
        assert mics == []
