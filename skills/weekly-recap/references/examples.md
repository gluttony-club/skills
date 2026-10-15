# Examples

Fictional projects. Use them to calibrate tone, length, emphasis and links,
not as content.

## A complete recap

Input, in short: 23 commits in `shop-web` (coupon stacking with 9 commits,
checkout redesign with 6, four fixes on iOS upload including one revert, plus
lint and typo commits) and 4 commits in `api-server`. After the first version,
the user added: "the iOS upload thing took two days; Safari sent the old token".

```markdown
# 周报 (2026-03-02 ~ 2026-03-08)

## 本周重点

- 新版结算页上线，下单流程从 **4 步减到 2 步**
- 优惠券支持叠加，结算时自动选出最优组合

## shop-web

- 重做结算页：地址、配送、支付合并为一页，**下单从 4 步减到 2 步**（[#128](https://example.com/pr/128)）
  - 保留未提交的表单内容，刷新不丢失
- 上线优惠券叠加规则：**结算时自动选出最优组合**（[#126](https://example.com/pr/126)）
  - 不可叠加的券给出原因提示
- iOS 图片上传问题修复（[#131](https://example.com/pr/131)）

## api-server

- 新增优惠券组合计算接口，供结算页调用（[#57](https://example.com/pr/57)）
- 订单导出支持按渠道筛选（[a1b2c3d](https://example.com/commit/a1b2c3d)）

## 攻克点

- **iOS 上传偶发失败**：上传早于登录态刷新，Safari 带上了过期 token → 上传前先刷新会话 → 不再偶发失败（[#131](https://example.com/pr/131)）

## 踩坑与经验

- **重试反而放大失败**：先加的自动重试仍在用旧 token，只会重复失败，已回滚 → 先确认根因再加重试（[e4f5a6b](https://example.com/commit/e4f5a6b)）
```

Why it works:

- `本周重点` gives the two outcomes worth saying first, in business terms.
- 9 coupon commits became one item; lint and typo commits are gone.
- One bold phrase per item at most, on the result or the number.
- The hard problem and the pitfall each tell cause → action → result or lesson,
  using only the user's answer and the commits (the revert).

## Before and after

**Activity instead of outcome**

- Before: `- 修改 checkout 页面组件和样式`
- After: `- 重做结算页：**下单从 4 步减到 2 步**（[#128](…)）`

**One commit per line**

- Before:
  ```markdown
  - feat(coupon): add stacking rules
  - feat(coupon): pick best combination
  - fix(coupon): rounding error
  - fix(coupon): hint for non-stackable coupons
  ```
- After: `- 上线优惠券叠加规则：**结算时自动选出最优组合**（[#126](…)）`, with one
  sub-item for the hint if it matters.

**Tags, hashes and noise**

- Before: `- [修复] a1b2c3d fix lint 和 typo`
- After: dropped.

**Everything bold**

- Before: `- **上线优惠券叠加规则**：**结算时自动选出最优组合**，**支持 3 种券**`
- After: `- 上线优惠券叠加规则：**结算时自动选出最优组合**，支持 3 种券`

**Invented cause**

- Before: `- **iOS 上传失败**：网络不稳定导致` (no commit or answer says so)
- After: write `- iOS 图片上传问题修复` without a cause, and mention below the
  recap that the user can add one (SKILL.md step 8).
