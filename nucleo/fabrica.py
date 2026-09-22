# -*- coding: utf-8 -*-
"""Monta um item do pacote do dia: Short narrado (A/B/C/E) ou longo (D/F).

Podado do `nucleo/fabrica.py` do Palavra-Viva-3x. O que saiu: `biblia`,
`idiomas` e `imagens` (Openverse). O que ficou intacto, porque é o que a
medição pagou:

- gancho ESCRITO no frame zero, em corpo maior (estilo `Gancho`);
- sem preto na abertura, sem fade no fim, fundo em ciclo fechado;
- teto de duração do Short com o orçamento de palavras descontando o gancho;
- `-framerate 30` na entrada de imagem (defeito de 27/07/2026).

O que é novo aqui: a fonte do texto é o poço de FATOS (não versículo), a
contagem regressiva é montada na hora (`Faltam N dias...`), e todo vídeo leva
o rodapé de crédito da Rockstar queimado no pixel — obrigação da política de
uso de material da Rockstar, e a linha que separa "canal com fonte declarada"
de "página dark".
"""

from __future__ import annotations

import math
import zlib
from pathlib import Path

from . import arte, canal, cenas, legendas, musica, playlists, render, thumbnail, tts

CAUDA_SHORT = 0.35        # silêncio no fim quebra a emenda do loop
CAUDA_LONGO = 3.5
PAUSA_GANCHO = 0.6
PAUSA_FATO = 1.4          # respiro entre fatos do longo
MAX_SHORT_S = 25.0
PALAVRAS_POR_S_SHORT = 2.30

# Alvo de minutos do longo por formato. "tudo" é o formato D ("Tudo o que
# sabemos sobre GTA 6"): PLANO.md §3 pede 15-25 min. Não existe repetição de
# ciclo aqui — repetir o mesmo bloco de fatos seis vezes é o defeito que o
# longo estoico pagou em 03/09/2026, e em conteúdo informativo a repetição é a
# impressão digital de produção em massa (o nicho de dormir é outra história).
ALVO_MIN = {"tudo": 18, "guia": 16, "noticia": 0}
MIN_FATOS_LONGO = 10


def _seed(pacote: dict, extra: str) -> int:
    return zlib.crc32(f"{pacote['data']}-{extra}".encode()) % 999_983


