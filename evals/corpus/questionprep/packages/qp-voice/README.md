# qp-voice

Speech in, speech out. Import name: `qp_voice`. Both classes are heavy; the API creates them lazily on
first use and unloads the speech-to-text model when the last interview session ends.

| Module | Purpose |
|---|---|
| `speech_to_text.py` | `SpeechToText`: decodes Opus audio with **ffmpeg**, transcribes with **Qwen3-ASR-0.6B** (CPU, float32; see *Requirements* for where the model is loaded from) and returns `{transcript, stutter_flag, disfluency_rate, details}` via `transcribe_and_analyze`. Also `analyze_disfluencies` (adjacent / windowed / phrase repetitions, fillers) and `combine_stress_signals` (browser model + stutter flag → `not_stressed / mild / stressed / highly_stressed`). |
| `text_to_speech.py` | `TextToSpeech`: Pocket-TTS (`alba` voice) → WAV bytes. |
| `testing.py` | Import-time benchmark scratch script; not part of the library. |

## Requirements

* `ffmpeg` on `PATH`.
* The Qwen3-ASR weights. They are found in this order: `QP_ASR_MODEL` (a folder or a Hugging Face id), a `Qwen3-ASR-0.6B/`
  folder (git-ignored) in the server's working directory or at the repository root, then the public id `Qwen/Qwen3-ASR-0.6B`,
  which is downloaded into the Hugging Face cache on first use (network needed). To fetch them once yourself:
  `hf download Qwen/Qwen3-ASR-0.6B --local-dir Qwen3-ASR-0.6B` (add `HF_HUB_DISABLE_XET=1` if the download stalls).
  The resolver is `qp_voice/asr_model.py`; a failed load now says which folders were checked.

The model resolver and the load-error path are tested (`tests/test_asr_model.py`); the API tests stub `get_tts` / `get_stt`.
