"""The image must be readable by its runtime user whatever the modes in the build context.

Production deploys with `git pull`; a restrictive umask on the VPS makes every checked-out file
0600. COPY preserves modes, so the files landed root-owned and unreadable by uid 10001 and the
blog crash-looped with PermissionError: /app/app.py.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path

BLOG = Path(__file__).resolve().parents[1]
DOCKER = shutil.which("docker")
SKIP = shutil.ignore_patterns(".venv", "__pycache__", "tests", "*.sqlite*")


@unittest.skipUnless(DOCKER, "docker is required to build the image")
class ImageIsReadableByRuntimeUser(unittest.TestCase):
    def test_build_with_0600_context_yields_readable_app(self):
        tag = "blog-perm-" + uuid.uuid4().hex[:8]
        with tempfile.TemporaryDirectory() as tmp:
            context = Path(tmp) / "blog"
            shutil.copytree(BLOG, context, ignore=SKIP)
            for root, dirs, files in os.walk(context):
                for name in dirs:
                    os.chmod(Path(root, name), 0o700)
                for name in files:
                    os.chmod(Path(root, name), 0o600)
            try:
                build = subprocess.run(["docker", "build", "-q", "-t", tag, str(context)], capture_output=True, text=True)
                self.assertEqual(build.returncode, 0, build.stderr[-1500:])
                run = subprocess.run(["docker", "run", "--rm", "--entrypoint", "/app/.venv/bin/python", tag, "-c",
                    "import pathlib\n"
                    "for p in ('/app/app.py', '/app/store.py', '/app/templates/base.html', '/app/static/blog.css'):\n"
                    "    pathlib.Path(p).read_text()\n"], capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr[-1500:])
            finally:
                subprocess.run(["docker", "rmi", "-f", tag], capture_output=True)


if __name__ == "__main__":
    unittest.main()
