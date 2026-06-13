from __future__ import annotations
from .schemas import BilingualRecipe
from .loanword_detector import KonglishDetector


class SchemaValidator:
    """Validates BilingualRecipe structural completeness."""

    def validate(self, recipe: BilingualRecipe | None) -> tuple[bool, float]:
        """
        Returns (is_valid, field_completeness).

        is_valid: True if recipe has at least one ingredient and one step.
        field_completeness: fraction of all possible fields (including optional) that are filled.
        """
        if recipe is None:
            return False, 0.0

        filled = 0
        total = 0

        for f in ("title_ko", "title_en", "source_language"):
            total += 1
            if getattr(recipe, f, None):
                filled += 1

        total += 1
        if recipe.cultural_notes:
            filled += 1

        for ing in recipe.ingredients:
            for f in ("name_ko", "name_en"):
                total += 1
                if getattr(ing, f, None):
                    filled += 1
            for f in ("quantity", "notes"):
                total += 1
                if getattr(ing, f, None):
                    filled += 1

        for step in recipe.steps:
            for f in ("instruction_ko", "instruction_en"):
                total += 1
                if getattr(step, f, None):
                    filled += 1
            total += 1
            if step.hidden_intent:
                filled += 1

        completeness = filled / total if total > 0 else 0.0
        is_valid = bool(recipe.ingredients and recipe.steps)
        return is_valid, completeness


class LoanwordPreservationScorer:
    """Scores how well loanwords from the source text appear in the recipe output."""

    def __init__(self):
        self._detector = KonglishDetector()

    def score(self, original_text: str, recipe: BilingualRecipe | None) -> float:
        """
        Returns 0.0–1.0: fraction of input loanwords preserved in any recipe field.
        Returns 1.0 when the input contains no detectable loanwords.
        """
        if recipe is None:
            return 0.0

        input_loanwords = set(self._detector.detect_loanwords(original_text))
        if not input_loanwords:
            return 1.0

        all_output_text = " ".join([
            " ".join(recipe.loanwords_detected),
            recipe.cultural_notes or "",
            *[f"{i.name_ko} {i.name_en} {i.notes or ''}" for i in recipe.ingredients],
            *[
                f"{s.instruction_ko} {s.instruction_en} {s.hidden_intent or ''}"
                for s in recipe.steps
            ],
        ]).lower()

        preserved = sum(1 for w in input_loanwords if w in all_output_text)
        return preserved / len(input_loanwords)
