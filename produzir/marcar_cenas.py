# -*- coding: utf-8 -*-
"""Gera conteudo/cenas.json a partir dos vídeos oficiais (detecção de corte).

`scdet` do ffmpeg acha os cortes; `nucleo.cenas.montar_cenas` agrupa planos
curtos e fatia planos longos até tudo caber entre 6 e 12 s — a janela em que o
cartão dá tempo de ler a frase.

**Cena sem `descricao` não vira cartão** (`cenas.aptas_para_cartao`). A
descrição é escrita à mão a partir do quadro extraído: é ela que faz o
`escalar.py` casar frase com cena (frase de polícia sobre cena de praia é o
erro que a página dark comete e o algoritmo pune).

⚠ **O "An Extended Look" tem restrição de idade no YouTube** (medido em
22/09/2026): o yt-dlp exige cookies de conta logada, e o runner do Actions não
tem navegador. Consequência aceita: o ARQUIVO de vídeo do pipeline é
trailer 1 + trailer 2; o Extended Look continua sendo FONTE de fatos (o poço
já traz os timestamps), mas as cenas dele saem marcadas `no_runner: true` e o
`escalar.py` as ignora enquanto o arquivo não estiver em disco.

Uso:
    python produzir/marcar_cenas.py --contato    # gera a folha de contato
    python produzir/marcar_cenas.py              # (re)escreve cenas.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from nucleo import cenas as C  # noqa: E402

CONTATO = RAIZ / "benchmark" / "contato"
DESCRICOES = RAIZ / "conteudo" / "descricoes_cenas.json"


def gerar(origens: list[str]) -> list[dict]:
    lista: list[dict] = []
    for origem in origens:
        mp4 = C.arquivo_de(origem)
        if not mp4:
            print(f"{origem}: arquivo ausente; pulando "
                  f"(rode produzir/baixar_oficial.py)")
            continue
        fim = C.duracao(mp4)
        cortes = C.detectar(mp4)
        novas = C.montar_cenas(origem, cortes, fim)
        for c in novas:
            c["no_runner"] = origem == "extended"
        print(f"{origem}: {len(cortes)} cortes -> {len(novas)} cenas "
              f"({fim:.0f}s de vídeo)")
        lista += novas
    return lista


def aplicar_descricoes(lista: list[dict]) -> list[dict]:
    """Costura as descrições escritas à mão (conteudo/descricoes_cenas.json).

    Ficam num arquivo separado de propósito: `cenas.json` é REGERÁVEL (basta
    rodar este script de novo), e o trabalho humano não pode ser perdido numa
    regeração.
    """
    if not DESCRICOES.exists():
        return lista
    d = json.loads(DESCRICOES.read_text(encoding="utf-8"))
    for c in lista:
        info = d.get(c["id"])
        if not info:
            continue
        c["descricao"] = info.get("descricao", "")
        c["tags"] = info.get("tags", [])
    return lista


def _grade(pasta: Path, destino: Path, colunas: int = 6) -> None:
    """Monta a grade com PIL: o `-pattern_type glob` do ffmpeg não existe na
    build do Windows (falha com exit 4294967256)."""
    from PIL import Image
    fotos = sorted(pasta.glob("*.jpg"))
    if not fotos:
        return
    ims = [Image.open(f) for f in fotos]
    w, h = ims[0].size
    linhas = (len(ims) + colunas - 1) // colunas
    folha = Image.new("RGB", (w * colunas, h * linhas), (10, 8, 16))
    for k, im in enumerate(ims):
        folha.paste(im.resize((w, h)), ((k % colunas) * w, (k // colunas) * h))
    folha.save(destino, quality=85)


def folha_de_contato(lista: list[dict]) -> None:
    """Um quadro por cena, em grade, para a descrição ser escrita olhando."""
    CONTATO.mkdir(parents=True, exist_ok=True)
    por_origem: dict[str, list[dict]] = {}
    for c in lista:
        por_origem.setdefault(c["video_origem"], []).append(c)
    for origem, cs in por_origem.items():
        mp4 = C.arquivo_de(origem)
        if not mp4:
            continue
        pasta = CONTATO / origem
        pasta.mkdir(exist_ok=True)
        for c in cs:
            meio = (c["inicio"] + c["fim"]) / 2
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{meio:.2f}",
                 "-i", str(mp4), "-vf", "scale=320:-2,drawtext="
                 f"fontfile='{(RAIZ / 'marca/fontes/Montserrat-Bold.ttf').as_posix().replace(':', chr(92) + ':')}'"
                 f":text='{c['id']}':x=6:y=6:fontsize=18:fontcolor=yellow:"
                 "box=1:boxcolor=black@0.6",
                 "-frames:v", "1", str(pasta / f"{c['id']}.jpg")], check=True)
        _grade(pasta, CONTATO / f"{origem}.jpg")
        print(f"folha de contato: {CONTATO / f'{origem}.jpg'} ({len(cs)} cenas)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contato", action="store_true",
                    help="gera também a folha de contato para descrever")
    ap.add_argument("--origens", nargs="*",
                    default=["trailer1", "trailer2", "extended"])
    a = ap.parse_args()

    lista = aplicar_descricoes(gerar(a.origens))
    C.gravar(lista)
    aptas = len(C.aptas_para_cartao(lista))
    print(f"conteudo/cenas.json: {len(lista)} cenas, {aptas} aptas para cartão")
    if a.contato:
        folha_de_contato(lista)


if __name__ == "__main__":
    main()
