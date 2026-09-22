# -*- coding: utf-8 -*-
"""Gera a marca do canal: avatar, selo do cartão, banner e capa padrão.

Tudo procedural (PIL), sem asset de terceiro. Duas regras que não se negociam:

- **nada da Rockstar no avatar ou no banner**. Logo de marca de terceiro na
  foto de perfil é motivo de derrubada do perfil inteiro, e é o erro mais
  comum das páginas dark do nicho. O que identifica o canal é a palmeira em
  silhueta sobre o gradiente noturno de Vice City.
- **o selo do cartão NÃO é o selo azul do Instagram**. Aquele desenho é da
  Meta; imitá-lo num cartão é fingir verificação. O nosso é um círculo ciano
  com um check branco — parece um selo, e não é o deles.

Paleta (marca/paleta.json): fundo #0B0716, rosa #FF3EA5, ciano #35E0FF,
laranja de pôr do sol #FF8A3D (só em capa), texto #FFFFFF.

Uso: python marca/gerar_marca.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).resolve().parent
FONTES = AQUI / "fontes"

FUNDO = (11, 7, 22)
ROSA = (255, 62, 165)
CIANO = (53, 224, 255)
LARANJA = (255, 138, 61)
BRANCO = (255, 255, 255)

PALETA = {
    "fundo": "#0B0716", "rosa": "#FF3EA5", "ciano": "#35E0FF",
    "laranja": "#FF8A3D", "texto": "#FFFFFF",
    "_nota": "Laranja só em capa de vídeo longo. Nunca usar logo da Rockstar "
             "no avatar, no banner ou no selo.",
}


def _fonte(nome: str, tamanho: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTES / nome), tamanho)


def _ceu(w: int, h: int) -> Image.Image:
    """Gradiente noturno de Vice City: roxo em cima, magenta e laranja na linha
    do horizonte."""
    img = Image.new("RGB", (w, h))
    dr = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        if t < 0.62:
            u = t / 0.62
            cor = tuple(int(FUNDO[i] + (ROSA[i] * 0.55 - FUNDO[i]) * u ** 2)
                        for i in range(3))
        else:
            u = (t - 0.62) / 0.38
            base = tuple(int(ROSA[i] * 0.55) for i in range(3))
            cor = tuple(int(base[i] + (LARANJA[i] * 0.9 - base[i]) * u)
                        for i in range(3))
        dr.line([(0, y), (w, y)], fill=cor)
    return img


def _sol(img: Image.Image, cx: int, cy: int, r: int) -> None:
    """Sol/lua de neon com as faixas horizontais do synthwave."""
    camada = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(camada)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=CIANO)
    for k in range(1, 7):                      # faixas vazadas
        y = cy - r + int(r * 2 * (0.45 + k * 0.09))
        d.rectangle((cx - r, y, cx + r, y + max(2, r // 22)), fill=(0, 0, 0))
    halo = camada.filter(ImageFilter.GaussianBlur(r // 5))
    from PIL import ImageChops
    img.paste(ImageChops.screen(img, halo))
    img.paste(ImageChops.screen(img, camada))


def _palmeira(dr: ImageDraw.ImageDraw, x: int, base_y: int, altura: int,
              cor=(0, 0, 0)) -> None:
    """Silhueta de palmeira: tronco curvo + seis folhas."""
    for i in range(altura):
        t = i / altura
        larg = max(2, int(altura * 0.035 * (1 - t * 0.55)))
        px = x + int(math.sin(t * 1.15) * altura * 0.10)
        dr.rectangle((px - larg, base_y - i, px + larg, base_y - i + 2), fill=cor)
    topo_x = x + int(math.sin(1.15) * altura * 0.10)
    topo_y = base_y - altura
    for ang in (-2.65, -2.1, -1.57, -1.05, -0.5, 0.05):
        pontos = []
        for k in range(14):
            u = k / 13
            comp = altura * 0.46 * u
            queda = altura * 0.30 * u * u
            pontos.append((topo_x + math.cos(ang) * comp,
                           topo_y + math.sin(ang) * comp + queda))
        dr.line(pontos, fill=cor, width=max(3, altura // 34), joint="curve")


def avatar(destino: Path, tamanho: int = 800) -> Path:
    img = _ceu(tamanho, tamanho)
    _sol(img, tamanho // 2, int(tamanho * 0.46), int(tamanho * 0.27))
    dr = ImageDraw.Draw(img)
    _palmeira(dr, int(tamanho * 0.30), int(tamanho * 0.94), int(tamanho * 0.52))
    _palmeira(dr, int(tamanho * 0.74), int(tamanho * 0.97), int(tamanho * 0.40))
    dr.rectangle((0, int(tamanho * 0.94), tamanho, tamanho), fill=(0, 0, 0))
    f = _fonte("BebasNeue-Regular.ttf", int(tamanho * 0.155))
    texto = "VICE"
    w = dr.textlength(texto, font=f)
    dr.text(((tamanho - w) / 2, int(tamanho * 0.70)), texto, font=f,
            fill=BRANCO, stroke_width=max(2, tamanho // 160),
            stroke_fill=(10, 5, 18))
    # máscara redonda: o Instagram e o YouTube recortam em círculo de qualquer
    # jeito; recortar aqui garante que nada importante fique fora
    mascara = Image.new("L", (tamanho, tamanho), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, tamanho, tamanho), fill=255)
    fora = Image.new("RGB", (tamanho, tamanho), FUNDO)
    fora.paste(img, (0, 0), mascara)
    fora.save(destino, quality=95)
    return destino


def selo(destino: Path, tamanho: int = 48) -> Path:
    """Círculo ciano com check branco — NÃO é o selo azul da Meta."""
    esc = 8
    img = Image.new("RGBA", (tamanho * esc, tamanho * esc), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = tamanho * esc
    d.ellipse((0, 0, r - 1, r - 1), fill=CIANO + (255,))
    d.line([(r * 0.28, r * 0.52), (r * 0.44, r * 0.68), (r * 0.74, r * 0.34)],
           fill=(255, 255, 255, 255), width=int(r * 0.10), joint="curve")
    img.resize((tamanho, tamanho), Image.LANCZOS).save(destino)
    return destino


def banner(destino: Path) -> Path:
    W, H = 2560, 1440                     # área segura central: 1546×423
    img = _ceu(W, H)
    _sol(img, W // 2, int(H * 0.46), 300)
    dr = ImageDraw.Draw(img)
    for x, alt in ((360, 620), (2180, 520), (620, 380), (1980, 430)):
        _palmeira(dr, x, int(H * 0.92), alt)
    dr.rectangle((0, int(H * 0.92), W, H), fill=(6, 4, 12))

    f = _fonte("BebasNeue-Regular.ttf", 190)
    titulo = "RUMO A VICE CITY"
    w = dr.textlength(titulo, font=f)
    dr.text(((W - w) / 2, H * 0.40), titulo, font=f, fill=BRANCO,
            stroke_width=8, stroke_fill=(10, 5, 18))
    f2 = _fonte("Montserrat-Bold.ttf", 62)
    sub = "TUDO SOBRE GTA 6, TODO DIA  ·  19.11.2026"
    w2 = dr.textlength(sub, font=f2)
    dr.text(((W - w2) / 2, H * 0.40 + 205), sub, font=f2, fill=CIANO,
            stroke_width=4, stroke_fill=(10, 5, 18))
    img.save(destino, quality=92)
    return destino


def main() -> None:
    (AQUI / "paleta.json").write_text(
        json.dumps(PALETA, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")
    a = avatar(AQUI / "avatar.png")
    Image.open(a).resize((96, 96), Image.LANCZOS).save(AQUI / "avatar-96.png")
    Image.open(a).resize((256, 256), Image.LANCZOS).save(AQUI / "avatar-256.png")
    selo(AQUI / "selo.png")
    banner(AQUI / "banner.png")
    print("marca gerada:", ", ".join(
        p.name for p in sorted(AQUI.glob("*.png"))))


if __name__ == "__main__":
    main()
