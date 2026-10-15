#!/usr/bin/env python3
"""Local data for weekly recaps: config, saved recaps, personal style notes.

  store.py add-repo [PATH] [--name NAME]    add a repo to config.json (creates it);
                                            a taken name becomes "parent/dir"
  store.py list [--latest N]                saved recaps, oldest first
  store.py path --start DATE --end DATE     where the recap for a range is saved
  store.py save --start DATE --end DATE [--input FILE] [--overwrite] [--copy]
  store.py text --start DATE --end DATE [--copy]
                                            the saved recap as plain text for a spreadsheet
                                            cell or a chat; --copy puts it on the clipboard

Data lives in $WEEKLY_RECAP_HOME (default ~/.weekly-recap):

  config.json              repos, optional author_aliases
  style.md                 the user's own writing preferences (optional)
  2026/26.10.12-26.10.18.md   one recap, named by its range (YY.MM.DD), under its start year

Nothing is ever deleted; replacing a recap keeps a .bak copy beside it.
Uses only the Python standard library (3.9+).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plain  # noqa: E402
from date_range import InputError, describe, parse_date  # noqa: E402

TITLE = re.compile(r"^#\s*[^(（]*[(（]\s*(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})\s*[)）]")
RANGE_FILE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{2})-(\d{2})\.(\d{2})\.(\d{2})\.md$")
# Names used before 0.6.0, still read and renamed on the next save of the same range.
WEEK_FILE = re.compile(r"^week-(\d{2})\.md$")
PERIOD_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})\.md$")


def data_home() -> Path:
    env = os.environ.get("WEEKLY_RECAP_HOME")
    return Path(env).expanduser() if env else Path.home() / ".weekly-recap"


def config_path() -> Path:
    return data_home() / "config.json"


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InputError(f"{path} is not valid JSON: {exc}") from None


def write_atomic(path: Path, text: str) -> None:
    """Write to a temp file, then rename, so a crash never leaves half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def backup(path: Path) -> Path:
    target = path.with_name(f"{path.name}.bak-{dt.datetime.now():%Y%m%d%H%M%S}")
    shutil.copy2(path, target)
    return target


def recap_path(start: str, end: str) -> tuple[Path, dict]:
    """<start year>/YY.MM.DD-YY.MM.DD.md, e.g. 2026/26.10.12-26.10.18.md, for any range."""
    first, last = parse_date(start), parse_date(end)
    rng = describe(first, last)
    return data_home() / str(first.year) / f"{first:%y.%m.%d}-{last:%y.%m.%d}.md", rng


def legacy_path(rng: dict) -> Path:
    """Where a recap for this range was saved before 0.6.0."""
    if rng["kind"] == "week":
        return data_home() / str(rng["iso_year"]) / f"week-{rng['iso_week']:02d}.md"
    return data_home() / rng["start"][:4] / f"{rng['start']}_to_{rng['end']}.md"


def current_path(start: str, end: str) -> tuple[Path, dict]:
    """The recap's path, after renaming a file saved under the old name to the new one."""
    path, rng = recap_path(start, end)
    old = legacy_path(rng)
    if not path.exists() and old.exists():
        os.replace(old, path)
    return path, rng


