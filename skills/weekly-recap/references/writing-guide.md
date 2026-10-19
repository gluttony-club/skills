# Writing guide

A recap has three readers. The team hears it at the weekly meeting and should
learn in about two minutes what got done and what comes next. The lead reads
what was delivered, how far it got, which hard problems were solved and what
was left behind for others. At the end of the year the user reads dozens of
them to write a review. Serve all three by being plain and true: what was
done, how far it got, what was hard, what others can reuse. Never dress it up.
Write in the language the user writes in (Chinese headings are shown here;
translate them for other languages).

## Layout

```markdown
# 周报 (START ~ END)

## 本周工作

### 上周计划完成情况

- 上周计划的事：已完成（已发布）

### <project name>

#### 功能交付

- **重要功能**（已发布）：做成了什么，对用户或业务有什么用
  - 范围或影响，一句话
- 次要功能（已提测）：做成了什么

#### 问题修复

- **有难度的问题**：现象
  - 原因：…
  - 解决：…
- 其他：小问题 A；小问题 B

#### 技术沉淀

- 留下的可复用的东西：是什么，哪里能用上
- 经验：一句以后能直接用的结论

### <next project name>

- 只有一类工作时，直接列条目（已发布）

### 团队贡献

- 对团队有用的事

## 下周计划

- 做什么：想达到的结果
```

- `本周工作` and `下周计划` are always the two parts, whatever day the meeting
  is held.
- Under `本周工作`, one `###` section per project (its `name`), the project with
  the most important work first. Inside a project, `####` sections in the
  order 功能交付, 问题修复, 技术沉淀; a project with only one kind of work lists
  its items directly, without a `####` heading. `上周计划完成情况` comes first
  and `团队贡献` last, as `###` sections of their own, since they are not tied
  to one project.
- A section appears only with content. `技术沉淀`, `团队贡献` and
  `上周计划完成情况` only when there is something true to put in them. Never
  write "无".
- Within a section, the most important item first.
- The project is named by its section; never repeat it in an item.

## 功能交付 (features)

- One item per feature, however many commits it took: what now works, for
  whom, and why it matters, in business language.
  - Good: `**Google One Tap 一键登录**（已发布）：未登录用户可一键用 Google 账号登录，与现有 Google 登录共用账号关联和注册奖励`
  - Weak: `新增 google-one-tap 组件和 /auth/one-tap 接口`
- No implementation details here (retries, deduplication, env names, file
  paths, libraries). They belong nowhere in the recap unless they are the cause
  of a fixed problem or a reusable piece under `技术沉淀`.
- A sub-item only for scope or effect that matters to users or the business
  (`覆盖设置页和积分不足弹窗 2 个入口`), at most one.

## 问题修复 (bug fixes)

- A fix that took real work, a non-obvious cause, a regression or a fix that
  protects revenue or data gets its own item: the symptom as the bold name,
  then `原因：` and `解决：` sub-items, from what a commit body or the user
  states. This is where the lead sees how someone solves problems.
- Without a stated cause, write the symptom and that it is fixed; never guess
  a cause.
- Routine fixes share one `其他：A；B` line, a few words each.

## 技术沉淀 (what was left for later)

Things that make the next piece of work easier, taken from the commits: a
helper or component pulled out for shared use, hard-coded values turned into
configuration, a duplicated logic made single, a guard added to a build or
release, a convention or document written down. Say what it is and where it is
used. Add `经验：` with a lesson worth keeping, stated as a rule someone else can
follow (`关键埋点不依赖第三方 SDK 的事件，由自己的代码在确定时机上报`), only when a
commit body or the user supports it. At most three items.

## 团队贡献 (team contribution)

Work that helps others beyond the user's own tasks: code in a shared package
others use, tooling or CI for the team, documentation, fixing a problem in
someone else's area, and what the user says (helped a colleague debug, gave a
talk, reviewed code). Only what the commits or the user show; omit the section
otherwise. Never infer contribution from volume of work.

## 上周计划完成情况 (last week's plan)

When the previous recap had a `下周计划`, list each planned item once with
where it stands, judged from this range's commits and statuses: `已完成（状态）`,
`进行中`, or `未开始`. When nothing in the commits relates to an item, write
`未看到相关提交` rather than guessing. Keep each to one line; add a reason only
when the user gave one.

## 下周计划 (next week)

- From the work in progress: features `已提测` or still on a branch become
  `推动 X 上线` or `完成 X`; a fix waiting for verification becomes `验证 X`.
- Add what the user wrote for next week, in their words, tidied.
- Each item: what will be done, and the result wanted; a date only when the
  user gave one. Do not invent new work.

## Status

Each commit carries a `status` worked out from the remote branches after a
fetch: `已发布` once it is on master or main, `已提测` once it is on the test
branch, `已预发布` on a pre-release branch, or none while still in progress.
Write the status in brackets after the item name, using these words only: no
branch names such as "已合入 master". An item's status is the least advanced
status among its commits, so it never claims more than is true; with no status
write `开发中`. When a repo was not fetched (`fetched: false`), its statuses may
be behind; say so in the note under the recap, not in the item. A team's own
`status_branches` labels replace these words.

## Emphasis

Bold the names of the 1–3 items that matter most in the whole recap, in
`功能交付` or `问题修复`; in `问题修复` the symptom names of hard problems are
bold too. Nothing else is bold.

## Never write

- Workload numbers: lines of code, numbers of tests, commits or files. They
  measure effort, read as padding, and say nothing about the result.
- Inflated words: 赋能、打造、极致、全面提升、显著优化, or any improvement
  without a fact behind it. Never invent metrics ("性能提升 30%").
- Labels or tags such as 【增长】【商业化】 to sort items by value.
- Type tags like `[feat]`, commit hashes, or links (unless `style.md` asks for
  links).
- Noise: merge commits, release bumps, formatting, lint, typo fixes,
  debug-log removal, small dependency bumps, doc-only touch-ups.

## Length

Not terse, not padded: each item one line, two with a sub-item; about 20–30
lines for a week, a little more for a longer range. When it runs long, merge
items and move routine fixes into `其他` before cutting anything that mattered.

## Before saving

Check: every claim traces to a commit or the user's words; no workload numbers
or inflated words; statuses as the script reports them, the least advanced per
item; at most 3 bold item names; empty sections left out; the plan holds only
work in progress and the user's own plans.
