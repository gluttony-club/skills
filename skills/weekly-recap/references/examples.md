# Examples

Fictional projects. Use them to calibrate tone, length, order and emphasis, not
as content.

## A complete recap

Input, in short: 23 commits in `shop-web` (checkout redesign with 6 commits,
coupon stacking with 9, four fixes on iOS upload including one revert, a config
refactor, two small fixes, plus lint and typo commits) and 4 commits in
`api-server`. The checkout pull request was merged into master; coupon stacking
went through the test branch. A commit body explains the iOS cause: the upload
ran before the session refresh, so Safari sent an expired token.

```markdown
# 周报 (2026-03-02 ~ 2026-03-08)

## shop-web

- **新版结算页**（已合入 master）：地址、配送、支付合并为一页，下单从 4 步减到 2 步
  - 刷新页面不丢失已填写的内容
- **优惠券叠加**（已提测）：结算时自动选出最优组合，不可叠加的券给出原因
- iOS 图片上传偶发失败已修复
- 其他：支付配置改为按环境读取；订单列表空状态文案修正；商品图懒加载

## api-server

- 新增优惠券组合计算接口，供结算页调用
- 订单导出支持按渠道筛选

## 难点与经验

- **iOS 上传偶发失败**：上传早于登录态刷新，Safari 带上了过期 token；先加的自动重试仍用旧 token，只会重复失败，已回滚 → 上传前先刷新会话，问题消失。经验：先确认根因再加重试
```

Why it works:

- No summary at the top: the two bold names are the week's highlights, and
  they lead their section.
- 9 coupon commits became one item; three small changes share the `其他` line
  instead of being dropped; lint and typo commits are gone.
- Statuses appear only where the pull requests show them.
- The iOS story is told once, in `难点与经验`; its item stays one short line.
- No links: nobody clicks them in a meeting.

## A week without hard problems

Most weeks look like this: no `难点与经验` section at all.

```markdown
# 周报 (2026-03-09 ~ 2026-03-15)

## shop-web

- **会员积分抵扣**（已提测）：结算时可用积分抵扣，最多抵扣订单金额的 20%
- 商品详情页支持视频主图
- 其他：购物车数量上限提示；修复切换地址后运费不刷新
```

## Before and after

**A summary that repeats the body**

- Before: a `## 本周重点` section listing the same three items that follow.
- After: no summary; bold the 1–3 most important item names and put them first.

**Activity instead of outcome**

- Before: `- 修改 checkout 页面组件和样式`
- After: `- **新版结算页**：下单从 4 步减到 2 步`

**One commit per line**

- Before:
  ```markdown
  - feat(coupon): add stacking rules
  - feat(coupon): pick best combination
  - fix(coupon): rounding error
  - fix(coupon): hint for non-stackable coupons
  ```
- After: `- **优惠券叠加**：结算时自动选出最优组合，不可叠加的券给出原因`

**Code names instead of business language**

- Before: `- 购买转化推送到 dataLayer，上报地址改为 DATA_REPORTING_BASE_URL`
- After: `- 购买转化可回传广告平台` and, in `其他`, `埋点上报地址改为配置项`

**A link after every item**

- Before: `- 商品详情页支持视频主图（[#141](…)）` on every line
- After: no links, unless `style.md` asks for them.

**Small work dropped to fit**

- Before: three real fixes left out because the section was "full".
- After: `- 其他：A；B；C`

**A routine bug written up as a hard problem**

- Before: `## 难点与经验` with `**按钮颜色不对**：样式写错 → 改正`
- After: the fix goes into `其他`, and the section is omitted.

**Everything bold**

- Before: `- **上线优惠券叠加**：**结算时自动选出最优组合**，**支持 3 种券**`
- After: `- **优惠券叠加**：结算时自动选出最优组合，支持 3 种券`

**Invented cause**

- Before: `- **iOS 上传失败**：网络不稳定导致` (no commit or user says so)
- After: `- iOS 图片上传偶发失败已修复`, and no `难点与经验` entry without a stated
  cause.
