# gluttony-club/skills

[简体中文](#简体中文) | [English](#english)

## 简体中文

gluttony-club 的开源 [Agent Skills](https://agentskills.io) 合集，同时支持 Claude Code 和 Codex（以及其他支持 Agent Skills 规范的工具）。

| Skill | 说明 | 状态 |
| --- | --- | --- |
| [`weekly-recap`](skills/weekly-recap/SKILL.md) | 从自己的 git 提交生成周报：做了什么、值得讲的亮点与攻克点、踩过的坑，用于周会汇报 | v0.2.1 |
| `okr-review` | 基于周报和 git 记录撰写 OKR 自评（目标、关键成果、权重、自评分、个人总结），周期可自选（半年 / 一年） | 计划中 |

### weekly-recap 能做什么

- 选择时间：本周、上周、指定某周或自定义时间段，按你电脑的本地时区，从起始日 00:00:00 到结束日 23:59:59
- 跨多个仓库收集**你自己**的提交：覆盖所有分支，按作者时间筛选，自动去重，并统计改动规模
- 自动生成提交和 PR 链接（支持 GitHub、GitLab、CNB、Gitee、Bitbucket；PR 编号从本地合并记录识别，不联网）
- 从提交中找出可能的攻克点和踩坑线索；看不出原因的不会乱写，生成后你可以随时补充
- 输出 Markdown 周报：本周重点、各项目进展、攻克点、踩坑与经验，重点加粗、条目带链接
- 保存到本地，并记住你的仓库和写作偏好，越用越贴合

### 安装

**Claude Code**（插件市场，在会话中执行）：

```
/plugin marketplace add gluttony-club/skills
/plugin install weekly-recap@gluttony-club
```

**Codex**（在会话中让 skill-installer 安装）：

```
$skill-installer install https://github.com/gluttony-club/skills/tree/main/skills/weekly-recap
```

也可以直接运行安装脚本：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo gluttony-club/skills --path skills/weekly-recap
```

**手动安装**（任意支持 Agent Skills 的工具）：把 `skills/weekly-recap/` 整个文件夹复制或软链接到该工具的 skills 目录，例如 `~/.claude/skills/` 或 `~/.agents/skills/`。

运行环境：git，以及 Python 3.9+（只用标准库，无需安装依赖）。

### 使用

直接说"帮我写上周的周报"，或显式调用：Claude Code 中为 `/weekly-recap:weekly-recap`（插件安装）或 `/weekly-recap`（手动安装），Codex 中为 `$weekly-recap`。

每次只问两件事：时间范围（本周、上周或自定义）和要包含的仓库（多选，可输入新路径）。选完直接生成并保存，选过的仓库会自动记住，没有提交的仓库自动略过。

### 更新

- **Claude Code**：在终端运行下面的命令，它会先检查插件市场有没有新版本；更新后重启 Claude Code 生效。Claude 桌面应用的插件页面没有更新按钮，也用这条命令。

  ```bash
  claude plugin update weekly-recap@gluttony-club
  ```

  也可以在 Claude Code 会话中执行 `/plugin marketplace update gluttony-club`，再在 `/plugin` 中更新 `weekly-recap`。
- **自动更新**：第三方插件市场默认不自动更新。在 Claude Code 会话中打开 `/plugin`，进入 **Marketplaces**，选中 `gluttony-club`，选择 **Enable auto-update**，之后发布的新版本会在后台自动更新。
- **Codex**：删除 `~/.codex/skills/weekly-recap` 后重新执行上面的安装命令。
- **手动安装**：软链接到本仓库的克隆则 `git pull` 即可。

### 数据与隐私

- 脚本只运行本地 `git` 命令，只读写 `~/.weekly-recap/`（可用环境变量 `WEEKLY_RECAP_HOME` 修改）；时间范围较长时，收集到的提交会临时写入系统临时目录（仅你本人可读）。不会上传到任何服务器，也不会自行 `git fetch`（需要时先征得你同意）。
- 周报草稿由你所使用的 AI 工具生成：提交标题、正文、文件路径和改动统计会作为对话内容发送给该工具的模型服务商，与你平时在对话中粘贴代码相同。涉及敏感仓库时请留意。
- 目录结构与配置项见 [references/data.md](skills/weekly-recap/references/data.md)。

### 开发

```bash
pip install skills-ref
agentskills validate skills/weekly-recap
```

## English

Open-source [Agent Skills](https://agentskills.io) by gluttony-club, for Claude Code, Codex and other tools that support the Agent Skills format.

| Skill | Description | Status |
| --- | --- | --- |
| [`weekly-recap`](skills/weekly-recap/SKILL.md) | A weekly recap from your own git commits for the team meeting: what you did, highlights, hard problems solved, pitfalls | v0.2.1 |
| `okr-review` | An OKR self-review (objectives, key results, weights, self-scores, personal summary) drafted from your weekly recaps and git history, for any review period | Planned |

### What weekly-recap does

- Pick a range: this week, last week, a given week, or a custom period, in your computer's local time zone, from 00:00:00 on the first day to 23:59:59 on the last.
- Collect **your own** commits across repositories: every branch, filtered by author date, de-duplicated, with change sizes.
- Link commits and pull requests (GitHub, GitLab, CNB, Gitee, Bitbucket; PR numbers come from local merge commits, no network).
- Point out likely hard problems and pitfalls without inventing causes; add the story afterwards if you like.
- Write a Markdown recap: key outcomes, progress per project, hard problems, pitfalls and lessons, with emphasis and links.
- Save it locally and remember your repositories and writing preferences.

### Install

**Claude Code** (plugin marketplace, inside a session):

```
/plugin marketplace add gluttony-club/skills
/plugin install weekly-recap@gluttony-club
```

**Codex** (ask the skill installer):

```
$skill-installer install https://github.com/gluttony-club/skills/tree/main/skills/weekly-recap
```

or run its script: `python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo gluttony-club/skills --path skills/weekly-recap`.

**Manual**: copy or symlink `skills/weekly-recap/` into your tool's skills directory, such as `~/.claude/skills/` or `~/.agents/skills/`.

Requires git and Python 3.9+ (standard library only).

### Use

Say "write my weekly recap for last week", or invoke it: `/weekly-recap:weekly-recap` (Claude Code plugin), `/weekly-recap` (manual install), `$weekly-recap` (Codex). It asks two things only, the range (this week, last week or your own) and the repositories (pick several or type a new path), then writes and saves the recap. Picked repositories are remembered; ones with no commits are skipped.

### Update

- **Claude Code**: run this in your shell. It checks the marketplace for a new version first; restart Claude Code to apply it. The plugins page in the Claude desktop app has no update button, so use this command there too.

  ```bash
  claude plugin update weekly-recap@gluttony-club
  ```

  Or, inside a Claude Code session, run `/plugin marketplace update gluttony-club`, then update `weekly-recap` in `/plugin`.
- **Auto-update**: third-party marketplaces don't update automatically by default. In a Claude Code session, open `/plugin`, go to **Marketplaces**, select `gluttony-club` and choose **Enable auto-update**; new releases then install in the background.
- **Codex**: delete `~/.codex/skills/weekly-recap` and run the install command again.
- **Manual**: `git pull` if you symlinked a clone of this repository.

### Data and privacy

- The scripts run only local `git` commands and read and write only `~/.weekly-recap/` (or `$WEEKLY_RECAP_HOME`), plus, for long ranges, a file of collected commits in the system temp directory that only you can read. Nothing is uploaded, and `git fetch` runs only after you agree.
- The recap is written by the AI tool you use, so commit subjects and bodies, file paths and change counts are sent to that tool's model provider as conversation content, just as when you paste code into a chat. Keep this in mind for sensitive repositories.
- Layout and config keys: [references/data.md](skills/weekly-recap/references/data.md).

### Development

```bash
pip install skills-ref
agentskills validate skills/weekly-recap
```

## License

[MIT](LICENSE)
