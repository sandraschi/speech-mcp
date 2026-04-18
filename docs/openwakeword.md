# openWakeWord — Reference for speech-mcp

## What it is

openWakeWord is a fully offline wake word/phrase detection library.
No API key. No phone-home. No license check. Apache 2.0.
Audio is processed entirely on-device using ONNX models via `onnxruntime`.

GitHub: https://github.com/dscripka/openWakeWord
PyPI: `openwakeword`
Latest stable: v0.6.0

Comparison to Picovoice Porcupine:
- Porcupine: higher raw accuracy, calls `kmp1.picovoice.net` on init to validate AccessKey
- openWakeWord: slightly lower accuracy, zero network contact ever, Apache licensed,
  no key of any kind required

---

## Installation

```bash
uv add openwakeword
# or: pip install openwakeword
```

On **Windows**, only `onnxruntime` is installed (no tflite — no Windows wheels exist).
On **Linux**, both `onnxruntime` and `tflite-runtime` are installed; tflite is the
default inference framework on Linux due to better efficiency.

`pyaudio` is also needed for microphone capture (already in speech-mcp venv):
```bash
uv add pyaudio
```

---

## Model download (one-time, on first use)

Models are **not bundled** in the pip package. They download from GitHub Releases on
first use and are cached locally. This is the only network access openWakeWord ever
makes, and only happens once per model.

```python
import openwakeword
openwakeword.utils.download_models()  # downloads all pre-trained models (~few MB each)
```

After download, models live in the package's `resources/models/` directory and are
loaded from disk on every subsequent use. No network contact after that.

To download selectively:
```python
openwakeword.utils.download_models(models=["hey_jarvis"])
```

---

## Pre-trained models (English only)

| Model name    | Detects                        | Notes                        |
|---------------|--------------------------------|------------------------------|
| `alexa`       | "alexa"                        |                              |
| `hey_jarvis`  | "hey jarvis"                   |                              |
| `hey_mycroft` | "hey mycroft"                  |                              |
| `hey_rhasspy` | "hey rhasspy"                  |                              |
| `timers`      | "set a 10 minute timer" etc.   | phrase, not single word      |
| `weather`     | "what's the weather" etc.      | phrase, not single word      |

All models are robust across different speaker accents. Each model detects multiple
phrase variations — see the individual docs pages on GitHub for the full lists.

Custom models can also be passed as `.onnx` file paths.

---

## Core API

### `Model` class

```python
from openwakeword.model import Model

oww = Model(
    wakeword_models=["hey_jarvis"],   # list of model names or .onnx paths
                                       # omit to load all pre-trained models
    inference_framework="onnx",        # "onnx" (Windows) or "tflite" (Linux default)
    vad_threshold=0.5,                 # 0.0–1.0; gates detections behind Silero VAD
                                       # set to 0.0 to disable VAD gating
    enable_speex_noise_suppression=False,  # Linux x86/arm64 only
)
```

**`wakeword_models`** — list of model names (strings) or absolute paths to `.onnx`
files. Omit or pass `[]` to load every pre-trained model.

**`inference_framework`** — `"onnx"` on Windows (only option), `"tflite"` or `"onnx"`
on Linux. Tflite is faster on Linux.

**`vad_threshold`** — A Silero VAD model runs in parallel. Detections are only
returned when VAD score simultaneously exceeds this threshold. Strongly recommended:
set to `0.5` for noisy environments. Set to `0.0` to disable entirely.

**`enable_speex_noise_suppression`** — Linux only. Applies SpeexDSP pre-processing
before the model. Helps with constant background noise (fans, HVAC). No effect/error
if set on Windows.

---

### `model.predict(frame)` — main inference call

```python
prediction = oww.predict(frame)
# Returns dict: {model_name: score, ...}
# e.g. {"hey_jarvis": 0.87, "alexa": 0.02}
```

**`frame`** — numpy array or list of 16-bit signed integers (PCM), 16kHz mono.
Frame length should be a **multiple of 1280 samples (80 ms)**.
Longer frames = more efficient but higher detection latency.
Recommended: 1280 samples (80 ms) for lowest latency, or 3840 (240 ms) for
efficiency.

Score interpretation: above `0.5` is a detection by default. The score is a
confidence value from the classification head, not a probability. Tune the threshold
for your environment — noisy rooms may need `0.7`.

---

### `model.predict_clip(path)` — predict on a WAV file

```python
scores = oww.predict_clip("path/to/file.wav")
# Returns dict of {model_name: [scores_per_frame]}
```

WAV must be 16-bit PCM, 16kHz, mono. Useful for offline testing.

---

### `model.reset()` — clear internal state

```python
oww.reset()
```

Clears the sliding window buffer used for detection. Call this after a successful
detection to prevent the model immediately re-triggering on residual audio.

---

## Audio format requirements

