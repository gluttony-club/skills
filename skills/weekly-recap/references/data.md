# Local data

Everything stays on the user's machine, in `~/.weekly-recap` (or the directory
in `$WEEKLY_RECAP_HOME`).

```
~/.weekly-recap/
├── config.json
├── style.md                          # optional: the user's writing preferences
└── 2026/
    ├── week-42.md                    # Monday-to-Sunday recap, ISO year and week
    └── 2026-09-28_to_2026-10-11.md   # any other range, under its start year
```

- Week files use the ISO year and week of the Monday (`2026-12-28 ~ 2027-01-03`
  is `2026/week-53.md`).
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
  "author_aliases": ["old-name", "old@example.com"],
  "timezone": "Asia/Shanghai"
}
```

| Key | Meaning |
| --- | --- |
| `repos[].name` | Section heading in the recap. |
| `repos[].path` | Local clone. |
| `repos[].links` | Optional. Link templates when the host is not GitHub, GitLab, CNB, Gitee or Bitbucket. |
| `author_aliases` | Optional. Other names or emails that are also the user, added to each repo's `git config user.name` / `user.email`. |
| `timezone` | Optional. IANA name or offset such as `+08:00`; default `Asia/Shanghai`. |

`store.py add-repo` writes this file (creating it if needed, backing it up
before changes). Other keys can be edited by hand.

## style.md

Free-form notes the user agreed to keep, one per line, for example:

```markdown
- 本周重点最多两条
- 纯文案改动不单独列出
```

They override [writing-guide.md](writing-guide.md). Only preferences go here,
never report content.

## Other skills

Other skills in this repository may read the saved recaps (for example to draft
a half-year OKR self-review). They rely on the layout and title format above.
