"""Narração com edge-tts (gratuito) + timestamps por palavra.

Dois modos:
- narrar(): uma chamada só, para Shorts (igual ao pipeline do Palabra Viva).
- narrar_versos(): uma chamada POR VERSÍCULO com pausa contemplativa entre
  eles, para os vídeos longos — dá o ritmo do gênero (leitura devocional) e
  timestamps exatos por versículo para legenda e capítulos.

edge-tts 7.x exige boundary="WordBoundary" no Communicate, senão os
timestamps por palavra não vêm.
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import edge_tts


async def _stream(texto: str, voz: str, rate: str, mp3: Path) -> list[dict]:
    com = edge_tts.Communicate(texto, voz, rate=rate, boundary="WordBoundary")
    palavras = []
    with mp3.open("wb") as fh:
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                fh.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                palavras.append({
                    "t": chunk["offset"] / 1e7,
                    "d": chunk["duration"] / 1e7,
                    "w": chunk["text"],
                })
    if not palavras:
        raise SystemExit("TTS não devolveu word boundaries")
    return palavras


def narrar(texto: str, voz: str, rate: str, mp3: Path) -> list[dict]:
    return asyncio.run(_stream(texto, voz, rate, mp3))


def duracao_audio(arquivo: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(arquivo)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def _silencio_mp3(path: Path, dur: float) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono:d={dur:.2f}",
         "-c:a", "libmp3lame", "-b:a", "48k", str(path)],
        check=True,
    )


def narrar_versos(versos: list[tuple[int, str]], voz: str, rate: str,
                  pausa: float, out_wav: Path, workdir: Path
                  ) -> tuple[list[dict], float]:
    """Narra versículo a versículo com pausa entre eles.

    Devolve (segmentos, duração_total). Cada segmento:
    {"verso": n, "ini": s, "fim": s, "palavras": [{t global, d, w}]}
    """
    workdir.mkdir(parents=True, exist_ok=True)
    silencio = workdir / "silencio.mp3"
    _silencio_mp3(silencio, pausa)

    segmentos = []
    lista = workdir / "concat.txt"
    linhas = []
    offset = 0.0
    for i, (num, texto) in enumerate(versos):
        seg = workdir / f"v{i:03d}.mp3"
        palavras = narrar(texto, voz, rate, seg)
        dur = duracao_audio(seg)
        for p in palavras:
            p["t"] += offset
        segmentos.append({
            "verso": num,
            "ini": offset,
            "fim": offset + dur,
            "palavras": palavras,
            "texto": texto,
        })
        linhas.append(f"file '{seg.name}'\n")
        offset += dur
        if i < len(versos) - 1:
            linhas.append(f"file '{silencio.name}'\n")
            offset += pausa
    lista.write_text("".join(linhas), encoding="utf-8")

    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", lista.name, "-ar", "44100", "-ac", "1", out_wav.resolve().as_posix()],
        cwd=workdir, check=True,
    )
    return segmentos, duracao_audio(out_wav)
