# Korean/English Kitchen ASR Benchmark

Compares **OpenAI gpt-4o-transcribe vs Deepgram Nova-3** on real kitchen audio — English, Korean, and code-switched speech, clean and noisy. Built to pick the right ASR model for [Spoken Kitchen](https://spoken.kitchen), a bilingual app that helps immigrant families preserve heirloom recipes passed down through voice.

No large dataset downloads. Runs on your own audio files.

**[View live benchmark report →](https://devtinapark.github.io/korean-asr-benchmark)**

---

## Results

| Model                   | CER        | WER        | Avg latency | Cost/min    |
| ----------------------- | ---------- | ---------- | ----------- | ----------- |
| openai-gpt4o-transcribe | **0.0528** | **0.1135** | 4.01s       | $0.0060     |
| deepgram-nova-3         | 0.0773     | 0.1784     | **1.97s**   | **$0.0052** |

**Noise robustness** (CER degradation clean → noisy):

| Model                   | Clean CER | Noisy CER | Δ       |
| ----------------------- | --------- | --------- | ------- |
| openai-gpt4o-transcribe | 0.0440    | 0.0660    | +0.0221 |
| deepgram-nova-3         | 0.0633    | 0.0969    | +0.0336 |

GPT-4o-transcribe wins on accuracy, especially on noisy Korean. Nova-3 wins on latency and cost. Both handle code-switched terms like 미역국 and 간 맞추기 inside English sentences near-perfectly.

---

## Why these two models

Both auto-detect language and handle code-switching within a single clip — no language hint required. For audio that shifts between English and Korean mid-sentence, that was non-negotiable.

| Model               | Provider     | Why                                                                                          |
| ------------------- | ------------ | -------------------------------------------------------------------------------------------- |
| `gpt-4o-transcribe` | OpenAI API   | Latest transcription model; auto-detects language; strong on Korean + English code-switching |
| `nova-3`            | Deepgram API | `detect_language=true`; ~2× faster latency; 13% cheaper at multilingual rate                 |

---

## Quick start

### 1. Install dependencies

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
brew install ffmpeg  # required for MP3 support
```

### 2. Add your audio

Place files in `kitchen_samples/audio/` and fill in `kitchen_samples/metadata.json`:

```json
[
  {
    "id": "001",
    "audio_file": "001_boil_water.MP3",
    "transcript": "물이 끓고 있어요. 불 좀 줄여줘.",
    "language": "ko",
    "noise": false
  },
  {
    "id": "001-noise",
    "audio_file": "001_boil_water_kitchen.MP3",
    "transcript": "물이 끓고 있어요. 불 좀 줄여줘.",
    "language": "ko",
    "noise": true
  }
]
```

Supported formats: `.wav`, `.mp3`, `.flac`, `.m4a`

### 3. Set API keys

```bash
export OPENAI_API_KEY=your_key      # platform.openai.com
export DEEPGRAM_API_KEY=your_key    # console.deepgram.com
```

### 4. Run

```bash
python -m src.main                                 # both models
python -m src.main --model openai-gpt4o-transcribe # single model
python -m src.main --model deepgram-nova-3
python -m src.main --list-models                   # list configured models
```

---

## Output

```
results/
├── benchmark_report.html   # open in browser
├── benchmark_report.md
├── results.csv
├── results.json
└── predictions/
    ├── openai-gpt4o-transcribe_predictions.csv
    └── deepgram-nova-3_predictions.csv
```

---

## Metrics

| Metric                   | What it measures                                         | Primary use         |
| ------------------------ | -------------------------------------------------------- | ------------------- |
| **CER**                  | Character Error Rate — spaces stripped before comparison | Korean (primary)    |
| **WER**                  | Word Error Rate                                          | English (secondary) |
| **Code-switch accuracy** | Korean terms in English sentences and vice versa         | Both                |
| **Noise delta**          | CER increase from clean → noisy clips                    | Robustness          |
| **Latency**              | API response time per clip (excludes rate-limit pauses)  | Production fit      |
| **Cost**                 | Audio duration × price/min                               | Budget planning     |

Composite score: CER 55% + WER 30% + Code-switch accuracy 15%. Latency excluded from quality score.

> **Korean CER note:** Spaces are stripped before computing CER since Korean spacing (띄어쓰기) is inconsistent across models and human transcribers. Follows KsponSpeech evaluation convention.

---

## Pricing (as of 2026-06)

| Model                          | Price/min | Free tier          |
| ------------------------------ | --------- | ------------------ |
| OpenAI gpt-4o-transcribe       | $0.006    | $5 new user credit |
| Deepgram Nova-3 (multilingual) | $0.0052   | $200 credit        |

> Deepgram's $0.0052/min is the multilingual pre-recorded rate. English-only is $0.0043/min. Use the multilingual rate if you're running `detect_language=true` on mixed-language audio.

---

## Tips for recording your own clips

- **Length:** 5–20 seconds per clip
- **Pairs:** record the same content clean + noisy to measure noise robustness
- **Content:** mix Korean, English, and code-switched phrases
- **Mark noisy clips:** set `"noise": true` in metadata.json — the report uses this for noise impact analysis

---

## References

- **KsponSpeech** — Ko et al., 2020. Korean spontaneous speech corpus. [MDPI Applied Sciences](https://www.mdpi.com/2076-3417/10/19/6936)
- **OpenAI Whisper paper** — Radford et al., 2022. Per-language CER baselines. [arxiv.org/abs/2212.04356](https://arxiv.org/abs/2212.04356)
- **HuggingFace Open ASR Leaderboard** — [huggingface.co/spaces/hf-audio/open_asr_leaderboard](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard)

---

## Contributing

PRs welcome — additional audio clips (CC0 licensed), new model wrappers, results from other languages.

## License

MIT
