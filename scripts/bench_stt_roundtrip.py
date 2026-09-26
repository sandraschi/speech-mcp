"""Round-trip STT bench: Kokoro TTS speaks known text, sherpa streaming transcribes.

Usage:
    uv run python scripts/bench_stt_roundtrip.py
    uv run python scripts/bench_stt_roundtrip.py --langs en
    uv run python scripts/bench_stt_roundtrip.py --zh-plumbing   # zh recognizer build check only

EN measures the real pipeline (kokoro is English-native). DE is TTS-limited
(kokoro mangles German phonemes) - the number measures the pipeline, not the
DE model; native DE audio still needed for a true DE score. ZH has no local
TTS - --zh-plumbing only proves the zh recognizer builds and runs.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

SENTENCES: dict[str, list[str]] = {
    "en": [
        "Hello Fritz, voice check one two three.",
        "The quick brown fox jumps over the lazy dog.",
        "Schedule a meeting for tomorrow at nine in the morning.",
    ],
    "de": [
        "Guten Morgen, Fritz, Sprachtest eins zwei drei.",
        "Bitte plane morgen um neun Uhr eine Besprechung.",
    ],
}

SHERPA_LANG = {"en": "en", "de": "de"}


def _norm(text: str) -> list[str]:
    return re.sub(r"[^\w\s']", "", text.lower()).split()


def _wer(ref: str, hyp: str) -> float:
    r = _norm(ref)
    h = _norm(hyp)
    if not r:
        return 0.0 if not h else 1.0
    prev = list(range(len(h) + 1))
    for i, rw in enumerate(r, 1):
        cur = [i]
        for j, hw in enumerate(h, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (rw != hw)))
        prev = cur
    return prev[-1] / len(r)


def _wav_to_16k_mono(wav_bytes: bytes) -> np.ndarray:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        n = wf.getnframes()
        ch = wf.getnchannels()
        rate = wf.getframerate()
        raw = wf.readframes(n)
    pcm = np.frombuffer(raw, dtype=np.int16).reshape(-1, ch).mean(axis=1).astype(np.float32)
    if rate != 16000:
        idx = np.linspace(0, len(pcm) - 1, int(len(pcm) * 16000 / rate))
        pcm = np.interp(idx, np.arange(len(pcm)), pcm).astype(np.float32)
    return np.clip(pcm, -32768, 32767).astype(np.int16)


def bench_lang(lang: str) -> list[dict]:
    from speech_mcp.providers.kokoro import KokoroProvider
    from speech_mcp.providers.sherpa_onnx import SherpaStreamingASR, ensure_model

    ensure_model(SHERPA_LANG[lang])
    asr = SherpaStreamingASR(lang=SHERPA_LANG[lang])
    koko = KokoroProvider()
    out = []
    for text in SENTENCES[lang]:
        wav = koko.synthesize_wav(text)
        pcm = _wav_to_16k_mono(wav)
        # Trailing silence mimics natural utterance end (endpoint needs it).
        pcm = np.concatenate([pcm, np.zeros(12800, dtype=np.int16)])
        asr.reset()
        chunk = 8000  # 0.5 s chunks at 16 kHz
        for i in range(0, len(pcm), chunk):
            asr.accept(pcm[i : i + chunk])
        hyp = asr.final()
        out.append({"ref": text, "hyp": hyp, "wer": round(_wer(text, hyp), 3)})
    return out


def zh_plumbing() -> dict:
    from speech_mcp.providers.sherpa_onnx import SherpaStreamingASR, default_model_dir, ensure_model

    dest = ensure_model("zh")
    asr = SherpaStreamingASR(lang="zh")
    silence = np.zeros(16000, dtype=np.int16)
    r = asr.accept(silence)
    return {
        "dir": str(dest),
        "shared_with_ja": str(dest) == str(default_model_dir("ja")),
        "recognizer_built": True,
        "silence_partial": r["partial"],
        "silence_endpoint": r["endpoint"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default="en,de", help="comma list: en,de")
    ap.add_argument("--zh-plumbing", action="store_true")
    args = ap.parse_args()

    for lang in [x.strip() for x in args.langs.split(",") if x.strip()]:
        print(f"== {lang} (kokoro TTS -> sherpa streaming) ==")
        for row in bench_lang(lang):
            print(f"  WER {row['wer']:.3f} | ref: {row['ref']}")
            print(f"                 hyp: {row['hyp'] or '(empty)'}")
        if lang == "de":
            print("  NOTE: DE score is TTS-limited (kokoro is English-native), not a DE-model score.")
    if args.zh_plumbing:
        print("== zh plumbing ==", zh_plumbing())


if __name__ == "__main__":
    main()
