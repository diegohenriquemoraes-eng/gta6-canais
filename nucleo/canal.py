# -*- coding: utf-8 -*-
"""Identidade do canal — o que no motor bíblico era `nucleo/idiomas.py`.

Lá havia 7 canais em 3 idiomas e a tabela existia para não repetir texto. Aqui
existe UM canal, em pt-BR, e mesmo assim o módulo vale: é o único lugar onde
moram voz, tags, hashtags, CTA, rodapé de crédito e o caminho das fontes do
repo. `render.py` e `thumbnail.py` foram copiados de lá e importam
`idiomas.FONTES_DIR`; aqui importam `canal.FONTES_DIR`.

Premissa registrada (22/09/2026): a fonte do cartão é a **Montserrat-Bold que
já está no repo**, não a Inter-Bold citada em ARQUITETURA.md §D. Baixar uma
fonte nova para o runner é uma dependência de rede a mais no caminho crítico
do render, e a Montserrat é justamente a fonte do corpo de texto da casa.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTES_DIR = RAIZ / "marca" / "fontes"

# A data que organiza o projeto inteiro: contagem regressiva, troca A/B -> E/F,
# vigência da pré-venda. Fonte: Newswire da Rockstar.
LANCAMENTO = date(2026, 11, 19)

BCP47 = "pt-BR"

# Voz TTS ainda não usada na casa (Antonio e Francisca são do psicologia-fria e
# do Palavra Viva Diária). `produzir/conferir_voz.py` valida no runner; se a
# Thalita não existir na versão de edge-tts instalada, cai em VOZ_RESERVA.
VOZ = "pt-BR-ThalitaMultilingualNeural"
VOZ_RESERVA = "pt-BR-AntonioNeural"
RATE_SHORT = "-4%"
RATE_LONGO = "-12%"

# Rodapé queimado no pixel, em todo vídeo com material da Rockstar.
CREDITO_ROCKSTAR = "Material oficial © Rockstar Games"


def credito_cc(canal_origem: str) -> str:
    """Rodapé dos formatos E/F: a CC BY exige crédito nominal."""
    return f"Gameplay: {canal_origem} · CC BY"


CONFIG = {
    "bcp47": BCP47,
    "voz": VOZ,
    "voz_short": VOZ,
    "rate_short": RATE_SHORT,
    "rate_longo": RATE_LONGO,
    "max_short_s": 25.0,
    "rotulo_capitulos": "Capítulos:",
    "rotulo_completo": "Vídeo completo",
    "rotulo_repeticao": "de novo",
    "fonte_texto": "Fontes oficiais da Rockstar Games e imprensa especializada",
    "tags": [
        "gta 6", "gta vi", "grand theft auto vi", "gta 6 brasil",
        "gta 6 lançamento", "vice city", "jason e lucia", "leonida",
        "gta 6 trailer", "gta 6 notícias", "rockstar games", "gta6",
    ],
    "hashtags": "#GTA6 #GTAVI #ViceCity",
    "ctas": [
        "Segue para não perder a contagem regressiva.",
        "Salva esse vídeo e volta amanhã: tem fato novo todo dia.",
        "Comenta qual detalhe você não tinha visto.",
    ],
    "cta": "Segue para não perder a contagem regressiva.",
}

# Playlists por formato do longo (o que o motor chamava de idiomas.PLAYLISTS).
PLAYLISTS = {
    "tudo": "Tudo sobre GTA 6 — a contagem regressiva",
    "guia": "GTA 6: guias e segredos",
    "noticia": "GTA 6: notícias oficiais",
}

# Selo do formato na capa do longo (thumbnail.rotulo).
ROTULO_FORMATO = {
    "tudo": "TUDO SOBRE GTA 6",
    "guia": "GUIA GTA 6",
    "noticia": "NOTÍCIA OFICIAL",
}


def dias_para_lancamento(hoje: date | None = None) -> int:
    """N da contagem regressiva. Zero ou negativo = o jogo já saiu."""
    return (LANCAMENTO - (hoje or date.today())).days
