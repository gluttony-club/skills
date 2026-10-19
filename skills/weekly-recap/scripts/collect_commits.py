#!/usr/bin/env python3
"""Collect the user's own git commits across repositories as JSON.

  collect_commits.py repos
      configured repositories, most recently committed to first, and the current directory
  collect_commits.py collect --start DATE --end DATE [--repo NAME_OR_PATH ...]
      commits authored in the range, with change sizes, links and clues, per repository

Repositories come from $WEEKLY_RECAP_HOME/config.json (default ~/.weekly-recap),
or from --repo. Before collecting, each repository's remotes are fetched so that
merges done on the web count (see progress.py); --no-fetch or "fetch": false in
config.json skips that. Uses only the Python standard library (3.9+).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import links  # noqa: E402
import progress  # noqa: E402
import signals  # noqa: E402
from date_range import InputError, bounds, local_timezone, parse_date  # noqa: E402
from store import config_path, load_config  # noqa: E402

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
    "typo": r"\btypos?\b|错别字",
    "format": r"\b(format(ting)?|prettier|lint|eslint|stylelint)\b|格式化",
    "deps": r"^(chore|build)\(deps(-dev)?\)|\bbump\b|升级依赖|更新依赖",
    "wip": r"^(wip|tmp|temp)\b",
    "debug-log": r"console\.log|debug log|调试日志",
    "release": r"^(chore\(release\)|release\b)|^v?\d+\.\d+\.\d+$",
}


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


def same_path(a: str | Path, b: str | Path) -> bool:
    return os.path.realpath(Path(a).expanduser()) == os.path.realpath(Path(b).expanduser())


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


def to_local(iso: str) -> dt.datetime:
    iso = iso[:-1] + "+00:00" if iso.endswith("Z") else iso  # Python < 3.11 rejects "Z"
    return dt.datetime.fromisoformat(iso).astimezone()  # this machine's local time zone


def collect_repo(entry: dict, start: dt.datetime, end: dt.datetime, config: dict, args,
                 fetched: dict | None = None) -> dict:
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
    commits, seen, duplicates, file_lists = [], set(), 0, {}
    for record in raw.split(RECORD):
        header, _, numstat = record.partition(END)
        fields = header.split(FIELD)
        if len(fields) != 7:
            continue
        sha, name, email, authored_iso, ref, subject, body = fields
        if name.lower() not in wanted and email.lower() not in wanted:
            continue  # git matched a substring only, e.g. "Jo" inside "John"
        authored = to_local(authored_iso)
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
        kind, scope = signals.conventional(subject)
        file_lists[sha] = [f["path"] for f in counted]
        commits.append({
            "sha": sha,
            "authored_at": authored.isoformat(timespec="minutes"),
            "ref": ref,
            "subject": subject,
            "type": kind,
            "scope": scope,
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

    urls = links.templates(top, entry)
    prs = links.pull_requests(top, start.isoformat(), {c["sha"] for c in commits})
    for c in commits:
        found = prs.get(c["sha"], [])
        squashed = links.squash_pr(c["subject"])
        if squashed and all(p["number"] != squashed for p in found):
            found.append({"number": squashed, "merged_at": None, "from_branch": None})
        c["commit_url"] = urls["commit"].format(sha=c["sha"]) if "commit" in urls else None
        c["prs"] = [{**p, "url": urls["pr"].format(number=p["number"]) if "pr" in urls else None}
                    for p in found]
    refs, labels = progress.statuses(top, config, start.isoformat(), commits)
    for c in commits:
        c["status"] = labels.get(c["sha"])  # None: on no progress branch yet, i.e. in progress
        for p in c["prs"]:
            p.pop("merge_sha", None)
    clues = signals.build(commits, file_lists)
    for c in commits:
        c["sha"] = c["sha"][:10]
    for group in (clues["topics"], clues["repeated_fixes"]):
        for item in group:
            item["commits"] = [sha[:10] for sha in item["commits"]]
    clues["explained"] = [sha[:10] for sha in clues["explained"]]
    for item in clues["reverts"]:
        item["sha"] = item["sha"][:10]

    result.update({
        "ok": True,
        "path": str(top),
        "authors": authors,
        "web_url": urls["web_url"],
        "forge": urls["forge"],
        **(fetched or {"fetched": None}),
        "status_branches": refs,
        "commit_count": len(commits),
        "duplicates_skipped": duplicates,
        "signals": clues,
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
        if match is None:
            path = Path(item).expanduser()
            if not path.exists():
                names = ", ".join(r.get("name", "?") for r in configured) or "none configured"
                raise InputError(f"{item!r} is neither a configured repo ({names}) nor an existing path")
            # A path to a configured repo keeps its name and link settings.
            top = git_toplevel(path)
            match = next((r for r in configured if top and same_path(r["path"], top)), None)
        chosen.append(match or {"path": str(Path(item).expanduser().resolve())})
    return chosen


def last_own_commit(top: Path, config: dict) -> str | None:
    """Author date of the user's latest commit on any branch, in local time; None if there is none."""
    authors = identities(top, config, [])
    if not authors:
        return None
    try:
        raw = run_git(top, "log", "--all", "--no-merges", "-n", "50", "--fixed-strings", "--regexp-ignore-case",
                      *[f"--author={a}" for a in authors], "--format=%aI%x1f%an%x1f%ae")
    except InputError:
        return None
    wanted = {a.lower() for a in authors}
    dates = [to_local(iso) for iso, name, email in (line.split("\x1f") for line in raw.splitlines())
             if name.lower() in wanted or email.lower() in wanted]
    return max(dates).isoformat(timespec="minutes") if dates else None


