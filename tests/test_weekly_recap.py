"""Tests for the weekly-recap scripts, run against throwaway git repositories.

    python -m unittest discover -s tests

Uses only the standard library. Time zone cases set TZ for the scripts they run,
so they are skipped on Windows, where TZ does not select a zone.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "weekly-recap" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import links  # noqa: E402
import signals  # noqa: E402
from collect_commits import trivial_hints  # noqa: E402

AUTHOR = ("Tester", "tester@example.com")
POSIX_TZ = os.name != "nt"


class RepoCase(unittest.TestCase):
    """A temp dir with WEEKLY_RECAP_HOME inside it, and helpers to build repos."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.home = self.tmp / "home"
        self.env = {**os.environ, "WEEKLY_RECAP_HOME": str(self.home)}

    def tearDown(self):
        self._tmp.cleanup()

    def repo(self, name: str, parent: str = "") -> Path:
        path = self.tmp / parent / name if parent else self.tmp / name
        path.mkdir(parents=True)
        self.git(path, "init", "-q", "-b", "main")
        # Like a real clone: the identity the scripts read to find the user's own commits.
        self.git(path, "config", "user.name", AUTHOR[0])
        self.git(path, "config", "user.email", AUTHOR[1])
        return path

    def git(self, repo: Path, *args: str, date: str | None = None) -> None:
        env = dict(self.env)
        if date:
            env["GIT_AUTHOR_DATE"] = date
        subprocess.run(["git", "-C", str(repo), "-c", f"user.name={AUTHOR[0]}",
                        "-c", f"user.email={AUTHOR[1]}", *args], check=True, env=env,
                       capture_output=True)

    def commit(self, repo: Path, subject: str, date: str, file: str = "a.txt") -> None:
        with open(repo / file, "a", encoding="utf-8") as fh:
            fh.write(subject + "\n")
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-q", "-m", subject, date=date)

    def run_script(self, script: str, *args: str, tz: str | None = None, cwd: Path | None = None,
                   check: bool = True) -> dict:
        env = dict(self.env)
        if tz:
            env["TZ"] = tz
        proc = subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True,
                              text=True, encoding="utf-8", env=env, cwd=cwd or self.tmp)
        if check and proc.returncode != 0:
            self.fail(f"{script} {args} exited {proc.returncode}: {proc.stderr}")
        return json.loads(proc.stdout) if proc.stdout.strip() else {}

    def collect(self, start: str, end: str, *repos: str, tz: str | None = None, extra=()) -> dict:
        args = ["collect", "--start", start, "--end", end, "--author", AUTHOR[0], *extra]
        for r in repos:
            args += ["--repo", r]
        return self.run_script("collect_commits.py", *args, tz=tz)


@unittest.skipUnless(POSIX_TZ, "TZ selects a zone only on POSIX")
class DateRangeTest(RepoCase):
    def test_range_crossing_daylight_saving_keeps_midnight_bounds(self):
        out = self.run_script("date_range.py", "period", "2026-10-26", "2026-11-08", tz="America/New_York")
        self.assertEqual(out["range"]["start_at"], "2026-10-26T00:00:00-04:00")
        self.assertEqual(out["range"]["end_at"], "2026-11-08T23:59:59-05:00")
        self.assertEqual(out["range"]["kind"], "period")

    def test_week_uses_local_zone(self):
        out = self.run_script("date_range.py", "week", "2026-10-15", tz="Asia/Tokyo")
        self.assertEqual(out["range"]["start_at"], "2026-10-12T00:00:00+09:00")
        self.assertEqual(out["range"]["end_at"], "2026-10-18T23:59:59+09:00")
        self.assertEqual((out["range"]["kind"], out["range"]["iso_week"]), ("week", 42))


