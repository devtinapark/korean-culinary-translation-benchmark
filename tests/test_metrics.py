"""
Unit tests for schema validation and loanword preservation metrics
"""
import unittest
from src.metrics import SchemaValidator, LoanwordPreservationScorer
from src.schemas import BilingualRecipe, IngredientItem, RecipeStep


def _make_recipe(**kwargs) -> BilingualRecipe:
    defaults = dict(
        title_ko="계란말이",
        title_en="Egg Roll",
        source_language="ko",
        ingredients=[
            IngredientItem(name_ko="달걀", name_en="egg", quantity="3개")
        ],
        steps=[
            RecipeStep(
                step_number=1,
                instruction_ko="달걀을 풀어주세요",
                instruction_en="Beat the eggs",
            )
        ],
        loanwords_detected=[],
        cultural_notes=None,
    )
    defaults.update(kwargs)
    return BilingualRecipe(**defaults)


class TestSchemaValidator(unittest.TestCase):

    def setUp(self):
        self.validator = SchemaValidator()

    def test_none_recipe_invalid(self):
        is_valid, completeness = self.validator.validate(None)
        self.assertFalse(is_valid)
        self.assertEqual(completeness, 0.0)

    def test_minimal_valid_recipe(self):
        recipe = _make_recipe()
        is_valid, completeness = self.validator.validate(recipe)
        self.assertTrue(is_valid)
        self.assertGreater(completeness, 0.0)
        self.assertLessEqual(completeness, 1.0)

    def test_fully_populated_recipe_higher_completeness(self):
        sparse = _make_recipe()
        full = _make_recipe(
            cultural_notes="손맛 — the cook's personal touch",
            ingredients=[
                IngredientItem(
                    name_ko="달걀",
                    name_en="egg",
                    quantity="3개",
                    notes="large eggs preferred",
                )
            ],
            steps=[
                RecipeStep(
                    step_number=1,
                    instruction_ko="달걀을 풀어주세요",
                    instruction_en="Beat the eggs",
                    hidden_intent="Uniform beating ensures even cooking and a smooth roll",
                )
            ],
        )
        _, sparse_completeness = self.validator.validate(sparse)
        _, full_completeness = self.validator.validate(full)
        self.assertGreater(full_completeness, sparse_completeness)

    def test_empty_ingredients_invalid(self):
        recipe = _make_recipe(ingredients=[])
        is_valid, _ = self.validator.validate(recipe)
        self.assertFalse(is_valid)

    def test_empty_steps_invalid(self):
        recipe = _make_recipe(steps=[])
        is_valid, _ = self.validator.validate(recipe)
        self.assertFalse(is_valid)


class TestLoanwordPreservationScorer(unittest.TestCase):

    def setUp(self):
        self.scorer = LoanwordPreservationScorer()

    def test_none_recipe_scores_zero(self):
        score = self.scorer.score("오늘은 pizza를 만들었어요", None)
        self.assertEqual(score, 0.0)

    def test_no_input_loanwords_scores_one(self):
        recipe = _make_recipe()
        score = self.scorer.score("안녕하세요 여러분", recipe)
        self.assertEqual(score, 1.0)

    def test_loanword_present_in_detected_list(self):
        recipe = _make_recipe(loanwords_detected=["pizza", "pasta"])
        score = self.scorer.score("오늘은 pizza와 pasta를 만들었어요", recipe)
        self.assertEqual(score, 1.0)

    def test_loanword_missing_from_output_scores_low(self):
        recipe = _make_recipe(loanwords_detected=[])
        score = self.scorer.score("오늘은 pizza를 만들었어요", recipe)
        self.assertLess(score, 1.0)

    def test_partial_loanword_preservation(self):
        recipe = _make_recipe(loanwords_detected=["pizza"])
        score = self.scorer.score("pizza와 pasta와 oven을 사용했어요", recipe)
        self.assertGreater(score, 0.0)
        self.assertLess(score, 1.0)

    def test_loanword_found_in_ingredient_notes(self):
        recipe = _make_recipe(
            loanwords_detected=[],
            ingredients=[
                IngredientItem(
                    name_ko="버터",
                    name_en="butter",
                    notes="Konglish: butter — 버터",
                )
            ],
        )
        score = self.scorer.score("버터를 넣어주세요", recipe)
        # "butter" detected in ingredient notes
        self.assertGreater(score, 0.0)


if __name__ == "__main__":
    unittest.main()
