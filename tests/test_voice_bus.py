"""Voice command bus helpers."""

import json
from unittest.mock import MagicMock, patch

from speech_mcp.voice_bus import fleet_voice_enabled, post_speech_intent


def test_fleet_voice_enabled_flag() -> None:
    with patch.dict("os.environ", {"FLEET_VOICE_DELEGATE": "1"}, clear=False):
        assert fleet_voice_enabled() is True
    with patch.dict("os.environ", {"FLEET_VOICE_DELEGATE": "0"}, clear=False):
        assert fleet_voice_enabled() is False


# resolve_entity is in fleet-agent; keep speech tests local
def test_post_speech_intent_json() -> None:
    payload_holder: list[bytes] = []

    def _fake_urlopen(req, timeout=0):
        payload_holder.append(req.data)
        resp = MagicMock()
        resp.read.return_value = json.dumps({"success": True, "entity": "boomy"}).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    with patch("urllib.request.urlopen", _fake_urlopen):
        out = post_speech_intent(wake="hey_jarvis", transcript="boomy patrol")
    assert out["success"] is True
    body = json.loads(payload_holder[0].decode())
    assert body["transcript"] == "boomy patrol"


# remove bogus import test - I added resolve_entity_import by mistake
