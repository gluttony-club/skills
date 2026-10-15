---
name: weekly-recap
description: Write a weekly recap (周报) from the user's own git commits across their repositories, to present at the weekly team meeting what they did, highlights, hard problems and pitfalls, with links. Use when the user asks for a weekly report or recap, 周报, 写周报, 周会汇报, or what they did this week or last week.
license: MIT
metadata:
  author: gluttony-club
  version: "0.1.0"
---

# Weekly recap

Turn the user's git commits from one week into a short recap, grouped by project,
that they can present at the weekly team meeting.

`<skill-dir>` below is the directory containing this SKILL.md. Scripts need
Python 3.9+ (`python3`; on Windows `py -3`) and print JSON.

## Steps

0. Load context:

   ```bash
   python3 <skill-dir>/scripts/store.py list --latest 2
   ```

   If `style_path` is set, read it: these are the user's own preferences and
   override the writing guide. Skim the latest recaps for continuity (ongoing
   work, the user's wording); do not copy their mistakes.

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
   Confirm the resolved `start ~ end` with the user before continuing. Every
   range is in the user's local time zone (this machine's), from 00:00:00 on the
   first day to 23:59:59 on the last (`start_at`, `end_at`).
2. Choose the repositories:

   ```bash
   python3 <skill-dir>/scripts/collect_commits.py repos
   ```

   It lists the repos in `~/.weekly-recap/config.json` (`ok: false` means the
   path is missing or not a git repo) and whether the current directory is a
   git repo outside the config. Let the user pick some or all, and offer to
   include the current repo. With no config, use the current repo or paths the
   user gives.

   Offer to remember a repo for next time, and only if the user agrees run
   `python3 <skill-dir>/scripts/store.py add-repo [PATH] [--name NAME]` (it
   creates the config if needed and backs it up before changing it). If it
   returns `added: false` with a `conflict`, the name is taken: ask the user for
   another and re-run with `--name`. Config keys are described in
   [references/data.md](references/data.md).

3. Collect the commits:

   ```bash
   python3 <skill-dir>/scripts/collect_commits.py collect --start START --end END \
     [--repo NAME_OR_PATH ...] [--author NAME_OR_EMAIL ...] [--output]
   ```

   - `--repo` takes a configured name or a path and can repeat; without it,
     every configured repo is used.
   - Commits are the user's own (git `user.name` / `user.email` of each repo, or
     `--author`), on every branch, authored within the range, merges excluded.
   - For long ranges add `--output` with no file name: the JSON goes to the
     system temp directory, never into a repository, and `written` gives the
     path to read.

   Then check each repo in the output:
   - `ok: false`: tell the user the `error` and carry on with the others.
   - No commits anywhere: say so and ask whether the range or the author
     identity is wrong before writing anything.

   Do not fetch or ask about fetching: the user's own commits are already in
   local history. Only if the user says work is missing (made on another
   machine, in the cloud, or squash-merged on the web), offer
   `git -C <path> fetch --all --prune`, run it once they agree, and collect again.

4. Judge what matters. `size` is `large` (>5 files or >100 lines), `medium`, or
   `small` (≤2 files and <20 lines); lock files and build output are not counted.
   `trivial_hints` flags subjects like merge, typo, format, deps, wip. Read the
   subject and body to understand each commit; for a large commit whose purpose
   is unclear, look at `git -C <path> show --stat <sha>`.

   Watch for squash merges done on the web: a subject ending in `(#N)` with a
   PR whose `merged_at` is null. While its feature branch still exists, the same
   work also appears as that branch's own commits, so it is counted twice. Treat
   them as one work item linked to the PR, and do not add up their sizes.

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

6. Write the recap in Markdown. Before writing, read
   [references/writing-guide.md](references/writing-guide.md) (layout, budget,
   emphasis, links, hard problems and pitfalls) and
   [references/examples.md](references/examples.md) (a full example and
   before/after pairs). The title is `# 周报 (START ~ END)` with the range from
   step 1; each repo section is named by its `name`.

   For links: when a commit has several `prs`, use the one whose `from_branch`
   is the feature branch rather than a release, test or sync branch; without a
   PR use `commit_url`; with neither, no link.

7. Show the draft to the user as Markdown and apply their changes.

8. Save it once the user is happy. Pass the final Markdown on stdin with a
   quoted heredoc, so no temporary file lands in a repository:

   ```bash
   python3 <skill-dir>/scripts/store.py save --start START --end END <<'RECAP'
   # 周报 (START ~ END)
   …the final Markdown…
   RECAP
   ```

   If it returns `"exists": true` (exit code 3), a recap for this range is
   already saved: ask whether to replace it, and only then re-run with
   `--overwrite` (the old file is kept as `.bak-<time>`). Tell the user the
   saved `path`.

9. Learn preferences. If the user's edits in step 7 reflect a lasting
   preference (wording, emphasis, a section they always drop), ask whether to
   remember it, and only then append one short line to `style.md` in
   `data_home` (from step 0), e.g.
   `printf '%s\n' '- 本周重点最多两条' >> "<data_home>/style.md"`. Never record
   report content there.

## Rules

- Only report what the commits and the user's answers support.
- Describe outcomes, not file edits. No type tags like `[feat]`; hashes only
  as link text.
- Merge related commits into one item; drop trivial ones.
