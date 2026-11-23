"""Scheduled tasks send drafts and report `awaiting_approval`; nothing tells them to publish."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "blog"))
import local_setup  # noqa: E402


class TaskInstructions(unittest.TestCase):
    def test_generated_schedule_text_sends_drafts_and_expects_awaiting_approval(self):
        for schedule in ("terca", "sabado"):
            text = local_setup.schedule_instructions(schedule)
            with self.subTest(schedule=schedule):
                self.assertIn("status=draft", text)
                self.assertIn("awaiting_approval", text)
                self.assertNotIn("status=published", text)
                self.assertNotIn("publicar esse conteúdo automaticamente", text)
                self.assertIn(f"{schedule}-AAAA-MM-DD", text)

    def test_docs_do_not_tell_the_tasks_to_send_published(self):
        text = (ROOT / "docs" / "blog.md").read_text()
        # The quoted block is the text pasted into the scheduled tasks.
        quoted = "\n".join(line for line in text.splitlines() if line.startswith(">"))
        self.assertIn("status=draft", quoted)
        self.assertIn("awaiting_approval", quoted)
        self.assertNotIn("status=published", quoted)
        self.assertNotIn("use `published`", text)


if __name__ == "__main__":
    unittest.main()
