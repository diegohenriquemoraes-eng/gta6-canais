"""Render dos vídeos com ffmpeg: Short 1080x1920 e longo 1920x1080.

Short: 1 imagem de fundo com Ken Burns lento (ou gradiente da casa como
fallback) + narração + legenda ASS queimada. Sem música.

Longo: sequência de imagens com Ken Burns, narração versículo a versículo e
pad ambiente procedural mixado baixinho. Preset mais rápido (veryfast) porque
o runner do Actions tem 2 núcleos e o vídeo tem 10+ minutos.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from . import canal

FPS = 30


def _fontsdir(pasta: Path) -> str:
    """Caminho RELATIVO à pasta de trabalho: 'C:' dentro de filtro ffmpeg
    quebra o parser (o dois-pontos vira separador de opção)."""
    return Path(os.path.relpath(canal.FONTES_DIR, pasta)).as_posix()


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def _zoompan(dur: float, w: int, h: int, seed: int, loop: bool = False) -> str:
    frames = int(dur * FPS)
    if loop:
        # Movimento em ciclo FECHADO: o último frame volta ao enquadramento do
        # primeiro (cosseno de 0 a 2π). Zoom linear termina em 1.10 e o loop do
        # feed emenda com um solavanco visível — e é o loop que leva a retenção
        # acima de 100%, que é o que viraliza no Short.
        z = f"zoom='1+0.07*(1-cos(2*PI*on/{frames}))/2'"
    elif seed % 2 == 0:
        # alterna zoom-in/zoom-out pelo seed para não ficar tudo igual
        z = f"zoom='min(1.10,1+0.10*on/{frames})'"
    else:
        z = f"zoom='max(1.0,1.10-0.10*on/{frames})'"
    return (
        f"scale={int(w * 1.3)}:{int(h * 1.3)}:force_original_aspect_ratio=increase,"
        f"crop={int(w * 1.3)}:{int(h * 1.3)},"
        f"zoompan={z}:x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:"
        f"s={w}x{h}:fps={FPS},"
        "eq=brightness=-0.16:saturation=0.88,vignette=PI/4.5"
    )


def render_short(pasta: Path, voz: str, ass: str, imagem: Path | None,
                 dur: float, seed: int, saida: str = "short.mp4",
                 fade_in: float = 0.0, fade_out: float = 0.0,
                 loop: bool = True) -> Path:
    """Short/Reel 9:16 pensado para o LOOP do feed (padrão desde 27/07/2026).

    Os três defaults mudaram juntos, e é o mesmo motivo: no Short a moeda é
    retenção, e ela só passa de 100% quando o vídeo emenda no próprio começo.

    - `fade_in=0`: sem preto no 1º frame — metade da audiência decide em 1,7 s,
      e 0,4 s de preto é um quarto dessa janela gasto sem mostrar nada.
    - `fade_out=0`: corte seco. Escurecer para o preto no fim avisa "acabou" e
      é onde a pessoa desliza, em vez de dar a segunda passada.
    - `loop=True`: o movimento de fundo fecha o ciclo (ver `_zoompan`), então a
      emenda do fim com o começo não tem solavanco.

    Quem quiser o comportamento antigo passa os três explicitamente.
    """
    fontsdir = _fontsdir(pasta)
    if imagem is not None:
        # -framerate FPS é OBRIGATÓRIO aqui. Sem ele a imagem entra a 25 fps
        # (default do demuxer de imagem), o zoompan devolve 1 frame por frame de
        # entrada e o `fps=30` do filtro só CARIMBA a saída como 30 — resultado:
        # 25*dur frames tocados a 30 fps, ou seja um vídeo 17% mais curto que a
        # narração. Defeito que saiu em todos os Shorts publicados até 27/07/2026
        # (um Short de 23,4s de áudio tinha 19,5s de imagem: a narração terminava
        # sobre o último frame parado, justo onde a retenção é decidida).
        entrada = ["-loop", "1", "-framerate", str(FPS),
                   "-t", f"{dur:.2f}", "-i", imagem.name]
        fundo = _zoompan(dur, 1080, 1920, seed, loop=loop)
    else:
        entrada = ["-f", "lavfi", "-i",
                   (f"gradients=s=1080x1920:c0=0x0B1230:c1=0x1B0F3B:c2=0x2A1450:"
                    f"nb_colors=3:seed={seed}:speed=0.015:r={FPS}:d={dur:.2f}")]
        fundo = "null"
    entra = f"fade=t=in:st=0:d={fade_in:.2f}," if fade_in > 0 else ""
    sai = (f"fade=t=out:st={dur - fade_out:.2f}:d={fade_out:.2f},"
           if fade_out > 0 else "")
    filtro = (
        f"[0:v]{fundo},ass={ass}:fontsdir='{fontsdir}',"
        f"{entra}{sai}"
        f"format=yuv420p[v];[1:a]apad=whole_dur={dur:.2f}[a]"
    )
    _run(["ffmpeg", "-y", "-loglevel", "error", *entrada, "-i", voz,
          "-filter_complex", filtro, "-map", "[v]", "-map", "[a]",
          "-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "medium",
          "-crf", "20", "-c:a", "aac", "-b:a", "160k",
          "-movflags", "+faststart", saida], pasta)
    return pasta / saida


FPS_ESTATICO = 15      # tela parada não precisa de 30 fps: metade dos frames,
                       # metade do tempo de encode, nenhum prejuízo visível


def render_longo_estatico(pasta: Path, voz_wav: str, pad_wav: str, ass: str,
                          imagem: Path | None, dur: float, seed: int,
                          saida: str = "longo.mp4") -> Path:
    """Longo com fundo ESCURO e parado + legenda queimada — o formato do nicho.

    Conferido em 24/07/2026 nos dois líderes de "salmos para dormir" em
    português: "Salmo 91 91 vezes" (48M views, 3h48) é tela preta com o
    versículo no rodapé, e "Os 6 Salmos mais poderosos" (10,5M, 3h16) é fundo
    escuro quase imóvel com o versículo no rodapé. Ninguém anima imagem: quem
    põe para dormir não quer o quarto piscando.

    Para nós, a economia é o que destrava a duração. O caminho com imagens
    renderiza um clipe com zoompan por imagem (30 deles numa hora de vídeo);
    aqui é UMA passada, sem zoompan, a 15 fps e com -tune stillimage.
    """
    fontsdir = _fontsdir(pasta)
    if imagem is not None:
        entrada = ["-loop", "1", "-framerate", str(FPS_ESTATICO),
                   "-t", f"{dur:.2f}", "-i", imagem.name]
        # a imagem entra bem escura: é fundo de quarto no escuro, não paisagem
        fundo = (f"scale=1920:1080:force_original_aspect_ratio=increase,"
                 f"crop=1920:1080,eq=brightness=-0.34:saturation=0.7,"
                 f"vignette=PI/4,fps={FPS_ESTATICO}")
    else:
        entrada = ["-f", "lavfi", "-i",
                   f"color=c=0x05070F:s=1920x1080:r={FPS_ESTATICO}:d={dur:.2f}"]
        fundo = "null"
    filtro = (
        f"[0:v]{fundo},ass={ass}:fontsdir='{fontsdir}',"
        f"fade=t=in:st=0:d=1.0,fade=t=out:st={dur - 2.0:.2f}:d=2.0,"
        f"format=yuv420p[v];"
        f"[1:a]apad=whole_dur={dur:.2f},volume=1.0[nar];"
        f"[2:a]apad=whole_dur={dur:.2f},volume=0.55[pad];"
        f"[nar][pad]amix=inputs=2:duration=first:normalize=0,"
        f"afade=t=out:st={dur - 3.0:.2f}:d=3.0[a]"
    )
    _run(["ffmpeg", "-y", "-loglevel", "error", *entrada,
          "-i", voz_wav, "-i", pad_wav,
          "-filter_complex", filtro, "-map", "[v]", "-map", "[a]",
          "-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "veryfast",
          "-tune", "stillimage", "-crf", "24", "-g", str(FPS_ESTATICO * 10),
          "-c:a", "aac", "-b:a", "160k",
          "-movflags", "+faststart", saida], pasta)
    return pasta / saida


def render_longo(pasta: Path, voz_wav: str, pad_wav: str, ass: str,
                 imagens: list[Path], dur: float, seed: int,
                 saida: str = "longo.mp4") -> Path:
    """Render em 3 etapas, uma imagem de cada vez.

    A versão anterior abria as 30 imagens como entradas simultâneas do ffmpeg
    e montava um filtro com 30 zoompan em paralelo. Funcionou com o vídeo de
    8 min (17 imagens) e MORREU no de 16 min no runner do Actions (2 núcleos):
    "Nothing was written into output file" / exit 234 — o zoompan segura frames
    grandes na memória e 30 deles ao mesmo tempo estouram a máquina.

    Agora cada imagem vira um clipe curto sozinha (memória constante, não
    importa se são 10 ou 40), os clipes são concatenados por cópia (sem
    recodificar) e só a última passada junta legenda e áudio.
    """
    fontsdir = _fontsdir(pasta)
    n = len(imagens)
    if n == 0:
        raise SystemExit("render_longo precisa de pelo menos 1 imagem")
    seg = dur / n

    # 1) um clipe por imagem
    nomes = []
    for i, img in enumerate(imagens):
        nome = f"bg{i:03d}.mp4"
        _run(["ffmpeg", "-y", "-loglevel", "error",
              "-loop", "1", "-framerate", str(FPS),   # ver render_short
              "-t", f"{seg:.3f}", "-i", img.name,
              "-vf", _zoompan(seg, 1920, 1080, seed + i),
              "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
              "-pix_fmt", "yuv420p", nome], pasta)
        nomes.append(nome)

    # 2) concatenação sem recodificar
    (pasta / "bg.txt").write_text(
        "".join(f"file '{nome}'\n" for nome in nomes), encoding="utf-8")
    _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
          "-i", "bg.txt", "-c", "copy", "bg.mp4"], pasta)

    # 3) legenda queimada + mixagem narração/pad
    filtro = (
        f"[0:v]ass={ass}:fontsdir='{fontsdir}',"
        f"fade=t=in:st=0:d=1.0,fade=t=out:st={dur - 2.0:.2f}:d=2.0,"
        f"format=yuv420p[v];"
        f"[1:a]apad=whole_dur={dur:.2f},volume=1.0[nar];"
        f"[2:a]apad=whole_dur={dur:.2f},volume=0.55[pad];"
        f"[nar][pad]amix=inputs=2:duration=first:normalize=0,"
        f"afade=t=out:st={dur - 3.0:.2f}:d=3.0[a]"
    )
    _run(["ffmpeg", "-y", "-loglevel", "error",
          "-i", "bg.mp4", "-i", voz_wav, "-i", pad_wav,
          "-filter_complex", filtro, "-map", "[v]", "-map", "[a]",
          "-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "veryfast",
          "-crf", "21", "-c:a", "aac", "-b:a", "160k",
          "-movflags", "+faststart", saida], pasta)

    for nome in nomes:  # os clipes intermediários não servem mais
        (pasta / nome).unlink(missing_ok=True)
    (pasta / "bg.mp4").unlink(missing_ok=True)
    return pasta / saida


def repetir_video(pasta: Path, arquivo: str, vezes: int,
                  saida: str = "longo.mp4") -> Path:
    """Repete o vídeo pronto N vezes SEM recodificar (concat -c copy).

    É assim que se chega às horas de duração que o nicho exige gastando quase
    nada de máquina: o ciclo é renderizado uma vez (imagem, narração e legenda
    juntas) e só o container é repetido. Benchmark de 19/07/2026 sobre 252
    vídeos: mediana dos longos é 38 min (es), 165 min (en) e 68 min (pt) — o
    campeão do nicho é literalmente "SALMO 91 91 VEZES", 228 min. Repetir é o
    formato, não um truque: o público deixa rolando a noite inteira.
    """
    if vezes <= 1:
        return pasta / arquivo
    lista = pasta / "ciclos.txt"
    lista.write_text("".join(f"file '{arquivo}'\n" for _ in range(vezes)),
                     encoding="utf-8")
    _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
          "-i", "ciclos.txt", "-c", "copy", "-movflags", "+faststart",
          saida], pasta)
    return pasta / saida
