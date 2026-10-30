"""Repository-structure sanity tests.

These tests do not import `agent_eval` or exercise any runtime behavior.
They check the documentation/layout contract of the repository itself:
required top-level docs exist, every directory of tracked files has a
README, no tracked markdown file is empty, and relative markdown links
within tracked markdown files resolve to a real path.

Uses `git ls-files` to discover tracked files, so these tests must be run
from inside a checkout of this git repository.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


TRACKED_FILES = _tracked_files()
TRACKED_MARKDOWN = [f for f in TRACKED_FILES if f.endswith(".md")]


def test_top_level_docs_exist():
    required = ["README.md", "ARCHITECTURE.md", "IDEATION.md"]
    missing = [name for name in required if not (REPO_ROOT / name).is_file()]
    assert not missing, f"missing required top-level docs: {missing}"


def test_every_layout_dir_has_a_readme():
    """Every directory that owns at least one tracked file must carry its
    own README.md (directly in that directory), so contributors can
    orient themselves without climbing back to the repo root."""
    dirs_with_tracked_files: set[Path] = set()
    for rel_path in TRACKED_FILES:
        dirs_with_tracked_files.add((REPO_ROOT / rel_path).parent)

    missing = sorted(
        str(d.relative_to(REPO_ROOT))
        for d in dirs_with_tracked_files
        if d != REPO_ROOT and not (d / "README.md").is_file()
    )
    assert not missing, f"directories missing a README.md: {missing}"


def test_no_markdown_file_is_empty():
    empty = [
        rel_path
        for rel_path in TRACKED_MARKDOWN
        if not (REPO_ROOT / rel_path).read_text(encoding="utf-8").strip()
    ]
    assert not empty, f"empty markdown files: {empty}"


def test_relative_markdown_links_resolve():
    broken: list[str] = []
    for rel_path in TRACKED_MARKDOWN:
        file_path = REPO_ROOT / rel_path
        text = file_path.read_text(encoding="utf-8")
        for target in LINK_PATTERN.findall(text):
            target = target.split(" ", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target_path, _, _anchor = target.partition("#")
            if not target_path:
                continue
            resolved = (file_path.parent / target_path).resolve()
            if not resolved.exists():
                broken.append(f"{rel_path} -> {target}")
    assert not broken, f"broken relative markdown links: {broken}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
