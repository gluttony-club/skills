# Local data

Everything stays on the user's machine, in `~/.weekly-recap` (or the directory
in `$WEEKLY_RECAP_HOME`).

```
~/.weekly-recap/
├── config.json
├── style.md                          # optional: the user's writing preferences
└── 2026/
    ├── 26.10.12-26.10.18.md          # a week
    └── 26.09.28-26.10.11.md          # any other range, e.g. two weeks
```

- Every recap is named by its range as `YY.MM.DD-YY.MM.DD.md`, in the folder of
  its start year (`2026-12-28 ~ 2027-01-03` is `2026/26.12.28-27.01.03.md`).
  Sorting by name sorts by date.
- Files saved before 0.6.0 as `week-42.md` or `2026-09-28_to_2026-10-11.md` are
  still listed, and renamed to the new form the first time `store.py save`,
  `path` or `text` is run for that range. Their `.bak-…` copies keep their names.
- The first line of every recap is `# 周报 (YYYY-MM-DD ~ YYYY-MM-DD)` (or another
  title, same date format). `store.py list` reads the range from it.
- Replacing a recap keeps the old one as `<file>.bak-<YYYYmmddHHMMSS>`. Nothing is
  deleted by the scripts.

## config.json

```json
{
  "repos": [
    { "name": "shop-web", "path": "/Users/me/code/shop-web" },
    { "name": "internal-tool", "path": "/Users/me/code/tool",
      "links": { "commit": "https://git.example.com/tool/commit/{sha}",
                 "pr": "https://git.example.com/tool/merge/{number}" } }
  ],
  "author_aliases": ["old-name", "old@example.com"]
}
```

| Key | Meaning |
| --- | --- |
| `repos[].name` | Section heading in the recap. |
| `repos[].path` | Local clone. |
| `repos[].links` | Optional. Link templates when the host is not GitHub, GitLab, CNB, Gitee or Bitbucket. |
| `author_aliases` | Optional. Other names or emails that are also the user, added to each repo's `git config user.name` / `user.email`. |

Dates use this machine's local time zone; there is no time zone setting. On
macOS or Linux, run the scripts with `TZ=Asia/Tokyo` (for example) to use
another one.

`store.py add-repo` writes this file (creating it if needed, backing it up
before changes). The skill adds every repo the user picks, without asking. When
a name is taken, the new repo is named `parent/dir`, e.g. `work/web`. Other
keys can be edited by hand.

## style.md

Free-form notes the user agreed to keep, one per line, for example:

```markdown
- 周报附上 PR 链接
- 不要自动复制到剪贴板
- 纯文案改动不单独列出
```

They override [writing-guide.md](writing-guide.md). Only preferences go here,
never report content.

## Other skills

Other skills in this repository may read the saved recaps (for example to draft
a half-year OKR self-review). They rely on the layout and title format above.
