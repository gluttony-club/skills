#!/usr/bin/env python3
"""Resolve the date range for a weekly recap and print it as JSON.

Weeks run Monday to Sunday in the given time zone (default Asia/Shanghai).

  date_range.py presets               this week and last week
  date_range.py week DATE             the week containing DATE (YYYY-MM-DD)
  date_range.py period START [END]    START to END inclusive; END defaults to today

Uses only the Python standard library (3.9+).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys

DEFAULT_TZ = "Asia/Shanghai"
# Used only when the IANA time zone database is missing (e.g. Windows without tzdata).
FALLBACK_HOURS = {"Asia/Shanghai": 8, "UTC": 0}
OFFSET_RE = re.compile(r"^([+-])(\d{1,2}):?(\d{2})?$")


class InputError(Exception):
    pass


def resolve_tz(name: str) -> dt.tzinfo:
    """Accept an IANA name such as Asia/Shanghai or an offset such as +08:00."""
    match = OFFSET_RE.match(name)
    if match:
        sign, hours, minutes = match.groups()
        delta = dt.timedelta(hours=int(hours), minutes=int(minutes or 0))
        return dt.timezone(-delta if sign == "-" else delta)
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(name)
    except Exception:
        if name in FALLBACK_HOURS:
            return dt.timezone(dt.timedelta(hours=FALLBACK_HOURS[name]))
        raise InputError(f"unknown time zone {name!r}; use a name like Asia/Shanghai or an offset like +08:00")


def parse_date(text: str) -> dt.date:
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        raise InputError(f"invalid date {text!r}, expected YYYY-MM-DD") from None


def describe(start: dt.date, end: dt.date) -> dict:
    """A Monday-to-Sunday range is a 'week' and gets its ISO week number."""
    if end < start:
        raise InputError(f"end date {end} is before start date {start}")
    result = {"start": start.isoformat(), "end": end.isoformat(), "days": (end - start).days + 1}
    if start.weekday() == 0 and end - start == dt.timedelta(days=6):
        iso_year, iso_week, _ = start.isocalendar()
        result.update(kind="week", iso_year=iso_year, iso_week=iso_week)
    else:
        result["kind"] = "period"
    return result


def week_of(day: dt.date) -> dict:
    monday = day - dt.timedelta(days=day.weekday())
    return describe(monday, monday + dt.timedelta(days=6))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tz", default=DEFAULT_TZ, help=f"time zone (default {DEFAULT_TZ})")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("presets", help="this week and last week")
    p_week = sub.add_parser("week", help="the week containing DATE")
    p_week.add_argument("date")
    p_period = sub.add_parser("period", help="START to END inclusive")
    p_period.add_argument("start")
    p_period.add_argument("end", nargs="?")
    args = parser.parse_args()

    tz = resolve_tz(args.tz)
    today = dt.datetime.now(tz).date()
    out = {"timezone": args.tz, "today": today.isoformat()}

    if args.command == "presets":
        out["this_week"] = week_of(today)
        out["last_week"] = week_of(today - dt.timedelta(days=7))
    elif args.command == "week":
        out["range"] = week_of(parse_date(args.date))
    else:
        end = parse_date(args.end) if args.end else today
        out["range"] = describe(parse_date(args.start), end)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
