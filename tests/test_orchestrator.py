from unittest.mock import patch

from scripts.utils.orchestrator import get_hardware_map, move_window_to_monitor


def test_hardware_map_acquisition():
    """Verify that orchestrator can fetch the hardware map from the probe script."""
    mock_json = '{"monitors": [{"left":0, "top":0, "width":1920, "height":1080}]}'
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = mock_json
        hw = get_hardware_map()
        assert len(hw["monitors"]) == 1


def test_window_movement_powershell_invocation():
    """Verify that window movement triggers the correct PowerShell snippet."""
    monitors = [{"left": 1920, "top": 0, "width": 1920, "height": 1080}]
    with patch("subprocess.run") as mock_run:
        move_window_to_monitor("chrome", 0, monitors)
        args, _kwargs = mock_run.call_args
        ps_cmd = args[0][2]
        assert "SetWindowPos" in ps_cmd
        assert "1920" in ps_cmd
        assert "chrome" in ps_cmd


def test_invalid_monitor_index_safety():
    """Verify that moving to an out-of-bounds monitor index returns silently."""
    with patch("subprocess.run") as mock_run:
        move_window_to_monitor("chrome", 5, [])
        mock_run.assert_not_called()
