"""How far each commit has got: fetch the remotes, then see which branches hold it.

A merge done on the web only reaches this machine with a fetch, so the remotes
are fetched first. `git fetch` updates remote-tracking branches such as
origin/master and nothing else: local branches and the working tree stay as
they are. It never prompts; a remote that needs a password, is unreachable or
is slow is skipped, and the local history is used as it is.

A commit's status is the furthest branch that contains it, by default:
main or master → 已合入 <branch>, a pre-release branch → 已预发布, a test
branch → 已提测. `status_branches` in config.json replaces these rules with the
team's own, as {"branch name": "label"}, furthest first. A commit squash- or
merge-committed on the web counts through its pull request number.
"""

from __future__ import annotations

import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

FETCH_TIMEOUT = 30  # seconds per repository

# (branch name pattern, label), furthest first. {branch} is the matched name.
DEFAULT_RULES = [
    (r"main|master", "已合入 {branch}"),
    (r"pre-?release|preprod|pre|staging|release", "已预发布"),
    (r"test|testing|qa|sit|uat", "已提测"),
]
SQUASH_PR = re.compile(r"\(#(\d+)\)\s*$")


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    return proc.stdout if proc.returncode == 0 else ""


def fetch(repo: Path) -> dict:
    """{"fetched": True}, {"fetched": False, "fetch_error": …}, or {"fetched": None} without a remote."""
    if not _git(repo, "remote").strip():
        return {"fetched": None}
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}
    env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes -o ConnectTimeout=10")
    try:
        proc = subprocess.run(["git", "-C", str(repo), "fetch", "--all", "--prune", "--quiet"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=FETCH_TIMEOUT, env=env, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"fetched": False, "fetch_error": f"timed out after {FETCH_TIMEOUT}s"}
    if proc.returncode != 0:
        lines = [line for line in proc.stderr.strip().splitlines() if line.strip()]
        return {"fetched": False, "fetch_error": lines[-1] if lines else f"git fetch exited {proc.returncode}"}
    return {"fetched": True}


def fetch_all(repos: list[Path]) -> dict[Path, dict]:
    """Fetch several repositories at once."""
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(zip(repos, pool.map(fetch, repos)))


def rules(config: dict) -> list[tuple[re.Pattern, str]]:
    custom = config.get("status_branches")
    if custom:
        return [(re.compile(f"^{re.escape(name)}$"), label) for name, label in custom.items()]
    return [(re.compile(f"^(?:{pattern})$", re.I), label) for pattern, label in DEFAULT_RULES]


def status_refs(repo: Path, config: dict) -> list[dict]:
    """Branches that mark progress, furthest first: remote-tracking ones, or local ones in a repo with
    no remote at all. A repo with a remote but nothing fetched yet has none: a local master says
    nothing about what was merged."""
    remote = [r for r in _git(repo, "for-each-ref", "refs/remotes", "--format=%(refname:short)").split()
              if "/" in r and not r.endswith("/HEAD")]
    names = [(r, r.split("/", 1)[1]) for r in remote]
    if not names and not _git(repo, "remote").strip():
        names = [(r, r) for r in _git(repo, "for-each-ref", "refs/heads", "--format=%(refname:short)").split()]
    found = []
    for rank, (pattern, label) in enumerate(rules(config)):
        for ref, name in names:
            if pattern.match(name):
                found.append({"ref": ref, "label": label.format(branch=name), "rank": rank})
    return found


def statuses(repo: Path, config: dict, since: str, commits: list[dict]) -> tuple[list[dict], dict[str, str]]:
    """The progress branches, and each commit's status label by full sha (absent while in progress).

    `commits` carry "sha" and "prs"; a pull request with a "merge_sha" or a squash
    subject "(#N)" on a branch counts as that branch holding the commit.
    """
    refs = status_refs(repo, config)
    best: dict[str, tuple[int, str]] = {}

    def mark(sha: str, rank: int, label: str) -> None:
        if sha not in best or rank < best[sha][0]:
            best[sha] = (rank, label)

    for ref in refs:
        on_branch = set(_git(repo, "rev-list", ref["ref"], f"--since={since}").split())
        squashed = {int(m.group(1)) for line in _git(repo, "log", ref["ref"], f"--since={since}",
                                                      "--format=%s").splitlines()
                    for m in [SQUASH_PR.search(line)] if m}
        for c in commits:
            prs = c.get("prs", [])
            if (c["sha"] in on_branch
                    or any(p.get("merge_sha") in on_branch for p in prs)
                    or any(p["number"] in squashed for p in prs)):
                mark(c["sha"], ref["rank"], ref["label"])
    labels = {sha: label for sha, (_, label) in best.items()}
    return [{"ref": r["ref"], "label": r["label"]} for r in refs], labels
