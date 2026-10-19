# Examples

Fictional projects. Use them to calibrate tone, length, order and emphasis, not
as content.

## A complete recap

Input, in short: the previous recap planned "推动优惠券叠加上线" and "重做结算页".
This range has 23 commits in `shop-web` and 4 in `api-server`: checkout
redesign (merged into master), coupon stacking (on the test branch), four fixes
on iOS upload including one revert, whose commit body says the upload ran
before the session refresh so Safari sent an expired token, a shared date
helper replacing three copies, payment settings moved into configuration, and
lint and typo commits. The user wrote for next week: "做会员积分抵扣；帮小王排查了
推送丢失的问题".

```markdown
# 周报 (2026-03-02 ~ 2026-03-08)

## 本周工作

### 上周计划完成情况

- 推动优惠券叠加上线：已提测，待发布
- 重做结算页：已完成（已发布）

### shop-web

#### 功能交付

- **新版结算页**（已发布）：地址、配送、支付合并为一页，下单从 4 步减到 2 步
- **优惠券叠加**（已提测）：结算时自动选出最优组合，不可叠加的券给出原因

#### 问题修复

- **iOS 图片上传偶发失败**
  - 原因：上传早于登录态刷新，Safari 带上了过期 token；先加的自动重试仍用旧 token，已回滚
  - 解决：上传前先刷新会话，问题消失
- 其他：订单列表空状态文案；切换地址后运费不刷新

#### 技术沉淀

- 日期格式化抽成公共方法，替换原来 3 处各自的实现
- 经验：偶发失败先确认根因再加重试，重试会掩盖问题

### api-server

- 新增优惠券组合计算接口，供结算页调用（已提测）
- 订单导出支持按渠道筛选（已发布）
- 支付渠道参数改为按环境配置，不再写死在代码里（已发布）

### 团队贡献

- 协助排查推送消息丢失的问题

## 下周计划

- 推动优惠券叠加上线，上线后核对优惠金额
- 开发会员积分抵扣
```

Why it works:

- Every line says what was done or how far it got; nothing is there to look
  busy. 9 coupon commits became one item; lint and typo commits are gone.
- The hard problem is told once, with its cause from the commit body; the
  routine fixes share one line.
- Each project has its own section, so no item names its project; the small
  api-server section lists its items without sub-headings.
- `技术沉淀` names what others can now reuse; the lesson is a rule, not a story.
- `团队贡献` holds only what the user said. No numbers of commits or tests.
- The plan follows the work in progress and the user's own words.

## A week without extras

Most weeks are like this: no hard problem, nothing left for others, no plan
from the previous recap. The empty sections are simply absent.

```markdown
# 周报 (2026-03-09 ~ 2026-03-15)

## 本周工作

### shop-web

#### 功能交付

- **会员积分抵扣**（已提测）：结算时可用积分抵扣，最多抵扣订单金额的 20%
- 商品详情页支持视频主图（已发布）

#### 问题修复

- 其他：购物车数量上限提示；切换地址后运费不刷新

## 下周计划

- 推动会员积分抵扣上线
```

## Before and after

**Workload instead of result**

- Before: `- **Google One Tap 登录**：新增 2400 行代码、1000+ 行测试`
- After: `- **Google One Tap 登录**（已发布）：未登录用户可一键用 Google 账号登录`

**Inflated words**

- Before: `- 全面赋能支付链路，显著提升转化体验`
- After: `- 下单从 4 步减到 2 步`, or nothing, if no commit says what changed.

**Implementation detail in a feature**

- Before: `- 购买转化推送到 dataLayer，推送成功才标记 reported，失败可重试`
- After: `- 购买转化可回传广告平台`

**A lesson hung under a feature**

- Before: a feature with the sub-item `经验：埋点查询失败时只跳过埋点`
- After: the feature alone; the lesson, if worth keeping, under `技术沉淀` as a
  rule, or the fix under `问题修复`.

**Value labels**

- Before: `- 【增长】【商业化】优惠券叠加`
- After: `- **优惠券叠加**（已提测）：结算时自动选出最优组合`

**A claimed status**

- Before: `- 优惠券叠加（已发布）` while its commits are only on the test branch
- After: `- 优惠券叠加（已提测）`

**Branch names as status**

- Before: `- 优惠券叠加（ai-chat-video，已合入 master）`
- After: under the project's own section, `- 优惠券叠加（已发布）`

**Invented cause**

- Before: `- **iOS 上传失败**：网络不稳定导致` (no commit or user says so)
- After: `- iOS 图片上传偶发失败已修复`, without a cause.
