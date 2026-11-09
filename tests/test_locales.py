"""The language files: the app's part of them (build.mjs checks the web interface's part)."""

from __future__ import annotations

import json
from pathlib import Path
from string import Formatter
from typing import Any

import pytest

LOCALES = Path(__file__).parents[1] / "device_proxy" / "app" / "device_proxy" / "locales"
SECTIONS = ("notifications", "reasons", "notify_status", "entities")
COMPLETE = ("de", "en")


def locale_files() -> dict[str, dict[str, Any]]:
    return {path.stem: json.loads(path.read_text("utf-8")) for path in LOCALES.glob("*.json")}


def names(texts: str | list[str]) -> set[str]:
    parts = [texts] if isinstance(texts, str) else texts
    return {field for part in parts for _, field, _, _ in Formatter().parse(part) if field}


@pytest.mark.parametrize("code", sorted(locale_files()))
@pytest.mark.parametrize("section", SECTIONS)
def test_a_language_uses_only_what_the_app_fills_in(code: str, section: str) -> None:
    files = locale_files()
    english = files["en"][section]
    for key, text in files[code].get(section, {}).items():
        assert key in english, f"{code}.{section}.{key} is not in en.json"
        assert isinstance(text, type(english[key])), f"{code}.{section}.{key}"
        assert names(text) <= names(english[key]), f"{code}.{section}.{key}"
        if isinstance(text, list):
            assert len(text) == 2, f"{code}.{section}.{key}: a title and a message"


@pytest.mark.parametrize("code", COMPLETE)
@pytest.mark.parametrize("section", SECTIONS)
def test_the_shipped_languages_are_complete(code: str, section: str) -> None:
    files = locale_files()
    assert set(files[code][section]) == set(files["en"][section])


def test_what_a_language_leaves_out_comes_in_english(monkeypatch: pytest.MonkeyPatch) -> None:
    from device_proxy import i18n

    assert set(i18n.LANGUAGES) == set(locale_files())
    files = {"en": {"s": {"a": "A", "b": "B"}}, "xx": {"s": {"a": "X"}}, "yy": {}}
    monkeypatch.setattr(i18n, "_FILES", files)
    assert i18n.section("s") == {
        "en": {"a": "A", "b": "B"},
        "xx": {"a": "X", "b": "B"},
        "yy": {"a": "A", "b": "B"},
    }
