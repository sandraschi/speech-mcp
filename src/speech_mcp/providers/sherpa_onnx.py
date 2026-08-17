"""Streaming ASR via sherpa-onnx — Japanese / English / German on CPU, with VAD barge-in.

sherpa-onnx (k2-fsa) provides streaming online recognizers (transducer) plus a
Silero-VAD segmenter. This provider wires both together so a voice loop can:

1. Run VAD over a live mic stream,
2. Stream accepted speech through the online recognizer and get partials,
3. Detect that the user spoke again (barge-in) while the assistant is talking.

Model support is focused on the languages this server cares about:

- ``en``: csukuangfj/sherpa-onnx-streaming-zipformer-en-2023-06-26
- ``ja``: csukuangfj/sherpa-onnx-streaming-zipformer-ar_en_id_ja_ru_th_vi_zh-2025-02-10
- ``de``: csukuangfj/sherpa-onnx-streaming-zipformer-de-kroko-2025-08-06

All three are transducer models (encoder/decoder/joiner). Model files are
resolved by glob so the exact per-release filenames don't matter.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

SHERPA_SAMPLE_RATE = 16000

# Language -> default model repo (transducer: encoder/decoder/joiner + tokens)
LANG_MODELS: dict[str, dict[str, str]] = {
    "en": {
        "repo": "csukuangfj/sherpa-onnx-streaming-zipformer-en-2023-06-26",
    },
    "ja": {
        "repo": "csukuangfj/sherpa-onnx-streaming-zipformer-ar_en_id_ja_ru_th_vi_zh-2025-02-10",
    },
    "de": {
        "repo": "csukuangfj/sherpa-onnx-streaming-zipformer-de-kroko-2025-08-06",
    },
}

SILERO_VAD_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx"


@dataclass
class SherpaModelSpec:
    """Resolved paths for a streaming transducer model."""

    encoder: str
    decoder: str
    joiner: str
    tokens: str
    bpe_vocab: str | None = None


def _glob_single(directory: Path, pattern: str) -> str | None:
    matches = sorted(directory.glob(pattern))
    return str(matches[0]) if matches else None


def resolve_model_files(model_dir: str | Path) -> SherpaModelSpec:
    """Auto-discover encoder/decoder/joiner/tokens in a model directory."""
    d = Path(model_dir)
    if not d.is_dir():
        raise FileNotFoundError(f"sherpa-onnx model dir not found: {d}")
    encoder = _glob_single(d, "*encoder*.onnx")
    decoder = _glob_single(d, "*decoder*.onnx")
    joiner = _glob_single(d, "*joiner*.onnx")
    tokens = _glob_single(d, "tokens.txt")
    if not (encoder and decoder and joiner and tokens):
        raise FileNotFoundError(
            f"incomplete transducer model in {d} "
            f"(encoder={bool(encoder)} decoder={bool(decoder)} joiner={bool(joiner)} tokens={bool(tokens)})"
        )
    bpe = _glob_single(d, "bpe.model")
    return SherpaModelSpec(encoder=encoder, decoder=decoder, joiner=joiner, tokens=tokens, bpe_vocab=bpe)


def default_model_dir(lang: str, base: str | None = None) -> Path:
    """Default local dir for a language's model (downloads land here)."""
    base = base or os.environ.get(
        "SHERPA_MODEL_DIR", str(Path(__file__).parent.parent.parent.parent / "models" / "sherpa-onnx")
    )
    return Path(base) / lang


def ensure_model(lang: str, model_dir: str | Path | None = None) -> Path:
    """Download the language model via huggingface_hub if not present locally."""
    lang = lang.lower()
    if lang not in LANG_MODELS:
        raise ValueError(f"Unsupported sherpa-onnx language '{lang}'. Supported: {sorted(LANG_MODELS)}")
    dest = Path(model_dir) if model_dir else default_model_dir(lang)
    dest.mkdir(parents=True, exist_ok=True)
    if not _glob_single(dest, "*encoder*.onnx"):
        from huggingface_hub import snapshot_download

        logger.info("Downloading sherpa-onnx streaming model for '%s' -> %s", lang, dest)
        snapshot_download(repo_id=LANG_MODELS[lang]["repo"], local_dir=dest)
        logger.info("Downloaded sherpa-onnx model for '%s'", lang)
    return dest


def ensure_silero_vad(vad_path: str | Path | None = None) -> str:
    """Download silero_vad.onnx (used for barge-in segmentation)."""
    path = Path(vad_path) if vad_path else Path(default_model_dir("vad").parent, "vad", "silero_vad.onnx")
    if path.exists():
        return str(path)
    import urllib.request

    logger.info("Downloading silero-vad -> %s", path)
    path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(SILERO_VAD_URL, path)
    return str(path)


