from __future__ import annotations
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .data_loader import TextScenarioLoader, TextScenario
from .model_wrapper import OpenRouterClient
from .metrics import SchemaValidator, LoanwordPreservationScorer
from .judge import CulturalSubtletyJudge
from .schemas import BilingualRecipe


@dataclass
class ScenarioResult:
    scenario_id: str
    language: str
    noise: bool
    is_valid: bool
    schema_completeness: float
    loanword_score: float
    cultural_score: int
    latency: float
    raw_response: str | None
    parsed_recipe: BilingualRecipe | None


@dataclass
class BenchmarkResult:
    model_name: str
    avg_schema_validity: float
    avg_loanword_score: float
    avg_cultural_score: float
    avg_latency: float
    num_scenarios: int
    error: str | None = None
    per_scenario: list[ScenarioResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        # Maps new metric names to the keys ModelRanker expects (cer/wer/loanword_accuracy slots).
        # cer slot   → schema validity (higher is better)
        # wer slot   → cultural score  (higher is better, 0 when judge is stubbed)
        # loanword   → loanword preservation
        # ModelRanker normalizes cer/wer with lower_is_better=True, so invert
        # higher-is-better metrics before passing them in.
        return {
            "cer": 1.0 - self.avg_schema_validity,          # lower = more valid
            "wer": 1.0 - (self.avg_cultural_score / 5.0),   # lower = higher judge score
            "loanword_accuracy": self.avg_loanword_score,    # already higher-is-better ✓
            "samples_per_second": 1.0 / self.avg_latency if self.avg_latency > 0 else 0.0,
            "cer_wer_ratio": 0.0,
            "error": self.error,
        }


class TranslationBenchmark:

    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

        metadata_path = str(Path(config_path).parent / "kitchen_samples" / "metadata.json")
        self._loader = TextScenarioLoader(metadata_path=metadata_path)
        self._validator = SchemaValidator()
        self._loanword_scorer = LoanwordPreservationScorer()
        self._judge = CulturalSubtletyJudge(model_id=self._config.get("judge_model"))
        self._scenarios: list[TextScenario] | None = None

    def setup_data(self):
        self._scenarios = self._loader.load()
        print(f"Loaded {len(self._scenarios)} text scenarios.")

    def evaluate_model(self, model_id: str) -> BenchmarkResult:
        if self._scenarios is None:
            self.setup_data()

        client = OpenRouterClient(model_id)
        results: list[ScenarioResult] = []

        for scenario in self._scenarios:
            t0 = time.perf_counter()
            recipe, raw = client.translate(scenario.text, scenario.language)
            latency = time.perf_counter() - t0

            is_valid, completeness = self._validator.validate(recipe)
            loanword_score = self._loanword_scorer.score(scenario.text, recipe)

            try:
                cultural_score = self._judge.score(scenario.text, recipe) if recipe else 0
            except NotImplementedError:
                cultural_score = 0

            results.append(ScenarioResult(
                scenario_id=scenario.id,
                language=scenario.language,
                noise=scenario.noise,
                is_valid=is_valid,
                schema_completeness=completeness,
                loanword_score=loanword_score,
                cultural_score=cultural_score,
                latency=latency,
                raw_response=raw,
                parsed_recipe=recipe,
            ))
            print(f"  [{scenario.id}] valid={is_valid} "
                  f"completeness={completeness:.2f} "
                  f"loanword={loanword_score:.2f} "
                  f"latency={latency:.2f}s")

        n = len(results)
        return BenchmarkResult(
            model_name=model_id,
            avg_schema_validity=sum(r.schema_completeness for r in results) / n if n else 0.0,
            avg_loanword_score=sum(r.loanword_score for r in results) / n if n else 0.0,
            avg_cultural_score=sum(r.cultural_score for r in results) / n if n else 0.0,
            avg_latency=sum(r.latency for r in results) / n if n else 0.0,
            num_scenarios=n,
            per_scenario=results,
        )

    def run_all_models(self) -> dict[str, BenchmarkResult]:
        models = self._config.get("models", [])
        all_results: dict[str, BenchmarkResult] = {}

        for model_cfg in models:
            model_id = model_cfg["id"]
            print(f"\nEvaluating {model_id}...")
            try:
                result = self.evaluate_model(model_id)
                all_results[model_id] = result
                print(f"  Schema validity: {result.avg_schema_validity:.3f} | "
                      f"Loanword score: {result.avg_loanword_score:.3f} | "
                      f"Avg latency: {result.avg_latency:.2f}s")
            except Exception as exc:
                all_results[model_id] = BenchmarkResult(
                    model_name=model_id,
                    avg_schema_validity=0.0,
                    avg_loanword_score=0.0,
                    avg_cultural_score=0.0,
                    avg_latency=0.0,
                    num_scenarios=0,
                    error=str(exc),
                )
                print(f"  ERROR: {exc}")

        return all_results

    def run_single_model(self, model_id: str) -> BenchmarkResult:
        if self._scenarios is None:
            self.setup_data()
        return self.evaluate_model(model_id)
