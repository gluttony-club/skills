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

## Steps

1. Ask the user which week: this week or last week (Monday to Sunday,
   Asia/Shanghai time). Tell them the concrete dates before continuing.
2. Find the user's identity with `git config user.name` and `git config user.email`.
3. List their commits on all branches for that week:

   ```bash
   TZ=Asia/Shanghai git log --all --no-merges \
     --author="<name or email>" \
     --since="<monday> 00:00:00" --until="<sunday> 23:59:59" \
     --pretty=format:"%h %ad %s" --date=short
   ```

4. Write the report in this shape, using the repository's directory name as the
   project name:

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
