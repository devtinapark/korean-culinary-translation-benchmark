"""
Results Reporter
Generates reports and visualizations for benchmark results
"""
from typing import Dict, List
import pandas as pd
from pathlib import Path
import json
import yaml


class BenchmarkReporter:
    """
    Creates comprehensive reports from benchmark results
    """

    def __init__(self, output_dir: str = "results"):
        """
        Initialize reporter

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_markdown_report(
        self,
        ranked_df: pd.DataFrame,
        top_models: List[str],
        metadata: Dict = None,
        per_model_samples: Dict[str, List[dict]] = None,
        cost_data: Dict[str, dict] = None,
    ) -> str:
        """
        Generate markdown report

        Args:
            ranked_df: DataFrame with ranked models
            top_models: List of top model names
            metadata: Additional metadata to include

        Returns:
            Markdown report string
        """
        md = []

        # Header
        md.append("# Multilingual ASR Benchmark Results")
        md.append("")
        md.append("## Kitchen Audio — EN / KO / ES / ZH")
        md.append("")

        # Metadata
        if metadata:
            md.append("### Configuration")
            md.append("")
            md.append(f"- **Dataset**: {metadata.get('dataset', 'Kitchen Audio Samples')}")
            md.append(f"- **Samples**: {metadata.get('num_samples', 'N/A')}")
            md.append(f"- **Models Tested**: {len(ranked_df)}")
            md.append(f"- **Note**: Composite score is relative — meaningful only when comparing multiple models")
            md.append("")

        # Summary
        md.append("## Summary")
        md.append("")
        md.append("Evaluates multilingual ASR models on real kitchen audio clips containing")
        md.append("casual speech, background noise, and code-switched language (Korean + English).")
        md.append("All models must auto-detect language without a language hint.")
        md.append("")

        # Model Results
        md.append("## Model Results")
        md.append("")

        for i, model_name in enumerate(top_models[:2], 1):
            row = ranked_df[ranked_df['model'] == model_name].iloc[0]

            md.append(f"### {i}. {model_name}")
            md.append("")
            md.append("**Combined metrics (all 8 clips):**")
            md.append("")
            md.append("| Metric | Value |")
            md.append("|--------|-------|")
            md.append(f"| Composite Score | {row['composite_score']:.4f} |")
            md.append(f"| CER (Character Error Rate) | {row['cer']:.4f} |")
            md.append(f"| WER (Word Error Rate) | {row['wer']:.4f} |")
            md.append(f"| Loanword / Code-switching Accuracy | {row['loanword_accuracy']:.4f} |")

            cost = (cost_data or {}).get(model_name)
            if cost:
                md.append(f"| Audio Duration | {cost['audio_minutes']:.2f} min |")
                md.append(f"| Price per Minute | ${cost['cost_per_minute']:.4f} |")
                md.append(f"| Estimated Cost (this run) | ${cost['estimated_cost']:.6f} |")
                md.append(f"| Avg Latency per Clip | {cost['avg_latency']:.2f}s |")
                md.append(f"| Total Latency | {cost['total_latency']:.2f}s |")
            md.append("")

            # Noise degradation delta
            samples = (per_model_samples or {}).get(model_name, [])
            clean = [s for s in samples if not s.get("noise")]
            noisy = [s for s in samples if s.get("noise")]
            if clean and noisy:
                clean_cer = sum(s["cer"] for s in clean) / len(clean)
                noisy_cer = sum(s["cer"] for s in noisy) / len(noisy)
                delta = noisy_cer - clean_cer
                md.append("**Noise impact:**")
                md.append("")
                md.append("| | Avg CER |")
                md.append("|---|---------|")
                md.append(f"| Clean clips | {clean_cer:.4f} |")
                md.append(f"| Noisy clips | {noisy_cer:.4f} |")
                md.append(f"| Degradation (Δ) | +{delta:.4f} |")
                md.append("")

            # Per-sample breakdown
            samples = (per_model_samples or {}).get(model_name)
            if samples:
                md.append("**Per-sample breakdown:**")
                md.append("")
                md.append("| Sample | CER | WER |")
                md.append("|--------|-----|-----|")
                for s in samples:
                    md.append(f"| {s['id']} | {s['cer']:.4f} | {s['wer']:.4f} |")
                md.append("")

        # Full Rankings
        md.append("## Full Rankings")
        md.append("")
        md.append("| Rank | Model | Composite Score | CER | WER | Loanword Acc | Cost (this run) |")
        md.append("|------|-------|----------------|-----|-----|--------------|-----------------|")

        for _, row in ranked_df.iterrows():
            cost = (cost_data or {}).get(row['model'])
            cost_str = f"${cost['estimated_cost']:.6f}" if cost else "—"
            md.append(
                f"| {row['rank']} | {row['model']} | {row['composite_score']:.4f} | "
                f"{row['cer']:.4f} | {row['wer']:.4f} | {row['loanword_accuracy']:.4f} | {cost_str} |"
            )

        md.append("")

        # Metrics Explanation
        md.append("## Metrics Explanation")
        md.append("")
        md.append("### Primary Metrics")
        md.append("")
        md.append("- **CER (Character Error Rate)**: Primary metric for Korean due to agglutinative nature")
        md.append("  - Lower is better (0 = perfect, 1 = complete failure)")
        md.append("  - More granular than WER for Korean text")
        md.append("")
        md.append("- **WER (Word Error Rate)**: Secondary metric")
        md.append("  - Lower is better")
        md.append("  - Word-level accuracy")
        md.append("")
        md.append("- **Loanword / Code-switching Accuracy**: accuracy on English loanwords and mixed-language terms")
        md.append("  - Critical for kitchen context (e.g., 오븐, 레시피, 간 맞추기)")
        md.append("  - Higher is better")
        md.append("")

        # Composite Score
        md.append("### Composite Score")
        md.append("")
        md.append("Weighted combination of metrics (scores are relative between models — run all 3 to get meaningful rankings):")
        md.append("- CER: 55% — primary accuracy metric")
        md.append("- WER: 30% — secondary accuracy metric")
        md.append("- Loanword / code-switching accuracy: 15%")
        md.append("")
        md.append("*Speed excluded: measures API latency, not model quality.*")
        md.append("*CER/WER ratio excluded: only meaningful for Korean-only models.*")
        md.append("")

        return "\n".join(md)

    def save_markdown_report(
        self,
        ranked_df: pd.DataFrame,
        top_models: List[str],
        metadata: Dict = None,
        filename: str = "benchmark_report.md",
        per_model_samples: Dict[str, List[dict]] = None,
        cost_data: Dict[str, dict] = None,
    ):
        """
        Save markdown report to file

        Args:
            ranked_df: DataFrame with ranked models
            top_models: List of top model names
            metadata: Additional metadata
            filename: Output filename
        """
        md = self.generate_markdown_report(ranked_df, top_models, metadata, per_model_samples, cost_data)
        output_path = self.output_dir / filename

        with open(output_path, 'w') as f:
            f.write(md)

        print(f"Markdown report saved to {output_path}")

    def save_csv_results(
        self,
        ranked_df: pd.DataFrame,
        filename: str = "results.csv"
    ):
        """
        Save results to CSV

        Args:
            ranked_df: DataFrame with ranked models
            filename: Output filename
        """
        output_path = self.output_dir / filename
        ranked_df.to_csv(output_path, index=False)
        print(f"CSV results saved to {output_path}")

    def save_json_results(
        self,
        ranked_df: pd.DataFrame,
        metadata: Dict = None,
        filename: str = "results.json"
    ):
        """
        Save results to JSON

        Args:
            ranked_df: DataFrame with ranked models
            metadata: Additional metadata
            filename: Output filename
        """
        output_path = self.output_dir / filename

        results = {
            "metadata": metadata or {},
            "rankings": ranked_df.to_dict('records')
        }

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"JSON results saved to {output_path}")

    def save_yaml_results(
        self,
        ranked_df: pd.DataFrame,
        metadata: Dict = None,
        filename: str = "results.yaml"
    ):
        """
        Save results to YAML

        Args:
            ranked_df: DataFrame with ranked models
            metadata: Additional metadata
            filename: Output filename
        """
        output_path = self.output_dir / filename

        results = {
            "metadata": metadata or {},
            "rankings": ranked_df.to_dict('records')
        }

        with open(output_path, 'w') as f:
            yaml.dump(results, f, default_flow_style=False, allow_unicode=True)

        print(f"YAML results saved to {output_path}")

    def save_top_models_list(
        self,
        top_models: List[str],
        filename: str = "top_models.txt"
    ):
        """
        Save list of top models to text file

        Args:
            top_models: List of top model names
            filename: Output filename
        """
        output_path = self.output_dir / filename

        with open(output_path, 'w') as f:
            f.write("Multilingual ASR Model Comparison — OpenAI vs Deepgram\n")
            f.write("=" * 50 + "\n\n")

            for i, model in enumerate(top_models[:2], 1):
                f.write(f"{i}. {model}\n")

        print(f"Top models list saved to {output_path}")

    def generate_all_reports(
        self,
        ranked_df: pd.DataFrame,
        top_models: List[str],
        metadata: Dict = None,
        per_model_samples: Dict[str, List[dict]] = None,
        cost_data: Dict[str, dict] = None,
    ):
        print("\n" + "="*60)
        print("Generating Reports")
        print("="*60 + "\n")

        self.save_markdown_report(ranked_df, top_models, metadata,
                                  per_model_samples=per_model_samples,
                                  cost_data=cost_data)
        self.save_csv_results(ranked_df)
        self.save_json_results(ranked_df, metadata)
        self.save_yaml_results(ranked_df, metadata)
        self.save_top_models_list(top_models)

        print("\n" + "="*60)
        print("All reports generated successfully!")
        print(f"Output directory: {self.output_dir}")
        print("="*60 + "\n")


class PredictionExporter:
    """
    Exports detailed predictions for analysis
    """

    def __init__(self, output_dir: str = "results/predictions"):
        """
        Initialize exporter

        Args:
            output_dir: Directory to save predictions
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_predictions(
        self,
        model_name: str,
        references: List[str],
        predictions: List[str],
        sample_ids: List[str] = None,
        per_sample_metrics: List[dict] = None,
    ):
        if sample_ids is None:
            sample_ids = [str(i) for i in range(len(references))]

        rows = []
        for i, (sid, ref, pred) in enumerate(zip(sample_ids, references, predictions)):
            row = {"sample_id": sid, "reference": ref, "prediction": pred}
            if per_sample_metrics and i < len(per_sample_metrics):
                row["cer"] = per_sample_metrics[i].get("cer", "")
                row["wer"] = per_sample_metrics[i].get("wer", "")
            rows.append(row)

        df = pd.DataFrame(rows)
        filename = f"{model_name.replace('/', '_')}_predictions.csv"
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False)
        print(f"Per-sample results saved to {output_path}")