def _to_float32(pcm_int16: np.ndarray) -> np.ndarray:
    return (pcm_int16.astype(np.float32)) / 32768.0


def _ensure_onnxruntime_dll() -> None:
    """On Windows a stray onnxruntime.dll in System32 can shadow the venv copy
    (sherpa-onnx loads it by name, and System32 is searched before PATH).

    os.add_dll_directory() makes the venv's onnxruntime (matching the wheel's
    compiled API version) load instead. Call before constructing a recognizer.
    """
    if os.name != "nt":
        return
    try:
        import onnxruntime

        capi = os.path.join(os.path.dirname(onnxruntime.__file__), "capi")
        if os.path.isdir(capi):
            os.add_dll_directory(capi)
    except Exception as e:  # pragma: no cover
        logger.debug("onnxruntime dll dir not added: %s", e)


class SherpaStreamingASR:
    """Online streaming recognizer for one language (transducer)."""

    _barge_in: SherpaBargeIn | None = None

    def __init__(
        self,
        lang: str = "en",
        model_dir: str | Path | None = None,
        num_threads: int = 2,
        provider: str | None = None,
        enable_endpoint: bool = True,
        rule1_min_trailing_silence: float = 1.2,
        rule2_min_trailing_silence: float = 2.4,
        rule3_min_utterance_length: int = 300,
    ) -> None:
        # Must run before importing sherpa_onnx: its .pyd loads onnxruntime
        # by name at import time, and a System32 copy would shadow the venv one.
        _ensure_onnxruntime_dll()
        import sherpa_onnx

        self.lang = lang.lower()
        self._dir = Path(model_dir) if model_dir else default_model_dir(self.lang)
        spec = resolve_model_files(self._dir)

        recognizer_cfg: dict = dict(
            tokens=spec.tokens,
            encoder=spec.encoder,
            decoder=spec.decoder,
            joiner=spec.joiner,
            num_threads=num_threads,
            sample_rate=SHERPA_SAMPLE_RATE,
            feature_dim=80,
            decoding_method="greedy_search",
            enable_endpoint_detection=enable_endpoint,
            rule1_min_trailing_silence=rule1_min_trailing_silence,
            rule2_min_trailing_silence=rule2_min_trailing_silence,
            rule3_min_utterance_length=rule3_min_utterance_length,
        )
        if spec.bpe_vocab:
            recognizer_cfg["bpe_vocab"] = spec.bpe_vocab
        if provider:
            recognizer_cfg["provider"] = provider

        self.recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(**recognizer_cfg)
        self.reset()

    def reset(self) -> None:
        self.stream = self.recognizer.create_stream()

    def accept(self, pcm_int16: np.ndarray) -> dict:
        """Feed one chunk of int16 PCM. Returns partial text + endpoint flag."""
        samples = _to_float32(pcm_int16)
        self.stream.accept_waveform(SHERPA_SAMPLE_RATE, samples)
        while self.recognizer.is_ready(self.stream):
            self.recognizer.decode_stream(self.stream)
        partial = self.recognizer.get_result(self.stream).strip()
        endpoint = self.recognizer.is_endpoint(self.stream)
        return {"partial": partial, "endpoint": endpoint}

    def final(self) -> str:
        """Flush and return the current utterance text."""
        text = self.recognizer.get_result(self.stream).strip()
        self.reset()
        return text


class SherpaBargeIn:
    """Barge-in detection via the streaming recognizer's endpoint detection.

    The sherpa-onnx Windows wheel's VoiceActivityDetector segfaults (access
    violation in pop), so barge-in uses the online recognizer's rule-based
    trailing-silence endpoint detection instead:

    - feed mic chunks to ``feed()``
    - a non-empty ``partial`` means the user is (or just was) speaking
    - an ``endpoint`` with text means one utterance completed

    NOTE: no echo cancellation - if the assistant's own TTS reaches the mic,
    it will look like the user. Use headset/beamforming in production, or
    gate feeding while the assistant speaks.
    """

    def __init__(self, asr: SherpaStreamingASR) -> None:
        self.asr = asr

    def feed(self, pcm_int16: np.ndarray) -> list[str]:
        """Feed a PCM chunk. Returns completed utterance texts (barge-in signal)."""
        result = self.asr.accept(pcm_int16)
        if result["endpoint"] and result["partial"]:
            text = self.asr.final()
            return [text] if text else []
        return []

    def speaking(self, pcm_int16: np.ndarray) -> bool:
        """True while the user is currently speaking (non-empty partial)."""
        result = self.asr.accept(pcm_int16)
        return bool(result["partial"])

    def reset(self) -> None:
        self.asr.reset()
