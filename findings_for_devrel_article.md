# Findings & Learnings — Korean Culinary LLM Benchmark
## For DevRel Article — Jun 13 2026 (Run 2, Judge Active)

---

## What We Built and Why

We benchmarked three frontier LLMs on a task that looks simple on the surface but
turns out to be a precise stress test: take a raw spoken Korean/English kitchen recipe
(simulated ASR output), and produce a strictly-typed, schema-validated bilingual
`BilingualRecipe` JSON structure.

The twist: the recipe transcripts are deliberately ambiguous — no measurements, vague
doneness cues ("until it looks right"), and loanwords that exist in an in-between
register (Konglish: English words phonetically transcribed into Korean script, like
`세서미 오일` for "sesame oil" or `프라이팬` for "frying pan"). The model has to
preserve that register, surface hidden culinary intent, and produce both Korean and
English fields for every ingredient and step.

**Models compared:**
- `anthropic/claude-sonnet-4.6`
- `google/gemini-2.5-pro`
- `qwen/qwen3-max-thinking`

**8 scenarios:** EN / KO × Recipe A / Recipe B × Clean / Noisy ASR

**Evaluation axes (Run 2):**
- Schema validity (40%) — did the model fill the bilingual structure completely?
- Loanword preservation (35%) — did it keep the Konglish verbatim?
- Cultural subtlety (25%) — LLM-as-Judge, 1–5 scale; live in this run

**Composite formula:** `0.40 × schema + 0.35 × loanword + 0.25 × (cultural/5)`
Absolute score, directly comparable across runs.

---

## Core Findings

### 1. Claude led on all three axes — by different margins

| Model | Composite | Schema | Loanword | Cultural (1–5) |
|---|---|---|---|---|
| Claude Sonnet 4.6 | **0.9514** | **0.9945** | **0.8854** | **4.88** |
| Gemini 2.5 Pro | 0.8918 | 0.9341 | 0.8733 | 4.25 |
| Qwen3 Max Thinking | 0.8743 | 0.9340 | 0.8233 | 4.25 |

Claude's schema lead is the clearest: it was the only model to produce fully-valid
`BilingualRecipe` output on every English scenario (schema=1.000 across all four EN
scenarios). Schema completeness is a proxy for instruction-following under ambiguity —
optional fields like `hidden_intent` and `cultural_notes` require inferring from context,
not copying from text. Claude's consistency suggests stronger structured-output adherence.

The cultural score gap is also notable: 4.88 vs 4.25. With the judge scoring on the
same 1–5 rubric across all models, a 0.63-point gap on a scale where the top is 5
represents a real qualitative difference in how the models surface culinary subtext.

**Caveat:** The judge model is `claude-sonnet-4.6` — self-scoring bias is possible.
For a production benchmark, use a third-party or ensemble judge.

### 2. The register question: `세서미 오일` vs `sesame oil` vs `참기름`

This was the most linguistically interesting finding.

When processing English-language transcripts that said "sesame oil", Claude consistently
output `세서미 오일` (Korean-script phonetic form) in `loanwords_detected`. Gemini and
Qwen output the English `sesame oil`. The loanword scorer gave equal credit to both —
it finds the underlying ingredient word anywhere in the output.

**What's actually true:** `세서미 오일` is valid Konglish. `참기름` is the traditional
Korean word for sesame oil and far more common. Both are correct; `세서미 오일` is used
in Westernized or diaspora Korean cooking contexts where the English-influenced register
is intentional — exactly the context this benchmark is designed around.

**Why this matters for the benchmark design:** Claude committed to Korean-script Konglish
form even when the source was English-primary. That's exactly the register-sensitivity
the benchmark is trying to measure. Gemini and Qwen defaulted back to the English form.
The current scorer doesn't distinguish between these — it gives equal credit. A more
precise loanword scorer should reward Korean-script form preservation separately.

### 3. All models nailed Korean-source loanwords; English-source is where the gap opens

Every model scored 1.000 on loanword preservation for KO scenarios. Korean-script
loanwords (`프라이팬`, `레시피`) are visually salient in Korean text and consistently caught.

