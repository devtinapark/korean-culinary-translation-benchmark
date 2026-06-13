from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TextScenario:
    id: str
    text: str
    language: str
    noise: bool


class TextScenarioLoader:
    """Loads the 8 text scenarios from kitchen_samples/metadata.json."""

    def __init__(self, metadata_path: str = "kitchen_samples/metadata.json"):
        self._path = Path(metadata_path)

    def load(self) -> list[TextScenario]:
        with open(self._path, encoding="utf-8") as f:
            records = json.load(f)
        return [
            TextScenario(
                id=r["id"],
                text=r["transcript"],
                language=r["language"],
                noise=r["noise"],
            )
            for r in records
        ]

    def __len__(self) -> int:
        return len(self.load())

    def __iter__(self):
        return iter(self.load())
