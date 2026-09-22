"""Thumbnail dos vídeos longos (Shorts não usam thumbnail no feed).

Desenho de 16/09/2026 — a capa é a alavanca de HORAS da casa: os dois canais
bíblicos somavam 152 mil impressões em 28 dias a 1,6–2,1 % de CTR, e cada
ponto de CTR vale ~1.800 h/ano. O desenho anterior (foto de dia escurecida à
esquerda + título dourado) tinha três defeitos vistos na capa renderizada:
campo de trigo ao sol num vídeo "para dormir", texto pequeno para a miniatura
e nenhum ponto focal. Agora:

- **Fundo noturno sempre**: a foto da biblioteca recebe uma gradação de noite
  (dessatura, tinge de azul profundo, vinheta) — qualquer foto vira noite, e o
  texto dourado tem contraste garantido. A variedade continua vindo da foto.
- **Ponto focal procedural** por seed: lua com halo nos formatos de dormir;
  clarão dourado nos demais. Nenhum asset de terceiros.
- **Texto grande** (título até 210 px, Bebas Neue) com contorno e sombra;
  subtítulo em Montserrat; **selo do formato** ("PARA DORMIR", "BIBLIA
  HABLADA", "HISTORIA BÍBLICA") em cima, para o canal ser reconhecido em série
  sem as capas ficarem idênticas.

1280x720, JPG < 2 MB (limite do YouTube).
"""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from . import canal

# Paleta Vice City (marca/paleta.json): o título sai no laranja de pôr do sol,
# o selo do formato em ciano, o fundo em roxo-noite.
OURO = (255, 138, 61)      # #FF8A3D — laranja de pôr do sol (título)
CIANO = (53, 224, 255)     # #35E0FF — selo do formato
BRANCO = (247, 244, 238)
CINZA = (200, 190, 205)
NOITE = (18, 10, 40)       # tinta da gradação de noite
SOMBRA = (7, 4, 14)

def rotulo(formato: str) -> str:
    """Selo do formato do longo ("TUDO SOBRE GTA 6", "GUIA GTA 6"...).

    Existe para o canal ser reconhecido em série sem as capas ficarem
    idênticas — a armadilha de 30/07/2026, quando 25 capas saíram com o mesmo
    gradiente e só o texto mudando.
    """
    return canal.ROTULO_FORMATO.get(formato or "", "")


def _fonte(nome: str, tamanho: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(canal.FONTES_DIR / nome), tamanho)


def _cobrir(img: Image.Image, w: int, h: int) -> Image.Image:
    razao = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * razao), round(img.height * razao)))
    x = (img.width - w) // 2
    y = (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def _noite(base: Image.Image) -> Image.Image:
    """Gradação de noite: dessatura, escurece, tinge de azul, vinheta."""
    W, H = base.size
    base = ImageEnhance.Color(base).enhance(0.45)
    base = ImageEnhance.Brightness(base).enhance(0.5)
    base = Image.blend(base, Image.new("RGB", (W, H), NOITE), 0.42)
    # vinheta: cantos escuros, centro-direita preservado (é onde fica o foco)
    vin = Image.new("L", (W, H), 150)
    ImageDraw.Draw(vin).ellipse((int(W * 0.05), int(-H * 0.25),
                                 int(W * 1.05), int(H * 1.25)), fill=0)
    vin = vin.filter(ImageFilter.GaussianBlur(120))
    base = Image.composite(Image.new("RGB", (W, H), SOMBRA), base, vin)
    # véu à esquerda, onde vai o texto
    veu = Image.new("L", (W, H), 0)
    dv = ImageDraw.Draw(veu)
    for x in range(W):
        dv.line([(x, 0), (x, H)],
                fill=int(150 * max(0.0, 1.0 - x / (W * 0.62))))
    return Image.composite(Image.new("RGB", (W, H), SOMBRA), base, veu)


def _foco(base: Image.Image, seed: int, lua: bool) -> Image.Image:
    """Ponto focal por seed: lua com halo (dormir) ou clarão dourado."""
    W, H = base.size
    rng = random.Random(seed)
    cx = rng.randint(int(W * 0.68), int(W * 0.88))
    cy = rng.randint(int(H * 0.16), int(H * 0.36))
    camada = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(camada)
    if lua:
        r = rng.randint(64, 88)
        d.ellipse((cx - r * 3, cy - r * 3, cx + r * 3, cy + r * 3),
                  fill=(70, 80, 110))
        camada = camada.filter(ImageFilter.GaussianBlur(70))
        d = ImageDraw.Draw(camada)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(252, 244, 222))
        camada = camada.filter(ImageFilter.GaussianBlur(1.2))
        # estrelas
        d = ImageDraw.Draw(camada)
        for _ in range(rng.randint(45, 75)):
            x, y = rng.randint(0, W - 1), rng.randint(0, int(H * 0.62))
            s = rng.choice((1, 1, 1, 2, 2, 3))
            v = rng.randint(120, 235)
            d.ellipse((x, y, x + s, y + s), fill=(v, v, int(v * 0.92)))
    else:
        r = rng.randint(150, 220)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(150, 110, 40))
        camada = camada.filter(ImageFilter.GaussianBlur(110))
    return _screen(base, camada)