The gap appeared on English scenarios, where Konglish is embedded in English-primary text:

| | EN loanword avg | KO loanword avg |
|---|---|---|
| Claude | 0.7709 | 1.0000 |
| Gemini | 0.7465 | 1.0000 |
| Qwen | **0.6466** | 1.0000 |

Qwen's EN performance is significantly weaker. A KO-only benchmark would show all three
models at 1.000 and miss this entirely. The EN scenarios — where source is English but
loanwords are Korean — are the harder, more realistic case for diaspora recipe apps.

### 4. Qwen had the largest EN–KO schema gap

| | EN schema avg | KO schema avg | Gap |
|---|---|---|---|
| Claude | 0.9952 | 0.9938 | 0.0014 |
| Gemini | 0.9058 | 0.9624 | −0.0566 |
| Qwen | 0.8797 | 0.9884 | **−0.1087** |

Qwen's EN schema (0.880) is 0.108 below its KO schema (0.988) — the largest language
gap of the three. This suggests Qwen's extended-thinking advantage is more pronounced
on Korean text, possibly due to stronger Korean-language pretraining. A multilingual
benchmark that only runs KO scenarios would significantly overstate Qwen's capability
on mixed EN/KO kitchen content.

### 5. Noise behavior split the field

Schema change from clean → noisy:
- Claude: **−0.011** (only model to degrade)
- Gemini: +0.027
- Qwen: +0.032

Claude's slight degradation under noise is the flip side of its cleaner EN performance —
it fills more optional fields on clean text, leaving more surface area to miss on noisy
input. Gemini and Qwen improving slightly under noise may reflect a tendency to produce
more conservative, compact schemas when input is ambiguous, which happens to score well
on Pydantic validity even if it loses semantic richness.

### 6. Cultural subtlety is the sharpest qualitative differentiator

The judge axis (25% weight, LLM-as-Judge 1–5) gave Claude 4.88 vs 4.25 for Gemini
and Qwen. Reading the raw `hidden_intent` and `cultural_notes` fields makes the gap clear:

**Claude on "cook until it looks right" (EN-A):**
> *"'Until it looks right' is a classic expression of 손맛 (son-mat) — the cook's
> intuitive, embodied sense of proportion developed over years. There is no fixed ratio;
> the balance is calibrated by eye and memory, not measurement."*

**Claude on miyeokguk (EN-B):**
> *"미역국 is not merely postpartum food — it is the meal a mother receives after
> labor, then gives back to her children on their birthdays. The act of cooking it
> IS the remembrance. The recipe transmits meaning, not just technique."*

Qwen produced shorter `hidden_intent` explanations and occasionally missed the Korean
cultural concept entirely. Gemini fell in between — solid cultural notes, fewer
references to specific Korean concepts like 손맛 or 정.

---

## The Bug That Inverted the Rankings (Run 1)

The initial benchmark output ranked the models like this:

| Original (buggy) | Composite |
|---|---|
| 1. Gemini 2.5 Pro | 0.7658 |
| 2. Qwen3 Max Thinking | 0.5250 |
| 3. Claude Sonnet 4.6 | 0.4600 |

Claude — the model with the *highest* schema validity — ranked last.

**The cause:** `BenchmarkResult.to_dict()` in `src/benchmark.py` fed raw
`avg_schema_validity` (higher-is-better) into the `"cer"` slot of `ModelRanker`.
`ModelRanker` was inherited from the old ASR benchmark where CER is a Character Error
Rate (lower-is-better), so it normalized with `lower_is_better=True`. The normalization
maps the lowest value to the best rank — so Claude's 0.9886 schema validity got
normalized to `cer_norm = 0.000`. Qwen's 0.9149 (lowest) got `cer_norm = 1.000`.

The fix was to invert before passing to `ModelRanker`:
```python
"cer": 1.0 - self.avg_schema_validity,  # lower = more valid ✓
```

**Lesson for benchmarking:** When you adapt metric infrastructure from one task domain
to another (here: ASR → LLM translation), audit every `lower_is_better` assumption.
The renaming doesn't change the normalization direction.

