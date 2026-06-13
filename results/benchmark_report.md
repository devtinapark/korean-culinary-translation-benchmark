# Multilingual ASR Benchmark Results

## Kitchen Audio — EN / KO / ES / ZH

### Configuration

- **Dataset**: Kitchen Audio Samples
- **Samples**: 8
- **Models Tested**: 2
- **Note**: Composite score is relative — meaningful only when comparing multiple models

## Summary

Evaluates multilingual ASR models on real kitchen audio clips containing
casual speech, background noise, and code-switched language (Korean + English).
All models must auto-detect language without a language hint.

## Model Results

### 1. openai-gpt4o-transcribe

**Combined metrics (all 8 clips):**

| Metric | Value |
|--------|-------|
| Composite Score | 1.0000 |
| CER (Character Error Rate) | 0.0528 |
| WER (Word Error Rate) | 0.1135 |
| Loanword / Code-switching Accuracy | 0.9742 |
| Audio Duration | 7.88 min |
| Price per Minute | $0.0060 |
| Estimated Cost (this run) | $0.047279 |
| Avg Latency per Clip | 4.01s |
| Total Latency | 32.10s |

**Noise impact:**

| | Avg CER |
|---|---------|
| Clean clips | 0.0440 |
| Noisy clips | 0.0660 |
| Degradation (Δ) | +0.0221 |

**Per-sample breakdown:**

| Sample | CER | WER |
|--------|-----|-----|
| en-a-clean | 0.0401 | 0.0473 |
| en-a-noise | 0.0518 | 0.0878 |
| en-b-clean | 0.0472 | 0.0818 |
| en-b-noise | 0.0572 | 0.1006 |
| ko-a-clean | 0.0548 | 0.2079 |
| ko-a-noise | 0.0651 | 0.1980 |
| ko-b-clean | 0.0337 | 0.0690 |
| ko-b-noise | 0.0899 | 0.1810 |

### 2. deepgram-nova-3

**Combined metrics (all 8 clips):**

| Metric | Value |
|--------|-------|
| Composite Score | 0.0000 |
| CER (Character Error Rate) | 0.0773 |
| WER (Word Error Rate) | 0.1784 |
| Loanword / Code-switching Accuracy | 0.9710 |
| Audio Duration | 7.88 min |
| Price per Minute | $0.0052 |
| Estimated Cost (this run) | $0.040975 |
| Avg Latency per Clip | 1.97s |
| Total Latency | 15.75s |

**Noise impact:**

| | Avg CER |
|---|---------|
| Clean clips | 0.0633 |
| Noisy clips | 0.0969 |
| Degradation (Δ) | +0.0336 |

**Per-sample breakdown:**

| Sample | CER | WER |
|--------|-----|-----|
| en-a-clean | 0.0518 | 0.0676 |
| en-a-noise | 0.0968 | 0.1622 |
| en-b-clean | 0.0730 | 0.1321 |
| en-b-noise | 0.0730 | 0.1195 |
| ko-a-clean | 0.0685 | 0.2376 |
| ko-a-noise | 0.0753 | 0.3168 |
| ko-b-clean | 0.0599 | 0.1638 |
| ko-b-noise | 0.1423 | 0.3276 |

## Full Rankings

| Rank | Model | Composite Score | CER | WER | Loanword Acc | Cost (this run) |
|------|-------|----------------|-----|-----|--------------|-----------------|
| 1 | openai-gpt4o-transcribe | 1.0000 | 0.0528 | 0.1135 | 0.9742 | $0.047279 |
| 2 | deepgram-nova-3 | 0.0000 | 0.0773 | 0.1784 | 0.9710 | $0.033883 |

## Metrics Explanation

### Primary Metrics

- **CER (Character Error Rate)**: Primary metric for Korean due to agglutinative nature
  - Lower is better (0 = perfect, 1 = complete failure)
  - More granular than WER for Korean text

- **WER (Word Error Rate)**: Secondary metric
  - Lower is better
  - Word-level accuracy

- **Loanword / Code-switching Accuracy**: accuracy on English loanwords and mixed-language terms
  - Critical for kitchen context (e.g., 오븐, 레시피, 간 맞추기)
  - Higher is better

### Composite Score

Weighted combination of metrics (scores are relative between models — run all 3 to get meaningful rankings):
- CER: 55% — primary accuracy metric
- WER: 30% — secondary accuracy metric
- Loanword / code-switching accuracy: 15%

*Speed excluded: measures API latency, not model quality.*
*CER/WER ratio excluded: only meaningful for Korean-only models.*
