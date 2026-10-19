# Examples

Fictional projects. Use them to calibrate tone, length, order and emphasis, not
as content.

## A complete recap

Input, in short: the previous recap planned "推动优惠券叠加上线" and "重做结算页".
This range has 23 commits in `shop-web` and 4 in `api-server`: checkout
redesign (merged into master), coupon stacking (on the test branch), four fixes
on iOS upload including one revert, whose commit body says the upload ran
before the session refresh so Safari sent an expired token, a shared date
helper replacing three copies, payment settings moved into configuration, a
release check that blocks builds with missing environment variables, and lint
and typo commits. The user wrote for next week: "做会员积分抵扣；帮小王排查了
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
  - 经验：偶发失败先确认根因再加重试，重试会掩盖问题
- 其他：订单列表空状态文案；切换地址后运费不刷新

### api-server

- 新增优惠券组合计算接口，供结算页调用（已提测）
- 订单导出支持按渠道筛选（已发布）

### 团队贡献

- 发布前自动检查缺失的环境变量，所有服务的构建都会拦下这类配置错误
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
- The date helper and the payment configuration are not mentioned: useful
  code hygiene, but nothing others use or a lead needs to hear. The release
  check is, so it sits under `团队贡献` with what it protects.
- The lesson hangs under the hard problem it came from, as a rule.
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

- 推动会员积分抵扣上线，上线后确认抵扣金额和订单金额对得上
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
- After: `- 用户付款成功后，广告平台能收到这笔购买`

**A lesson hung under a feature**

- Before: a feature with the sub-item `经验：埋点查询失败时只跳过埋点`
- After: the feature alone; the fix, if worth telling, under `问题修复`, with a
  `经验：` sub-item only when the lesson is not obvious.

**A section padded with refactors**

- Before: a `技术沉淀` section with `请求 ID 生成抽成公共方法`, `上报地址改为配置项`
  and a lesson that repeats a fix above
- After: no such section. The first goes under 其他 as the problem it fixed
  (`用 http 地址访问时创建故事报错`), the second is left out, the lesson is dropped.

**Shorthand in 其他**

- Before: `- 其他：非 HTTPS 页面请求出错；Docker 构建缺少依赖`
- After: `- 其他：用 http 地址访问时创建故事报错；加入埋点共享包后 Docker 镜像构建失败`
  (which feature, in what situation, what went wrong)

**Value labels**

- Before: `- 【增长】【商业化】优惠券叠加`
- After: `- **优惠券叠加**（已提测）：结算时自动选出最优组合`

**A serious fix buried in 其他**

- Before: `- 其他：埋点相关查询失败导致下单和商品列表失败；Docker 构建缺少依赖`
- After: its own item, since ordering failed:
  ```markdown
  - **埋点异常导致下单和商品列表失败**
    - 原因：埋点要用的商品信息、用户最近购买的套餐查询失败时，会连带让下单和整个商品列表一起报错
    - 解决：把埋点和下单、商品列表分开，埋点出错只跳过埋点，不影响用户下单和看商品
  - 其他：Docker 构建缺少依赖
  ```

**A catch-all name**

- Before: `- 体验优化（已发布）：背景音乐淡入淡出、离开挽留图预加载、页脚社媒入口`
- After: `- 背景音乐（已发布）：开始播放时声音慢慢变大，关掉时慢慢变小`,
  `- 离开挽留弹窗（已发布）：弹窗一打开图片就能显示` and
  `- 页脚社媒入口（已发布）：补充 5 个社媒入口`

**Jargon**

- Before: `- **购买漏斗与转化漏报**`, with the cause `转化上报失败后过早标记为完成`
- After: `- **购买相关埋点漏报**`, with the cause
  `付款成功的数据上报失败后被当成已上报，不会再补报`
- Before: `- 页脚社媒入口（已发布）：添加 Organization 结构化数据`
- After: `- 页脚社媒链接（已发布）：补充方便搜索引擎识别网站的信息`

**A plan without a finish line**

- Before: `- 推动 Tad 6.0 模型升级上线`
- After: `- 推动 Tad 6.0 模型升级上线，上线后确认音乐生成、翻唱和查积分都正常`

**A claimed status**

- Before: `- 优惠券叠加（已发布）` while its commits are only on the test branch
- After: `- 优惠券叠加（已提测）`

**Branch names as status**

- Before: `- 优惠券叠加（ai-chat-video，已合入 master）`
- After: under the project's own section, `- 优惠券叠加（已发布）`

**Invented cause**

- Before: `- **iOS 上传失败**：网络不稳定导致` (no commit or user says so)
- After: `- iOS 图片上传偶发失败已修复`, without a cause.