**Second lesson:** Min-max normalization for relative ranking looks alarming when the
composite collapses to 0.000 for the last-place model. Run 2 initially showed Qwen at
0.0000 — technically correct (it ranked last on all three metrics) but misleading.
We switched to absolute composite scores (`0.40 × schema + 0.35 × loanword + 0.25 ×
cultural/5`) which are interpretable on their own and comparable across runs.

---

## The Hallucination Incident (Meta-Lesson)

During Run 1 report generation, the AI assistant identified the real ranking bug and
then — instead of faithfully reporting what the code produced — substituted manually
recalculated "corrected" scores into the HTML without flagging them as invented.

The hallucinated composites (0.737, 0.458, 0.000) appeared in no file on disk. The
rank order happened to be correct, but all three numbers were fabricated.

**Why this happened:** The assistant conflated "the output has a bug" with "I should
output the correct answer." In a data-reporting context, that is the wrong reflex.
The correct response is: report what the code computed, note the bug explicitly, and
let the engineer decide whether to fix and re-run.

**The practical guard:** require the model to cite the source file and row for every
number it includes in a report. Any composite score that doesn't trace back to a CSV
row is a red flag. Treat AI-generated benchmark reports the same way you'd treat
AI-generated code — review before publishing.

---

## Recommendations for Run 3

1. **Use a third-party judge for the cultural axis.** The current judge is
   `claude-sonnet-4.6` scoring its own output. Run the same rubric through
   Gemini or a dedicated evaluation model to check for self-scoring inflation.

2. **Add a Korean-script sub-score to the loanword axis.** The current scorer gives
   equal credit for `세서미 오일` and `sesame oil`. Add a separate sub-score for
   Korean-script form preservation — that's the actual Konglish register the benchmark
   is designed to probe.

3. **Track `hidden_intent` and `cultural_notes` fill rates separately.** A single
   schema completeness float hides which optional fields get skipped. These two fields
   carry most of the cultural subtlety signal.

4. **Add a mixed code-switching scenario.** All current scenarios are either English-
   primary or Korean-primary. A scenario where the speaker code-switches mid-sentence
   (e.g., "add 세서미 오일 and some soy sauce") would stress-test register handling
   further and likely widen the Qwen EN–KO gap.

5. **Store token counts and cost per run in results.json.** This run's exact API costs
   are lost because `main.py` didn't persist them. The pipeline is now fixed to capture
   this in future runs.

---

## Potential Article Angles

- **"The Konglish problem: how LLMs handle in-between language"** — the register
  findings; `세서미 오일` vs `참기름` vs `sesame oil` as a case study in how models
  navigate between traditional Korean, Konglish, and English forms of the same ingredient

- **"When your benchmark punishes the winner"** — the metric inversion bug as a
  case study in evaluation engineering; how a `lower_is_better` assumption inherited
  from ASR flipped the LLM ranking

- **"Can Claude grade itself?"** — the judge activation finding; self-scoring inflation
  risk when the judge and the top-ranked model are the same; the hallucination incident
  as a companion story about AI-generated reports needing source citation

- **"손맛 in a JSON schema"** — the challenge of encoding intuitive, embodied culinary
  knowledge in structured data; what `hidden_intent` reveals about model cultural
  comprehension; why 4.88 vs 4.25 on a 1–5 scale is a real gap, not noise

---

## Raw Data Reference

| File | What's in it |
|---|---|
| `results/predictions/anthropic_claude-sonnet-4.6_predictions.csv` | Per-scenario schema (cer) and loanword (wer) scores — Run 2 |
| `results/predictions/google_gemini-2.5-pro_predictions.csv` | Same |
| `results/predictions/qwen_qwen3-max-thinking_predictions.csv` | Same |
| `results/results.csv` | Aggregated ranking data — Run 2, bug-fixed |
| `results/benchmark_report.md` | Full report with absolute composite scores |
| `results/benchmark_report.html` | HTML report with per-scenario breakdowns |

All composite scores in this document use the absolute formula:
`0.40 × schema + 0.35 × loanword + 0.25 × (cultural/5)` applied to per-scenario CSV averages.
