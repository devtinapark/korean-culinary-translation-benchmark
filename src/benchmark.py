"""
ASR Benchmark Runner
Evaluates ASR models against kitchen audio samples
"""
from typing import Dict, List
import time
import yaml
from pathlib import Path
from dataclasses import dataclass, field

from .data_loader import KitchenAudioLoader, AudioPreprocessor
from .model_wrapper import create_model_wrapper
from .metrics import KoreanMetricsCalculator, LoanwordAccuracyCalculator, InferenceSpeedCalculator


@dataclass
class BenchmarkResult:
    model_name: str
    cer: float = None
    wer: float = None
    cer_wer_ratio: float = None
    loanword_accuracy: float = None
    loanword_cer: float = None
    samples_per_second: float = None
    total_time: float = None
    num_samples: int = 0
    error: str = None
    predictions: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    sample_ids: List[str] = field(default_factory=list)
    per_sample_metrics: List[dict] = field(default_factory=list)
    total_audio_minutes: float = 0.0
    cost_per_minute: float = 0.0
    estimated_cost: float = 0.0
    latencies: List[float] = field(default_factory=list)  # seconds per clip
    avg_latency: float = 0.0
    total_latency: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "model_name": self.model_name,
            "cer": self.cer,
            "wer": self.wer,
            "cer_wer_ratio": self.cer_wer_ratio,
            "loanword_accuracy": self.loanword_accuracy,
            "loanword_cer": self.loanword_cer,
            "samples_per_second": self.samples_per_second,
            "total_time": self.total_time,
            "num_samples": self.num_samples,
            "error": self.error,
        }


class ASRBenchmark:

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.data_loader = None
        self.metrics_calculator = KoreanMetricsCalculator()
        self.loanword_calculator = LoanwordAccuracyCalculator()
        self.results: Dict[str, BenchmarkResult] = {}

    def _load_config(self) -> Dict:
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def setup_data(self):
        ds = self.config["dataset"]
        print("\n" + "=" * 60)
        print("Loading Kitchen Audio Samples")
        print("=" * 60)

        self.data_loader = KitchenAudioLoader(
            audio_dir=ds["audio_dir"],
            transcripts_dir=ds.get("transcripts_dir"),
            metadata_file=ds.get("metadata_file"),
        )
        self.data_loader.load()

        if len(self.data_loader) == 0:
            raise RuntimeError(
                "No audio samples found.\n"
                f"  Place .wav files in: {ds['audio_dir']}\n"
                f"  Place matching .txt files in: {ds.get('transcripts_dir')}\n"
                "  Or fill in: kitchen_samples/metadata.json"
            )

        print(f"Ready: {len(self.data_loader)} samples\n")

    def evaluate_model(self, model_name: str, model_config: Dict) -> BenchmarkResult:
        result = BenchmarkResult(model_name=model_name)

        print(f"\n{'=' * 60}")
        print(f"Evaluating: {model_name}")
        print(f"{'=' * 60}")

        try:
            model = create_model_wrapper(
                model_name=model_name,
                model_config=model_config,
                device=self.config["benchmark"].get("device", "cpu"),
            )

            references, predictions, sample_ids = [], [], []
            per_sample_metrics = []
            total_audio_seconds = 0.0
            start_time = time.time()

            for sample in self.data_loader:
                audio, sr = AudioPreprocessor.prepare_for_model(
                    sample.audio, sample.sampling_rate
                )
                total_audio_seconds += len(audio) / sr

                t0 = time.time()
                prediction = model.transcribe(audio, sr)
                latency = time.time() - t0

                predictions.append(prediction)
                references.append(sample.text)
                sample_ids.append(sample.id)

                # Per-sample metrics
                sample_cer = self.metrics_calculator.calculate_cer([sample.text], [prediction])
                sample_wer = self.metrics_calculator.calculate_wer([sample.text], [prediction])
                per_sample_metrics.append({
                    "id": sample.id,
                    "cer": round(sample_cer, 4),
                    "wer": round(sample_wer, 4),
                    "latency_sec": round(latency, 2),
                    "noise": "noise" in sample.id,
                })
                print(f"  [{sample.id}]")
                print(f"    ref : {sample.text[:80]}{'...' if len(sample.text) > 80 else ''}")
                print(f"    pred: {prediction[:80]}{'...' if len(prediction) > 80 else ''}")
                print(f"    CER: {sample_cer:.4f}  WER: {sample_wer:.4f}  latency: {latency:.2f}s")


            total_time = time.time() - start_time

            metrics = self.metrics_calculator.calculate_all_metrics(references, predictions)
            loanword_metrics = self.loanword_calculator.calculate_loanword_accuracy(references, predictions)
            speed = InferenceSpeedCalculator.calculate_speed(len(references), total_time)

            result.cer = metrics.cer
            result.wer = metrics.wer
            result.cer_wer_ratio = metrics.cer_wer_ratio
            result.loanword_accuracy = loanword_metrics.get("loanword_accuracy", 0.0)
            result.loanword_cer = loanword_metrics.get("loanword_cer", 0.0)
            result.samples_per_second = speed["samples_per_second"]
            result.total_time = total_time
            result.num_samples = len(references)
            result.predictions = predictions
            result.references = references
            result.sample_ids = sample_ids
            result.per_sample_metrics = per_sample_metrics

            cost_per_minute = model_config.get("cost_per_minute", 0.0)
            audio_minutes = total_audio_seconds / 60
            result.total_audio_minutes = round(audio_minutes, 3)
            result.cost_per_minute = cost_per_minute
            result.estimated_cost = round(audio_minutes * cost_per_minute, 6)

            latencies = [s["latency_sec"] for s in per_sample_metrics]
            result.latencies = latencies
            result.avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
            result.total_latency = round(sum(latencies), 2)

            print(f"\n  ── Combined ──────────────────────────────")
            print(f"  CER: {metrics.cer:.4f}  WER: {metrics.wer:.4f}  "
                  f"Loanword acc: {result.loanword_accuracy:.4f}")

        except Exception as e:
            print(f"  ERROR: {e}")
            result.error = str(e)

        return result

    def run_all_models(self) -> Dict[str, BenchmarkResult]:
        models_config = self.config["models"]
        print(f"\n{'=' * 60}")
        print(f"Running {len(models_config)} models")
        print("=" * 60)

        for model_name, model_config in models_config.items():
            result = self.evaluate_model(model_name, model_config)
            self.results[model_name] = result

        return self.results

    def run_single_model(self, model_name: str) -> BenchmarkResult:
        if model_name not in self.config["models"]:
            raise ValueError(f"Model '{model_name}' not found in config. "
                             f"Available: {list(self.config['models'].keys())}")

        result = self.evaluate_model(model_name, self.config["models"][model_name])
        self.results[model_name] = result
        return result
