"""Stage 14 (carried from 13): repository hygiene that git itself enforces.

Files written for Linux containers must keep LF endings on a Windows checkout,
whatever each machine's ``core.autocrlf`` is. ``.gitattributes`` is what makes
that true; this test pins which files it covers.
"""

from __future__ import annotations

import pytest

from app.core.config import PROJECT_ROOT

GITATTRIBUTES = PROJECT_ROOT / ".gitattributes"


def lf_patterns() -> set[str]:
    patterns: set[str] = set()
    for raw in GITATTRIBUTES.read_text("utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pattern, *attributes = line.split()
        if {"text", "eol=lf"} <= set(attributes):
            patterns.add(pattern)
    return patterns


@pytest.mark.parametrize(
    "pattern",
    [
        "*.py",
        "*.md",
        "*.html",
        "*.yaml",
        "*.txt",
        "Dockerfile",
        "*.js",
        "*.css",
        ".dockerignore",
        ".env.example",
    ],
)
def test_file_type_is_forced_to_lf(pattern):
    assert pattern in lf_patterns()
