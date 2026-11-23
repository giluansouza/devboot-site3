"""Local and ephemeral files must be ignored; the directories that carry the harness must not be."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def ignored(path, root=ROOT):
    # --no-index: judge the rules alone. Without it check-ignore skips tracked files, so a tracked
    # path always reads as "not ignored" and the negative test below could never fail.
    return subprocess.run(["git", "-C", str(root), "check-ignore", "--no-index", "-q", path]).returncode == 0


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

    def test_the_check_goes_red_when_the_harness_directory_is_ignored(self):
        # Scratch repo carrying our .gitignore plus the mistake this test exists to catch.
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            (Path(tmp) / ".gitignore").write_text((ROOT / ".gitignore").read_text() + ".claude/\n")
            # The harness files are TRACKED in the real repo. check-ignore without --no-index
            # skips tracked paths and would call these "not ignored": the very blind spot to catch.
            agent = Path(tmp) / ".claude" / "agents" / "x.md"
            agent.parent.mkdir(parents=True)
            agent.write_text("x\n")
            subprocess.run(["git", "-C", tmp, "add", "-f", ".claude/agents/x.md"], check=True)
            self.assertTrue(ignored(".claude/agents/x.md", root=tmp))


class DockerIgnore(unittest.TestCase):
    def test_build_context_excludes_harness_and_local_files(self):
        lines = {line.strip() for line in (ROOT / "blog" / ".dockerignore").read_text().splitlines()}
        for entry in (".venv", "__pycache__", "tests", ".claude"):
            self.assertIn(entry, lines, entry + " must stay out of the image build context")


class DeployDoc(unittest.TestCase):
    def setUp(self):
        self.doc = (ROOT / "docs" / "deploy-blog.md").read_text()

    def test_web_is_force_recreated_so_a_renamed_conf_is_picked_up(self):
        # git replaces nginx/default.conf by rename; a single-file bind mount keeps the old inode.
        self.assertRegex(self.doc, r"docker compose up -d --no-deps --force-recreate web")
        self.assertNotRegex(self.doc, r"docker compose up -d --no-deps web\n")
        self.assertIn("diff - nginx/default.conf", self.doc)
        self.assertIn("grep -i '^location: /blog/'", self.doc)

    def test_font_mime_probe_is_in_the_post_deploy_checks(self):
        self.assertIn("/blog/assets/fonts/archivo-800-latin.woff2 | grep -i content-type", self.doc)

    def test_readability_check_covers_directories(self):
        self.assertIn("-type d ! -perm -o+x", self.doc)


if __name__ == "__main__":
    unittest.main()