| Property    | Value          |
|-------------|----------------|
| Sample rate | 16000 Hz       |
| Bit depth   | 16-bit signed  |
| Channels    | 1 (mono)       |
| Frame size  | multiples of 1280 samples (80 ms) |

PyAudio setup:
```python
import pyaudio
CHUNK = 1280  # 80 ms at 16kHz
pa = pyaudio.PyAudio()
stream = pa.open(
    rate=16000,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=CHUNK,
)
pcm_bytes = stream.read(CHUNK, exception_on_overflow=False)
# Convert to list of ints for predict():
import struct
pcm = list(struct.unpack(f"{CHUNK}h", pcm_bytes))
```

---

## Minimal working example (mic loop)

```python
import pyaudio
import struct
import openwakeword
from openwakeword.model import Model

openwakeword.utils.download_models()

oww = Model(wakeword_models=["hey_jarvis"], vad_threshold=0.5, inference_framework="onnx")

CHUNK = 1280
pa = pyaudio.PyAudio()
stream = pa.open(rate=16000, channels=1, format=pyaudio.paInt16,
                 input=True, frames_per_buffer=CHUNK)

print("Listening for 'hey jarvis'...")
while True:
    pcm_bytes = stream.read(CHUNK, exception_on_overflow=False)
    pcm = list(struct.unpack(f"{CHUNK}h", pcm_bytes))
    scores = oww.predict(pcm)
    for name, score in scores.items():
        if score > 0.5:
            print(f"Detected: {name} ({score:.2f})")
            oww.reset()
```

---

## VAD integration detail

openWakeWord bundles **Silero VAD** (`silero_vad.onnx`). When `vad_threshold > 0`,
every frame is also passed through the VAD model. A wake word detection is only
reported if the VAD score for that frame also exceeds the threshold. This gates out
false positives from music, TV speech, and background noise that might acoustically
resemble a wake word.

The VAD model is the same one used across the ecosystem (Home Assistant, Rhasspy,
etc.) and runs in ~1 ms on CPU.

---

## Custom model training

Training requires Linux (Piper TTS for synthetic data generation does not run on
Windows). The process is:

1. Generate synthetic positive samples with Piper TTS (automated via Google Colab
   notebook in the repo)
2. Collect negative data (background noise, music, unrelated speech) — or use the
   provided datasets
3. Pre-compute embeddings from the frozen Google speech embedding backbone
4. Train a small fully-connected or 2-layer RNN classifier on top
5. Export to ONNX
6. Use the `.onnx` file directly in `Model(wakeword_models=["path/to/model.onnx"])`

The Colab notebook can train a basic model in under an hour. Custom training is
Linux-only but the resulting `.onnx` model runs fine on Windows.

---

## Custom verifier models (speaker-specific filtering)

If false-accept rate is too high for a specific deployment, a **verifier model** can
be trained on as little as ~10 seconds of speech from the target speaker. The
verifier runs as a second-stage filter: the base model detects the wake word, then
the verifier checks if it was spoken by the known speaker.

```python
oww = Model(
    wakeword_models=["hey_jarvis"],
    custom_verifier_models={"hey_jarvis": "path/to/verifier.pkl"},
    custom_verifier_threshold=0.1,
)
```

The verifier is a simple logistic regression classifier (sklearn `.pkl`), not a
neural network. It takes the same shared audio embeddings as input.

---

## Performance characteristics

Target performance for all included models:
- False-reject rate: < 5% (1 in 20 intended activations missed)
- False-accept rate: < 0.5 per hour of continuous mixed audio

These are measured against realistic noisy audio with reverberation, not clean studio
recordings. With `vad_threshold=0.5` the false-accept rate is substantially lower.

The README explicitly acknowledges that Porcupine has better raw accuracy and is
better suited for highly constrained hardware. On a standard desktop/server, the
difference is not meaningful in practice.

---

## What openWakeWord never does

- Never opens a network connection after the one-time model download
- No AccessKey, no license validation, no heartbeat
- No DLL with embedded hostnames
- Audio stays entirely on-device
- All inference via onnxruntime (pure Python/C++ locally)

---

## Integration plan for speech-mcp

Replace `pvporcupine` in `tools/wake_word.py`:

```python
# Remove:
import pvporcupine

# Add:
import openwakeword
from openwakeword.model import Model
```

`Model` init happens once at thread start, `predict()` replaces `porcupine.process()`.
Frame size changes from Porcupine's 512 samples → openWakeWord's 1280 samples (80 ms).
No AccessKey parameter. No `delete()` call needed on cleanup.

Available wake words narrow from 16 (Porcupine built-ins) to 6 pre-trained models,
but custom `.onnx` models can be dropped in for any phrase.

`pvporcupine` can stay in `pyproject.toml` as optional or be removed — it's not
harmful to have installed, just unused.
