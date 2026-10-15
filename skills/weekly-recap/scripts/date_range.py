#!/usr/bin/env python3
"""Resolve the date range for a weekly recap and print it as JSON.

All times are in this machine's local time zone. A range runs from 00:00:00 on
its first day to 23:59:59 on its last; a week runs Monday to Sunday.

  date_range.py presets               this week and last week
  date_range.py week DATE             the week containing DATE (YYYY-MM-DD)
  date_range.py period START [END]    START to END inclusive; END defaults to today

Uses only the Python standard library (3.9+).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys


class InputError(Exception):
    pass


def parse_date(text: str) -> dt.date:
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        raise InputError(f"invalid date {text!r}, expected YYYY-MM-DD") from None


def local_timezone() -> str:
    """This machine's time zone as shown to the user, e.g. "CST (UTC+08:00)"."""
    now = dt.datetime.now().astimezone()
    offset = now.strftime("%z")
    return f"{now.tzname()} (UTC{offset[:3]}:{offset[3:]})"


def bounds(start: dt.date, end: dt.date) -> tuple[dt.datetime, dt.datetime]:
    """First and last second of the range in local time, both inclusive.

    astimezone() on a naive time reads it as local time with that day's offset,
    so a range across a daylight saving change still starts and ends at midnight.
    """
    if end < start:
        raise InputError(f"end date {end} is before start date {start}")
    return (dt.datetime.combine(start, dt.time(0, 0, 0)).astimezone(),
            dt.datetime.combine(end, dt.time(23, 59, 59)).astimezone())


def describe(start: dt.date, end: dt.date) -> dict:
    """A Monday-to-Sunday range is a 'week' and gets its ISO week number."""
    first, last = bounds(start, end)
    result = {"start": start.isoformat(), "end": end.isoformat(), "days": (end - start).days + 1,
              "start_at": first.isoformat(), "end_at": last.isoformat()}
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
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("presets", help="this week and last week")
    p_week = sub.add_parser("week", help="the week containing DATE")
    p_week.add_argument("date")
    p_period = sub.add_parser("period", help="START to END inclusive")
    p_period.add_argument("start")
    p_period.add_argument("end", nargs="?")
    args = parser.parse_args()

    today = dt.date.today()
    out = {"timezone": local_timezone(), "today": today.isoformat()}

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
