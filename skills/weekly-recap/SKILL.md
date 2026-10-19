---
name: weekly-recap
description: Write a weekly recap (周报) from the user's own git commits across their repositories, for the weekly team meeting - this week's work (features, hard bug fixes, progress, what was left for others) and next week's plan. Use when the user asks for a weekly report or recap, 周报, 写周报, 周会汇报, or what they did this week or last week.
license: MIT
metadata:
  author: gluttony-club
  version: "0.7.1"
---

# Weekly recap

Turn the user's git commits from one week into a plain, true recap in two
parts, `本周工作` and `下周计划`, that they present at the weekly team meeting
and later reread for their year-end review.

`<skill-dir>` below is the directory containing this SKILL.md. Scripts need
Python 3.9+ (`python3`; on Windows `py -3`) and print JSON.

## Flow

Every request for a recap runs the whole flow from step 0, including a second
or third request in the same conversation: ask again and never reuse an
earlier answer, unless the new request itself names the range or the repos.

The user answers **one prompt with three questions**, the range, the repos and
an optional note for next week, and nothing else before the recap is written
and saved. The only exception is a repo typed in as a new path (step 2), after
which the repo question is asked again, as often as the user keeps adding
paths. Do not ask anything not listed here: no date confirmation, no "remember
this repo?", no questions about hard problems, no "replace the saved recap?",
no "fetch?". Skip a question the user's request already answers ("上周的周报",
"tad_web 的周报", "下周做积分抵扣").

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

1. Ask the three questions in one prompt. With a multiple-choice tool, put all
   of them in a single call; without one, ask them in one plain message.

   - **Range** (single choice): this week and last week, each labelled with its
     dates from `presets` (e.g. "本周 10/12–10/18"). The tool's free-text
     "Other" takes a custom range or any date; resolve it with
     `date_range.py period START [END]` or `date_range.py week DATE` and go on
     without confirming it.
   - **Repos** (multiple choice): `current_dir` first, labelled as the current
     directory, then configured repos in the order `repos` lists them (most
     recently committed to first), leaving out the configured repo that is the
     current directory (`in_config: true`) so it is listed once. If they do
     not all fit, add an option for "all N remembered repos". "Other" takes
     paths or configured names. Skip `current_dir` when it is not a git repo;
     with neither a current repo nor a config, ask for paths only.

     When the tool allows only one choice per question (Codex, for one), offer
     sets instead of single repos: the repos with a `last_commit_at` in the
     last 14 days (name them in the label), all N remembered repos, and the
     current directory alone; "Other" takes several names or paths separated
     by commas. Repos without commits are skipped later anyway, so the larger
     sets cost nothing.
   - **Next week** (single choice, optional): "根据进行中的工作拟定下周计划"
     (first, the default) and "不写下周计划". "Other" takes the user's own plans
     for next week and anything else worth reporting that git cannot show,
     such as helping a colleague, a talk or reviews.

   Every range is in the user's local time zone (this machine's), from 00:00:00
   on the first day to 23:59:59 on the last (`start_at`, `end_at`).

2. Remember every picked repo that is not configured yet, the current directory
   included, without asking:

   ```bash
   python3 <skill-dir>/scripts/store.py add-repo PATH
   ```

   A taken name becomes `parent/dir` (`renamed_from` says so). Config keys are
   described in [references/data.md](references/data.md).

   A path typed into "Other" adds a repo; it is not the whole answer, since
   typing there can drop the boxes the user ticked. One "Other" entry may hold
   several paths, separated by commas, semicolons, spaces or new lines (keep a
   path that contains spaces whole when it is quoted or plainly one path).
   When the answer adds any new repo and there are other repos the user could
   also pick, run `collect_commits.py repos` again and ask the repo question
   again, alone, with the repos just added first (labelled as just added) and
   the rest as in step 1. Repeat for as long as the answer adds new paths; the
   first answer that adds none is the selection. When the new paths are the
   only repos there are, go on without asking again.

3. Collect the commits, and last week's plan:

   ```bash
   python3 <skill-dir>/scripts/collect_commits.py collect --start START --end END \
     [--repo NAME_OR_PATH ...] [--author NAME_OR_EMAIL ...] [--output]
   python3 <skill-dir>/scripts/store.py plan --before START
   ```

   - Pass each picked repo with `--repo` (a configured name or a path); without
     it, every configured repo is used.
   - Commits are the user's own (git `user.name` / `user.email` of each repo, or
     `--author`), on every branch, authored within the range, merges excluded.
   - The script first fetches each repo's remotes, without asking: `git fetch`
     only updates remote-tracking branches such as origin/master, never local
     branches or files, and it never waits for a password. This brings in
     merges done on the web, so each commit's `status` (`已发布` on master or
     main, `已预发布`, `已提测` on the test branch, or null while in progress)
     is current. A repo with
     `fetched: false` uses local history; its `fetch_error` goes in the note
     under the recap. `"fetch": false` in config.json turns fetching off.
   - For long ranges add `--output` with no file name: the JSON goes to the
     system temp directory, never into a repository, and `written` gives the
     path to read.
   - `plan` returns the `items` of the `下周计划` in the latest recap that ends
     before START, for `上周计划完成情况`; empty when there is none.

   Then check each repo in the output:
   - `ok: false`: tell the user the `error` and carry on with the others.
   - `commit_count: 0`: the repo had no work in the range. Leave it out of the
     recap and carry on; do not ask about it.
   - No commits in any repo: tell the user in one message, naming the range,
     the repos and the `authors` checked, and end the task. Do not ask a
     question or offer other repos, ranges or next steps; the user chose them
     already and will ask again if something was wrong.

