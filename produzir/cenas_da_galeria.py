# -*- coding: utf-8 -*-
"""Transforma a galeria oficial em cenas de cartão (foto parada com zoom lento).

Por que existe: os trailers 1 e 2 somam 257 s de material, o que dá **28 cenas
aptas**. Com a regra de uma frase por cena a cada 7 dias, isso trava o
Instagram em 4 cartões/dia sem folga nenhuma — abaixo dos 4-6 que o PLANO.md
§3 pede. A galeria oficial tem **306 imagens**; com elas o formato G tem
material para meses.

A descrição de cada cena sai do NOME DO ARQUIVO da Rockstar
(`jason-and-lucia-07.jpg`, `mount-kalaga-national-park-03.jpg`), não de uma
leitura da imagem. É deliberado: o nome é o que a própria Rockstar diz que a
foto mostra. Nada é inventado sobre o conteúdo.

Ficam de fora: cartelas de logo, capas de álbum, postais em formatos de papel
de parede (`-ultrawide`, `-tablet`, `-phone`, `-square`) e as imagens de
`opengraph`/`twitter` — não há o que mostrar num cartão.

Uso: python produzir/cenas_da_galeria.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from nucleo import cenas as C  # noqa: E402

DUR_FOTO = 8.0            # dentro da janela de 6-12 s das cenas de vídeo

FORA = ("opengraph", "twitter-image", "cover-art", "-ultrawide", "-tablet",
        "-phone", "-square", "-portrait", "-landscape", "an-extended-look",
        "vi.", "t1.", "t2.", "poster", "logo")

# Assunto -> (descrição, tags). A chave casa por prefixo do nome do arquivo.
ASSUNTOS = {
    "jason-and-lucia": ("Jason e Lucia juntos, em imagem oficial da Rockstar",
                        ["jason", "lucia", "dupla", "personagem"]),
    "jason-duval": ("Jason Duval em imagem oficial da Rockstar",
                    ["jason", "personagem"]),
    "lucia-caminos": ("Lucia Caminos em imagem oficial da Rockstar",
                      ["lucia", "personagem"]),
    "vice-city": ("Vice City em imagem oficial da Rockstar",
                  ["cidade", "vice-city", "mapa", "lugar"]),
    "leonida-keys": ("As Leonida Keys em imagem oficial da Rockstar",
                     ["lugar", "mapa", "leonida", "praia"]),
    "port-gellhorn": ("Port Gellhorn em imagem oficial da Rockstar",
                      ["lugar", "mapa", "leonida"]),
    "mount-kalaga-national-park": (
        "O Mount Kalaga National Park em imagem oficial da Rockstar",
        ["lugar", "mapa", "natureza", "leonida"]),
    "grassrivers": ("Grassrivers em imagem oficial da Rockstar",
                    ["lugar", "mapa", "natureza", "pantano", "leonida"]),
    "ambrosia": ("Ambrosia em imagem oficial da Rockstar",
                 ["lugar", "mapa", "leonida"]),
    "boobie-ike": ("Boobie Ike em imagem oficial da Rockstar",
                   ["personagem", "boobie"]),
    "real-dimez": ("A dupla Real Dimez em imagem oficial da Rockstar",
                   ["personagem", "musica"]),
    "raul-bautista": ("Raul Bautista em imagem oficial da Rockstar",
                      ["personagem"]),
    "drequan-priest": ("Dre'Quan Priest em imagem oficial da Rockstar",
                       ["personagem", "musica"]),
    "cal-hampton": ("Cal Hampton em imagem oficial da Rockstar",
                    ["personagem"]),
    "brian-heder": ("Brian Heder em imagem oficial da Rockstar",
                    ["personagem"]),
    "vintage-vice-city": ("Conteúdo do Vintage Vice City Pack, o bônus de "
                          "pré-venda", ["bonus", "vintage", "pre-venda"]),
    "ultimate-edition": ("Conteúdo exclusivo da Ultimate Edition de GTA 6",
                         ["ultimate", "edicoes", "bonus"]),
}


def _assunto(nome: str) -> tuple[str, list[str]] | None:
    for chave in sorted(ASSUNTOS, key=len, reverse=True):
        if nome.startswith(chave):
            return ASSUNTOS[chave]
    return None


def gerar() -> list[dict]:
    if not C.GALERIA.is_dir():
        print("galeria ausente — rode produzir/baixar_oficial.py")
        return []
    saida = []
    for p in sorted(C.GALERIA.iterdir()):
        if p.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        nome = p.stem
        if any(f in p.name for f in FORA):
            continue
        assunto = _assunto(nome)
        if not assunto:
            continue          # sem assunto conhecido, sem descrição, sem cartão
        descricao, tags = assunto
        saida.append({
            "id": f"galeria-{nome}",
            "video_origem": "galeria",
            "arquivo": p.name,
            "inicio": 0.0,
            "fim": DUR_FOTO,
            "descricao": descricao,
            "tags": tags,
            "licenca": "rockstar_oficial",
            "credito": "",
            "no_runner": False,
        })
    return saida


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    novas = gerar()
    print(f"{len(novas)} fotos da galeria viram cena")
    if a.dry_run:
        for c in novas[:8]:
            print(f"  {c['id']}: {c['descricao']} {c['tags']}")
        return
    atuais = [c for c in C.carregar() if c["video_origem"] != "galeria"]
    C.gravar(atuais + novas)
    aptas = [c for c in C.aptas_para_cartao() if not c.get("no_runner")]
    print(f"conteudo/cenas.json: {len(atuais) + len(novas)} cenas, "
          f"{len(aptas)} aptas para cartão")


if __name__ == "__main__":
    main()
