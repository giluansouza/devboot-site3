"""Turn source photos into what public/loja/img/<slug>/ serves. Needs Pillow:

    uv run --with pillow python preparar_foto.py <slug> <photo> [<photo> ...]

The photos become 1.webp, 2.webp, ... (800 x 800, the product padded onto the white `photo`
square, never cropped, ~20 KB each: the site is read on 4G) and og.jpg (1200 x 630, for the
WhatsApp / Google preview). The first photo is the cover. Then list them in produtos.json:

    "fotos": [{"arquivo": "1.webp", "fonte": "<URL the photo came from>"}, ...], "og": "og.jpg"

and run `uv run python gerar.py`. Source photos must be at least 1000 px on the short side.

The scene photo of a line (the tile on the shop home) is a different job:

    uv run --with pillow python preparar_foto.py --ambiente <line-slug> <photo>

It writes public/loja/img/_linhas/<line-slug>/700.webp and 480.webp (the same picture, ratio
700:478, never padded or cropped: a source of another ratio is refused). Then, in produtos.json,
under that line: "ambiente": {"fonte": "<image URL>", "alt": "<scene, in Portuguese>",
"produto": "<slug of the product it shows>"}.
"""
import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
LADO, OG = 800, (1200, 630)
AMBIENTE = (700, 478)          # keep equal to AMBIENTE_LARGURA/ALTURA in gerar.py
AMBIENTE_LARGURAS = (480, 700)


def sobre_branco(origem):
    im = Image.open(origem).convert("RGBA")
    if min(im.size) < 1000:
        raise SystemExit(f"{origem}: {im.size[0]}x{im.size[1]} is below 1000 px")
    fundo = Image.new("RGBA", im.size, (255, 255, 255, 255))
    fundo.alpha_composite(im)
    return fundo.convert("RGB")


def quadrado(im, lado):
    """Fit inside a white square of `lado` px: pad, never crop."""
    im = im.copy()
    im.thumbnail((lado, lado), Image.LANCZOS)
    tela = Image.new("RGB", (lado, lado), (255, 255, 255))
    tela.paste(im, ((lado - im.width) // 2, (lado - im.height) // 2))
    return tela


def main(slug, fotos):
    saida = RAIZ / "public" / "loja" / "img" / slug
    saida.mkdir(parents=True, exist_ok=True)
    for velho in saida.glob("*"):
        velho.unlink()
    for i, f in enumerate(fotos, 1):
        im = sobre_branco(f)
        quadrado(im, LADO).save(saida / f"{i}.webp", "WEBP", quality=80, method=6)
    capa = sobre_branco(fotos[0])
    capa.thumbnail((OG[1], OG[1]), Image.LANCZOS)
    tela = Image.new("RGB", OG, (255, 255, 255))
    tela.paste(capa, ((OG[0] - capa.width) // 2, (OG[1] - capa.height) // 2))
    tela.save(saida / "og.jpg", "JPEG", quality=84, optimize=True)
    for a in sorted(saida.iterdir()):
        print(f"{a.relative_to(RAIZ)}  {a.stat().st_size / 1024:.1f} KB")


def ambiente(linha, origem):
    im = Image.open(origem).convert("RGB")
    larg, alt = AMBIENTE
    if im.width < larg or abs(im.width / im.height - larg / alt) > 0.01 * larg / alt:
        raise SystemExit(f"{origem}: {im.width}x{im.height} is not at least {larg} px wide at the "
                         f"{larg}:{alt} ratio (1% tolerance); a scene photo is never padded or cropped")
    saida = RAIZ / "public" / "loja" / "img" / "_linhas" / linha
    saida.mkdir(parents=True, exist_ok=True)
    for velho in saida.glob("*"):
        velho.unlink()
    for w in AMBIENTE_LARGURAS:
        h = round(w * alt / larg)
        im.resize((w, h), Image.LANCZOS).save(saida / f"{w}.webp", "WEBP", quality=80, method=6)
    for a in sorted(saida.iterdir()):
        print(f"{a.relative_to(RAIZ)}  {a.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--ambiente":
        ambiente(sys.argv[2], Path(sys.argv[3]))
    elif len(sys.argv) < 3 or sys.argv[1].startswith("--"):
        raise SystemExit(__doc__)
    else:
        main(sys.argv[1], [Path(p) for p in sys.argv[2:]])
