from __future__ import annotations
import json
import os

import openai
from pydantic import ValidationError

from .schemas import BilingualRecipe

SYSTEM_PROMPT = """\
You are a culinary translator and cultural linguist specializing in Korean cuisine.

Given an unstructured text (ASR output from a spoken Korean or English recipe), extract \
a fully structured bilingual recipe. You MUST:

1. Preserve ALL loanwords (Konglish) exactly as spoken — words like 오븐(oven), 피자(pizza), \
레시피(recipe), 버터(butter), 파스타(pasta), 세서미 오일(sesame oil). Do NOT translate them \
away — list them verbatim in `loanwords_detected`.
2. Extract the HIDDEN CULINARY INTENT behind vague instructions (e.g., "until it looks right" → \
hidden_intent: "visual doneness cue that develops with experience; watch for color and texture \
changes rather than relying on timing").
3. Capture cultural meaning in `cultural_notes` that cannot be expressed in the recipe steps alone \
(e.g., generational transmission, ritual significance, 손맛 — the untranslatable quality of a \
cook's personal touch).
4. Provide BOTH Korean (ko fields) and English (en fields) for every ingredient and step.

Output ONLY a single valid JSON object — no markdown, no explanation, no surrounding text.

Schema:
{schema}"""


class OpenRouterClient:
    def __init__(self, model_id: str):
        self._client = openai.OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
        )
        self.model_id = model_id
        self._schema = json.dumps(BilingualRecipe.model_json_schema(), indent=2)

    def translate(
        self, text: str, source_lang: str
    ) -> tuple[BilingualRecipe | None, str | None]:
        """Call the model and validate output. Returns (recipe, raw_response)."""
        system = SYSTEM_PROMPT.format(schema=self._schema)
        response = self._client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": f"Source language: {source_lang}\n\nTranscript:\n{text}",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw = response.choices[0].message.content or ""
        try:
            parsed = json.loads(raw)
            recipe = BilingualRecipe.model_validate(parsed)
            return recipe, raw
        except (json.JSONDecodeError, ValidationError):
            return None, raw


def create_openrouter_client(model_id: str) -> OpenRouterClient:
    return OpenRouterClient(model_id)
