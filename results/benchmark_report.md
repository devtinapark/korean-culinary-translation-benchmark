# LLM Translation & Schema-Validation Benchmark

## Korean Culinary ASR Transcripts — EN / KO × Clean / Noisy

### Configuration

- **Dataset**: Korean Culinary ASR Transcripts
- **Scenarios**: 8
- **Models Tested**: 3
- **Note**: Composite score is relative — run all models to get meaningful rankings

## Summary

Evaluates LLM translation quality on unstructured ASR text from spoken Korean/English recipes.
Each model must extract a structured bilingual recipe, preserve Konglish loanwords verbatim,
and surface hidden culinary intent behind vague spoken instructions.

## Model Results

### 1. google/gemini-2.5-pro

**Combined metrics (all 8 scenarios):**

| Metric | Value |
|--------|-------|
| Composite Score | 0.7658 |
| Schema Validity / Completeness | 0.9350 |
| Cultural Subtlety Score (Judge) | 0.0000 |
| Loanword Preservation | 0.8882 |

**Noise impact on schema validity:**

| | Avg Schema Validity |
|---|---------------------|
| Clean scenarios | 0.9411 |
| Noisy scenarios | 0.9290 |
| Delta (Δ) | -0.0122 |

**Per-scenario breakdown:**

| Scenario | Schema Validity | Loanword Pres. |
|----------|----------------|----------------|
| en-a-clean | 0.9592 | 0.8252 |
| en-a-noise | 0.9565 | 0.8155 |
| en-b-clean | 0.8864 | 0.7281 |
| en-b-noise | 0.8636 | 0.7368 |
| ko-a-clean | 1.0000 | 1.0000 |
| ko-a-noise | 0.9767 | 1.0000 |
| ko-b-clean | 0.9189 | 1.0000 |
| ko-b-noise | 0.9189 | 1.0000 |

### 2. qwen/qwen3-max-thinking

**Combined metrics (all 8 scenarios):**

| Metric | Value |
|--------|-------|
| Composite Score | 0.5250 |
| Schema Validity / Completeness | 0.9149 |
| Cultural Subtlety Score (Judge) | 0.0000 |
| Loanword Preservation | 0.8352 |

**Noise impact on schema validity:**

| | Avg Schema Validity |
|---|---------------------|
| Clean scenarios | 0.9120 |
| Noisy scenarios | 0.9178 |
| Delta (Δ) | +0.0058 |

**Per-scenario breakdown:**

| Scenario | Schema Validity | Loanword Pres. |
|----------|----------------|----------------|
| en-a-clean | 0.8222 | 0.7282 |
| en-a-noise | 0.8222 | 0.6990 |
| en-b-clean | 0.8723 | 0.6491 |
| en-b-noise | 0.8723 | 0.6053 |
| ko-a-clean | 0.9535 | 1.0000 |
| ko-a-noise | 0.9767 | 1.0000 |
| ko-b-clean | 1.0000 | 1.0000 |
| ko-b-noise | 1.0000 | 1.0000 |

## Full Rankings

| Rank | Model | Score | Schema Validity | Cultural Score | Loanword Pres. |
|------|-------|-------|----------------|---------------|----------------|
| 1 | google/gemini-2.5-pro | 0.7658 | 0.9350 | 0.0000 | 0.8882 |
| 2 | qwen/qwen3-max-thinking | 0.5250 | 0.9149 | 0.0000 | 0.8352 |
| 3 | anthropic/claude-sonnet-4.6 | 0.4600 | 0.9886 | 0.0000 | 0.8859 |

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
  - 0 = judge stub not yet activated
  - Higher is better

### Composite Score

Weighted combination (scores are relative — run all models for meaningful rankings):
- Schema validity: 40%
- Loanword preservation: 35%
- Cultural subtlety (judge): 25%

*Latency tracked but excluded from ranking — measures API speed, not translation quality.*
