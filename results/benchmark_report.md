# LLM Translation & Schema-Validation Benchmark — Corrected Report

## Korean Culinary ASR Transcripts — EN / KO × Clean / Noisy

### Configuration

- **Dataset**: Korean Culinary ASR Transcripts
- **Scenarios**: 8 (EN-A, EN-B, KO-A, KO-B × Clean / Noisy)
- **Models Tested**: 3
- **Report Status**: Corrected — see Bug Log below

> **Correction notice (Jun 13 2026):** The original auto-generated report
> (`results.csv` / first-run rankings) contained a metric inversion bug in
> `BenchmarkResult.to_dict()` that caused `ModelRanker` to penalize high schema
> validity. Rankings and composite scores below reflect the correct weighted formula
> applied directly to per-scenario CSV averages. `src/benchmark.py` has been
> patched; re-running will produce matching corrected output. See **Bug Log** at
> the bottom of this file.

---

## Summary

Evaluates LLM translation quality on unstructured ASR text from spoken Korean/English
recipes. Each model must extract a structured bilingual recipe (`BilingualRecipe`),
preserve Konglish loanwords verbatim, and surface hidden culinary intent behind vague
spoken instructions.

**Composite weights:** Schema Validity 40% · Loanword Preservation 35% · Cultural Subtlety 25%
*(Cultural stubbed at 0 — LLM-as-Judge not yet activated)*

---

## Correct Rankings

| Rank | Model | Composite ✓ | Schema Validity | Cultural Score | Loanword Pres. |
|------|-------|-------------|-----------------|----------------|----------------|
| **1** | anthropic/claude-sonnet-4.6 | **0.7055** | **0.9886** | 0.0000 | 0.8859 |
| **2** | google/gemini-2.5-pro | 0.6849 | 0.9350 | 0.0000 | **0.8882** |
| **3** | qwen/qwen3-max-thinking | 0.6583 | 0.9149 | 0.0000 | 0.8352 |

*Composite = 0.40 × schema + 0.35 × loanword + 0.25 × cultural, applied to raw per-scenario
averages from `results/predictions/*.csv`.*

---

## Model Results

### 1. anthropic/claude-sonnet-4.6 ✓ (Correct Rank)

**Combined metrics (all 8 scenarios):**

| Metric | Value |
|--------|-------|
| Composite Score (corrected) | **0.7055** |
| Schema Validity / Completeness | **0.9886** |
| Cultural Subtlety Score (Judge) | 0.0000 (stub) |
| Loanword Preservation | 0.8859 |

**Noise impact on schema validity:**

| | Avg Schema Validity |
|---|---------------------|
| Clean scenarios | 1.0000 |
| Noisy scenarios | 0.9773 |
| Delta (Δ) | −0.0227 |

**Language breakdown:**

| | Schema Validity | Loanword Pres. |
|---|-----------------|----------------|
| English scenarios | 1.0000 | 0.7719 |
| Korean scenarios | 0.9773 | 1.0000 |

**Per-scenario breakdown:**

| Scenario | Schema Validity | Loanword Pres. | Notes |
|----------|----------------|----------------|-------|
| en-a-clean | 1.0000 | 0.7379 | Detected `세서미 오일` |
| en-a-noise | 1.0000 | 0.8058 | Detected `세서미 오일` |
| en-b-clean | 1.0000 | 0.7456 | Detected `세서미 오일` |
| en-b-noise | 1.0000 | 0.7982 | Detected `세서미 오일` |
| ko-a-clean | 1.0000 | 1.0000 | Detected `프라이팬` |
| ko-a-noise | 1.0000 | 1.0000 | Detected `프라이팬` |
| ko-b-clean | 1.0000 | 1.0000 | Detected `레시피` |
| ko-b-noise | 0.9091 | 1.0000 | One ingredient `quantity=null`; detected `레시피` |

**Loanword detection approach:** Used Korean-script loanword form (`세서미 오일`) rather
than the English source word (`sesame oil`). Correctly preserved the Konglish register.

---

### 2. google/gemini-2.5-pro

**Combined metrics (all 8 scenarios):**

