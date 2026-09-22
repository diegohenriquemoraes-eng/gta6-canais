# -*- coding: utf-8 -*-
"""O CARTÃO (formato G) — a peça que o ViceScale vende e que aqui é de graça.

Cena de 6-12 s do material oficial dentro de um cartão 1080×1920: fundo com o
próprio clipe borrado e escurecido, cabeçalho com avatar + nome + selo, frase
grande em fonte do repo, rodapé de crédito. Sem narração (o áudio é o do clipe,
baixinho) e sem fade — no feed o preto na abertura é um quarto da janela de
decisão jogada fora.

Três layouts, como no original (VICESCALE.md §2):

| layout | cabeçalho | vídeo | frase | rodapé |
|---|---|---|---|---|
| 1 "Twitter" | avatar + nome + selo + @handle, y 120 | 1080×1350 em y 560 | 64 px, y 300 | crédito |
| 2 "meme" | — | 1080×1350 em y 420 | 72 px, y 150 | avatar + nome, y 1800 |
| 3 "dividido" | — | 1080×960 em y 0 + foto oficial 1080×760 em y 1160 | faixa em y 960 | crédito |

Duas armadilhas já pagas no motor e respeitadas aqui:

- **`gblur`/`boxblur` vai ANTES do `scale`**: borrar em 108×192 e ampliar dá a
  mesma névoa por 1/100 do custo, e o runner tem 2 núcleos.
- **`drawtext` não quebra linha sozinho**: a frase é quebrada em ≤ 22
  caracteres por linha antes de ir para o `textfile`, senão ela sai cortada na
  borda do vídeo.

Custo medido no motor: clipe de 10 s com blur em miniatura e dois `drawtext`
renderiza em ~6-9 s no runner (`libx264 -preset veryfast -crf 23`).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from . import canal

W, H = 1080, 1920
FPS = 30
LARGURA_LINHA = 22        # caracteres por linha da frase (drawtext não quebra)
MAX_LINHAS = 4
LAYOUTS = (1, 2, 3)


def quebrar(frase: str, largura: int = LARGURA_LINHA,
            max_linhas: int = MAX_LINHAS) -> list[str]:
    """Quebra por palavra; palavra que não cabe sozinha fica na própria linha."""
    linhas: list[str] = []
    atual = ""
    for p in frase.split():
        cand = f"{atual} {p}".strip()
        if len(cand) > largura and atual:
            linhas.append(atual)
            atual = p
        else:
            atual = cand
    if atual:
        linhas.append(atual)
    if len(linhas) > max_linhas:
        # em vez de cortar a frase (mentira visual), afrouxa a largura
        return quebrar(frase, largura + 4, max_linhas + 1) if largura < 40 \
            else linhas[:max_linhas]
    return linhas


def _escapar(texto: str) -> str:
    """Escape do drawtext quando o texto vai INLINE (nome, handle, rodapé)."""
    return (texto.replace("\\", "\\\\").replace(":", "\\:")
            .replace("'", "’").replace("%", "\\%"))


def _fonte() -> str:
    """Caminho da fonte para dentro do filtro, com `:` escapado (Windows)."""
    return (canal.FONTES_DIR / "Montserrat-Bold.ttf").as_posix().replace(":", "\\:")


# Geometria por layout: (y do vídeo, altura do vídeo, y da frase, corpo)
GEOMETRIA = {
    1: {"y_video": 560, "h_video": 1350, "y_frase": 300, "corpo": 64,
        "cabecalho": True, "rodape_y": H - 70},
    2: {"y_video": 420, "h_video": 1350, "y_frase": 150, "corpo": 72,
        "cabecalho": False, "rodape_y": H - 70},
    3: {"y_video": 0, "h_video": 960, "y_frase": 1000, "corpo": 60,
        "cabecalho": False, "rodape_y": H - 40},
}


def filtergraph(layout: int, inicio: float, fim: float, n_linhas: int,
                corpo: int, tem_avatar: bool, tem_selo: bool,
                tem_foto: bool, identidade: dict, rodape: str,
                zoom: float = 1.0, dx: int = 0) -> str:
    """Monta o -filter_complex. Separado do render para o teste poder validá-lo."""
    g = GEOMETRIA[layout]
    fonte = _fonte()
    dur = fim - inicio
    partes = [
        f"[0:v]trim={inicio:.2f}:{fim:.2f},setpts=PTS-STARTPTS,fps={FPS}[src]",
        "[src]split=2[a][b]",
        # fundo: recorta 9:16, MINIATURIZA, borra, amplia e escurece
        (f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,"
         f"crop={W}:{H},scale=108:192,boxblur=8:2,"
         f"scale={W}:{H}:flags=bicubic,eq=brightness=-0.28:saturation=1.15,"
         f"setsar=1[bg]"),
        # primeiro plano: a cena em si, com zoom/deslocamento do pacote
        (f"[b]scale={int(W * zoom)}:-2,"
         f"crop={W}:min(ih\\,{g['h_video']}):{max(0, dx)}:(ih-oh)/2,"
         f"setsar=1[fg]"),
        f"[bg][fg]overlay=(W-w)/2:{g['y_video']}[v0]",
    ]
    ultimo = "v0"
    entrada = 1
    if tem_avatar:
        if layout == 1:
            pos = "60:96"
        elif layout == 2:
            pos = f"60:{H - 200}"
        else:
            pos = f"60:{H - 200}"
        partes.append(f"[{ultimo}][{entrada}:v]overlay={pos}[v{entrada}]")
        ultimo = f"v{entrada}"
        entrada += 1
    if tem_foto and layout == 3:
        partes.append(f"[{ultimo}][{entrada}:v]overlay=0:1160[v{entrada}]")
        ultimo = f"v{entrada}"
        entrada += 1

    if g["cabecalho"] or layout in (2, 3):
        nome = _escapar(identidade.get("nome", ""))
        handle = _escapar("@" + identidade.get("handle", ""))
        y_nome = 120 if layout == 1 else H - 190
        partes.append(
            f"[{ultimo}]drawtext=fontfile='{fonte}':text='{nome}':"
            f"x=176:y={y_nome}:fontsize=40:fontcolor=white:"
            f"shadowcolor=black@0.7:shadowx=2:shadowy=2[vn]")
        partes.append(
            f"[vn]drawtext=fontfile='{fonte}':text='{handle}':"
            f"x=176:y={y_nome + 50}:fontsize=32:fontcolor=0xC4BED9:"
            f"shadowcolor=black@0.7:shadowx=2:shadowy=2[vh]")
        ultimo = "vh"

    # a frase: uma chamada de drawtext por linha (o filtro não quebra sozinho)
    for i in range(n_linhas):
        y = g["y_frase"] + i * int(corpo * 1.25)
        partes.append(
            f"[{ultimo}]drawtext=fontfile='{fonte}':"
            f"textfile='linha{i}.txt':x=(w-text_w)/2:y={y}:"
            f"fontsize={corpo}:fontcolor=white:borderw=4:bordercolor=0x0B0716:"
            f"shadowcolor=black@0.6:shadowx=3:shadowy=3[vf{i}]")
        ultimo = f"vf{i}"

    if tem_selo:
        # o selo fica à direita do nome, em x fixo: o drawtext não devolve a
        # largura do texto para o overlay, e medir a fonte em Python só para
        # isso custaria mais do que vale.
        y_selo = 124 if layout == 1 else H - 186
        partes.append(f"[{ultimo}][{entrada}:v]overlay=430:{y_selo}[vs]")
        ultimo = "vs"
        entrada += 1

    partes.append(
        f"[{ultimo}]drawtext=fontfile='{fonte}':text='{_escapar(rodape)}':"
        f"x=(w-text_w)/2:y={g['rodape_y']}:fontsize=26:fontcolor=0xD8CCC4:"
        f"shadowcolor=black@0.8:shadowx=2:shadowy=2,format=yuv420p[vout]")
    partes.append(f"[0:a]atrim={inicio:.2f}:{fim:.2f},asetpts=PTS-STARTPTS,"
                  f"volume=0.7,apad=whole_dur={dur:.2f}[aout]")
    return ";".join(partes)


def montar(clipe: Path, inicio: float, fim: float, frase: str, layout: int,
           identidade: dict, outdir: Path, rodape: str = "",
           foto: Path | None = None, zoom: float = 1.0, dx: int = 0,
           saida: str = "cartao.mp4") -> Path:
    """Renderiza o cartão. `identidade`: {avatar, selo, nome, handle}."""
    if layout not in LAYOUTS:
        raise SystemExit(f"layout {layout} não existe (use 1, 2 ou 3)")
    outdir.mkdir(parents=True, exist_ok=True)
    linhas = quebrar(frase)
    for i, li in enumerate(linhas):
        (outdir / f"linha{i}.txt").write_text(li, encoding="utf-8")

    corpo = GEOMETRIA[layout]["corpo"]
    if len(linhas) > 3:                 # frase longa encolhe para caber
        corpo = int(corpo * 0.85)

    avatar = identidade.get("avatar")
    selo = identidade.get("selo")
    entradas = ["-i", str(clipe)]
    if avatar and Path(avatar).exists():
        entradas += ["-i", str(avatar)]
    if foto and layout == 3 and Path(foto).exists():
        entradas += ["-i", str(foto)]
    if selo and Path(selo).exists():
        entradas += ["-i", str(selo)]

    filtro = filtergraph(
        layout, inicio, fim, len(linhas), corpo,
        bool(avatar and Path(avatar).exists()),
        bool(selo and Path(selo).exists()),
        bool(foto and layout == 3 and Path(foto).exists()),
        identidade, rodape or canal.CREDITO_ROCKSTAR, zoom, dx)

    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *entradas,
         "-filter_complex", filtro, "-map", "[vout]", "-map", "[aout]",
         "-t", f"{fim - inicio:.2f}", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "23", "-r", str(FPS), "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", saida],
        cwd=outdir, check=True)
    return outdir / saida
