# Korean Culinary Translation Benchmark

## Project Purpose

Benchmarks three LLMs (via OpenRouter) on their ability to ingest raw text strings
— simulated ASR outputs of spoken Korean/English kitchen recipes — and map them into
a strictly-typed, schema-validated bilingual recipe structure while preserving
regional loanwords (Konglish) and surfacing hidden culinary intent.

Models compared:
- `anthropic/claude-3.7-sonnet`
- `google/gemini-2.5-pro`
- `qwen/qwen3-max-thinking`

## Stack

- **Python 3.10+** — uses `match`/`case`, `X | Y` union types
- **Pydantic V2** — `BaseModel`, `model_validator`, strict JSON schema validation
- **OpenAI SDK** — pointed at OpenRouter (`base_url="https://openrouter.ai/api/v1"`)
- **OpenRouter API key** — set `OPENROUTER_API_KEY` in environment

## Output Contract

Every model call must return a `BilingualRecipe` (defined in `src/schemas.py`):

```
BilingualRecipe
├── title_ko / title_en
├── source_language: "ko" | "en" | "mixed"
├── ingredients: list[IngredientItem]  (name_ko, name_en, quantity, notes)
├── steps: list[RecipeStep]            (step_number, instruction_ko, instruction_en, hidden_intent)
├── loanwords_detected: list[str]      — must retain Konglish verbatim
└── cultural_notes: str | None         — meaning that transcends the recipe structure
```

## Evaluation Axes

| Metric | Weight | What it measures |
|---|---|---|
| Schema validity / completeness | 40% | Pydantic validation + filled optional fields |
| Loanword preservation | 35% | Input Konglish present in recipe output |
| Cultural subtlety (LLM-as-Judge) | 25% | 1–5 score; stubbed in `src/judge.py` |

## Key Files

| File | Role |
|---|---|
| `src/schemas.py` | Pydantic V2 models: `IngredientItem`, `RecipeStep`, `BilingualRecipe` |
| `src/model_wrapper.py` | `OpenRouterClient` — calls API, validates JSON → `BilingualRecipe` |
| `src/data_loader.py` | `TextScenarioLoader` — reads 8 transcripts from `kitchen_samples/metadata.json` |
| `src/metrics.py` | `SchemaValidator`, `LoanwordPreservationScorer` |
| `src/loanword_detector.py` | `KonglishDetector` — reusable; detects English loanwords in Korean text |
| `src/judge.py` | `CulturalSubtletyJudge` — stub; wire `judge_model` in `config.yaml` to activate |
| `src/benchmark.py` | `TranslationBenchmark` — orchestrates 8 scenarios × N models |
| `src/ranking.py` | `ModelRanker` — reusable; weights configured via `config.yaml` |
| `tests/test_transcripts.py` | 8 fixture transcript strings (En/Ko × A/B × Clean/Noisy) |

## Running

```bash
# Full benchmark (all 3 models)
python -m src.main

# Single model
python -m src.main --model anthropic/claude-3.7-sonnet

# List configured models
python -m src.main --list-models
```

## Loanword Preservation (Critical)

Words like `오븐`, `피자`, `레시피`, `버터`, `파스타`, `세서미 오일`, `간 맞추기` must appear
verbatim in `loanwords_detected`. The `KonglishDetector` in `src/loanword_detector.py`
identifies these from the source text — use it to score preservation.

## Adding Models

Add entries to `config.yaml` under `models:`. Any OpenRouter model ID works.
The `OpenRouterClient` is model-agnostic.