4. Judge what matters. `size` is `large` (>5 files or >100 lines), `medium`, or
   `small` (≤2 files and <20 lines); lock files and build output are not counted.
   Size helps judge importance only; never report it. `trivial_hints` flags
   subjects like merge, typo, format, deps, wip. Read the subject and body to
   understand each commit; for a large commit whose purpose is unclear, look at
   `git -C <path> show --stat <sha>`.

   Watch for squash merges done on the web: a subject ending in `(#N)` with a
   PR whose `merged_at` is null. While its feature branch still exists, the same
   work also appears as that branch's own commits, so it is counted twice. Treat
   them as one work item, and do not add up their sizes.

   Each repo also has `signals`, pointers to what may be worth telling:
   - `topics`: commits grouped by conventional-commit scope, largest first; a
     starting point for merging commits into work items.
   - `repeated_fixes`: files hit by several commits including two or more fixes,
     a sign of a hard problem.
   - `reverts`: work that was undone, often a lesson.
   - `explained`: commits whose body explains why; read these for causes,
     trade-offs and lessons.

   Group the work by project, then sort each project's items into `功能交付`,
   `问题修复` and `技术沉淀` (shared helpers, configuration instead of hard-coded
   values, removed duplication, build or release guards, conventions).
   `团队贡献` is a section of its own, across projects.

5. Do not stop to ask what was hard. Write what the commits and the user's
   note support. A cause goes into `问题修复` only when a commit body or the
   user states it. Never invent causes, contributions or plans.

6. Write the recap in Markdown. Before writing, read
   [references/writing-guide.md](references/writing-guide.md) (the two parts,
   each section, status, what never to write, length) and
   [references/examples.md](references/examples.md) (full examples and
   before/after pairs). The title is `# 周报 (START ~ END)` with the range from
   step 1, then `## 本周工作` with a `###` section per project (`####` for
   功能交付, 问题修复, 技术沉淀 inside it), and `## 下周计划`.

   No links unless `style.md` asks for them. Then, when a commit has several
   `prs`, use the one whose `from_branch` is the feature branch rather than a
   release, test or sync branch; without a PR use `commit_url`.

7. Save it right away, replacing any recap saved for the same range (the old one
   is kept as `.bak-<time>`), and copy its plain-text form to the clipboard.
   Pass the Markdown on stdin with a quoted heredoc, so no temporary file lands
   in a repository:

   ```bash
   python3 <skill-dir>/scripts/store.py save --start START --end END --overwrite --copy <<'RECAP'
   # 周报 (START ~ END)
   …the Markdown…
   RECAP
   ```

   In PowerShell, pipe a here-string instead:
   `@'…'@ | py -3 <skill-dir>/scripts/store.py save --start START --end END --overwrite --copy`.

   The plain-text form is what a spreadsheet cell or a chat box keeps: no title,
   `本周工作` and `下周计划` as plain lines, `一、` for projects, `（一）` for
   功能交付 and the like, numbered items, `【】` for bold. Leave out `--copy` when `style.md` says not
   to touch the clipboard.

8. Show the result as `plain_text` inside a fenced `text` code block, exactly
   as the script returned it, so the user can copy it with the block's copy
   button and paste it into a spreadsheet or chat. Do not also show the
   rendered Markdown: the same content twice is noise. After the block, one
   line with the saved `path` (the Markdown original) and, when `copied` is
   true, that the same text is already on the clipboard.
   `store.py text --start START --end END --copy` produces it again for a
   saved recap. Below that, in one line: repos that could not be fetched
   (their statuses may be behind), work that looked hard (repeated fixes, a
   revert) but has no stated cause, which the user can add, and repos left
   out for having no commits. This line is not a question and needs no answer.

9. If the user asks for changes, apply them and save again with `--overwrite --copy`.
   When they state a lasting preference ("以后都…", "always…"), append one
   short line to `style.md` in `data_home` (from step 0), e.g.
   `printf '%s\n' '- 周报附上 PR 链接' >> "<data_home>/style.md"`. Never record
   report content there, and do not ask whether to remember a one-off edit.

## Rules

- Plain and true: only what the commits and the user's own words support,
  nothing dressed up for the lead or the year-end review.
- Describe outcomes, not file edits. No workload numbers (lines, tests,
  commits, files), no inflated words, no value labels, no type tags like
  `[feat]`, no hashes.
- Merge related commits into one item; drop trivial ones.
