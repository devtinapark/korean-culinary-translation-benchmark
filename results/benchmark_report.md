# LLM Translation & Schema-Validation Benchmark

## Korean Culinary ASR Transcripts — EN / KO × Clean / Noisy

### Configuration

- **Dataset**: Korean Culinary ASR Transcripts
- **Scenarios**: 8
- **Models Tested**: 3
- **Note**: Composite score is min-max normalized across this run — relative, not absolute

## Summary

Evaluates LLM translation quality on unstructured ASR text from spoken Korean/English recipes.
Each model must extract a structured bilingual recipe, preserve Konglish loanwords verbatim,
and surface hidden culinary intent behind vague spoken instructions.
Run 2: metric inversion bug patched; LLM-as-Judge active (`anthropic/claude-sonnet-4.6`).

## Model Results

### 1. anthropic/claude-sonnet-4.6

**Combined metrics (all 8 scenarios):**

| Metric | Value |
|--------|-------|
| Composite Score (absolute) | 0.9514 |
| Schema Validity / Completeness | 0.9945 |
| Cultural Subtlety Score (Judge, 1–5) | 4.875 |
| Loanword Preservation | 0.8854 |

**Noise impact on schema validity:**

| | Avg Schema Validity |
|---|---------------------|
| Clean scenarios | 1.0000 |
| Noisy scenarios | 0.9889 |
| Delta (Δ) | -0.0111 |

**Per-scenario breakdown:**

| Scenario | Schema Validity | Loanword Pres. |
|----------|----------------|----------------|
| en-a-clean | 1.0000 | 0.8155 |
| en-a-noise | 0.9808 | 0.7767 |
| en-b-clean | 1.0000 | 0.7368 |
| en-b-noise | 1.0000 | 0.7544 |
| ko-a-clean | 1.0000 | 1.0000 |
| ko-a-noise | 0.9750 | 1.0000 |
| ko-b-clean | 1.0000 | 1.0000 |
| ko-b-noise | 1.0000 | 1.0000 |

**Loanword register (EN scenarios):** Claude consistently used `세서미 오일` (Korean-script
Konglish form) while Gemini and Qwen used English "sesame oil". Both are valid — `참기름`
is the more common traditional Korean term, but `세서미 오일` is an accepted Konglish form
in modern Korean cooking. Claude's commitment to Korean-script form even on EN-source
scenarios is the more interesting behavioral finding here.

---

### 2. google/gemini-2.5-pro

**Combined metrics (all 8 scenarios):**

| Metric | Value |
|--------|-------|
| Composite Score (absolute) | 0.8918 |
| Schema Validity / Completeness | 0.9341 |
| Cultural Subtlety Score (Judge, 1–5) | 4.250 |
| Loanword Preservation | 0.8733 |

**Noise impact on schema validity:**

| | Avg Schema Validity |
|---|---------------------|
| Clean scenarios | 0.9206 |
| Noisy scenarios | 0.9477 |
| Delta (Δ) | +0.0271 |

**Per-scenario breakdown:**

| Scenario | Schema Validity | Loanword Pres. |
|----------|----------------|----------------|
| en-a-clean | 0.9623 | 0.8447 |
| en-a-noise | 0.9565 | 0.7379 |
| en-b-clean | 0.8182 | 0.7193 |
| en-b-noise | 0.8864 | 0.6842 |
| ko-a-clean | 0.9750 | 1.0000 |
| ko-a-noise | 0.9722 | 1.0000 |
| ko-b-clean | 0.9268 | 1.0000 |
| ko-b-noise | 0.9756 | 1.0000 |

---

### 3. qwen/qwen3-max-thinking

**Combined metrics (all 8 scenarios):**

| Metric | Value |
|--------|-------|
| Composite Score (absolute) | 0.8743 |
| Schema Validity / Completeness | 0.9340 |
| Cultural Subtlety Score (Judge, 1–5) | 4.250 |
| Loanword Preservation | 0.8233 |

**Noise impact on schema validity:**

| | Avg Schema Validity |
|---|---------------------|
| Clean scenarios | 0.9178 |
| Noisy scenarios | 0.9502 |
| Delta (Δ) | +0.0324 |

**Per-scenario breakdown:**

| Scenario | Schema Validity | Loanword Pres. |
|----------|----------------|----------------|
| en-a-clean | 0.8222 | 0.7087 |
| en-a-noise | 0.8667 | 0.6408 |
| en-b-clean | 0.8723 | 0.5965 |
| en-b-noise | 0.9574 | 0.6404 |
| ko-a-clean | 0.9767 | 1.0000 |
| ko-a-noise | 0.9767 | 1.0000 |
| ko-b-clean | 1.0000 | 1.0000 |
| ko-b-noise | 1.0000 | 1.0000 |


---

## Full Rankings

| Rank | Model | Absolute Score | Schema Validity | Cultural (1–5) | Loanword Pres. |
|------|-------|---------------|----------------|---------------|----------------|
| 1 | anthropic/claude-sonnet-4.6 | 0.9514 | 0.9945 | 4.88 | 0.8854 |
| 2 | google/gemini-2.5-pro | 0.8918 | 0.9341 | 4.25 | 0.8733 |
| 3 | qwen/qwen3-max-thinking | 0.8743 | 0.9340 | 4.25 | 0.8233 |

## Metrics Explanation

### Primary Metrics

- **Schema Validity / Completeness**: fraction of `BilingualRecipe` fields populated
  - is_valid = True requires ≥1 ingredient and ≥1 step
  - completeness counts optional fields (quantity, notes, hidden_intent, cultural_notes)
  - Higher is better

- **Loanword Preservation**: fraction of input Konglish terms retained in any output field
  - Checks `loanwords_detected`, ingredient notes, step text, cultural_notes
  - 1.0 when input has no detectable loanwords
  - Higher is better

- **Cultural Subtlety Score (LLM-as-Judge)**: 1–5 scale scored by a judge LLM
  - 5 = all loanwords retained, hidden intent surfaced, cultural notes meaningful
  - Judge model: `anthropic/claude-sonnet-4.6` (set via `judge_model` in `config.yaml`)
  - Higher is better

### Composite Score

Weighted combination — min-max normalized (scores are relative within this run):
- Schema validity: 40%
- Loanword preservation: 35%
- Cultural subtlety (judge): 25%

*Latency tracked but excluded from ranking — measures API speed, not translation quality.*