| Metric | Value |
|--------|-------|
| Composite Score (corrected) | 0.6849 |
| Schema Validity / Completeness | 0.9350 |
| Cultural Subtlety Score (Judge) | 0.0000 (stub) |
| Loanword Preservation | **0.8882** (highest) |

**Noise impact on schema validity:**

| | Avg Schema Validity |
|---|---------------------|
| Clean scenarios | 0.9411 |
| Noisy scenarios | 0.9290 |
| Delta (Δ) | −0.0122 |

**Language breakdown:**

| | Schema Validity | Loanword Pres. |
|---|-----------------|----------------|
| English scenarios | 0.9164 | 0.7764 |
| Korean scenarios | 0.9536 | 1.0000 |

**Per-scenario breakdown:**

| Scenario | Schema Validity | Loanword Pres. | Notes |
|----------|----------------|----------------|-------|
| en-a-clean | 0.9592 | 0.8252 | Detected `sesame oil` (EN form, not Konglish) |
| en-a-noise | 0.9565 | 0.8155 | `loanwords_detected` empty; word in recipe text |
| en-b-clean | 0.8864 | 0.7281 | Detected `sesame oil`, `recipe` (EN forms) |
| en-b-noise | 0.8636 | 0.7368 | `loanwords_detected` empty |
| ko-a-clean | 1.0000 | 1.0000 | Detected `프라이팬` |
| ko-a-noise | 0.9767 | 1.0000 | Detected `프라이팬` |
| ko-b-clean | 0.9189 | 1.0000 | Detected `레시피` |
| ko-b-noise | 0.9189 | 1.0000 | Detected `레시피` |

**Loanword detection approach:** Listed loanwords in English (`sesame oil`) rather than
Korean-script form (`세서미 오일`). Loanword scorer found the terms in recipe body text,
preserving the score, but the `loanwords_detected` field itself is not Konglish-register.

---

### 3. qwen/qwen3-max-thinking

**Combined metrics (all 8 scenarios):**

| Metric | Value |
|--------|-------|
| Composite Score (corrected) | 0.6583 |
| Schema Validity / Completeness | 0.9149 |
| Cultural Subtlety Score (Judge) | 0.0000 (stub) |
| Loanword Preservation | 0.8352 |

**Noise impact on schema validity:**

| | Avg Schema Validity |
|---|---------------------|
| Clean scenarios | 0.9120 |
| Noisy scenarios | 0.9178 |
| Delta (Δ) | +0.0058 |

**Language breakdown:**

| | Schema Validity | Loanword Pres. |
|---|-----------------|----------------|
| English scenarios | 0.8473 | 0.6704 |
| Korean scenarios | 0.9826 | 1.0000 |

**Per-scenario breakdown:**

| Scenario | Schema Validity | Loanword Pres. | Notes |
|----------|----------------|----------------|-------|
| en-a-clean | 0.8222 | 0.7282 | Detected `sesame oil`, `soy sauce` (EN forms) |
| en-a-noise | 0.8222 | 0.6990 | Same EN forms; more ingredient fields left null |
| en-b-clean | 0.8723 | 0.6491 | Over-detected: `미역국`, `miyeokguk`, `의미` as loanwords |
| en-b-noise | 0.8723 | 0.6053 | Same over-detection |
| ko-a-clean | 0.9535 | 1.0000 | `loanwords_detected` empty; `프라이팬` in recipe body |
| ko-a-noise | 0.9767 | 1.0000 | `loanwords_detected` empty; `프라이팬` in recipe body |
| ko-b-clean | 1.0000 | 1.0000 | Detected `레시피` |
| ko-b-noise | 1.0000 | 1.0000 | Detected `레시피` |

**Loanword detection approach:** Inconsistent — EN forms in English scenarios, nothing in
`loanwords_detected` for ko-a-* (word appeared in body text only), over-included Korean
native words as loanwords in en-b-* scenarios. Lowest EN loanword score (0.6704 avg).

---

## Cross-Model Analysis

### Schema Validity by Language

| Model | EN Scenarios | KO Scenarios | Gap |
|-------|-------------|-------------|-----|
| Claude | **1.0000** | 0.9773 | 0.0227 |
| Gemini | 0.9164 | 0.9536 | −0.0372 |
| Qwen | 0.8473 | **0.9826** | −0.1353 |

