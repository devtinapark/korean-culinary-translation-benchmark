"""
LLM-as-a-Judge stub for cultural subtlety preservation scoring (1–5 scale).

To activate: implement _call_judge() using the template in its docstring,
then set self.is_active = True and delegate score() to it.
"""
from __future__ import annotations
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

    Stub — returns NotImplementedError until wired to a live model.
    The benchmark catches this and records cultural_score=0, which is
    excluded from composite ranking until the judge is activated.
    """

    def __init__(self, model_id: str | None = None):
        self.model_id = model_id
        self.is_active = False

    def score(self, original_text: str, recipe: BilingualRecipe) -> int:
        """
        Score cultural subtlety preservation on a 1–5 scale.

        Raises NotImplementedError until _call_judge() is implemented.
        """
        raise NotImplementedError(
            "CulturalSubtletyJudge is not yet wired to a model. "
            "Implement _call_judge() and set self.is_active = True to activate."
        )

    def _call_judge(self, original_text: str, recipe: BilingualRecipe) -> int:
        """
        Call the judge LLM and parse its 1–5 integer response.

        Implementation template:
            import openai, os
            client = openai.OpenAI(
                api_key=os.environ["OPENROUTER_API_KEY"],
                base_url="https://openrouter.ai/api/v1",
            )
            prompt = JUDGE_RUBRIC.format(
                original_text=original_text,
                recipe_json=recipe.model_dump_json(indent=2),
            )
            resp = client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=5,
            )
            raw = resp.choices[0].message.content.strip()
            score = int(raw)
            assert 1 <= score <= 5, f"Judge returned out-of-range score: {raw}"
            return score
        """
        raise NotImplementedError
