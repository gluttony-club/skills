# Writing guide

The recap is read aloud at the weekly team meeting. In about two minutes the
listener should learn what got done, which of it mattered most, and what was
hard. Write in the language the user writes in (Chinese headings are shown
here; translate them for other languages).

## Layout

```markdown
# 周报 (START ~ END)

## <repo name>

- **重要工作项**（状态）：做成了什么，对用户或业务的作用
  - 补充：关键做法或经验，一句话
- 次要工作项：结果
- 其他
  - 小改动 A
  - 小改动 B

## <next repo name>

- …

## 难点与经验

- **问题**：现象，一句话
  - 原因：…
  - 解决：… → 结果，或以后怎么避免
```

Every point that is read on its own gets its own line, so the recap stays
readable when pasted as plain text into a spreadsheet cell or a chat.

- No summary section at the top. Importance is shown by order and bold inside
  each repo section, so nothing is said twice.
- One `##` section per repo with work in the range, the repo with the most
  important work first. Leave out repos with nothing worth saying.
- Inside a repo, order items by importance, not by date or commit order.
- No "next week" section: plans are not known from git.

## Main items

- Outcome first: what now works, for whom, and why it matters; then how, only
  if it helps. Answer "so what?".
  - Good: `**优惠券叠加**：结算时自动选出最优组合，不可叠加的券给出原因`
  - Weak: `修改 coupon 相关代码`、`优化优惠券`
- One work item per feature or problem, however many commits it took.
- Keep numbers the commits state (entry points, steps, seconds, pages, events).
  Never invent metrics such as "性能提升 30%".
- Business language over code names. Keep a technical term only when the team
  would say it in the meeting (Google One Tap, Stripe, Safari); leave out
  variable names, env vars, file paths and API internals.
- At most 2 sub-items per item (the `其他` item excepted), each one short
  clause. Use a sub-item for a lesson worth keeping ("经验：…") when it does
  not deserve a 难点 entry.

## Minor work

Small fixes, refactors, config and build changes that are real work but not
worth a main item go into one last item per repo, `- 其他`, with one sub-item
each of a few words. Do not drop real work to save space; drop only noise (see
below).

## Status

Add a status in brackets after the item name only when the pull requests or
branch names say it plainly, e.g. merged through a test branch → `（已提测）`,
merged into master or main → `（已合入 master）`, a release tag → `（已上线）`.
When unsure, write no status. Never guess "已上线".

## Emphasis

- Bold the name of the 1–3 most important items in the whole recap, nothing
  else in them. Every other item stays plain, so a glance at the bold words
  gives the week's highlights.
- In `难点与经验`, bold the problem name at the start of each entry.
- If everything is bold, nothing is.

## Links

- No links by default: the recap is listened to, and anyone who needs the code
  finds it in the repository.
- Only when `style.md` asks for links, end each important item with its feature
  pull request (`[#128](…)`), or the most significant commit as a 7-character
  sha. Never paste bare URLs.

## 难点与经验 (hard problems and lessons)

This section is optional and absent in most weeks. Include an entry only for
work that was genuinely hard or taught something the team should keep:

- a cause that was not obvious and is stated in a commit body or by the user,
- a problem fixed several times (`repeated_fixes`) or undone (`reverts`),
- a mistake whose lesson others can reuse.

Routine bugs, however many, do not qualify. At most 2 entries. Write each as
the bold symptom in a few words, then two sub-items: `原因：…` and
`解决：… → 结果`; for a mistake, end with how to avoid it next time. Use only causes a commit body or the user states; without
one, leave the entry out rather than guess. When there is no entry, omit the
whole section; never write "无". Do not repeat an item's detail here and in its
repo section: keep the item short and tell the story once, here.

## Drop or merge

Drop: merge commits, release bumps, formatting, lint, typo fixes, debug-log
removal, small dependency bumps, doc-only touch-ups. Merge many commits on one
feature into one item, and related small fixes into one "…问题修复" item or
under `其他`.

## Length

About 20 lines or fewer for a normal week. If it runs longer, merge items or
move small ones into `其他` before cutting anything that mattered.

## Before saving

Check: every claim traces to a commit or the user's words; items lead with
outcomes; at most 3 bold item names; statuses only where certain; no links
unless `style.md` asks; `难点与经验` only for genuinely hard work.