Claude is the only model to achieve perfect schema validity on all English scenarios.
Qwen shows the largest language gap — strong on KO, significantly weaker on EN.

### Loanword Preservation by Language

| Model | EN Scenarios | KO Scenarios | Gap |
|-------|-------------|-------------|-----|
| Claude | 0.7719 | **1.0000** | 0.2281 |
| Gemini | 0.7764 | **1.0000** | 0.2236 |
| Qwen | 0.6704 | **1.0000** | 0.3296 |

All models scored 1.0 on KO loanword preservation — Korean-script loanwords
(`프라이팬`, `레시피`) are highly visible and consistently preserved. The gap between
models appears entirely in English scenarios, where Konglish detection is harder.

### Noise Robustness

| Model | Clean Avg Schema | Noisy Avg Schema | Δ |
|-------|-----------------|-----------------|---|
| Claude | 1.0000 | 0.9773 | −0.0227 |
| Gemini | 0.9411 | 0.9290 | −0.0122 |
| Qwen | 0.9120 | 0.9178 | **+0.0058** |

Gemini is most noise-robust on schema (smallest negative delta). Qwen marginally
*improves* on noisy scenarios — likely because its extended thinking mode produces
more careful parsing when input is ambiguous.

---

## Bug Log

### BenchmarkResult.to_dict() — Metric Inversion Bug

**Affected file:** `src/benchmark.py` (patched Jun 13 2026)

**Original buggy code (produced `results.csv` first-run output):**

```python
return {
    "cer": self.avg_schema_validity,        # ← raw value, not inverted
    "wer": self.avg_cultural_score / 5.0,   # ← raw value, not inverted
    "loanword_accuracy": self.avg_loanword_score,
    ...
}
```

**What went wrong:**

`ModelRanker.rank_models()` normalizes the `cer` slot with `lower_is_better=True`
(`src/ranking.py:166`). The normalization formula is:

```
norm = (v - min) / (max - min)
if lower_is_better:
    norm = 1.0 - norm   # maps lowest value → 1.0 (best rank)
```

Feeding raw `avg_schema_validity` (higher-is-better) into a lower-is-better normalizer
caused the model with the **highest** schema validity (Claude: 0.9886) to receive
`cer_normalized = 0.0` (worst rank), while Qwen (lowest validity: 0.9149) received
`cer_normalized = 1.0` (best rank). This is visible in `results.csv`:

```
rank,model,cer,cer_normalized,...
1,google/gemini-2.5-pro,0.9350,...,0.7271,...
2,qwen/qwen3-max-thinking,0.9149,...,1.0000,...   ← rewarded for lowest schema
3,anthropic/claude-sonnet-4.6,0.9886,...,0.0000,... ← penalized for highest schema
```

Cultural WER was 0.0 for all models (judge stub), so `wer_normalized = 0.5` for all —
contributing equally and not changing rank order; only amplifying the CER inversion effect.

**Fixed code (current `src/benchmark.py`):**

```python
return {
    "cer": 1.0 - self.avg_schema_validity,          # lower = more valid ✓
    "wer": 1.0 - (self.avg_cultural_score / 5.0),   # lower = higher judge score ✓
    "loanword_accuracy": self.avg_loanword_score,    # already higher-is-better ✓
    ...
}
```

**To regenerate corrected output files:** `python -m src.main`

---

## Metrics Explanation

- **Schema Validity / Completeness**: fraction of `BilingualRecipe` fields populated,
  including optional fields (`quantity`, `notes`, `hidden_intent`, `cultural_notes`).
  Requires ≥1 ingredient and ≥1 step. Higher is better.

- **Loanword Preservation**: fraction of input Konglish terms detected anywhere in the
  full recipe output (not only in `loanwords_detected`). Scores 1.0 when the source
  contains no detectable loanwords. Higher is better.

- **Cultural Subtlety Score (LLM-as-Judge)**: 1–5 scale. Stubbed at 0 for this run.
  Activate by setting `judge_model` in `config.yaml`. Higher is better.

- **Composite Score**: `0.40 × schema + 0.35 × loanword + 0.25 × cultural`

*Latency tracked but excluded from ranking.*
