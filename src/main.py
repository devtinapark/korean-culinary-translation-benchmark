"""
LLM Translation & Schema-Validation Benchmark — entry point
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import yaml

from .benchmark import TranslationBenchmark
from .ranking import ModelRanker, RankingCriteria
from .reporter import BenchmarkReporter, PredictionExporter


def run_full_benchmark(
    config_path: str = "config.yaml",
    top_n: int = 3,
    output_dir: str = "results",
) -> None:
    print("\n" + "=" * 80)
    print("LLM TRANSLATION BENCHMARK — Claude vs Gemini vs Qwen".center(80))
    print("=" * 80 + "\n")

    benchmark = TranslationBenchmark(config_path)
    benchmark.setup_data()
    raw_results = benchmark.run_all_models()

    results_dict = {name: r.to_dict() for name, r in raw_results.items()}

    cfg = yaml.safe_load(open(config_path))
    weights = cfg.get("evaluation", {})
    criteria = RankingCriteria(
        cer_weight=weights.get("schema_validity_weight", 0.40),
        wer_weight=weights.get("cultural_score_weight", 0.25),
        loanword_weight=weights.get("loanword_weight", 0.35),
        speed_weight=0.0,
        ratio_weight=0.0,
    )
    ranker = ModelRanker(criteria)
    top_df, top_models = ranker.get_top_n(results_dict, n=top_n)
    ranked_df = ranker.rank_models(results_dict)

    ranker.print_ranking_table(ranked_df)

    metadata = {
        "dataset": "Korean Culinary ASR Transcripts",
        "num_scenarios": 8,
        "config_file": config_path,
        "models_tested": list(raw_results.keys()),
    }

    per_model_samples = {
        name: [
            {
                "id": r.scenario_id,
                "noise": r.noise,
                "cer": r.schema_completeness,   # schema validity in cer display slot
                "wer": r.loanword_score,         # loanword score in wer display slot
            }
            for r in result.per_scenario
        ]
        for name, result in raw_results.items()
    }

    cost_data = {
        name: {
            "prompt_tokens": r.total_prompt_tokens,
            "completion_tokens": r.total_completion_tokens,
            "cost_usd": r.cost_usd,
            "absolute_composite": r.absolute_composite,
        }
        for name, r in raw_results.items()
    }

    reporter = BenchmarkReporter(output_dir)
    reporter.generate_all_reports(ranked_df, top_models, metadata, per_model_samples, cost_data)

    exporter = PredictionExporter(str(Path(output_dir) / "predictions"))
    for model_name, result in raw_results.items():
        exporter.export_predictions(
            model_name=model_name,
            references=[r.scenario_id for r in result.per_scenario],
            predictions=[
                r.parsed_recipe.model_dump_json() if r.parsed_recipe else "null"
                for r in result.per_scenario
            ],
            sample_ids=[r.scenario_id for r in result.per_scenario],
            per_sample_metrics=[
                {"cer": r.schema_completeness, "wer": r.loanword_score}
                for r in result.per_scenario
            ],
        )

    print("\n" + "=" * 80)
    print("Benchmark Complete!".center(80))
    print("=" * 80)
    print(f"\nReport:      {output_dir}/benchmark_report.md")
    print(f"Rankings:    {output_dir}/results.csv")
    print(f"Top models:  {output_dir}/top_models.txt\n")


def run_single_model(
    model_id: str,
    config_path: str = "config.yaml",
    output_dir: str = "results",
) -> None:
    print(f"\n{'=' * 80}")
    print(f"Single model: {model_id}".center(80))
    print("=" * 80 + "\n")

    benchmark = TranslationBenchmark(config_path)
    benchmark.setup_data()
    result = benchmark.run_single_model(model_id)

    print(f"\nResults for {model_id}:")
    print(f"  Schema validity:  {result.avg_schema_validity:.4f}")
    print(f"  Loanword score:   {result.avg_loanword_score:.4f}")
    print(f"  Cultural score:   {result.avg_cultural_score:.4f}")
    print(f"  Avg latency:      {result.avg_latency:.2f}s")
    print(f"  Scenarios run:    {result.num_scenarios}")
    if result.error:
        print(f"  Error: {result.error}")

    results_dict = {model_id: result.to_dict()}
    ranker = ModelRanker()
    ranked_df = ranker.rank_models(results_dict)

    reporter = BenchmarkReporter(output_dir)
    reporter.generate_all_reports(ranked_df, [model_id], {"model": model_id})


def list_models(config_path: str = "config.yaml") -> None:
    cfg = yaml.safe_load(open(config_path))
    print("\nConfigured models:")
    for m in cfg.get("models", []):
        print(f"  - {m['id']}  (provider: {m.get('provider', 'openrouter')})")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="LLM Translation & Schema-Validation Benchmark"
    )
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--model", default=None, help="Run a single model by ID")
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--list-models", action="store_true")
    args = parser.parse_args()

    try:
        if not Path(args.config).exists():
            print(f"Error: config file not found: {args.config}")
            sys.exit(1)

        if args.list_models:
            list_models(args.config)
        elif args.model:
            run_single_model(args.model, args.config, args.output_dir)
        else:
            run_full_benchmark(args.config, args.top_n, args.output_dir)

    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)
    except Exception as exc:
        print(f"\nError: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
