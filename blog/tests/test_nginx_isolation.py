"""The landing must not depend on the blog container.

Runs the real nginx image against the real nginx/default.conf and the real
public/ directory, with a stub standing in for the blog. Needs Docker; without
it the tests are skipped, loudly.
"""
import shutil
import http.client
import re
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONF = ROOT / "nginx" / "default.conf"
PUBLIC = ROOT / "public"
IMAGE = "nginx:stable-alpine"

STUB_CONF = """server {
    listen 8000;
    location / { default_type text/plain; return 200 "uri=$request_uri host=$http_host"; }
}
"""

DOCKER = shutil.which("docker")


def docker(*args, check=True):
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=check)


def create_network(name):
    """A user-defined network (Docker's embedded DNS, as in production). On a machine with many
    compose projects Docker's default address pools run out ("fully subnetted"), so fall back to
    an explicit subnet from a block nobody uses."""
    if docker("network", "create", name, check=False).returncode == 0:
        return
    for n in range(40):
        if docker("network", "create", "--subnet", f"10.241.{n}.0/24", name, check=False).returncode == 0:
            return
    raise AssertionError("could not create a Docker network for the probe")


def get(port, path):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=10) as r:
            return r.status, r.read().decode("utf-8", "replace"), r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), e.headers


def head(port, path, host):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", path, headers={"Host": host})
    r = conn.getresponse()
    return r.status, r.getheader("Location")


@unittest.skipUnless(DOCKER, "docker is required to probe nginx")
class LandingIndependentOfBlog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tag = "nginxprobe-" + uuid.uuid4().hex[:8]
        # Registered before anything is created: runs even if setUpClass fails halfway or a test
        # fails. Removes only what carries THIS run's tag; never prunes networks it did not create.
        cls.addClassCleanup(cls.remove_everything_created, cls.tag)
        tmp = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, tmp, True)
        cls.stub_conf = tmp / "stub.conf"
        cls.stub_conf.write_text(STUB_CONF)
        create_network(cls.tag)

    @staticmethod
    def remove_everything_created(tag):
        for name in docker("ps", "-aq", "--filter", f"label=probe={tag}", check=False).stdout.split():
            docker("rm", "-f", name, check=False)
        docker("network", "rm", tag, check=False)

    def run_container(self, name, *args):
        unique = f"{self.tag}-{name}-{uuid.uuid4().hex[:6]}"
        r = docker("run", "-d", "--rm", "--label", f"probe={self.tag}", "--name", unique,
                   "--network", self.tag, *args)
        return unique

    def start_web(self):
        name = self.run_container(
            "web", "-p", "127.0.0.1::80",
            "-v", f"{PUBLIC}:/usr/share/nginx/html:ro",
            "-v", f"{CONF}:/etc/nginx/conf.d/default.conf:ro", IMAGE)
        time.sleep(1.5)
        state = docker("inspect", "-f", "{{.State.Running}}", name, check=False).stdout.strip()
        self.assertEqual(state, "true", "web did not stay up:\n" + docker("logs", name, check=False).stderr)
        port = docker("port", name, "80/tcp").stdout.split(":")[-1].strip()
        return name, int(port)

    def start_stub(self, tag="blog"):
        return self.run_container(
            tag, "--network-alias", "blog",
            "-v", f"{self.stub_conf}:/etc/nginx/conf.d/default.conf:ro", IMAGE)

    def test_nginx_config_is_valid_without_a_blog_host(self):
        r = docker("run", "--rm", "--network", "none",
                   "-v", f"{PUBLIC}:/usr/share/nginx/html:ro",
                   "-v", f"{CONF}:/etc/nginx/conf.d/default.conf:ro", IMAGE, "nginx", "-t", check=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_blog_redirect_is_relative_so_it_keeps_the_public_scheme(self):
        # Behind Traefik nginx sees plain http; an absolute Location would downgrade to http://.
        web, port = self.start_web()
        status, location = head(port, "/blog", "www.devboot.com.br")
        self.assertEqual(status, 308)
        self.assertEqual(location, "/blog/")

    def test_landing_survives_blog_absent_then_reaches_it_when_it_appears_and_moves(self):
        web, port = self.start_web()

        # blog absent: landing and static paths stay up, blog paths fail without hanging the site
        self.assertEqual(get(port, "/")[0], 200)
        self.assertEqual(get(port, "/robots.txt")[0] in (200, 404), True)
        status, body, _ = get(port, "/blog/")
        self.assertEqual(status, 502)
        self.assertIn("O blog está fora do ar", body)
        self.assertEqual(get(port, "/api/blog/x")[0], 502)
        self.assertEqual(get(port, "/mcp")[0], 502)
        self.assertEqual(get(port, "/")[0], 200)

        # blog appears AFTER nginx started: reached without a restart, URIs untouched
        blog1 = self.start_stub("blog1")
        time.sleep(11)  # resolver valid=10s
        for path in ("/blog/", "/blog/artigo-x", "/blog/sitemap.xml?a=1&b=2", "/api/blog/articles/7",
                     "/api/blog", "/mcp", "/.well-known/oauth-protected-resource",
                     "/.well-known/oauth-protected-resource/mcp"):
            with self.subTest(path=path):
                status, body, _ = get(port, path)
                self.assertEqual(status, 200, body)
                self.assertIn(f"uri={path} ", body + " ")
                self.assertIn("host=127.0.0.1:", body)
        self.assertEqual(get(port, "/")[0], 200)

        # blog recreated with a different IP: reached again without a restart
        docker("rm", "-f", blog1)
        filler = self.run_container("filler", IMAGE)  # takes the freed address range slot
        self.start_stub("blog2")
        deadline = time.time() + 30
        status = None
        while time.time() < deadline:
            status, body, _ = get(port, "/blog/x")
            if status == 200:
                break
            time.sleep(1)
        self.assertEqual(status, 200, "nginx never reached the recreated blog")
        self.assertIn("uri=/blog/x ", body + " ")
        self.assertTrue(filler)


@unittest.skipUnless(DOCKER, "docker is required to probe nginx")
class ProbeCleansUpAfterItself(unittest.TestCase):
    def test_network_and_containers_are_removed_when_setup_or_a_test_fails(self):
        seen = {}

        class Failing(LandingIndependentOfBlog):
            @classmethod
            def setUpClass(cls):
                super().setUpClass()
                seen["tag"] = cls.tag
                subprocess.run(["docker", "run", "-d", "--rm", "--label", f"probe={cls.tag}", "--name", cls.tag + "-x",
                                "--network", cls.tag, IMAGE, "sleep", "60"], capture_output=True, check=True)
                raise RuntimeError("setup fails after the network and a container exist")

            def test_never_runs(self):
                pass

        result = unittest.TextTestRunner(stream=open("/dev/null", "w")).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Failing))
        self.assertFalse(result.wasSuccessful())
        networks = docker("network", "ls", "--filter", f"name={seen['tag']}", "-q").stdout.split()
        containers = docker("ps", "-aq", "--filter", f"label=probe={seen['tag']}").stdout.split()
        self.assertEqual((networks, containers), ([], []))


class ComposeDoesNotGateTheLanding(unittest.TestCase):
    def test_web_does_not_wait_for_a_healthy_blog(self):
        text = (ROOT / "docker-compose.yml").read_text()
        web = re.search(r"^  web:\n(.*?)(?=^  \S)", text, re.S | re.M).group(1)
        self.assertNotIn("service_healthy", web)


if __name__ == "__main__":
    unittest.main()
