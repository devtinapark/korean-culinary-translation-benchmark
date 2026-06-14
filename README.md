# Korean Culinary Translation Benchmark

Benchmarks three LLMs on their ability to ingest raw ASR text from spoken Korean/English kitchen recipes and produce a strictly-typed bilingual recipe structure — while preserving regional loanwords (Konglish) and surfacing hidden culinary intent.

Models compared via [OpenRouter](https://openrouter.ai):
- `anthropic/claude-sonnet-4.6`
- `google/gemini-2.5-pro`
- `qwen/qwen3-max-thinking`

> Model IDs are OpenRouter-specific. `anthropic/claude-3.7-sonnet` does not exist there — use `anthropic/claude-sonnet-4.6`. Verify any ID with `python -m src.main --list-models` or the [OpenRouter models list](https://openrouter.ai/models).

---

## Evaluation

| Metric | Weight | What it measures |
|---|---|---|
| Schema validity / completeness | 40% | Pydantic validation + filled optional fields |
| Loanword preservation | 35% | Input Konglish present verbatim in output |
| Cultural subtlety (LLM-as-Judge) | 25% | 1–5 score; judge model set via `judge_model` in `config.yaml` |

Each model receives 8 text scenarios (En/Ko × A/B × Clean/Noisy) and must return a validated `BilingualRecipe` JSON object.

---

## Quick start

### 1. Install dependencies

```bash
conda activate korean-asr
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# edit .env → OPENROUTER_API_KEY=sk-or-...
export $(cat .env | xargs)
```

### 3. Run

```bash
python -m src.main                                          # all 3 models
python -m src.main --model anthropic/claude-sonnet-4.6    # single model
python -m src.main --list-models                           # verify model IDs
```

---

## Output

```
results/
├── benchmark_report.md
├── results.csv / results.json / results.yaml
├── top_models.txt
└── predictions/
    └── <model>_predictions.csv
```

---

## Output schema

Every model call must return a `BilingualRecipe` (defined in `src/schemas.py`):

```
BilingualRecipe
├── title_ko / title_en
├── source_language: "ko" | "en" | "mixed"
├── ingredients: list[IngredientItem]  — name_ko, name_en, quantity, notes
├── steps: list[RecipeStep]            — instruction_ko, instruction_en, hidden_intent
├── loanwords_detected: list[str]      — Konglish terms verbatim from source
└── cultural_notes: str | None
```

---

## Adding models

Add entries to `config.yaml` under `models:`. Any OpenRouter model ID works — the `OpenRouterClient` is model-agnostic.

---

## License

MIT
