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
| 1 "Twitter" | avatar + nome + selo + @handle, y 80 | 1080×1000 em y 620 | 62 px, y 300 | crédito |
| 2 "meme" | — | 1080×1000 em y 600 | 70 px, y 250 | avatar + nome, y 1700 |
| 3 "dividido" | — | 1080×560 em y 250 + foto oficial 1080×560 em y 1120 | faixa em y 900 | avatar + nome, y 1760 |

⚠ **A zona de vídeo é 1080×608, não 1080×1350.** O desenho original supunha
uma fonte vertical; os trailers são 16:9, e `crop` para 1350 px de altura
exigiria ampliar o clipe 2,2× — o enquadramento morre e o rosto some. Medido no
primeiro render (22/09/2026): o clipe entrava com 608 px e o cartão saía com
uma tarja preta de 700 px, com a frase por cima da foto no layout 3. Agora a
zona é fixa (`force_original_aspect_ratio=increase` + `crop`), qualquer clipe
preenche exatamente, e cada elemento tem a sua faixa.

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


# ⚠ **Refeito em 23/09/2026, olhando o grid publicado.** Com a faixa de 608 px
# o cartão saía com o bloco inteiro no terço superior e **450 px de nada** entre
# o vídeo e o rodapé. Dois estragos, os dois visíveis na página:
#
# 1. no GRID do perfil o Instagram mostra um recorte central (≈4:5), e a frase,
#    que estava em y 340, caía fora ou pela metade — foi o que o Diego viu;
# 2. o vazio inferior fazia o post parecer arte quebrada, e não composição.
#
# A correção não é encher a tela com o clipe: recortar 16:9 para 9:16 come 68 %
# da largura e mata o enquadramento — foi a lição de 22/09 e ela continua
# valendo. O que muda é que a faixa **cresce de 608 para 1000 px** (corta 33 % das
# laterais) e o conjunto frase+vídeo passa a ser **centrado na tela**,
# com a sobra dividida em cima e embaixo. Assim o recorte do grid pega o fim da
# frase e o vídeo inteiro, que é o que a página do nicho mostra.
H_VIDEO = 1000
H_VIDEO_DIVIDIDO = 560    # o layout 3 tem DOIS blocos; 2×760 não cabe

# Geometria por layout. `y_nome` é onde entram avatar, nome, selo e @handle.
# `h_video` é a altura da faixa daquele layout.
GEOMETRIA = {
    1: {"y_video": 620, "y_frase": 300, "corpo": 62, "y_nome": 104,
        "y_avatar": 80, "rodape_y": H - 70, "h_video": H_VIDEO},
    2: {"y_video": 600, "y_frase": 250, "corpo": 70, "y_nome": 1700,
        "y_avatar": 1676, "rodape_y": H - 70, "h_video": H_VIDEO},
    3: {"y_video": 250, "y_frase": 900, "corpo": 58, "y_nome": 1760,
        "y_avatar": 1736, "rodape_y": H - 44, "y_foto": 1120,
        "h_video": H_VIDEO_DIVIDIDO},
}


def largura_texto(texto: str, corpo: int) -> int:
    """Largura em px do texto na fonte do cartão — o `drawtext` não devolve a
    largura para o `overlay`, e o selo precisa ficar depois do nome."""
    from PIL import ImageDraw, ImageFont
    f = ImageFont.truetype(str(canal.FONTES_DIR / "Montserrat-Bold.ttf"), corpo)
    from PIL import Image
    return int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(texto, font=f))


