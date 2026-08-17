import pyaudio

# Legacy PortAudio aliases on Windows - not real user-facing mics.
_ALIAS_FILTER = ("sound mapper", "primary sound capture", "input ()")


def _friendly_name(raw: str) -> str:
    """Windows PortAudio names sometimes embed a driver path, e.g.
    'Input (@System32\\drivers\\bthhfenum.sys,#4;%1 Hands-Free HF Audio%0\\r\\n
    ;(iPhoneSas (2)))'. Keep only the trailing human-readable name in parens.
    """
    if ";" in raw:
        tail = raw.rsplit(";", 1)[-1].strip()
        if tail.startswith("("):
            inner = tail.lstrip("(").rstrip(")").strip()
            if inner:
                return inner
    return raw


def get_microphones():
    """Enumerate unique microphones.

    PortAudio on Windows reports every format-variant, 31-char-truncated name
    and legacy alias as a separate device (e.g. the same webcam at
    44.1/48/32 kHz appears 3x). We dedupe by a normalized name, keep the
    highest sample-rate variant, and drop the legacy aliases.
    """
    p = pyaudio.PyAudio()
    raw = []
    try:
        count = p.get_device_count()
        for i in range(count):
            info = p.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0:
                raw.append(
                    {
                        "index": i,
                        "name": (info.get("name") or "").strip(),
                        "channels": info.get("maxInputChannels", 0),
                        "rate": info.get("defaultSampleRate", 0),
                    }
                )
    finally:
        p.terminate()

    seen: dict[str, dict] = {}
    for m in raw:
        friendly = _friendly_name(m["name"])
        low = friendly.lower()
        if any(alias in low for alias in _ALIAS_FILTER):
            continue
        key = low[:31]  # PortAudio truncates names to 31 chars - treat as same device
        prev = seen.get(key)
        # Prefer the entry with the longer (untruncated) name and highest rate
        if prev is None or (len(friendly) > len(prev["name"]) or m["rate"] > prev["rate"]):
            m["name"] = friendly
            seen[key] = m

    return sorted(seen.values(), key=lambda m: m["name"].lower())


if __name__ == "__main__":
    mics = get_microphones()
    print(f"Detected {len(mics)} Microphones/Input Devices:")
    for m in mics:
        print(f"  [{m['index']}] {m['name']} ({m['channels']} channels, {m['rate']} Hz)")
