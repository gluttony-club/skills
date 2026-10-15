---
name: weekly-recap
description: Write a weekly recap (周报) of the user's own git commits in the current repository, to present at the weekly team meeting what they did and what is worth sharing. Use when the user asks for a weekly report or recap, 周报, 写周报, or what they did this week or last week.
license: MIT
metadata:
  author: gluttony-club
  version: "0.0.1"
---

# Weekly recap

Turn the user's git commits from one week into a short recap, grouped by project,
that they can present at the weekly team meeting.

`<skill-dir>` below is the directory containing this SKILL.md. Scripts need
Python 3.9+ (`python3`; on Windows `py -3`) and print JSON.

## Steps

1. Choose the date range. Never compute dates yourself; use the script:

   ```bash
   python3 <skill-dir>/scripts/date_range.py presets
   ```

   Offer the user, with the concrete dates from the output:
   - this week (`this_week`)
   - last week (`last_week`)
   - another week: ask for any date in it, then run `date_range.py week DATE`
   - a custom range, e.g. across a holiday: ask for the start and end dates, then
     run `date_range.py period START [END]` (END defaults to today)

   Ask for dates in a plain message. If your environment has a multiple-choice
   prompt, use it only to pick among the options above, never for typing dates.
   Confirm the resolved `start ~ end` with the user before continuing.
2. Find the user's identity with `git config user.name` and `git config user.email`.
3. List their commits on all branches in that range, using `start` and `end`
   from step 1:

   ```bash
   TZ=Asia/Shanghai git log --all --no-merges \
     --author="<name or email>" \
     --since="<start> 00:00:00" --until="<end> 23:59:59" \
     --pretty=format:"%h %ad %s" --date=short
   ```

4. Write the report in this shape, using the repository's directory name as the
   project name. The title uses the range from step 1:

   ```markdown
   # 周报 (2026-10-12 ~ 2026-10-18)

   project-name

   - 完成订阅支付接入
     - 对接下单与回调接口
   - 修复登录态丢失问题
   ```

5. Show the draft to the user and apply their changes.

## Rules

- Describe outcomes, not file edits. No type tags like `[feat]` or commit hashes.
- Merge related commits into one item. Drop trivial ones (formatting, typos, merges).
- Only report what the commits support.
