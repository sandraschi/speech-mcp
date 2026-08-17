"""Download sherpa-onnx streaming ASR models + silero VAD for the configured languages.

Usage:
    uv run python scripts/download_sherpa_models.py            # en ja de
    uv run python scripts/download_sherpa_models.py de          # just German
    uv run python scripts/download_sherpa_models.py --vad       # also VAD
    uv run python scripts/download_sherpa_models.py ja --vad    # Japanese + VAD

Models land in models/sherpa-onnx/{lang}/ (override with SHERPA_MODEL_DIR).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Download sherpa-onnx streaming models")
    parser.add_argument("lang", nargs="*", default=["en", "ja", "de"], help="Languages: en, ja, de")
    parser.add_argument("--vad", action="store_true", help="Also download silero VAD for barge-in")
    args = parser.parse_args()

    from speech_mcp.providers.sherpa_onnx import ensure_model, ensure_silero_vad

    for lang in args.lang:
        try:
            dest = ensure_model(lang)
            print(f"  {lang}: {dest}")
        except Exception as exc:
            print(f"  {lang}: FAILED - {exc}")
            raise SystemExit(1) from exc
    if args.vad:
        print(f"  vad: {ensure_silero_vad()}")

    print("Done. Set SHERPA_ASR_ENABLED=1 (+ SHERPA_ASR_LANG=ja|en|de, SHERPA_BARGE_IN=1) to enable.")


if __name__ == "__main__":
    main()
