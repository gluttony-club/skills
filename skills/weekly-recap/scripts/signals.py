"""Clues for what is worth telling at the weekly meeting.

These are pointers, not conclusions: the model reads them, then asks the user
what was hard and what they learned before writing highlights or pitfalls.
"""

from __future__ import annotations

import re
from collections import defaultdict

CONVENTIONAL = re.compile(r"^(?:\W+\s*)?(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?!?:\s", re.I)
# Fixes written without a conventional prefix: "fix upload", "[hotfix] …", "修复上传失败".
FIX = re.compile(r"^(?:\W+\s*)?(?:fix(?:e[sd]|ing)?|hotfix|bugfix)\b|修复|修正", re.I)
REVERT = re.compile(r"This reverts commit ([0-9a-f]{7,40})")
# Words that usually mean the commit explains a cause or a trade-off.
EXPLAINS = re.compile(
    r"\b(because|root cause|caused by|so that|otherwise|workaround|race|regression|instead of|"
    r"compat\w*|fallback)\b|原因|导致|排查|竞态|兼容|规避|否则|回退|绕过",
    re.I,
)
DOCS = re.compile(r"\.(md|mdx|rst|txt)$|(^|/)(docs?|CHANGELOG[^/]*)(/|$)", re.I)
EXPLAINED_BODY_CHARS = 100


def conventional(subject: str) -> tuple[str | None, str | None]:
    """("feat", "tracking") for "feat(tracking): …"; leading emoji are ignored."""
    match = CONVENTIONAL.match(subject)
    return (match.group("type").lower(), match.group("scope")) if match else (None, None)


def is_fix(commit: dict) -> bool:
    """A conventional type decides when present; otherwise look for fix words."""
    if commit["type"]:
        return commit["type"] in ("fix", "hotfix")
    return bool(FIX.search(commit["subject"]))


def build(commits: list[dict], file_lists: dict[str, list[str]]) -> dict:
    """Group commits into topics and point at repeated fixes, reverts and explained commits.

    `file_lists` maps a commit sha to every non-generated file it changed.
    """
    topics: dict[str, dict] = defaultdict(lambda: {"commits": [], "lines": 0})
    for c in commits:
        key = c["scope"] or "(no scope)"
        topics[key]["commits"].append(c["sha"])
        topics[key]["lines"] += c["lines_added"] + c["lines_deleted"]

    # Files that several commits touched, at least two of them fixes: iteration on one problem.
    touched: dict[str, list[dict]] = defaultdict(list)
    for c in commits:
        for path in file_lists.get(c["sha"], []):
            if not DOCS.search(path):  # docs are updated alongside features, not "fixed"
                touched[path].append(c)
    repeated = []
    for path, cs in touched.items():
        fixes = [c for c in cs if is_fix(c)]
        if len(cs) >= 3 and len(fixes) >= 2:
            repeated.append({"file": path, "commits": [c["sha"] for c in cs], "fixes": len(fixes)})
    repeated.sort(key=lambda r: (-r["fixes"], -len(r["commits"])))

    reverts = []
    for c in commits:
        match = REVERT.search(c["body"])
        if match or c["subject"].lower().startswith("revert"):
            reverts.append({"sha": c["sha"], "reverts": match.group(1)[:10] if match else None,
                            "subject": c["subject"]})

    return {
        "topics": sorted(({"topic": k, "commit_count": len(v["commits"]), **v} for k, v in topics.items()),
                         key=lambda t: -t["lines"]),
        "repeated_fixes": repeated[:8],
        "reverts": reverts,
        # Commits whose body explains why: good sources for hard problems and lessons.
        "explained": [c["sha"] for c in commits
                      if len(c["body"]) >= EXPLAINED_BODY_CHARS or EXPLAINS.search(c["body"])],
    }