def _screen(a: Image.Image, b: Image.Image) -> Image.Image:
    from PIL import ImageChops
    return ImageChops.screen(a, b)


def gerar(destino: Path, imagem: Path | None, titulo: str, subtitulo: str,
          marca: str, seed: int = 0, rotulo_formato: str = "",
          lua: bool | None = None) -> Path:
    W, H = 1280, 720
    if imagem is not None and imagem.exists():
        base = _cobrir(Image.open(imagem).convert("RGB"), W, H)
    else:
        from . import arte as _imgs
        tmp = destino.with_suffix(".fundo.jpg")
        _imgs.gerar_gradiente(tmp, W, H, seed)
        base = Image.open(tmp).convert("RGB")
        tmp.unlink(missing_ok=True)

    base = _noite(base)
    if lua is None:
        # No canal bíblico a lua marcava o formato "para dormir". Aqui o ponto
        # focal é sempre o clarão de neon do horizonte de Vice City.
        lua = False
    base = _foco(base, seed, lua)

    dr = ImageDraw.Draw(base)
    X = 70

    # título: até 2 linhas, corpo grande, autoajuste
    linhas = _quebrar(titulo.upper(), 13)[:2]
    maior = max(len(li) for li in linhas)
    corpo = 210 if maior <= 8 else 176 if maior <= 11 else 146
    f_tit = _fonte("BebasNeue-Regular.ttf", corpo)
    alt_tit = len(linhas) * (corpo - 6)
    f_sub = _fonte("Montserrat-Bold.ttf", 52)
    f_rot = _fonte("Montserrat-Bold.ttf", 32)
    alt_bloco = alt_tit + 84 + (66 if rotulo_formato else 0)
    y = (H - alt_bloco) // 2 + 10

    if rotulo_formato:
        tw = dr.textlength(rotulo_formato, font=f_rot)
        caixa = (X, y, X + tw + 40, y + 50)
        dr.rounded_rectangle(caixa, radius=12, fill=(20, 12, 34),
                             outline=CIANO, width=3)
        dr.text((X + 20, y + 7), rotulo_formato, font=f_rot, fill=CIANO)
        y += 66

    for li in linhas:
        dr.text((X + 6, y + 8), li, font=f_tit, fill=SOMBRA)   # sombra
        dr.text((X, y), li, font=f_tit, fill=OURO,
                stroke_width=5, stroke_fill=SOMBRA)
        y += corpo - 6

    sub = subtitulo.strip()
    if sub:
        f = f_sub
        while dr.textlength(sub, font=f) > W - X - 60 and f.size > 34:
            f = _fonte("Montserrat-Bold.ttf", f.size - 4)
        dr.text((X + 2, y + 16), sub, font=f, fill=BRANCO,
                stroke_width=3, stroke_fill=SOMBRA)

    f_marca = _fonte("Montserrat-Bold.ttf", 28)
    dr.text((X, H - 66), marca, font=f_marca, fill=CINZA,
            stroke_width=2, stroke_fill=SOMBRA)

    base.save(destino, quality=88)
    if destino.stat().st_size > 2_000_000:
        base.save(destino, quality=76)
    return destino


def _quebrar(texto: str, largura: int) -> list[str]:
    if "\n" in texto:
        return [li.strip() for li in texto.split("\n") if li.strip()]
    palavras = texto.split()
    linhas, atual = [], ""
    for p in palavras:
        cand = f"{atual} {p}".strip()
        if len(cand) > largura and atual:
            linhas.append(atual)
            atual = p
        else:
            atual = cand
    if atual:
        linhas.append(atual)
    return linhas
