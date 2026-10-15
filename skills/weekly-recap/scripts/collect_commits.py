#!/usr/bin/env python3
"""Collect the user's own git commits across repositories as JSON.

  collect_commits.py repos
      configured repositories, and whether the current directory is one of them
  collect_commits.py collect --start DATE --end DATE [--repo NAME_OR_PATH ...]
      commits authored in the range, with change sizes, for each repository

Repositories come from $WEEKLY_RECAP_HOME/config.json (default ~/.weekly-recap),
or from --repo. Only local git commands run; nothing is fetched from the network.
Uses only the Python standard library (3.9+).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from date_range import DEFAULT_TZ, InputError, parse_date, resolve_tz  # noqa: E402

# Separators that never appear in commit text, so the log output parses safely.
RECORD, FIELD, END = "\x1e", "\x1f", "\x1d"
LOG_FORMAT = RECORD + FIELD.join(["%H", "%an", "%ae", "%aI", "%S", "%s", "%b"]) + END

# Lock files and build output: excluded from line counts so they do not inflate a change.
GENERATED = re.compile(
    r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb?|Cargo\.lock|poetry\.lock|uv\.lock"
    r"|Pipfile\.lock|composer\.lock|Gemfile\.lock|go\.sum|Podfile\.lock)$"
    r"|\.min\.(js|css)$|\.map$|\.snap$|(^|/)(dist|node_modules|vendor|__snapshots__)/"
)

# Subjects that usually mean low-value work. Only a hint: the model makes the call.
TRIVIAL = {
    "merge": r"^merge\b",
    "revert": r"^revert\b",
    "typo": r"\btypos?\b|错别字",
    "format": r"\b(format(ting)?|prettier|lint|eslint|stylelint)\b|格式化",
    "deps": r"^(chore|build)\(deps(-dev)?\)|\bbump\b|升级依赖|更新依赖",
    "wip": r"^(wip|tmp|temp)\b",
    "debug-log": r"console\.log|debug log|调试日志",
    "release": r"^(chore\(release\)|release\b)|^v?\d+\.\d+\.\d+$",
}


def data_home() -> Path:
    env = os.environ.get("WEEKLY_RECAP_HOME")
    return Path(env).expanduser() if env else Path.home() / ".weekly-recap"


def load_config() -> dict:
    path = data_home() / "config.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InputError(f"{path} is not valid JSON: {exc}") from None


def run_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise InputError(f"git {args[0]} failed in {repo}: {proc.stderr.strip()}")
    return proc.stdout


def git_toplevel(path: Path) -> Path | None:
    try:
        return Path(run_git(path, "rev-parse", "--show-toplevel").strip())
    except (InputError, FileNotFoundError, NotADirectoryError):
        return None


def git_config(repo: Path, key: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), "config", "--get", key], capture_output=True, text=True)
    return proc.stdout.strip()


def identities(repo: Path, config: dict, cli: list[str]) -> list[str]:
    """Names and emails that count as the user: --author, else git config, plus config aliases."""
    found = list(cli) or [git_config(repo, "user.name"), git_config(repo, "user.email")]
    if not cli:
        found += config.get("author_aliases", [])
    unique: dict[str, str] = {}
    for item in found:
        if item.strip():
            unique.setdefault(item.strip().lower(), item.strip())
    return list(unique.values())


def trivial_hints(subject: str) -> list[str]:
    # Ignore a leading emoji or gitmoji code such as "🔀 " or ":art: ".
    subject = re.sub(r"^(?::[a-z0-9_+-]+:|[^\w\[(:])+\s*", "", subject.strip())
    return [name for name, pattern in TRIVIAL.items() if re.search(pattern, subject, re.I)]


def size_class(files: int, lines: int) -> str:
    if files > 5 or lines > 100:
        return "large"
    if files <= 2 and lines < 20:
        return "small"
    return "medium"


def parse_numstat(block: str) -> list[dict]:
    files = []
    for line in block.strip().splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            added, deleted, path = parts
            binary = added == "-"
            files.append({"path": path, "added": 0 if binary else int(added),
                          "deleted": 0 if binary else int(deleted), "generated": bool(GENERATED.search(path))})
    return files


def to_local(iso: str, tz: dt.tzinfo) -> dt.datetime:
    iso = iso[:-1] + "+00:00" if iso.endswith("Z") else iso  # Python < 3.11 rejects "Z"
    return dt.datetime.fromisoformat(iso).astimezone(tz)


def collect_repo(entry: dict, start: dt.datetime, end: dt.datetime, tz: dt.tzinfo, config: dict, args) -> dict:
    path = Path(entry["path"]).expanduser()
    result = {"name": entry.get("name") or path.name, "path": str(path), "ok": False}
    top = git_toplevel(path) if path.exists() else None
    if top is None:
        result["error"] = "path does not exist" if not path.exists() else "not a git repository"
        return result

    authors = identities(top, config, args.author)
    if not authors:
        result["error"] = "no author identity: set git user.name/user.email or pass --author"
        return result

    # --all: every local and remote-tracking branch. Committer date is never earlier than
    # author date, so --since on it is a safe lower bound; the exact window is applied below.
    raw = run_git(top, "log", "--all", "--no-merges", "--source", "--numstat",
                  "--fixed-strings", "--regexp-ignore-case", *[f"--author={a}" for a in authors],
                  f"--since={start.isoformat()}", f"--pretty=format:{LOG_FORMAT}")

    wanted = {a.lower() for a in authors}
    commits, seen, duplicates = [], set(), 0
    for record in raw.split(RECORD):
        header, _, numstat = record.partition(END)
        fields = header.split(FIELD)
        if len(fields) != 7:
            continue
        sha, name, email, authored_iso, ref, subject, body = fields
        if name.lower() not in wanted and email.lower() not in wanted:
            continue  # git matched a substring only, e.g. "Jo" inside "John"
        authored = to_local(authored_iso, tz)
        if not start <= authored <= end:
            continue
        key = (email.lower(), authored_iso, subject)  # same commit copied by cherry-pick or rebase
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)

        files = parse_numstat(numstat)
        counted = [f for f in files if not f["generated"]]
        added, deleted = sum(f["added"] for f in counted), sum(f["deleted"] for f in counted)
        largest = sorted(files, key=lambda f: f["added"] + f["deleted"], reverse=True)[: args.max_files]
        body = body.strip()
        commits.append({
            "sha": sha[:10],
            "authored_at": authored.isoformat(timespec="minutes"),
            "ref": ref,
            "subject": subject,
            "body": body[: args.body_chars] + ("…" if len(body) > args.body_chars else ""),
            "files_changed": len(counted),
            "lines_added": added,
            "lines_deleted": deleted,
            "size": size_class(len(counted), added + deleted),
            "trivial_hints": trivial_hints(subject),
            "top_files": [f"{f['path']} (+{f['added']} -{f['deleted']}){' [generated]' if f['generated'] else ''}"
                          for f in largest],
        })
    commits.sort(key=lambda c: c["authored_at"])

    git_dir = Path(run_git(top, "rev-parse", "--absolute-git-dir").strip())
    fetch_head = git_dir / "FETCH_HEAD"
    result.update({
        "ok": True,
        "path": str(top),
        "authors": authors,
        "has_remote": bool(run_git(top, "remote").strip()),
        "hours_since_fetch": round((time.time() - fetch_head.stat().st_mtime) / 3600, 1)
        if fetch_head.exists() else None,
        "commit_count": len(commits),
        "duplicates_skipped": duplicates,
        "commits": commits,
    })
    return result


def select_repos(config: dict, wanted: list[str]) -> list[dict]:
    configured = [r for r in config.get("repos", []) if r.get("path")]
    if not wanted:
        return configured or [{"path": str(Path.cwd())}]
    chosen = []
    for item in wanted:
        match = next((r for r in configured if r.get("name") == item), None)
        if match is None and not Path(item).expanduser().exists():
            names = ", ".join(r.get("name", "?") for r in configured) or "none configured"
            raise InputError(f"{item!r} is neither a configured repo ({names}) nor an existing path")
        chosen.append(match or {"path": str(Path(item).expanduser().resolve())})
    return chosen


def cmd_repos(args, config: dict) -> dict:
    repos = []
    for r in config.get("repos", []):
        path = Path(r.get("path", "")).expanduser()
        repos.append({**r, "ok": path.exists() and git_toplevel(path) is not None})
    cwd = git_toplevel(Path.cwd())
    in_config = cwd is not None and any(
        os.path.realpath(Path(r.get("path", "")).expanduser()) == os.path.realpath(cwd) for r in repos)
    return {
        "config_path": str(data_home() / "config.json"),
        "config_exists": (data_home() / "config.json").exists(),
        "repos": repos,
        "current_dir": {"git_repo": str(cwd) if cwd else None, "in_config": in_config},
    }


def cmd_collect(args, config: dict) -> dict:
    tz = resolve_tz(args.tz)
    start = dt.datetime.combine(parse_date(args.start), dt.time.min, tzinfo=tz)
    end = dt.datetime.combine(parse_date(args.end), dt.time.max, tzinfo=tz)
    if end < start:
        raise InputError("--end is before --start")
    repos = [collect_repo(r, start, end, tz, config, args) for r in select_repos(config, args.repo)]
    return {
        "timezone": args.tz,
        "start": args.start,
        "end": args.end,
        "size_rule": "large: >5 files or >100 lines; small: <=2 files and <20 lines; "
                     "lock files and build output are not counted",
        "total_commits": sum(r.get("commit_count", 0) for r in repos),
        "repos": repos,
    }


def main() -> int:
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tz", default=config.get("timezone", DEFAULT_TZ), help="time zone (default Asia/Shanghai)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("repos", help="list configured repositories")
    p = sub.add_parser("collect", help="collect commits in a date range")
    p.add_argument("--start", required=True, help="first day, YYYY-MM-DD")
    p.add_argument("--end", required=True, help="last day, YYYY-MM-DD (inclusive)")
    p.add_argument("--repo", action="append", default=[], help="configured name or path; repeatable")
    p.add_argument("--author", action="append", default=[], help="name or email; repeatable")
    p.add_argument("--max-files", type=int, default=5, help="largest files listed per commit (default 5)")
    p.add_argument("--body-chars", type=int, default=300, help="commit body characters kept (default 300)")
    p.add_argument("--output", help="write the JSON to this file instead of printing it")
    args = parser.parse_args()

    out = cmd_repos(args, config) if args.command == "repos" else cmd_collect(args, config)
    text = json.dumps(out, ensure_ascii=False, indent=2)
    if getattr(args, "output", None):
        Path(args.output).expanduser().write_text(text + "\n", encoding="utf-8")
        print(json.dumps({"written": args.output, "total_commits": out["total_commits"]}))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
