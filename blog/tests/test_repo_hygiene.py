"""Local and ephemeral files must be ignored; the directories that carry the harness must not be."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def ignored(path):
    return subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q", path]).returncode == 0


@unittest.skipUnless(shutil.which("git"), "git is required")
class GitIgnore(unittest.TestCase):
    def test_local_and_ephemeral_paths_are_ignored(self):
        for path in (".env", ".claude/settings.local.json", ".claude/worktrees/x/blog/app.py",
                     "blog/__pycache__/app.cpython-312.pyc", "blog/tests/__pycache__/x.pyc",
                     "blog/.venv/bin/python", ".local/chatgpt/local.env", "data/blog.sqlite3"):
            with self.subTest(path=path):
                self.assertTrue(ignored(path), path + " must be ignored")

    def test_shared_harness_files_are_not_ignored(self):
        for path in (".claude/settings.json", ".claude/agents/change-reviewer.md",
                     ".claude/skills/branch-table/SKILL.md", "blog/app.py"):
            with self.subTest(path=path):
                self.assertFalse(ignored(path), path + " must stay tracked")


if __name__ == "__main__":
    unittest.main()
