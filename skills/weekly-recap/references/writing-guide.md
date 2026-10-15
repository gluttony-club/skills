# Writing guide

The recap is read aloud at the weekly team meeting. The listener should learn, in
about two minutes, what got done, what mattered most, and what the team can learn
from it. Write in the language the user writes in (Chinese headings are shown
here; translate them for other languages).

## Layout

```markdown
# 周报 (START ~ END)

## 本周重点

- 1–3 lines: the outcomes you would say first if you had 20 seconds

## <repo name>

- 工作项：结果（链接）
  - 补充：关键做法或影响

## <next repo name>

- …

## 攻克点

- **问题**：原因 → 做法 → 结果（链接）

## 踩坑与经验

- **坑**：发生了什么 → 原因 → 以后怎么避免（链接）
```

- `本周重点` is always first. It names outcomes, not repos ("新版结算页上线，下单流程从 4 步减到 2 步"),
  and may repeat an item from a repo section in summary form.
- One `##` section per repo with work in the range, ordered by importance.
  Leave out repos with nothing worth saying.
- `攻克点` and `踩坑与经验` are optional. Include an item only when the commits or
  the user's answers support it; omit the whole section when empty. Never write
  "无".
- No "next week" section: plans are not known from git.

## Budget

- Whole recap: about 25 lines or fewer.
- Per repo: at most 5 main items. Merge or drop the rest.
- Per main item: at most 2 sub-items, each one short clause.
- `攻克点` and `踩坑与经验`: at most 2 items each, one or two lines per item.

## Main items

- Shape: `<what was delivered>：<result or value>（link）`. Start with a verb or a
  feature name; end with what it changes for users, the business or the team.
  - Good: `上线优惠券叠加规则：结算时自动选出最优组合（[#128](…)）`
  - Weak: `修改 coupon 相关代码`、`优化优惠券`
- One work item per feature or problem, however many commits it took.
- Keep numbers that commits support (event counts, entry points, pages,
  removed lines for a cleanup). Do not invent metrics such as "性能提升 30%".
- Prefer the business view over code names. Keep a technical term only when the
  team would use it in the meeting (e.g. Redis, OAuth, Safari).

## Emphasis

- Bold the single most important phrase of an item: usually its result or a
  number (`**3 个支付渠道**`, `**退款改为全自动**`).
- At most one bold phrase per main item, none in most sub-items. If everything is
  bold, nothing is.
- In `攻克点` and `踩坑与经验`, bold the problem name at the start of the item.

## Links

- Every main item and every `攻克点` / `踩坑与经验` item ends with one link.
- Prefer the feature pull request; else the most significant commit, shown as
  its 7-character sha. Omit the link when no URL is available.
- Link text is short: `[#128](…)` or `[a1b2c3d](…)`. Never paste bare URLs.

## Hard problems and pitfalls

Write them as a story the team can learn from, in this order:

1. **The symptom** in one phrase, bold.
2. **The cause**, as the commits or the user explain it.
3. **What was done.**
4. **The result**, or for a pitfall, **how to avoid it next time**.

Example: `- **iOS 上传偶发失败**：上传早于登录态刷新，Safari 带上了过期 token → 上传前先刷新会话 → 不再偶发失败（[#131](…)）`

Candidates come from `signals` (`repeated_fixes`, `reverts`, `explained`) and
from asking the user (SKILL.md step 5). Use only causes that a commit body or the
user states.

## Drop or merge

Drop unless it is the point of the work: merges, release bumps, formatting,
lint, typo fixes, debug-log removal, small dependency bumps, small style tweaks,
doc touch-ups. Merge many small commits on one feature into one item, and several
related small fixes into one "…问题修复" item.

## Before showing the draft

Check: every claim traces to a commit or the user's words; each main item has a
result, at most one bold phrase and a link when available; the budget holds.
