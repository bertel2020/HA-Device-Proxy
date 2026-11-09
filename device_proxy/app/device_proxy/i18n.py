"""The texts of notifications and Home Assistant entities: one file per language in locales/.

The web interface takes its part of the same files when it is built (panel-src/build.mjs).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FALLBACK = "en"
_FILES: dict[str, dict[str, Any]] = {
    path.stem: json.loads(path.read_text(encoding="utf-8"))
    for path in sorted((Path(__file__).parent / "locales").glob("*.json"))
}
LANGUAGES = tuple(_FILES)


def section(name: str) -> dict[str, dict[str, Any]]:
    """Language → the texts of a section; what a language leaves out comes in English."""
    english = _FILES[FALLBACK][name]
    return {code: {**english, **texts.get(name, {})} for code, texts in _FILES.items()}