def filtergraph(layout: int, inicio: float, fim: float, n_linhas: int,
                corpo: int, tem_avatar: bool, tem_selo: bool,
                tem_foto: bool, identidade: dict, rodape: str,
                zoom: float = 1.0, dx: int = 0, estatico: bool = False) -> str:
    """Monta o -filter_complex. Separado do render para o teste poder validá-lo.

    `estatico=True`: a origem é uma FOTO da galeria oficial, não um clipe. A
    entrada já entra com `-loop 1 -framerate 30 -t dur` (o `-framerate` é
    obrigatório: sem ele o demuxer de imagem entrega 25 fps e o vídeo sai 17 %
    mais curto que a trilha — o defeito de 27/07/2026), então aqui não há
    `trim`, e o áudio vem da trilha procedural, não do clipe.
    """
    g = GEOMETRIA[layout]
    hv = g["h_video"]
    fonte = _fonte()
    dur = fim - inicio
    if estatico:
        # zoom lento de 1.0 a 1.06: foto totalmente parada num feed de vídeo
        # parece erro de carregamento
        entrada_v = (f"[0:v]fps={FPS},scale={W * 2}:-2,"
                     f"zoompan=z='min(1.06,1+0.06*on/{int(dur * FPS)})':"
                     f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:"
                     f"s={W}x{hv * 2}:fps={FPS}[src]")
    else:
        entrada_v = (f"[0:v]trim={inicio:.2f}:{fim:.2f},setpts=PTS-STARTPTS,"
                     f"fps={FPS}[src]")
    partes = [
        entrada_v,
        "[src]split=2[a][b]",
        # fundo: recorta 9:16, MINIATURIZA, borra, amplia e escurece
        (f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,"
         f"crop={W}:{H},scale=108:192,boxblur=8:2,"
         f"scale={W}:{H}:flags=bicubic,"
         f"eq=brightness=-0.08:contrast=1.08:saturation=1.30,setsar=1[bg]"),
        # primeiro plano: caixa FIXA de 1080x608, preenchida por cover-crop.
        # `dx` desloca o recorte na horizontal (o "deslocamento H" do
        # ViceScale); `zoom` aproxima antes do corte.
        (f"[b]scale={int(W * zoom)}:{int(hv * zoom)}:"
         f"force_original_aspect_ratio=increase,"
         f"crop={W}:{hv}:(iw-ow)/2+{dx}:(ih-oh)/2,setsar=1[fg]"),
        f"[bg][fg]overlay=(W-w)/2:{g['y_video']}[v0i]",
        # ⚠ MOLDURA (23/09/2026). Em cena noturna — metade do acervo — o fundo
        # borrado e a faixa de vídeo ficam os dois pretos, e o cartão parece
        # uma tela vazia com uma legenda. A linha fina na cor do canal é o que
        # diz onde o vídeo começa e acaba. Custa um filtro e resolve no olho.
        (f"[v0i]drawbox=x=0:y={g['y_video'] - 3}:w={W}:h=3:"
         f"color=0x35E0FF@0.75:t=fill,"
         f"drawbox=x=0:y={g['y_video'] + hv}:w={W}:h=3:"
         f"color=0xFF3EA5@0.75:t=fill[v0]"),
    ]
    ultimo = "v0"
    entrada = 1
    if tem_avatar:
        partes.append(f"[{ultimo}][{entrada}:v]overlay=60:{g['y_avatar']}"
                      f"[v{entrada}]")
        ultimo = f"v{entrada}"
        entrada += 1
    if tem_foto and layout == 3:
        # a foto oficial entra na mesma caixa 1080×608 do vídeo
        partes.append(f"[{entrada}:v]scale={W}:{hv}:"
                      f"force_original_aspect_ratio=increase,"
                      f"crop={W}:{hv}[foto]")
        partes.append(f"[{ultimo}][foto]overlay=0:{g['y_foto']}[v{entrada}]")
        ultimo = f"v{entrada}"
        entrada += 1

    if True:
        nome_txt = identidade.get("nome", "")
        nome = _escapar(nome_txt)
        handle = _escapar("@" + identidade.get("handle", ""))
        y_nome = g["y_nome"]
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
        # o selo fica logo à direita do nome; a largura do nome é medida com a
        # mesma fonte em `largura_texto` (o primeiro render colocou o selo em
        # x fixo e ele caiu em cima da palavra "City")
        x_selo = 176 + largura_texto(identidade.get("nome", ""), 40) + 14
        partes.append(f"[{ultimo}][{entrada}:v]overlay={x_selo}:{y_nome + 4}[vs]")
        ultimo = "vs"
        entrada += 1

    partes.append(
        f"[{ultimo}]drawtext=fontfile='{fonte}':text='{_escapar(rodape)}':"
        f"x=(w-text_w)/2:y={g['rodape_y']}:fontsize=26:fontcolor=0xD8CCC4:"
        f"shadowcolor=black@0.8:shadowx=2:shadowy=2,format=yuv420p[vout]")
    if estatico:
        # a trilha procedural entra como a ÚLTIMA entrada de áudio; o índice é
        # resolvido pelo chamador em `montar`
        partes.append(f"[{entrada}:a]atrim=0:{dur:.2f},asetpts=PTS-STARTPTS,"
                      f"volume=0.8,apad=whole_dur={dur:.2f}[aout]")
    else:
        partes.append(f"[0:a]atrim={inicio:.2f}:{fim:.2f},asetpts=PTS-STARTPTS,"
                      f"volume=0.7,apad=whole_dur={dur:.2f}[aout]")
    return ";".join(partes)