@unittest.skipUnless(POSIX_TZ, "TZ selects a zone only on POSIX")
class CollectTest(RepoCase):
    def test_range_includes_first_and_last_second_only(self):
        repo = self.repo("web")
        for date, subject in [("2026-10-11T23:59:59+08:00", "before"), ("2026-10-12T00:00:00+08:00", "first"),
                              ("2026-10-18T23:59:59+08:00", "last"), ("2026-10-19T00:00:00+08:00", "after"),
                              ("2026-10-12T00:30:00+09:00", "tokyo-sunday-night")]:
            self.commit(repo, subject, date)
        shanghai = self.collect("2026-10-12", "2026-10-18", str(repo), tz="Asia/Shanghai")
        self.assertEqual(sorted(c["subject"] for c in shanghai["repos"][0]["commits"]), ["first", "last"])
        self.assertEqual(shanghai["start_at"], "2026-10-12T00:00:00+08:00")
        tokyo = self.collect("2026-10-12", "2026-10-18", str(repo), tz="Asia/Tokyo")
        self.assertEqual(sorted(c["subject"] for c in tokyo["repos"][0]["commits"]),
                         ["before", "first", "tokyo-sunday-night"])

    def test_repo_without_commits_in_range_is_ok_and_empty(self):
        busy, idle, empty = self.repo("busy"), self.repo("idle"), self.repo("empty")
        self.commit(busy, "feat: work", "2026-10-13T10:00:00+08:00")
        self.commit(idle, "feat: old work", "2026-09-01T10:00:00+08:00")
        out = self.collect("2026-10-12", "2026-10-18", str(busy), str(idle), str(empty), tz="Asia/Shanghai")
        counts = {r["name"]: (r["ok"], r["commit_count"]) for r in out["repos"]}
        self.assertEqual(counts, {"busy": (True, 1), "idle": (True, 0), "empty": (True, 0)})
        self.assertEqual(out["total_commits"], 1)

    def test_path_to_configured_repo_keeps_its_name_and_links(self):
        repo = self.repo("clone")
        self.commit(repo, "feat: a", "2026-10-13T10:00:00+08:00")
        self.home.mkdir()
        (self.home / "config.json").write_text(json.dumps({"repos": [
            {"name": "my-web", "path": str(repo), "links": {"commit": "https://git.corp/c/{sha}"}}]}))
        (repo / "src").mkdir()
        out = self.run_script("collect_commits.py", "collect", "--start", "2026-10-12", "--end", "2026-10-18",
                              "--author", AUTHOR[0], "--repo", ".", tz="Asia/Shanghai", cwd=repo / "src")
        found = out["repos"][0]
        self.assertEqual(found["name"], "my-web")
        self.assertTrue(found["commits"][0]["commit_url"].startswith("https://git.corp/c/"))

    def test_default_output_is_a_private_temp_file(self):
        repo = self.repo("web")
        self.commit(repo, "feat: a", "2026-10-13T10:00:00+08:00")
        first = self.collect("2026-10-12", "2026-10-18", str(repo), tz="Asia/Shanghai", extra=["--output"])
        second = self.collect("2026-10-12", "2026-10-18", str(repo), tz="Asia/Shanghai", extra=["--output"])
        try:
            self.assertNotEqual(first["written"], second["written"])
            self.assertEqual(stat.S_IMODE(os.stat(first["written"]).st_mode), 0o600)
            self.assertFalse(str(first["written"]).startswith(str(repo)))
            self.assertEqual(json.loads(Path(first["written"]).read_text())["total_commits"], 1)
        finally:
            for out in (first, second):
                Path(out["written"]).unlink(missing_ok=True)

    def test_repos_are_listed_most_recently_committed_first(self):
        old, new = self.repo("old"), self.repo("new")
        self.commit(old, "feat: old", "2026-05-01T10:00:00+08:00")
        self.commit(new, "feat: new", "2026-10-01T10:00:00+08:00")
        for repo in (old, new):
            self.run_script("store.py", "add-repo", str(repo))
        out = self.run_script("collect_commits.py", "repos", tz="Asia/Shanghai", cwd=new)
        self.assertEqual([r["name"] for r in out["repos"]], ["new", "old"])
        self.assertEqual(out["current_dir"]["name"], "new")
        self.assertTrue(out["current_dir"]["in_config"])


class StoreTest(RepoCase):
    def test_add_repo_renames_a_taken_name_instead_of_failing(self):
        first, second = self.repo("web", parent="work"), self.repo("web", parent="personal")
        self.assertTrue(self.run_script("store.py", "add-repo", str(first))["added"])
        out = self.run_script("store.py", "add-repo", str(second))
        self.assertTrue(out["added"])
        self.assertEqual(out["repo"]["name"], "personal/web")
        self.assertEqual(out["renamed_from"], "web")
        again = self.run_script("store.py", "add-repo", str(first))
        self.assertEqual((again["added"], again["reason"]), (False, "already configured"))

    def test_save_overwrite_keeps_a_backup(self):
        def save(text: str, *extra: str) -> dict:
            proc = subprocess.run([sys.executable, str(SCRIPTS / "store.py"), "save", "--start", "2026-10-12",
                                   "--end", "2026-10-18", *extra], input=text, capture_output=True, text=True,
                                  encoding="utf-8", env=self.env)
            return json.loads(proc.stdout)

        self.assertTrue(save("# 周报 (2026-10-12 ~ 2026-10-18)\n- v1\n")["saved"])
        refused = save("# 周报 (2026-10-12 ~ 2026-10-18)\n- v2\n")
        self.assertEqual((refused["saved"], refused["exists"]), (False, True))
        replaced = save("# 周报 (2026-10-12 ~ 2026-10-18)\n- v2\n", "--overwrite")
        self.assertTrue(replaced["saved"])
        self.assertIn("v1", Path(replaced["backup"]).read_text(encoding="utf-8"))
        self.assertIn("v2", Path(replaced["path"]).read_text(encoding="utf-8"))
        self.assertTrue(replaced["path"].endswith(os.path.join("2026", "week-42.md")))


class SignalsTest(unittest.TestCase):
    def fix(self, subject: str) -> bool:
        return signals.is_fix({"type": signals.conventional(subject)[0], "subject": subject})

    def test_fixes_without_a_conventional_prefix_count(self):
        for subject in ["fix: upload", "Fix upload on Safari", "fixed crash", "[hotfix] token", "修复上传失败"]:
            self.assertTrue(self.fix(subject), subject)

    def test_conventional_type_decides_and_lookalikes_do_not_count(self):
        for subject in ["feat: 新增修正逻辑", "fixture update", "prefix cleanup", 'Revert "fix: x"']:
            self.assertFalse(self.fix(subject), subject)

    def test_reverts_are_not_flagged_trivial(self):
        self.assertEqual(trivial_hints('Revert "feat: x"'), [])
        self.assertIn("typo", trivial_hints("fix typo in README"))


class LinksTest(unittest.TestCase):
    def test_web_url_keeps_http_port_and_drops_ssh_port_and_credentials(self):
        cases = {
            "https://git.corp.com:8443/team/web.git": "https://git.corp.com:8443/team/web",
            "http://10.0.0.5:8080/team/web.git": "http://10.0.0.5:8080/team/web",
            "https://user:tok@gitlab.corp.com:8443/a/b.git": "https://gitlab.corp.com:8443/a/b",
            "ssh://git@git.corp.com:2222/team/web.git": "https://git.corp.com/team/web",
            "git@github.com:a/b.git": "https://github.com/a/b",
        }
        for remote, web in cases.items():
            self.assertEqual(links.web_url(remote), web, remote)
        self.assertEqual(links.forge_of("https://gitlab.corp.com:8443/a/b"), "gitlab")


if __name__ == "__main__":
    unittest.main()
