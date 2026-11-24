"""The red-green gate (.githooks/config) has to keep covering this suite as well as the blog's.

check-red-green picks the app whose tests the branch changed and expands `{dir}` to it, so one
app-agnostic TEST_CMD serves both. Two edits would silently blind it to one app: hardcoding an app
into the command, or pinning TEST_DIR (the tool then looks at that app only)."""
import re
import unittest
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[2] / ".githooks" / "config"


def linhas_ativas():
    return [l for l in CONFIG.read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("#")]


def test_cmd():
    achadas = [m.group(1) for l in linhas_ativas() if (m := re.fullmatch(r'TEST_CMD="(.*)"', l.strip()))]
    return achadas[0] if achadas else None


class PortaoCobreALoja(unittest.TestCase):
    # @covers-existing: the config was already app-agnostic; this keeps it that way
    def test_the_gate_is_declared(self):
        self.assertTrue(test_cmd(), ".githooks/config must declare TEST_CMD or the pre-push gate is not installed")

    # @covers-existing: the config was already app-agnostic; this keeps it that way
    def test_the_command_runs_whichever_app_the_branch_changed(self):
        cmd = test_cmd()
        self.assertIn("{dir}", cmd)
        for app in ("blog", "loja"):
            self.assertNotIn(app, cmd, f"TEST_CMD names {app}: the other app would be tested with it too")

    # @covers-existing: the config was already app-agnostic; this keeps it that way
    def test_no_single_app_is_pinned(self):
        pinadas = [l for l in linhas_ativas() if l.strip().startswith("TEST_DIR")]
        self.assertEqual(pinadas, [], "TEST_DIR pins one app: the other app's tests would never be checked")

    # @covers-existing: the config was already app-agnostic; this keeps it that way
    def test_the_runner_is_pytest_because_only_it_gives_the_gate_a_report_per_case(self):
        self.assertIn("pytest", test_cmd())


if __name__ == "__main__":
    unittest.main()
