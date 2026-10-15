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
2. Choose the repositories:

   ```bash
   python3 <skill-dir>/scripts/collect_commits.py repos
   ```

   It lists the repos in `~/.weekly-recap/config.json` (`ok: false` means the
   path is missing or not a git repo) and whether the current directory is a
   git repo outside the config. Let the user pick some or all, and offer to
   include the current repo. With no config, use the current repo or paths the
   user gives. The config looks like this; create or edit it only if the user
   asks:

   ```json
   { "repos": [ { "name": "project-a", "path": "/path/to/project-a" } ] }
   ```

   Links are detected for GitHub, GitLab, CNB, Gitee and Bitbucket remotes. For
   other hosts a repo entry may add
   `"links": {"commit": "https://host/…/{sha}", "pr": "https://host/…/{number}"}`.

3. Collect the commits:

   ```bash
   python3 <skill-dir>/scripts/collect_commits.py collect --start START --end END \
     [--repo NAME_OR_PATH ...] [--author NAME_OR_EMAIL ...] [--output FILE]
   ```

   - `--repo` takes a configured name or a path and can repeat; without it,
     every configured repo is used.
   - Commits are the user's own (git `user.name` / `user.email` of each repo, or
     `--author`), on every branch, authored within the range, merges excluded.
   - Use `--output FILE` for long ranges and read the file.

   Then check each repo in the output:
   - `ok: false`: tell the user the `error` and carry on with the others.
   - `has_remote: true` and `hours_since_fetch` null or above 24: commits pushed
     from elsewhere may be missing. Offer `git -C <path> fetch --all --prune`; run
     it only if the user agrees, then collect again.
   - No commits anywhere: say so and ask whether the range or the author
     identity is wrong before writing anything.

4. Judge what matters. `size` is `large` (>5 files or >100 lines), `medium`, or
   `small` (≤2 files and <20 lines); lock files and build output are not counted.
   `trivial_hints` flags subjects like merge, typo, format, deps, wip. Read the
   subject and body to understand each commit; for a large commit whose purpose
   is unclear, look at `git -C <path> show --stat <sha>`.

   Each repo also has `signals`, pointers to what may be worth telling:
   - `topics`: commits grouped by conventional-commit scope, largest first; a
     starting point for merging commits into work items.
   - `repeated_fixes`: files hit by several commits including two or more fixes,
     a sign of a hard problem or a pitfall.
   - `reverts`: work that was undone, often a pitfall.
   - `explained`: commits whose body explains why; read these for causes and
     trade-offs.

5. Ask about highlights and pitfalls. Git shows what changed, rarely what was
   hard or what was learned. From the signals, name 1–3 candidates (e.g. "the
   upload fixes on Safari look like a hard problem") and ask the user in one
   message what was hard, the root cause, or the lesson. Accept "skip" and write
   without them; never invent causes the user did not give and the commits do
   not show.

6. Write the report in this shape, with one block per repo, named by its
   `name`. The title uses the range from step 1:

   ```markdown
   # 周报 (2026-10-12 ~ 2026-10-18)

   project-name

   - 完成订阅支付接入（[#128](https://example.com/pr/128)）
     - 对接下单与回调接口
   - 修复登录态丢失问题（[a1b2c3d](https://example.com/commit/a1b2c3d)）
   ```

   Links: give each main item one link at the end. Prefer its pull request
   (`prs[].url`; when there are several, the one whose `from_branch` is the
   feature branch rather than a release or sync), else its main commit
   (`commit_url`, shown as the 7-character sha). Leave the link out when the
   URL is null.

7. Show the draft to the user and apply their changes.

## Rules

- Describe outcomes, not file edits. No type tags like `[feat]`; hashes only
  as link text.
- Merge related commits into one item. Drop trivial ones (formatting, typos, merges).
- Large changes and repeated fixes of one problem deserve detail; small ones
  get one line or are merged.
- Only report what the commits support.
