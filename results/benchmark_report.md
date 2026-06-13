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

### 1. anthropic/claude-sonnet-4.6

**Combined metrics (all 8 scenarios):**

| Metric | Value |
|--------|-------|
| Composite Score | 1.0000 |
| Schema Validity / Completeness | 0.0055 |
| Cultural Subtlety Score (Judge) | 0.0250 |
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

### 2. google/gemini-2.5-pro

**Combined metrics (all 8 scenarios):**

| Metric | Value |
|--------|-------|
| Composite Score | 0.2821 |
| Schema Validity / Completeness | 0.0659 |
| Cultural Subtlety Score (Judge) | 0.1500 |
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

## Full Rankings

| Rank | Model | Score | Schema Validity | Cultural Score | Loanword Pres. |
|------|-------|-------|----------------|---------------|----------------|
| 1 | anthropic/claude-sonnet-4.6 | 1.0000 | 0.0055 | 0.0250 | 0.8854 |
| 2 | google/gemini-2.5-pro | 0.2821 | 0.0659 | 0.1500 | 0.8733 |
| 3 | qwen/qwen3-max-thinking | 0.0000 | 0.0660 | 0.1500 | 0.8233 |

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
