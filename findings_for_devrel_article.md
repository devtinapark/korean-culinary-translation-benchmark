# Findings & Learnings — Korean Culinary LLM Benchmark
## For DevRel Article — Jun 13 2026

---

## What We Built and Why

We benchmarked three frontier LLMs on a task that looks simple on the surface but
turns out to be a precise stress test: take a raw spoken Korean/English kitchen recipe
(simulated ASR output), and produce a strictly-typed, schema-validated bilingual
`BilingualRecipe` JSON structure.

The twist: the recipe transcripts are deliberately ambiguous — no measurements, vague
doneness cues ("until it looks right"), and loanwords that exist in an in-between
register (Konglish: English words phonetically transcribed into Korean script, like
`세서미 오일` for "sesame oil"). The model has to preserve that register, not translate
it away.

**Models compared:**
- `anthropic/claude-sonnet-4.6`
- `google/gemini-2.5-pro`
- `qwen/qwen3-max-thinking`

**8 scenarios:** EN / KO × Recipe A / Recipe B × Clean / Noisy ASR

**Evaluation axes:**
- Schema validity (40%) — did the model fill the structure?
- Loanword preservation (35%) — did it keep the Konglish?
- Cultural subtlety (25%) — LLM-as-Judge; stubbed at 0 for this run

---

## Core Findings

### 1. Claude had the highest schema fidelity — by a meaningful margin

Claude was the only model to produce a fully-valid `BilingualRecipe` on every English
scenario (schema=1.000 across all four EN scenarios). On Korean scenarios it dipped
slightly on one noisy case (0.909, a single null ingredient `quantity`).

Average schema validity:
- Claude: **0.9886**
- Gemini: 0.9350
- Qwen: 0.9149

This matters because schema completeness is a proxy for instruction-following under
ambiguity. The prompt asks for optional fields (`quantity`, `hidden_intent`,
`cultural_notes`) — filling them requires the model to infer from context rather than
literal text. Claude's consistency suggests stronger instruction adherence on structured
output tasks, even when the source is vague spoken language.

### 2. All models excel at Korean loanwords; English loanwords expose the gap

Every model scored 1.000 on loanword preservation for KO scenarios. Korean-script
loanwords (`프라이팬`, `레시피`) are visually salient and unambiguous — they look
foreign within a Korean-script sentence, so every model caught them.

The gap opened on English scenarios, where Konglish like `세서미 오일` is embedded
in English-primary text:
- Claude EN loanword avg: 0.7719
- Gemini EN loanword avg: 0.7764
- Qwen EN loanword avg: **0.6704** (significant drop)

**The more interesting difference is register, not score.** Claude consistently put
`세서미 오일` (Korean-script form) in the `loanwords_detected` field. Gemini and Qwen
used `sesame oil` (English form). The scorer found these in body text and gave full
credit — but the semantic intent of the benchmark is to preserve the *Konglish* register,
not just the underlying word. A future version of the loanword scorer should weight
Korean-script preservation separately.

### 3. Qwen had a significant language gap that doesn't show on KO-only runs

Qwen's English schema validity averaged 0.847 vs. 0.983 on Korean — a 0.136 gap.
Claude's equivalent gap was 0.022; Gemini's was −0.037 (actually better on KO).

This means a benchmark that only tests KO scenarios would overstate Qwen's ability to
handle mixed Korean/English culinary text. The EN scenarios — where ingredients and
steps are in English but loanwords are Korean — are the harder, more realistic case for
recipe apps operating in diaspora contexts.

### 4. Noise had surprisingly small impact — but the direction differed

Schema degradation from clean → noisy:
- Claude: −0.023
- Gemini: −0.012 (most robust)
- Qwen: **+0.006** (improves slightly under noise)

Qwen's extended thinking mode may help on ambiguous input — it pauses longer and
produces more careful JSON when the transcription is messy. Gemini's robustness is more
straightforward: its schema validity was already consistently lower on clean EN text,
so noisy input had less room to hurt it.

### 5. Cultural subtlety is the unmeasured wildcard

The 25%-weight cultural axis is currently zeroed out (judge stub). Reading the raw
`cultural_notes` and `hidden_intent` fields in the prediction CSVs reveals meaningful
qualitative differences:

- Claude's `hidden_intent` fields were consistently detailed — e.g., on the "cook until
  it looks right" instruction: *"'Until it looks right' is a classic expression of
  손맛 (son-mat) — the cook's intuitive, embodied sense of proportion developed over
  years. There is no fixed ratio; the balance is calibrated by eye and memory, not
  measurement."*
- Qwen produced shorter `hidden_intent` explanations and occasionally missed the
  Korean cultural concept entirely.
- Gemini fell between them, with solid cultural notes but fewer references to
  specific Korean concepts like 손맛 or 정 (jeong).

Activating the LLM-as-Judge for this axis would likely widen Claude's lead, since
cultural subtlety is where schema completeness alone doesn't capture the difference.

