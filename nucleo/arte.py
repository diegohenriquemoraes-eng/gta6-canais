# -*- coding: utf-8 -*-
"""Gradiente da casa — o fundo que aparece quando não há imagem boa.

No motor bíblico isto morava em `nucleo/imagens.py`, junto do cliente do
Openverse. Aqui o Openverse não entra (a imagem vem da galeria oficial da
Rockstar e das cenas do trailer), então só o gradiente sobreviveu — e com a
paleta de Vice City: roxo-noite no topo, magenta no meio, azul profundo na
base.

Regra herdada e mantida: **melhor liso e limpo que errado**. Falhar para o
gradiente é sempre preferível a publicar uma imagem fora do assunto.
"""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

COR_TOPO = (11, 7, 22)      # #0B0716
COR_MEIO = (74, 16, 62)     # magenta apagado
COR_BASE = (12, 20, 58)     # azul profundo


def gerar_gradiente(destino: Path, w: int, h: int, seed: int) -> Path:
    rng = random.Random(seed)
    desloc = rng.uniform(-0.15, 0.15)
    img = Image.new("RGB", (w, h))
    dr = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h + desloc * (0.5 - abs(y / h - 0.5))
        t = min(1.0, max(0.0, t))
        if t < 0.5:
            a, b, tt = COR_TOPO, COR_MEIO, t * 2
        else:
            a, b, tt = COR_MEIO, COR_BASE, (t - 0.5) * 2
        cor = tuple(int(a[i] + (b[i] - a[i]) * tt) for i in range(3))
        dr.line([(0, y), (w, y)], fill=cor)
    img.save(destino, quality=92)
    return destino
