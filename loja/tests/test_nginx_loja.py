"""An unknown /loja/... answers 404 with the shop's own page; the rest of the site is untouched.

Runs the real nginx image against the real nginx/default.conf and the real public/ directory,
like blog/tests/test_nginx_isolation.py. There is no blog container here: the landing and the
/blog/ fallback page must behave as they do when it is absent. Needs Docker; without it the
tests are skipped, loudly.
"""
import json
import shutil
import subprocess
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
DOCKER = shutil.which("docker")
PAGINA_404 = "Esse produto não está na vitrine"


def docker(*args, check=True):
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=check)


def criar_rede(nome):
    """A user-defined network (Docker's embedded DNS, as in production). On a machine with many
    compose projects Docker's default address pools run out ("fully subnetted"), so fall back to
    an explicit subnet from a block nobody uses."""
    if docker("network", "create", nome, check=False).returncode == 0:
        return
    for n in range(40):
        if docker("network", "create", "--subnet", f"10.241.{n}.0/24", nome, check=False).returncode == 0:
            return
    raise AssertionError("could not create a Docker network for the probe")


class _SemRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def get(port, path, follow=False):
    opener = urllib.request.build_opener(*([] if follow else [_SemRedirect]))
    try:
        with opener.open(f"http://127.0.0.1:{port}{path}", timeout=10) as r:
            return r.status, r.read().decode("utf-8", "replace"), r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), e.headers


@unittest.skipUnless(DOCKER, "docker is required to probe nginx")
class LojaNotFound(unittest.TestCase):
    conf = CONF

    @classmethod
    def setUpClass(cls):
        cls.tag = "nginxloja-" + uuid.uuid4().hex[:8]
        name = f"{cls.tag}-web"
        criar_rede(cls.tag)
        # registered at once: class cleanups run even when setUpClass fails below (LIFO, so the
        # container goes before its network)
        cls.addClassCleanup(docker, "network", "rm", cls.tag, check=False)
        cls.addClassCleanup(docker, "rm", "-f", name, check=False)
        docker("run", "-d", "--rm", "--label", f"probe={cls.tag}", "--name", name, "--network", cls.tag,
               "-p", "127.0.0.1::80",
               "-v", f"{PUBLIC}:/usr/share/nginx/html:ro", "-v", f"{cls.conf}:/etc/nginx/conf.d/default.conf:ro", IMAGE)
        time.sleep(1.5)
        running = docker("inspect", "-f", "{{.State.Running}}", name, check=False).stdout.strip()
        if running != "true":
            raise AssertionError("web did not stay up:\n" + docker("logs", name, check=False).stderr)
        cls.port = int(docker("port", name, "80/tcp").stdout.split(":")[-1].strip())
        dados = json.loads((ROOT / "loja" / "produtos.json").read_text(encoding="utf-8"))
        cls.paginas = ["/loja/"] + [f"/loja/{s}/" for s in dados["linhas"]] + [f"/loja/{p['slug']}/" for p in dados["produtos"]]

    def test_config_is_valid(self):
        r = docker("run", "--rm", "--network", "none", "-v", f"{PUBLIC}:/usr/share/nginx/html:ro",
                   "-v", f"{CONF}:/etc/nginx/conf.d/default.conf:ro", IMAGE, "nginx", "-t", check=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_unknown_loja_addresses_answer_404_with_the_shop_page(self):
        for path in ("/loja/nao-existe/", "/loja/nao-existe", "/loja/a/b/c/", "/loja/img/falta.webp",
                     "/loja/nao-existe.html"):
            with self.subTest(path=path):
                status, body, headers = get(self.port, path)
                self.assertEqual(status, 404)
                self.assertIn(PAGINA_404, body)
                self.assertIn("text/html", headers["Content-Type"])

    def test_every_generated_page_is_200_and_is_not_the_404_page(self):
        for path in self.paginas:
            with self.subTest(path=path):
                status, body, _ = get(self.port, path)
                self.assertEqual(status, 200)
                self.assertNotIn(PAGINA_404, body)

    def test_shop_assets_are_served(self):
        for path, tipo in (("/loja/loja.css", "text/css"), ("/loja/loja.js", "javascript"),
                           ("/loja/sprite.svg", "image/svg+xml"), ("/loja/sitemap.xml", "xml")):
            with self.subTest(path=path):
                status, _, headers = get(self.port, path)
                self.assertEqual(status, 200)
                self.assertIn(tipo, headers["Content-Type"])

    def test_a_folder_without_trailing_slash_does_not_leave_the_public_scheme(self):
        status, _, headers = get(self.port, "/loja/cameras-e-gravadores")
        # behind Traefik nginx sees plain http: an absolute Location would downgrade the scheme
        self.assertIn(status, (200, 301, 308))
        if status != 200:
            self.assertTrue(headers["Location"].startswith("/"), headers["Location"])
        status, _, headers = get(self.port, "/loja")
        self.assertEqual((status, headers["Location"]), (308, "/loja/"))
        self.assertEqual(get(self.port, "/loja", follow=True)[0], 200)

    def test_the_404_page_is_not_a_public_address_of_its_own(self):
        status, _, _ = get(self.port, "/loja/404.html")
        self.assertEqual(status, 404)

    def test_landing_and_blog_fallback_and_other_404s_are_unaffected(self):
        status, body, _ = get(self.port, "/")
        self.assertEqual(status, 200)
        self.assertNotIn(PAGINA_404, body)
        status, body, _ = get(self.port, "/blog/")  # no blog container in this probe
        self.assertEqual(status, 502)
        self.assertIn("O blog está fora do ar", body)
        status, body, _ = get(self.port, "/nada-aqui/")
        self.assertEqual(status, 404)
        self.assertNotIn(PAGINA_404, body)
        self.assertEqual(get(self.port, "/robots.txt")[0], 200)


@unittest.skipUnless(DOCKER, "docker is required to probe nginx")
class ProbeCleansUpWhenSetUpFails(unittest.TestCase):
    """A probe whose setUpClass fails must not leave its network or container behind: Docker's
    address pools are small on a machine with many projects, and a leaked network blocks the next run."""

    def test_nothing_is_left_when_the_container_cannot_start(self):
        import io
        import tempfile
        quebrada = Path(tempfile.mkdtemp()) / "quebrada.conf"
        quebrada.write_text("this is not an nginx directive;\n")
        Falha = type("Falha", (LojaNotFound,), {"conf": quebrada})
        resultado = unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Falha))
        tag = Falha.tag
        try:
            self.assertFalse(resultado.wasSuccessful(), "the broken conf should have failed the probe")
            self.assertNotEqual(docker("network", "inspect", tag, check=False).returncode, 0,
                                f"network {tag} was leaked")
            self.assertEqual(docker("ps", "-aq", "--filter", f"label=probe={tag}").stdout.split(), [],
                             "container was leaked")
        finally:  # never leave our own debris, whatever the assertions said
            for n in docker("ps", "-aq", "--filter", f"label=probe={tag}").stdout.split():
                docker("rm", "-f", n, check=False)
            docker("network", "rm", tag, check=False)


if __name__ == "__main__":
    unittest.main()