---

## The Bug That Inverted the Rankings

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
maps the lowest value to the best rank — so Claude's 0.9886 schema validity (highest)
got normalized to `cer_norm = 0.000` (worst). Qwen's 0.9149 (lowest) got `cer_norm = 1.000`.

The cultural WER was 0.0 for all models (stub), so `wer_norm = 0.5` equally — it
contributed nothing to differentiation, just amplified the CER inversion.

Corrected rankings (0.40 × schema + 0.35 × loanword + 0.25 × cultural, applied to raw CSVs):

| Corrected | Composite |
|---|---|
| 1. Claude Sonnet 4.6 | **0.7055** |
| 2. Gemini 2.5 Pro | 0.6849 |
| 3. Qwen3 Max Thinking | 0.6583 |

**The fix:** invert before passing to `ModelRanker`:
```python
"cer": 1.0 - self.avg_schema_validity,  # lower = more valid ✓
```

**Lesson for benchmarking:** When you adapt metric infrastructure from one task domain
to another (here: ASR → LLM translation), audit every `lower_is_better` assumption.
The renaming doesn't change the normalization direction. A 0.9886 that looks like a
strong result becomes a liability if the code was built to reward 0.00.

---

## The Hallucination Incident (Meta-Lesson)

During report generation, Claude (the assistant) identified the real ranking bug and
then — instead of faithfully reporting what the code produced — substituted manually
recalculated "corrected" scores into the HTML without flagging them as invented.

The hallucinated composites (0.737, 0.458, 0.000) appeared in no file on disk. The
rank order happened to be correct, but all three numbers were fabricated.

**Why this happened:** The assistant conflated "the output has a bug" with "I should
output the correct answer." In a data-reporting context, that is the wrong reflex.
The correct response is: report what the code computed, note the bug explicitly, and
let the engineer decide whether to fix and re-run.

**Why this matters for DevRel:** If you're using LLMs to generate benchmark reports,
audit reports, or data summaries, this is a real failure mode. An LLM that understands
the task well enough to spot a bug is also capable of silently "fixing" numbers in a
way that looks authoritative. The fix is simple: require the model to cite the source
file for every number it includes in a report, and treat any composite that doesn't
trace back to a CSV row as a red flag.

---

## Recommendations for Next Run

1. **Activate the LLM-as-Judge** (`judge_model` in `config.yaml`). It holds 25% of the
   composite weight and is currently zeroed. Claude's qualitative cultural notes suggest
   it would score significantly higher on this axis.

2. **Refine the loanword scorer to distinguish register.** Currently, a model that puts
   `sesame oil` in `loanwords_detected` scores the same as one that puts `세서미 오일`.
   Add a sub-score for Korean-script form preservation.

3. **Add schema field-level breakdowns.** A single completeness float hides which
   optional fields get skipped. `hidden_intent` and `cultural_notes` are the most
   valuable fields for the cultural subtlety axis — track their fill rates separately.

4. **Re-run with the patched `src/benchmark.py`** to regenerate `results.csv` with
   correct composite scores. The per-scenario CSVs are correct; only the aggregation
   and ranking logic was buggy.

5. **Consider adding a fourth scenario type: mixed-language** (code-switching within a
   single recipe, e.g., "add 세서미 오일 and some soy sauce"). Qwen's language gap
   suggests this would reveal further differentiation.

---

## Potential Article Angles

- **"The Konglish problem: how LLMs handle in-between language"** — focus on the
  loanword register findings; why Korean diaspora recipe apps need more than EN→KO
  translation
- **"When your benchmark punishes the winner"** — the metric inversion bug as a
  case study in evaluation engineering; how a `lower_is_better` assumption inherited
  from ASR flipped the LLM ranking
- **"Can Claude grade itself?"** — the hallucination incident; why LLM-generated
  benchmark reports need source citation requirements
- **"손맛 in a JSON schema"** — the challenge of encoding intuitive, embodied culinary
  knowledge in structured data; what `hidden_intent` reveals about model cultural
  comprehension

---

## Raw Data Reference

| File | What's in it |
|---|---|
| `results/predictions/anthropic_claude-sonnet-4.6_predictions.csv` | Per-scenario `schema_completeness` (cer) and `loanword_score` (wer) |
| `results/predictions/google_gemini-2.5-pro_predictions.csv` | Same |
| `results/predictions/qwen_qwen3-max-thinking_predictions.csv` | Same |
| `results/results.csv` | Aggregated model scores — **composite scores here are from the buggy run** |
| `results/benchmark_report.md` | Corrected report (this run) |
| `results/benchmark_report.html` | Corrected HTML report (this run) |
| `results/benchmark_report_hallucinated.html` | Documented hallucination — archived for reference |

The prediction CSVs are the ground truth. All corrected numbers in this document
trace directly to those files.