def _ts_capitulo(seg: float) -> str:
    m, s = divmod(int(seg), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _cta(seed: int) -> str:
    variantes = canal.CONFIG["ctas"]
    return variantes[seed % len(variantes)]


def _encurtar(texto: str, limite: int) -> str:
    texto = " ".join(texto.split())
    if len(texto) <= limite:
        return texto
    corte = texto[:limite]
    for fim in (". ", "; ", ", "):
        pos = corte.rfind(fim)
        if pos > limite * 0.6:
            return corte[:pos + 1].rstrip()
    return corte.rsplit(" ", 1)[0].rstrip(",;") + "…"


def bloco_oferta(texto: str) -> str:
    """Bloco da oferta na descrição.

    Fica ACIMA dos capítulos de propósito: o YouTube corta a descrição depois
    de ~3 linhas, e o que converte precisa estar antes do "mostrar mais".
    Nunca sobre a imagem — a política da Rockstar veta usar o material como
    promoção de produto (PLANO.md §2).
    """
    return f"\n\n{texto.strip()}" if texto and texto.strip() else ""


def bloco_playlist(formato: str) -> str:
    lista_id = playlists.obter(formato)
    nome = canal.PLAYLISTS.get(formato, "")
    if not (lista_id and nome):
        return ""
    return f"\n\n🎬 {nome}:\nhttps://www.youtube.com/playlist?list={lista_id}"


def _rodape(fato: dict) -> str:
    """Crédito queimado no vídeo. CC BY exige nome; Rockstar exige a marca."""
    credito = fato.get("credito_cc")
    return canal.credito_cc(credito) if credito else canal.CREDITO_ROCKSTAR


def narracao_do_fato(fato: dict, dias: int) -> str:
    """O texto falado. Formato A recebe a contagem regressiva na frente.

    A contagem é montada AQUI e não no poço porque ela muda todo dia: gravá-la
    no fato obrigaria a reescrever 150 arquivos por dia. Quando o jogo já saiu
    (`dias <= 0`), o formato A é desligado pelo agendador e esta função nunca
    é chamada com contagem negativa — o `max` é cinto de segurança.
    """
    if fato.get("formato") == "A" and dias > 0:
        plural = "Faltam" if dias > 1 else "Falta"
        return f"{plural} {max(dias, 1)} dias para GTA 6. {fato['narracao']}"
    return fato["narracao"]


def _fundo_do_fato(fato: dict, outdir: Path, seed: int) -> Path | None:
    """Imagem de fundo: quadro da cena oficial, foto da galeria ou gradiente.

    A ordem é deliberada. `cenas.quadro` extrai um frame do trailer/Extended
    Look já baixado; se `marca/oficial/` não estiver no runner (é gitignorado,
    o workflow o reconstrói), cai na galeria; se nem isso, gradiente da casa.
    Nunca imagem de terceiro sem licença — a regra é falhar para o liso.
    """
    alvo = outdir / "fundo.jpg"
    try:
        if cenas.fundo_para_fato(fato, alvo, seed):
            return alvo
    except Exception as exc:                      # nunca derruba o render
        print(f"  cena indisponível ({exc}); caindo para o gradiente", flush=True)
    arte.gerar_gradiente(alvo, 1080, 1920, seed)
    return alvo


def montar_short(pacote: dict, idx: int, outdir: Path, url_longo: str = "",
                 oferta: str = "", dias: int | None = None) -> dict:
    """Formato A (contagem), B (viu no trailer), C (notícia) ou E (gameplay CC)."""
    cfg = canal.CONFIG
    fato = pacote["shorts"][idx]
    outdir.mkdir(parents=True, exist_ok=True)
    dias = canal.dias_para_lancamento() if dias is None else dias

    gancho = (fato.get("gancho") or "").strip()
    if not gancho:
        raise SystemExit(f"fato {fato.get('id')} sem gancho — o poço reprova isso")

    texto = narracao_do_fato(fato, dias)
    teto = cfg["max_short_s"]
    orcamento = int((teto - CAUDA_SHORT - PAUSA_GANCHO) * PALAVRAS_POR_S_SHORT)
    orcamento -= len(gancho.split())
    palavras = texto.split()
    if len(palavras) > orcamento:
        # corta em FRASE inteira, nunca no meio (lição do corpus estoico)
        corte, total = [], 0
        for frase in texto.replace("! ", ". ").replace("? ", ". ").split(". "):
            n = len(frase.split())
            if corte and total + n > orcamento:
                break
            corte.append(frase.rstrip("."))
            total += n
        texto = ". ".join(corte).rstrip(".") + "."

    voz = outdir / "voz.wav"
    segmentos, dur_voz = tts.narrar_versos(
        [(0, gancho), (1, texto)], cfg["voz_short"], cfg["rate_short"],
        PAUSA_GANCHO, voz, outdir / "tts")
    blocos = []
    for i, seg in enumerate(segmentos):
        legendas.alinhar_display(seg["texto"], seg["palavras"])
        if i == 0:
            g = legendas.agrupar(seg["palavras"], largura=200, max_palavras=40)
            blocos += [{**b, "estilo": "Gancho"} for b in g[:1]]
        else:
            blocos += legendas.agrupar(seg["palavras"])
    dur = dur_voz + CAUDA_SHORT

    cabecalho = (f"FALTAM {dias} DIAS" if fato.get("formato") == "A" and dias > 0
                 else fato.get("rotulo", "GTA 6"))
    legendas.ass_short(outdir / "legenda.ass", blocos, cabecalho,
                       _rodape(fato), dur, _cta(_seed(pacote, f"cta{idx}")))

    seed = _seed(pacote, f"short{idx}")
    img = _fundo_do_fato(fato, outdir, seed)
    video = render.render_short(outdir, voz.name, "legenda.ass", img, dur, seed)

    ponte = (f"\n\n▶ {cfg['rotulo_completo']}: {url_longo}\n" if url_longo
             else "\n")
    fonte_cc = ""
    if fato.get("credito_cc"):
        fonte_cc = (f"\n\nGameplay de {fato['credito_cc']} "
                    f"(licença Creative Commons BY): {fato.get('fonte_cc', '')}")
    descricao = (
        f"{_encurtar(texto, 320)}"
        f"\n\nFonte: {fato['fonte']}"
        + fonte_cc
        + ponte
        + bloco_oferta(oferta)
        + f"\n\n{_cta(seed)}\n\n{cfg['hashtags']} #Shorts"
        + f"\n\n{_rodape(fato)}"
    )
    return {
        "arquivo": video,
        "titulo": _titulo_short(fato, dias),
        "descricao": descricao,
        "tags": cfg["tags"] + ["shorts"],
        "thumb": None,
        "duracao_s": round(dur, 1),
        "referencia": fato["id"],
        "tipo_item": f"short-{idx + 1}",
    }


def _titulo_short(fato: dict, dias: int) -> str:
    """Título ≤ 100 chars. O gancho é a promessa; a contagem ancora a busca."""
    base = fato.get("titulo") or fato["gancho"]
    if fato.get("formato") == "A" and dias > 0:
        titulo = f"{base} | Faltam {dias} dias para GTA 6 #shorts"
    else:
        titulo = f"{base} | GTA 6 #shorts"
    return titulo[:100]


def _estimar_min(fatos: list[dict]) -> float:
    total = sum(len(f["narracao"].split()) / 2.3 + PAUSA_FATO for f in fatos)
    return (total + CAUDA_LONGO) / 60


def montar_longo(pacote: dict, outdir: Path, oferta: str = "",
                 dias: int | None = None) -> dict:
    """Formato D: os fatos do dia encadeados, 15-25 min, fundo escuro parado."""
    cfg = canal.CONFIG
    longo = pacote["longo"]
    formato = longo.get("formato", "tudo")
    outdir.mkdir(parents=True, exist_ok=True)
    dias = canal.dias_para_lancamento() if dias is None else dias

    fatos = longo["fatos"]
    if len(fatos) < MIN_FATOS_LONGO:
        raise SystemExit(f"longo com {len(fatos)} fatos; mínimo {MIN_FATOS_LONGO}")

    # 1) abertura falada própria — a camada autoral do longo. Sem ela o vídeo é
    #    leitura encadeada de material de terceiro, que a política de
    #    monetização lista como inelegível (answer/1311392).
    abertura = longo.get("abertura") or (
        f"Faltam {dias} dias para GTA 6. Neste vídeo eu reuni os fatos que a "
        f"Rockstar já confirmou sobre o jogo, um de cada vez, com a fonte de "
        f"cada um. Nada de rumor sem fonte e nada de vazamento."
        if dias > 0 else
        "GTA 6 já está nas ruas. Neste vídeo eu reuni o que a Rockstar "
        "confirmou sobre o jogo, um fato de cada vez, com a fonte de cada um.")

    partes = [(0, abertura)]
    for i, f in enumerate(fatos, start=1):
        partes.append((i, f"{f['gancho']}. {f['narracao']}"))

    voz = outdir / "voz.wav"
    segmentos, dur_voz = tts.narrar_versos(
        partes, cfg["voz"], cfg["rate_longo"], PAUSA_FATO, voz, outdir / "tts")
    dur = dur_voz + CAUDA_LONGO

    # 2) seções -> legenda + capítulos
    secoes = []
    rotulos = ["Abertura"] + [f["gancho"] for f in fatos]
    for seg, rot in zip(segmentos, rotulos):
        legendas.alinhar_display(seg["texto"], seg["palavras"])
        blocos = legendas.agrupar(seg["palavras"], largura=34, max_palavras=7)
        secoes.append({"cabecalho": rot[:70], "ini": seg["ini"],
                       "fim": seg["fim"] + PAUSA_FATO, "blocos": blocos,
                       "rotulo": rot})
    rodape = canal.CREDITO_ROCKSTAR
    legendas.ass_longo(outdir / "legenda.ass", secoes, rodape, dur,
                       _cta(_seed(pacote, "cta-longo")))
    srt = outdir / "legenda.srt"
    legendas.srt_longo(srt, secoes)

    # 3) fundo: UMA imagem escura e parada (formato do nicho e o que cabe no
    #    runner de 2 núcleos — ver render.render_longo_estatico)
    seed = _seed(pacote, "longo")
    capa_fonte = outdir / "capa-fonte.jpg"
    if not cenas.fundo_para_fato({"cena": longo.get("cena", ""),
                                  "tags": longo.get("tags_extra", [])},
                                 capa_fonte, seed, largura=1920):
        arte.gerar_gradiente(capa_fonte, 1920, 1080, seed)

    pad = outdir / "pad.wav"
    musica.gerar_pad(dur, _seed(pacote, "pad"), pad)
    video = render.render_longo_estatico(
        outdir, "voz.wav", "pad.wav", "legenda.ass", capa_fonte, dur, seed)

    # 4) capa
    thumb = outdir / "thumb.jpg"
    thumbnail.gerar(thumb, capa_fonte, longo["thumb_titulo"],
                    longo.get("thumb_sub", ""), "@" + pacote.get("handle", ""),
                    _seed(pacote, "thumb"),
                    rotulo_formato=thumbnail.rotulo(formato))

    caps = [f"{_ts_capitulo(s['ini'])} {s['rotulo'][:80]}" for s in secoes]
    caps[0] = f"0:00 {secoes[0]['rotulo'][:80]}"
    tags = list(cfg["tags"])
    for t in longo.get("tags_extra", []):
        if t not in tags and sum(len(x) + 1 for x in tags) + len(t) < 470:
            tags.append(t)
    fontes = sorted({f["fonte"] for f in fatos})[:12]
    descricao = (
        f"{longo['titulo']}"
        + (f"\n\n{longo['descricao_busca']}" if longo.get("descricao_busca") else "")
        + bloco_oferta(oferta)
        + bloco_playlist(formato)
        + f"\n\n{cfg['rotulo_capitulos']}\n" + "\n".join(caps)
        + "\n\nFontes deste vídeo:\n" + "\n".join(f"• {u}" for u in fontes)
        + f"\n\n{_cta(seed)}\n\n{cfg['hashtags']}"
        + f"\n\n{rodape}"
    )
    return {
        "arquivo": video,
        "titulo": longo["titulo"][:100],
        "descricao": descricao,
        "tags": tags,
        "thumb": thumb,
        "legenda_srt": srt,
        "duracao_s": round(dur, 1),
        "referencia": ", ".join(f["id"] for f in fatos[:6]),
        "tipo_item": "longo",
    }


def minutos_estimados(fatos: list[dict]) -> float:
    """Usado pelo reabastecedor para escolher quantos fatos o longo leva."""
    return _estimar_min(fatos)


def fatos_para_alvo(candidatos: list[dict], formato: str) -> list[dict]:
    """Quantos fatos cabem no alvo de minutos do formato (sem repetir nenhum)."""
    alvo = ALVO_MIN.get(formato, 18)
    escolhidos: list[dict] = []
    for f in candidatos:
        escolhidos.append(f)
        if alvo and _estimar_min(escolhidos) >= alvo:
            break
    if len(escolhidos) < MIN_FATOS_LONGO:
        escolhidos = candidatos[:max(MIN_FATOS_LONGO, len(escolhidos))]
    return escolhidos


__all__ = ["montar_short", "montar_longo", "fatos_para_alvo",
           "minutos_estimados", "narracao_do_fato", "ALVO_MIN"]