def cmd_repos(args, config: dict) -> dict:
    repos = []
    for r in config.get("repos", []):
        path = Path(r.get("path", "")).expanduser()
        top = git_toplevel(path) if path.exists() else None
        repos.append({**r, "ok": top is not None, "last_commit_at": last_own_commit(top, config) if top else None})
    # Most recently committed to first, so the likeliest picks lead the list.
    repos.sort(key=lambda r: r["last_commit_at"] or "", reverse=True)
    cwd = git_toplevel(Path.cwd())
    configured = next((r for r in repos if cwd and same_path(r.get("path", ""), cwd)), None)
    return {
        "config_path": str(config_path()),
        "config_exists": config_path().exists(),
        "repos": repos,
        "current_dir": {
            "git_repo": str(cwd) if cwd else None,
            "name": (configured or {}).get("name") or (cwd.name if cwd else None),
            "in_config": configured is not None,
            "last_commit_at": last_own_commit(cwd, config) if cwd else None,
        },
    }


def cmd_collect(args, config: dict) -> dict:
    start, end = bounds(parse_date(args.start), parse_date(args.end))
    entries = select_repos(config, args.repo)
    tops = [git_toplevel(Path(e["path"]).expanduser()) for e in entries]
    fetched = {}
    if not args.no_fetch and config.get("fetch", True):
        fetched = progress.fetch_all([t for t in tops if t is not None])
    repos = [collect_repo(e, start, end, config, args, fetched.get(t)) for e, t in zip(entries, tops)]
    return {
        "timezone": local_timezone(),
        "start": args.start,
        "end": args.end,
        "start_at": start.isoformat(),
        "end_at": end.isoformat(),
        "size_rule": "large: >5 files or >100 lines; small: <=2 files and <20 lines; "
                     "lock files and build output are not counted",
        "total_commits": sum(r.get("commit_count", 0) for r in repos),
        "repos": repos,
    }


def main() -> int:
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("repos", help="list configured repositories")
    p = sub.add_parser("collect", help="collect commits in a date range")
    p.add_argument("--start", required=True, help="first day, YYYY-MM-DD")
    p.add_argument("--end", required=True, help="last day, YYYY-MM-DD (inclusive)")
    p.add_argument("--repo", action="append", default=[], help="configured name or path; repeatable")
    p.add_argument("--author", action="append", default=[], help="name or email; repeatable")
    p.add_argument("--no-fetch", action="store_true", help="use local history only; do not fetch remotes")
    p.add_argument("--max-files", type=int, default=5, help="largest files listed per commit (default 5)")
    p.add_argument("--body-chars", type=int, default=300, help="commit body characters kept (default 300)")
    p.add_argument("--output", nargs="?", const="", metavar="FILE",
                   help="write the JSON to FILE instead of printing it; with no FILE, to the system temp directory")
    args = parser.parse_args()

    out = cmd_repos(args, config) if args.command == "repos" else cmd_collect(args, config)
    text = json.dumps(out, ensure_ascii=False, indent=2)
    output = getattr(args, "output", None)
    if output is not None:
        if output:
            target = Path(output).expanduser()
            target.write_text(text + "\n", encoding="utf-8")
        else:
            # A new file in the system temp directory, outside any repository and readable
            # only by the user (mkstemp creates it with mode 0600 and a unique name).
            fd, name = tempfile.mkstemp(prefix=f"weekly-recap-{args.start}_{args.end}-", suffix=".json")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
            target = Path(name)
        print(json.dumps({"written": str(target), "total_commits": out["total_commits"]}))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
