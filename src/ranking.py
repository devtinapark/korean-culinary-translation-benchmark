"""
Model Ranking System
Objectively ranks ASR models based on multiple criteria
"""
from typing import List, Dict, Tuple
import pandas as pd
from dataclasses import dataclass


@dataclass
class RankingCriteria:
    """
    Weights for the LLM translation benchmark.

    Field names are kept stable for ModelRanker compatibility.
    Semantic mapping (new → old slot):
      cer_weight      → schema validity rate (40%)
      wer_weight      → cultural subtlety score (25%)
      loanword_weight → loanword preservation score (35%)
    """
    cer_weight: float = 0.40      # schema validity (higher is better)
    wer_weight: float = 0.25      # cultural subtlety score (higher is better)
    loanword_weight: float = 0.35  # Konglish / loanword preservation
    speed_weight: float = 0.0
    ratio_weight: float = 0.0


class ModelRanker:
    """
    Ranks ASR models based on objective metrics
    """

    def __init__(self, criteria: RankingCriteria = None):
        """
        Initialize ranker

        Args:
            criteria: RankingCriteria object with weights
        """
        self.criteria = criteria or RankingCriteria()

        # Validate weights sum to 1.0
        total_weight = (
            self.criteria.cer_weight +
            self.criteria.wer_weight +
            self.criteria.loanword_weight +
            self.criteria.speed_weight +
            self.criteria.ratio_weight
        )
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

    def normalize_metric(
        self,
        values: List[float],
        lower_is_better: bool = True
    ) -> List[float]:
        """
        Normalize metrics to 0-1 scale

        Args:
            values: List of metric values
            lower_is_better: If True, lower values get higher scores

        Returns:
            Normalized scores
        """
        if not values or all(v is None for v in values):
            return [0.0] * len(values)

        # Filter out None values for min/max calculation
        valid_values = [v for v in values if v is not None]
        if not valid_values:
            return [0.0] * len(values)

        min_val = min(valid_values)
        max_val = max(valid_values)

        # Avoid division by zero
        if max_val == min_val:
            return [0.5] * len(values)

        normalized = []
        for v in values:
            if v is None:
                normalized.append(0.0)
            else:
                norm = (v - min_val) / (max_val - min_val)
                # Invert if lower is better
                if lower_is_better:
                    norm = 1.0 - norm
                normalized.append(norm)

        return normalized

    def calculate_composite_score(
        self,
        cer: float,
        wer: float,
        loanword_acc: float,
        speed: float,
        ratio: float,
        cer_norm: float,
        wer_norm: float,
        loanword_norm: float,
        speed_norm: float,
        ratio_norm: float
    ) -> float:
        """
        Calculate weighted composite score

        Args:
            cer, wer, loanword_acc, speed, ratio: Raw metrics
            cer_norm, wer_norm, loanword_norm, speed_norm, ratio_norm: Normalized scores

        Returns:
            Composite score (0-1, higher is better)
        """
        score = (
            self.criteria.cer_weight * cer_norm +
            self.criteria.wer_weight * wer_norm +
            self.criteria.loanword_weight * loanword_norm +
            self.criteria.speed_weight * speed_norm +
            self.criteria.ratio_weight * ratio_norm
        )

        return score

    def rank_models(
        self,
        results: Dict[str, Dict]
    ) -> pd.DataFrame:
        """
        Rank models based on benchmark results

        Args:
            results: Dictionary of model_name -> results dict

        Returns:
            DataFrame with ranked models
        """
        # Extract metrics
        models = []
        cer_values = []
        wer_values = []
        loanword_values = []
        speed_values = []
        ratio_values = []

        for model_name, result in results.items():
            # Skip models with errors
            if result.get('error') is not None:
                continue

            models.append(model_name)
            cer_values.append(result.get('cer'))
            wer_values.append(result.get('wer'))
            loanword_values.append(result.get('loanword_accuracy', 0.0))
            speed_values.append(result.get('samples_per_second', 0.0))
            ratio_values.append(result.get('cer_wer_ratio', 0.0))

        if not models:
            return pd.DataFrame()

        # Normalize metrics
        cer_norm = self.normalize_metric(cer_values, lower_is_better=True)
        wer_norm = self.normalize_metric(wer_values, lower_is_better=True)
        loanword_norm = self.normalize_metric(loanword_values, lower_is_better=False)
        speed_norm = self.normalize_metric(speed_values, lower_is_better=False)
        ratio_norm = self.normalize_metric(ratio_values, lower_is_better=False)

        # Calculate composite scores
        composite_scores = []
        for i in range(len(models)):
            score = self.calculate_composite_score(
                cer_values[i], wer_values[i], loanword_values[i],
                speed_values[i], ratio_values[i],
                cer_norm[i], wer_norm[i], loanword_norm[i],
                speed_norm[i], ratio_norm[i]
            )
            composite_scores.append(score)

        # Create DataFrame
        df = pd.DataFrame({
            'model': models,
            'cer': cer_values,
            'wer': wer_values,
            'cer_wer_ratio': ratio_values,
            'loanword_accuracy': loanword_values,
            'samples_per_second': speed_values,
            'composite_score': composite_scores,
            'cer_normalized': cer_norm,
            'wer_normalized': wer_norm,
            'loanword_normalized': loanword_norm,
            'speed_normalized': speed_norm,
            'ratio_normalized': ratio_norm
        })

        # Sort by composite score (descending)
        df = df.sort_values('composite_score', ascending=False)

        # Add rank
        df.insert(0, 'rank', range(1, len(df) + 1))

        return df

    def get_top_n(
        self,
        results: Dict[str, Dict],
        n: int = 5
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Get top N models

        Args:
            results: Dictionary of model_name -> results dict
            n: Number of top models to return

        Returns:
            Tuple of (ranked_df, top_model_names)
        """
        ranked_df = self.rank_models(results)

        if ranked_df.empty:
            return ranked_df, []

        top_n_df = ranked_df.head(n)
        top_model_names = top_n_df['model'].tolist()

        return top_n_df, top_model_names

    def print_ranking_table(self, ranked_df: pd.DataFrame):
        """
        Print formatted ranking table

        Args:
            ranked_df: DataFrame with ranked models
        """
        if ranked_df.empty:
            print("No models to rank")
            return

        print("\n" + "="*100)
        print("MODEL RANKING - LLM Translation Benchmark".center(100))
        print("="*100)

        # Select columns to display
        display_cols = [
            'rank', 'model', 'composite_score', 'cer', 'wer',
            'loanword_accuracy',
        ]
        available_cols = [c for c in display_cols if c in ranked_df.columns]

        # Format for display
        display_df = ranked_df[available_cols].copy()
        display_df['composite_score'] = display_df['composite_score'].apply(lambda x: f"{x:.4f}")
        display_df['cer'] = display_df['cer'].apply(lambda x: f"{x:.4f}")
        display_df['wer'] = display_df['wer'].apply(lambda x: f"{x:.4f}" if x else "—")
        display_df['loanword_accuracy'] = display_df['loanword_accuracy'].apply(lambda x: f"{x:.4f}")

        # Rename columns for display
        display_df.columns = [
            c if c not in ('cer', 'wer', 'loanword_accuracy', 'composite_score', 'rank', 'model')
            else {
                'cer': 'Schema Valid',
                'wer': 'Cultural Score',
                'loanword_accuracy': 'Loanword Pres.',
                'composite_score': 'Score',
                'rank': 'Rank',
                'model': 'Model',
            }[c]
            for c in display_df.columns
        ]

        print(display_df.to_string(index=False))
        print("="*100 + "\n")

    def print_top_n_summary(
        self,
        top_df: pd.DataFrame,
        top_models: List[str],
        n: int = 5
    ):
        """
        Print summary of top N models

        Args:
            top_df: DataFrame with top models
            top_models: List of top model names
            n: Number of models
        """
        print("\n" + "="*100)
        print(f"TOP {n} MODELS — LLM TRANSLATION BENCHMARK".center(100))
        print("="*100)

        for i, model_name in enumerate(top_models, 1):
            row = top_df[top_df['model'] == model_name].iloc[0]

            print(f"\n{i}. {model_name}")
            print("-" * 80)
            print(f"   Composite Score:   {row['composite_score']:.4f}")
            print(f"   Schema Validity:   {row['cer']:.4f}")
            print(f"   Cultural Score:    {row['wer']:.4f}")
            print(f"   Loanword Preserv.: {row['loanword_accuracy']:.4f}")

            strengths = []
            if row['cer_normalized'] > 0.7:
                strengths.append("high schema completeness")
            if row['loanword_normalized'] > 0.7:
                strengths.append("strong Konglish preservation")
            if row['wer_normalized'] > 0.7:
                strengths.append("high cultural subtlety score")

            if strengths:
                print(f"   Strengths: {', '.join(strengths)}")

        print("\n" + "="*100 + "\n")
