---
name: weekly-recap
description: Write a weekly recap (周报) from the user's own git commits across their repositories, to present at the weekly team meeting what they did, highlights, hard problems and pitfalls, with links. Use when the user asks for a weekly report or recap, 周报, 写周报, 周会汇报, or what they did this week or last week.
license: MIT
metadata:
  author: gluttony-club
  version: "0.3.0"
---

# Weekly recap

Turn the user's git commits from one week into a short recap, grouped by project,
that they can present at the weekly team meeting.

`<skill-dir>` below is the directory containing this SKILL.md. Scripts need
Python 3.9+ (`python3`; on Windows `py -3`) and print JSON.

## Flow

The user answers **one prompt with two questions**, the range and the repos,
and nothing else before the recap is written and saved. Do not ask anything not listed here:
no date confirmation, no "remember this repo?", no questions about hard
problems before writing, no "replace the saved recap?". Skip a question the
user's request already answers ("上周的周报", "tad_web 的周报").

## Steps

0. Load context, all at once:

   ```bash
   python3 <skill-dir>/scripts/store.py list --latest 2
   python3 <skill-dir>/scripts/date_range.py presets
   python3 <skill-dir>/scripts/collect_commits.py repos
   ```

   If `style_path` is set, read it: these are the user's own preferences and
   override the writing guide. Skim the latest recaps for continuity (ongoing
   work, the user's wording); do not copy their mistakes. Never compute dates
   yourself.

1. Ask the two questions in one prompt. With a multiple-choice tool, put both
   questions in a single call; without one, ask both in one plain message.

   - **Range** (single choice): this week and last week, each labelled with its
     dates from `presets` (e.g. "本周 10/12–10/18"). The tool's free-text
     "Other" takes a custom range or any date; resolve it with
     `date_range.py period START [END]` or `date_range.py week DATE` and go on
     without confirming it.
   - **Repos** (multiple choice): `current_dir` first, labelled as the current
     directory, then configured repos in the order `repos` lists them (most
     recently committed to first). If they do not all fit, add an option for
     "all N remembered repos". "Other" takes a path or a configured name; a
     path not yet configured is new. Skip `current_dir` when it is not a git
     repo; with neither a current repo nor a config, ask for paths only.

   Every range is in the user's local time zone (this machine's), from 00:00:00
   on the first day to 23:59:59 on the last (`start_at`, `end_at`).

2. Remember every picked repo that is not configured yet, the current directory
   included, without asking:

   ```bash
   python3 <skill-dir>/scripts/store.py add-repo PATH
   ```

   A taken name becomes `parent/dir` (`renamed_from` says so). Config keys are
   described in [references/data.md](references/data.md).

3. Collect the commits:

   ```bash
   python3 <skill-dir>/scripts/collect_commits.py collect --start START --end END \
     [--repo NAME_OR_PATH ...] [--author NAME_OR_EMAIL ...] [--output]
   ```

   - Pass each picked repo with `--repo` (a configured name or a path); without
     it, every configured repo is used.
   - Commits are the user's own (git `user.name` / `user.email` of each repo, or
     `--author`), on every branch, authored within the range, merges excluded.
   - For long ranges add `--output` with no file name: the JSON goes to the
     system temp directory, never into a repository, and `written` gives the
     path to read.

   Then check each repo in the output:
   - `ok: false`: tell the user the `error` and carry on with the others.
   - `commit_count: 0`: the repo had no work in the range. Leave it out of the
     recap and carry on; do not ask about it.
   - No commits in any repo: tell the user in one message, naming the range,
     the repos and the `authors` checked, and end the task. Do not ask a
     question or offer other repos, ranges or next steps; the user chose them
     already and will ask again if something was wrong.

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

5. Do not stop to ask about highlights or pitfalls. Write what the commits
   support; for a hard problem or pitfall the signals point at but no commit
   body explains, give what happened without a cause. Never invent causes.

6. Write the recap in Markdown. Before writing, read
   [references/writing-guide.md](references/writing-guide.md) (layout, budget,
   emphasis, links, hard problems and pitfalls) and
   [references/examples.md](references/examples.md) (a full example and
   before/after pairs). The title is `# 周报 (START ~ END)` with the range from
   step 1; each repo section is named by its `name`.

   For links: when a commit has several `prs`, use the one whose `from_branch`
   is the feature branch rather than a release, test or sync branch; without a
   PR use `commit_url`; with neither, no link.

7. Save it right away, replacing any recap saved for the same range (the old one
   is kept as `.bak-<time>`). Pass the Markdown on stdin with a quoted heredoc,
   so no temporary file lands in a repository:

   ```bash
   python3 <skill-dir>/scripts/store.py save --start START --end END --overwrite <<'RECAP'
   # 周报 (START ~ END)
   …the Markdown…
   RECAP
   ```

   In PowerShell, pipe a here-string instead:
   `@'…'@ | py -3 <skill-dir>/scripts/store.py save --start START --end END --overwrite`.

8. Show the recap as Markdown with the saved `path`. Below it, in one line,
   name any hard problem or pitfall that lacks a cause and say the user can add
   one; this is not a question and needs no answer. Repos left out for having
   no commits can be named in the same line.

9. If the user asks for changes, apply them and save again with `--overwrite`.
   When they state a lasting preference ("以后都…", "always…"), append one
   short line to `style.md` in `data_home` (from step 0), e.g.
   `printf '%s\n' '- 本周重点最多两条' >> "<data_home>/style.md"`. Never record
   report content there, and do not ask whether to remember a one-off edit.

## Rules

- Only report what the commits and the user's own words support.
- Describe outcomes, not file edits. No type tags like `[feat]`; hashes only
  as link text.
- Merge related commits into one item; drop trivial ones.