def cmd_add_repo(args) -> dict:
    proc = subprocess.run(["git", "-C", args.path, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if proc.returncode != 0:
        raise InputError(f"{args.path} is not inside a git repository")
    top = proc.stdout.strip()
    config = load_config()
    repos = config.setdefault("repos", [])
    for repo in repos:
        if os.path.realpath(os.path.expanduser(repo.get("path", ""))) == os.path.realpath(top):
            return {"added": False, "reason": "already configured", "repo": repo}
    wanted = args.name or Path(top).name
    name = unique_name(wanted, Path(top), {r.get("name") for r in repos})
    saved = backup(config_path()) if config_path().exists() else None
    repos.append({"name": name, "path": top})
    write_atomic(config_path(), json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    return {"added": True, "repo": {"name": name, "path": top}, "renamed_from": wanted if name != wanted else None,
            "config_path": str(config_path()), "backup": str(saved) if saved else None}


def unique_name(wanted: str, top: Path, taken: set) -> str:
    """The wanted name if free, else "parent/dir", else that with a number, so adding never stops to ask."""
    if wanted not in taken:
        return wanted
    base = f"{top.parent.name}/{top.name}"
    candidates = [base] + [f"{base}-{i}" for i in range(2, 100)]
    return next(c for c in candidates if c not in taken)


def describe_file(path: Path) -> dict | None:
    named, week, period = (RANGE_FILE.match(path.name), WEEK_FILE.match(path.name),
                           PERIOD_FILE.match(path.name))
    if not (named or week or period):
        return None
    with path.open(encoding="utf-8", errors="replace") as fh:
        title = TITLE.match(fh.readline().strip())
    try:
        if title:  # the heading is the source of truth for the range
            start, end = title.groups()
        elif named:
            y1, m1, d1, y2, m2, d2 = named.groups()
            start, end = f"20{y1}-{m1}-{d1}", f"20{y2}-{m2}-{d2}"
        elif period:
            start, end = period.groups()
        else:
            monday = dt.date.fromisocalendar(int(path.parent.name), int(week.group(1)), 1)
            start, end = monday.isoformat(), (monday + dt.timedelta(days=6)).isoformat()
        kind = describe(parse_date(start), parse_date(end))["kind"]
    except (ValueError, InputError):
        return None
    return {"path": str(path), "start": start, "end": end, "kind": kind}


def cmd_list(args) -> dict:
    home = data_home()
    recaps = []
    for year_dir in sorted(p for p in home.glob("[0-9][0-9][0-9][0-9]") if p.is_dir()):
        for path in year_dir.glob("*.md"):
            entry = describe_file(path)
            if entry:
                recaps.append(entry)
    # One entry per range: a file under the current name wins over an old-style one.
    by_range: dict = {}
    for entry in recaps:
        key = (entry["start"], entry["end"])
        if key not in by_range or RANGE_FILE.match(Path(entry["path"]).name):
            by_range[key] = entry
    recaps = list(by_range.values())
    recaps.sort(key=lambda r: (r["start"], r["end"]))
    if args.latest:
        recaps = recaps[-args.latest:]
    style = home / "style.md"
    return {"data_home": str(home), "style_path": str(style) if style.exists() else None,
            "count": len(recaps), "recaps": recaps}


def cmd_path(args) -> dict:
    path, rng = current_path(args.start, args.end)
    return {"path": str(path), "exists": path.exists(), "range": rng}


def cmd_save(args) -> dict:
    path, rng = current_path(args.start, args.end)
    text = sys.stdin.read() if args.input == "-" else Path(args.input).expanduser().read_text(encoding="utf-8")
    if not text.strip():
        raise InputError("the recap is empty")
    saved = None
    if path.exists():
        if not args.overwrite:
            return {"saved": False, "exists": True, "path": str(path),
                    "hint": "ask the user, then re-run with --overwrite (a .bak copy is kept)"}
        saved = backup(path)
    write_atomic(path, text if text.endswith("\n") else text + "\n")
    out = {"saved": True, "path": str(path), "range": rng, "backup": str(saved) if saved else None}
    return {**out, **plain_output(text, args.copy)}


def plain_output(markdown: str, copy: bool) -> dict:
    """The plain text, which the user is shown to copy, and whether it is also on the clipboard."""
    text = plain.plain_text(markdown)
    tool = plain.copy_to_clipboard(text) if copy else None
    return {"plain_text": text, "copied": tool is not None, "clipboard": tool}


def cmd_text(args) -> dict:
    path, _ = current_path(args.start, args.end)
    if not path.exists():
        raise InputError(f"no recap saved for {args.start} ~ {args.end}")
    return {"path": str(path), **plain_output(path.read_text(encoding="utf-8"), args.copy)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("add-repo", help="add a repo to config.json")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--name", help="section name in recaps (default: directory name)")
    p = sub.add_parser("list", help="saved recaps, oldest first")
    p.add_argument("--latest", type=int, metavar="N", help="only the N most recent")
    for name in ("path", "save", "text"):
        p = sub.add_parser(name)
        p.add_argument("--start", required=True)
        p.add_argument("--end", required=True)
        if name == "save":
            p.add_argument("--input", default="-", help="Markdown file, or - for stdin (default)")
            p.add_argument("--overwrite", action="store_true", help="replace an existing recap, keeping a backup")
        if name in ("save", "text"):
            p.add_argument("--copy", action="store_true", help="copy the plain-text form to the clipboard")
    args = parser.parse_args()

    handler = {"add-repo": cmd_add_repo, "list": cmd_list, "path": cmd_path, "save": cmd_save,
               "text": cmd_text}[args.command]
    out = handler(args)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 3 if out.get("exists") and not out.get("saved", True) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
