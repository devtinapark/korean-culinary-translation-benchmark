"""
LLM-as-a-Judge for cultural subtlety preservation scoring (1–5 scale).

Requires OPENROUTER_API_KEY in environment and judge_model set in config.yaml.
"""
from __future__ import annotations
import os
import openai
from .schemas import BilingualRecipe

JUDGE_RUBRIC = """\
Score the following bilingual recipe translation on CULTURAL SUBTLETY PRESERVATION (1–5):

1 = All cultural context lost; loanwords translated away; no regional nuance retained
2 = Minimal cultural context; most Konglish lost or incorrectly rendered
3 = Partial preservation; some Konglish retained; limited culinary subtext extracted
4 = Good preservation; most loanwords correct; some hidden intent captured in steps
5 = Excellent; all loanwords retained verbatim; hidden culinary intent surfaced in every \
    vague step; cultural_notes adds meaningful context beyond the recipe itself

Original transcript (source):
{original_text}

Extracted bilingual recipe (JSON):
{recipe_json}

Respond with ONLY a single integer 1, 2, 3, 4, or 5. No explanation."""


class CulturalSubtletyJudge:
    """
    LLM-as-a-Judge scorer for cultural subtlety preservation.

    Active when model_id is set in config.yaml (judge_model key).
    Falls back to 0 and logs a warning if model_id is None.
    """

    def __init__(self, model_id: str | None = None):
        self.model_id = model_id
        self.is_active = model_id is not None
        if self.is_active:
            self._client = openai.OpenAI(
                api_key=os.environ["OPENROUTER_API_KEY"],
                base_url="https://openrouter.ai/api/v1",
            )

    def score(self, original_text: str, recipe: BilingualRecipe) -> int:
        """Score cultural subtlety preservation on a 1–5 scale."""
        if not self.is_active:
            return 0
        return self._call_judge(original_text, recipe)

    def _call_judge(self, original_text: str, recipe: BilingualRecipe) -> int:
        """Call the judge LLM and parse its 1–5 integer response."""
        prompt = JUDGE_RUBRIC.format(
            original_text=original_text,
            recipe_json=recipe.model_dump_json(indent=2),
        )
        resp = self._client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=5,
        )
        raw = resp.choices[0].message.content.strip()
        score = int(raw)
        if not 1 <= score <= 5:
            raise ValueError(f"Judge returned out-of-range score: {raw!r}")
        return score
