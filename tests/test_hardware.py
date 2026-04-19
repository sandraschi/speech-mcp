from unittest.mock import MagicMock, patch

from scripts.utils.hardware_probe import get_cameras, get_microphones, get_monitors


def test_monitor_enumeration_logic():
    """Verify that monitor enumeration handles the ctypes callback logic."""
    # We mock EnumDisplayMonitors to simulate the callback
    with patch("ctypes.windll.user32.EnumDisplayMonitors") as mock_enum:
        def fake_enum(hdc, rect, callback, data):
            # Simulate a 1080p monitor
            rect_obj = MagicMock()
            rect_obj.contents.left = 0
            rect_obj.contents.top = 0
            rect_obj.contents.right = 1920
            rect_obj.contents.bottom = 1080
            callback(0, 0, rect_obj, 0)
            return True

        mock_enum.side_effect = fake_enum
        monitors = get_monitors()
        assert len(monitors) == 1
        assert monitors[0]["width"] == 1920

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
