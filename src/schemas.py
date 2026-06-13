from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, model_validator


class IngredientItem(BaseModel):
    name_ko: str
    name_en: str
    quantity: str | None = None
    notes: str | None = None  # e.g. "Konglish: 버터 = butter; salted preferred"


class RecipeStep(BaseModel):
    step_number: int
    instruction_ko: str
    instruction_en: str
    hidden_intent: str | None = None  # extracted culinary subtext behind vague phrasing


class BilingualRecipe(BaseModel):
    title_ko: str
    title_en: str
    source_language: Literal["ko", "en", "mixed"]
    ingredients: list[IngredientItem]
    steps: list[RecipeStep]
    loanwords_detected: list[str]  # Konglish terms from the source, preserved verbatim
    cultural_notes: str | None = None  # meaning that transcends the recipe structure

    @model_validator(mode="after")
    def normalize_step_numbers(self) -> "BilingualRecipe":
        for i, step in enumerate(self.steps, 1):
            step.step_number = i
        return self
