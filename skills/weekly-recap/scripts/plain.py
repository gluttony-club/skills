"""The recap as plain text, and copying it to the clipboard.

Spreadsheet cells and many chat boxes keep only plain text: pasting rendered
Markdown loses its bullets, bold and indentation. The plain form carries the
structure in characters instead, three levels deep: "一、" for sections, "1. "
for items, "   - " for sub-items, and 【】 for bold. Every point gets its own
line. The "# 周报 (…)" title is left out, since the cell or message it goes into
already says what it is.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

HEADING = re.compile(r"^#{1,6}\s+(.*)$")
ITEM = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.*)$")
RULE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")
# An older "其他：A；B；C" line, split into one sub-item per change.
OTHER_LINE = re.compile(r"^(其他|Other)\s*[：:]\s*(.+)$", re.I)
NUMERALS = "一二三四五六七八九十"


def section_number(n: int) -> str:
    return f"{NUMERALS[n - 1]}、" if n <= len(NUMERALS) else f"{n}、"


def inline(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\((\S+?)\)", r"\1（\2）", text)  # a kept link stays readable
    text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: f"【{m.group(1) or m.group(2)}】", text)
    return re.sub(r"`([^`]+)`", r"\1", text)


def plain_text(markdown: str) -> str:
    lines: list[str] = []
    number = section = 0
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if not line.strip() or RULE.match(line):
            continue
        heading = HEADING.match(line)
        if heading:
            if line.startswith("# "):
                continue  # the title
            if lines:
                lines.append("")
            section += 1
            lines.append(section_number(section) + inline(heading.group(1)))
            number = 0
            continue
        item = ITEM.match(line)
        if item and item.group(1):
            lines.append("   - " + inline(item.group(2)))
        elif item:
            number += 1
            body = inline(item.group(2))
            other = OTHER_LINE.match(body)
            parts = [x.strip() for x in re.split(r"[；;]", other.group(2))] if other else []
            if len(parts) > 1:
                lines.append(f"{number}. {other.group(1)}")
                lines += ["   - " + part for part in parts if part]
            else:
                lines.append(f"{number}. " + body)
        else:
            lines.append(inline(line.strip()))
    return "\n".join(lines) + "\n"


def copy_to_clipboard(text: str) -> str | None:
    """Copy with the platform's clipboard tool; return the tool's name, or None if none worked."""
    if sys.platform == "darwin":
        tools = [["pbcopy"]]
    elif os.name == "nt":
        tools = [["clip"]]
    else:
        tools = [["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]
    for tool in tools:
        if not shutil.which(tool[0]):
            continue
        # clip reads UTF-16 with a BOM; pbcopy needs a UTF-8 locale or it garbles Chinese.
        data = ("﻿" + text).encode("utf-16-le") if tool[0] == "clip" else text.encode("utf-8")
        env = {**os.environ, "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}
        try:
            # No captured output: xclip and wl-copy stay alive to serve the selection.
            subprocess.run(tool, input=data, env=env, check=True, timeout=5,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError):
            continue
        return tool[0]
    return None