def montar(clipe: Path, inicio: float, fim: float, frase: str, layout: int,
           identidade: dict, outdir: Path, rodape: str = "",
           foto: Path | None = None, zoom: float = 1.0, dx: int = 0,
           saida: str = "cartao.mp4", estatico: bool = False,
           seed: int = 0) -> Path:
    """Renderiza o cartão. `identidade`: {avatar, selo, nome, handle}.

    `estatico=True` quando `clipe` é uma FOTO da galeria oficial: a imagem
    ganha zoom lento e a trilha procedural da casa (`nucleo/musica.py`) — nossa,
    sintetizada, sem risco de claim. Nunca biblioteca de música de terceiro.
    """
    if layout not in LAYOUTS:
        raise SystemExit(f"layout {layout} não existe (use 1, 2 ou 3)")
    outdir.mkdir(parents=True, exist_ok=True)
    linhas = quebrar(frase)
    for i, li in enumerate(linhas):
        (outdir / f"linha{i}.txt").write_text(li, encoding="utf-8")

    corpo = GEOMETRIA[layout]["corpo"]
    if len(linhas) > 3:                 # frase longa encolhe para caber
        corpo = int(corpo * 0.85)

    # Caminhos ABSOLUTOS: o ffmpeg roda com cwd na pasta de saída (é de lá que
    # ele lê os `linha*.txt` do drawtext), então caminho relativo do repo não
    # resolve. As fontes já vão absolutas por `_fonte()`.
    avatar = identidade.get("avatar")
    selo = identidade.get("selo")
    dur = fim - inicio
    if estatico:
        entradas = ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.2f}",
                    "-i", str(Path(clipe).resolve())]
    else:
        entradas = ["-i", str(Path(clipe).resolve())]
    if avatar and Path(avatar).exists():
        entradas += ["-i", str(Path(avatar).resolve())]
    if foto and layout == 3 and Path(foto).exists():
        entradas += ["-i", str(Path(foto).resolve())]
    if selo and Path(selo).exists():
        entradas += ["-i", str(Path(selo).resolve())]

    if estatico:
        from . import musica
        trilha = outdir / f"trilha-{seed}.wav"
        musica.gerar_trilha_fria(dur, seed, trilha)
        entradas += ["-i", str(trilha.resolve())]

    filtro = filtergraph(
        layout, inicio, fim, len(linhas), corpo,
        bool(avatar and Path(avatar).exists()),
        bool(selo and Path(selo).exists()),
        bool(foto and layout == 3 and Path(foto).exists()),
        identidade, rodape or canal.CREDITO_ROCKSTAR, zoom, dx, estatico)

    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *entradas,
         "-filter_complex", filtro, "-map", "[vout]", "-map", "[aout]",
         "-t", f"{fim - inicio:.2f}", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "23", "-r", str(FPS), "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", saida],
        cwd=outdir, check=True)
    return outdir / saida
