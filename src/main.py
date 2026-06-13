"""
Korean ASR Benchmark - Main Entry Point
Systematically evaluates and ranks ASR models for Korean language
"""
import argparse
import sys
from pathlib import Path

from .benchmark import ASRBenchmark
from .ranking import ModelRanker, RankingCriteria
from .reporter import BenchmarkReporter
from .html_reporter import save_html_report


def run_full_benchmark(
    config_path: str = "config.yaml",
    top_n: int = 2,  # OpenAI vs Deepgram
    output_dir: str = "results"
):
    """
    Run full benchmark pipeline

    Args:
        config_path: Path to configuration file
        top_n: Number of top models to select
        output_dir: Output directory for results
    """
    print("\n" + "="*80)
    print("MULTILINGUAL ASR BENCHMARK — OpenAI vs Deepgram".center(80))
    print("="*80 + "\n")

    # Initialize benchmark
    benchmark = ASRBenchmark(config_path)

    # Setup data
    benchmark.setup_data()

    # Run benchmark on all models
    results = benchmark.run_all_models()

    # Convert results to dict format
    results_dict = {name: result.to_dict() for name, result in results.items()}

    # Rank models
    print("\n" + "="*80)
    print("Ranking Models")
    print("="*80 + "\n")

    ranker = ModelRanker()
    ranked_df = ranker.rank_models(results_dict)

    # Get top N
    top_df, top_models = ranker.get_top_n(results_dict, n=top_n)

    # Print rankings
    ranker.print_ranking_table(ranked_df)
    ranker.print_top_n_summary(top_df, top_models, n=top_n)

    # Generate reports
    reporter = BenchmarkReporter(output_dir)

    metadata = {
        "dataset": "Kitchen Audio Samples",
        "num_samples": len(benchmark.data_loader) if benchmark.data_loader else 0,
        "config_file": config_path
    }

    per_model_samples = {name: r.per_sample_metrics for name, r in results.items()}
    cost_data = {
        name: {
            "audio_minutes": r.total_audio_minutes,
            "cost_per_minute": r.cost_per_minute,
            "estimated_cost": r.estimated_cost,
            "avg_latency": r.avg_latency,
            "total_latency": r.total_latency,
        }
        for name, r in results.items()
    }
    reporter.generate_all_reports(ranked_df, top_models, metadata,
                                  per_model_samples=per_model_samples,
                                  cost_data=cost_data)

    save_html_report(output_dir, ranked_df, top_models,
                     per_model_samples=per_model_samples,
                     cost_data=cost_data,
                     metadata=metadata)

    from .reporter import PredictionExporter
    exporter = PredictionExporter(f"{output_dir}/predictions")
    for name, result in results.items():
        if result.predictions:
            exporter.export_predictions(
                name, result.references, result.predictions,
                sample_ids=result.sample_ids,
                per_sample_metrics=result.per_sample_metrics,
            )

    print("\n" + "="*80)
    print("Benchmark Complete!".center(80))
    print("="*80)
    print(f"\nRankings saved to: {output_dir}/top_models.txt")
    print(f"Full report: {output_dir}/benchmark_report.md")
    print(f"Results: {output_dir}/results.csv\n")


def run_single_model(
    model_name: str,
    config_path: str = "config.yaml",
    output_dir: str = "results"
):
    """
    Run benchmark on a single model

    Args:
        model_name: Name of model from config
        config_path: Path to configuration file
        output_dir: Output directory for results
    """
    print(f"\n{'='*80}")
    print(f"Running single model benchmark: {model_name}".center(80))
    print("="*80 + "\n")

    benchmark = ASRBenchmark(config_path)
    benchmark.setup_data()

    result = benchmark.run_single_model(model_name)

    # Save results
    results_dict = {model_name: result.to_dict()}
    ranker = ModelRanker()
    ranked_df = ranker.rank_models(results_dict)

    reporter = BenchmarkReporter(output_dir)
    metadata = {
        "dataset": "Kitchen Audio Samples",
        "num_samples": len(benchmark.data_loader),
        "model": model_name,
    }
    per_model_samples = {model_name: result.per_sample_metrics}
    cost_data = {model_name: {
        "audio_minutes": result.total_audio_minutes,
        "cost_per_minute": result.cost_per_minute,
        "estimated_cost": result.estimated_cost,
        "avg_latency": result.avg_latency,
        "total_latency": result.total_latency,
    }}
    reporter.generate_all_reports(ranked_df, [model_name], metadata,
                                  per_model_samples=per_model_samples,
                                  cost_data=cost_data)

    save_html_report(output_dir, ranked_df, [model_name],
                     per_model_samples=per_model_samples,
                     cost_data=cost_data,
                     metadata=metadata)

    from .reporter import PredictionExporter
    exporter = PredictionExporter(f"{output_dir}/predictions")
    if result.predictions:
        exporter.export_predictions(
            model_name,
            result.references,
            result.predictions,
            sample_ids=result.sample_ids,
            per_sample_metrics=result.per_sample_metrics,
        )

    print("\n" + "="*80)
    print("Complete!".center(80))
    print("="*80)
    print(f"\nReport: {output_dir}/benchmark_report.md")
    print(f"CSV:    {output_dir}/results.csv")
    print(f"Predictions: {output_dir}/predictions/{model_name.replace('/', '_')}_predictions.csv\n")


def list_models(config_path: str = "config.yaml"):
    """
    List all available models in config

    Args:
        config_path: Path to configuration file
    """
    import yaml

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    models = config.get('models', {})

    print("\n" + "="*80)
    print("Available Models".center(80))
    print("="*80 + "\n")

    for i, (model_name, model_config) in enumerate(models.items(), 1):
        print(f"{i}. {model_name}")
        print(f"   HuggingFace ID: {model_config['name']}")
        if 'language' in model_config:
            print(f"   Language: {model_config['language']}")
        print()

    print(f"Total: {len(models)} models\n")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Korean ASR Benchmark - Systematic evaluation of ASR models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full benchmark on all models
  python -m src.main

  # Run benchmark with custom config
  python -m src.main --config my_config.yaml

  # Compare Whisper vs Deepgram (default 2)
  python -m src.main --top-n 2

  # Run single model
  python -m src.main --model whisper-large-v3

  # List available models
  python -m src.main --list-models
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )

    parser.add_argument(
        '--model',
        type=str,
        help='Run benchmark on a single model'
    )

    parser.add_argument(
        '--top-n',
        type=int,
        default=2,
        help='Number of top models to select (default: 2)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='results',
        help='Output directory for results (default: results)'
    )

    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List all available models in config'
    )

    args = parser.parse_args()

    try:
        # Check if config file exists
        if not Path(args.config).exists():
            print(f"Error: Config file not found: {args.config}")
            sys.exit(1)

        # Handle commands
        if args.list_models:
            list_models(args.config)

        elif args.model:
            run_single_model(
                args.model,
                args.config,
                args.output_dir
            )

        else:
            run_full_benchmark(
                args.config,
                args.top_n,
                args.output_dir
            )

    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
        sys.exit(0)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
