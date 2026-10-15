"""Web links for commits and pull requests, found from local git data only.

The repository's web address comes from its remote URL. Pull request numbers come
from merge commits written by the hosting service ("Merge pull request #12 …"),
so no network access or API token is needed.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

# URL templates per hosting service; {web} is the repository's web address.
FORGES = {
    "github": {"commit": "{web}/commit/{sha}", "pr": "{web}/pull/{number}"},
    "gitlab": {"commit": "{web}/-/commit/{sha}", "pr": "{web}/-/merge_requests/{number}"},
    "cnb": {"commit": "{web}/-/commit/{sha}", "pr": "{web}/-/pulls/{number}"},
    "gitee": {"commit": "{web}/commit/{sha}", "pr": "{web}/pulls/{number}"},
    "bitbucket": {"commit": "{web}/commits/{sha}", "pr": "{web}/pull-requests/{number}"},
}

# Merge commit messages that carry a pull/merge request number.
PR_PATTERNS = [
    re.compile(r"^Merge pull request #(\d+)"),               # GitHub, CNB
    re.compile(r"^合并来自 .+ 的合并请求 #(\d+)"),             # CNB (Chinese UI)
    re.compile(r"See merge request \S+!(\d+)"),               # GitLab (in the body)
    re.compile(r"\(pull request #(\d+)\)"),                   # Bitbucket
]
SQUASH_PR = re.compile(r"\(#(\d+)\)\s*$")                     # "Subject (#123)" squash merges
SOURCE_BRANCH = re.compile(r"^Merge pull request #\d+ from (\S+)|^合并来自 (\S+) 的合并请求")


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    return proc.stdout if proc.returncode == 0 else ""


def web_url(remote: str) -> str | None:
    """https://host/owner/repo for an https, ssh or scp-style remote; credentials removed."""
    remote = remote.strip()
    scheme = "https"
    scp = re.match(r"^[\w.-]+@([\w.-]+):(?!//)(.+)$", remote)  # git@host:owner/repo.git
    if scp:
        host, path = scp.groups()
    else:
        parts = urlsplit(remote)
        if parts.scheme not in ("http", "https", "ssh", "git") or not parts.hostname:
            return None
        host, path = parts.hostname, parts.path  # .hostname drops user:token@ and :port
        # The web UI shares an http(s) remote's scheme and port; an ssh or git port is not the web's.
        if parts.scheme in ("http", "https"):
            scheme = parts.scheme
            if parts.port:
                host = f"{host}:{parts.port}"
    path = re.sub(r"\.git$", "", path.strip("/"))
    return f"{scheme}://{host}/{path}" if path else None


def forge_of(web: str) -> str | None:
    host = urlsplit(web).hostname or ""
    if host == "github.com":
        return "github"
    if host == "cnb.cool":
        return "cnb"
    if host == "gitee.com":
        return "gitee"
    if host == "bitbucket.org":
        return "bitbucket"
    if "gitlab" in host:
        return "gitlab"
    return None


def templates(repo: Path, entry: dict) -> dict:
    """Link templates for a repo. A "links" object in its config entry overrides detection:
    {"commit": "https://…/{sha}", "pr": "https://…/{number}"}."""
    remotes = _git(repo, "remote").split()
    remote = "origin" if "origin" in remotes else (remotes[0] if remotes else None)
    web = web_url(_git(repo, "remote", "get-url", remote)) if remote else None
    forge = forge_of(web) if web else None
    found = {k: v.replace("{web}", web) for k, v in FORGES[forge].items()} if forge else {}
    found.update(entry.get("links", {}))
    return {"web_url": web, "forge": forge, **found}


def pull_requests(repo: Path, since: str, shas: set[str]) -> dict[str, list[dict]]:
    """Map each commit in `shas` to the pull requests that merged it, oldest first:
    [{"number": 242, "merged_at": "…", "from_branch": "…"}].

    For every PR merge commit since `since`, the commits it brought in are those
    reachable from its second parent but not from its first.
    """
    found: dict[str, list[dict]] = {}
    log = _git(repo, "log", "--all", "--merges", "--reverse", f"--since={since}",
               "--format=%H%x1f%P%x1f%cI%x1f%s%x1f%b%x1e")
    for record in log.split("\x1e"):
        # strip("\n") only: str.strip() would also eat the \x1f separators (they count as whitespace).
        fields = record.strip("\n").split("\x1f")
        if len(fields) != 5:
            continue
        _, parents, merged_at, subject, body = fields
        number = next((int(m.group(1)) for p in PR_PATTERNS
                       for m in [p.search(subject) or p.search(body)] if m), None)
        parent_list = parents.split()
        if number is None or len(parent_list) < 2:
            continue
        merged = _git(repo, "rev-list", f"--since={since}", parent_list[1], f"^{parent_list[0]}").split()
        source = SOURCE_BRANCH.search(subject)
        pr = {"number": number, "merged_at": merged_at[:16],
              "from_branch": (source.group(1) or source.group(2)) if source else None}
        for sha in shas.intersection(merged):
            if all(p["number"] != number for p in found.setdefault(sha, [])):
                found[sha].append(pr)
    return found


def squash_pr(subject: str) -> int | None:
    match = SQUASH_PR.search(subject)
    return int(match.group(1)) if match else None
