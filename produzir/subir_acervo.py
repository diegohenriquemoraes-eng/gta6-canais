# -*- coding: utf-8 -*-
"""Empacota o material oficial e sobe para o repo de mídia — o runner baixa de lá.

**Por que isso existe.** O runner do Actions não consegue baixar os vídeos da
Rockstar: o YouTube devolve *"Sign in to confirm you're not a bot"* para o
yt-dlp em IP de datacenter (medido em 23/09/2026), e o Extended Look ainda tem
restrição de idade. A galeria oficial é gitignorada por tamanho. Resultado: o
Short sobrevivia (cai no gradiente), mas **o cartão do Instagram falhava**
— ele precisa do arquivo de verdade: `origem de trailer2-013 ausente`.

A saída é hospedar o acervo onde o runner alcança: os **Releases do repo
público de mídia**, que já existe para servir MP4 ao Instagram.

**O acervo sobe REDUZIDO.** As fotos da galeria são 4K (~1,4 MB cada, 432 MB no
total) e o render usa no máximo 1080 px de largura — a zona de vídeo do cartão
é 1080×608 e o fundo do Short é 1080×1920. Reduzir para 1080p derruba o pacote
para uma fração do tamanho sem tirar um pixel útil, e o que trafega toda vez
que o cache do Actions expira é isso.

Uso:
    python produzir/subir_acervo.py              # empacota e sobe
    python produzir/subir_acervo.py --so-montar  # só monta o pacote local
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tarfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

OFICIAL = RAIZ / "marca" / "oficial"
GALERIA = OFICIAL / "galeria"
TMP = RAIZ / "saida" / "acervo"
PACOTE = TMP / "acervo-oficial.tar"

REPO_MIDIA = "diegohenriquemoraes-eng/gta6-media"
TAG = "acervo"
LARGURA_MAX = 1080


def reduzir_galeria(destino: Path) -> int:
    """Reamostra as fotos para 1080 px de largura. Devolve quantas entraram."""
    from PIL import Image
    destino.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in sorted(GALERIA.iterdir()):
        if p.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        alvo = destino / (p.stem + ".jpg")
        if alvo.exists():
            n += 1
            continue
        try:
            im = Image.open(p).convert("RGB")
            if im.width > LARGURA_MAX:
                h = round(im.height * LARGURA_MAX / im.width)
                im = im.resize((LARGURA_MAX, h), Image.LANCZOS)
            im.save(alvo, quality=88, optimize=True)
            n += 1
        except Exception as exc:
            print(f"  ! {p.name}: {exc}")
    return n


def montar() -> Path:
    TMP.mkdir(parents=True, exist_ok=True)
    reduzida = TMP / "galeria"
    print("[1] Reduzindo a galeria para 1080 px")
    n = reduzir_galeria(reduzida)
    mb = sum(f.stat().st_size for f in reduzida.iterdir()) / 1e6
    print(f"  {n} imagens, {mb:.0f} MB (eram "
          f"{sum(f.stat().st_size for f in GALERIA.iterdir()) / 1e6:.0f} MB)")

    print("[2] Empacotando trailers + galeria")
    with tarfile.open(PACOTE, "w") as tar:
        for nome in ("trailer1.mp4", "trailer2.mp4", "extended.mp4"):
            f = OFICIAL / nome
            if f.exists():
                tar.add(f, arcname=nome)
                print(f"  + {nome} ({f.stat().st_size / 1e6:.0f} MB)")
        for f in sorted(reduzida.iterdir()):
            tar.add(f, arcname=f"galeria/{f.name}")
    print(f"  pacote: {PACOTE.name} ({PACOTE.stat().st_size / 1e6:.0f} MB)")
    return PACOTE


def subir(pacote: Path) -> None:
    print("[3] Enviando para o Release do repo de mídia")
    if subprocess.run(["gh", "release", "view", TAG, "-R", REPO_MIDIA],
                      capture_output=True).returncode != 0:
        subprocess.run(["gh", "release", "create", TAG, "-R", REPO_MIDIA,
                        "--title", "Acervo oficial",
                        "--notes", "Trailers da Rockstar e galeria oficial "
                                   "reduzida a 1080 px, para o runner do "
                                   "Actions. Material de divulgação "
                                   "© Rockstar Games."], check=True)
    subprocess.run(["gh", "release", "upload", TAG, str(pacote),
                    "-R", REPO_MIDIA, "--clobber"], check=True)
    print(f"  no ar: https://github.com/{REPO_MIDIA}/releases/download/"
          f"{TAG}/{pacote.name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-montar", action="store_true")
    a = ap.parse_args()
    if not GALERIA.is_dir():
        raise SystemExit("galeria ausente — rode produzir/baixar_oficial.py")
    p = montar()
    if not a.so_montar:
        subir(p)


if __name__ == "__main__":
    main()
