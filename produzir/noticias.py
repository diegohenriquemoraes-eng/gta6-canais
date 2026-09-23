# -*- coding: utf-8 -*-
"""Formato C: notícia do dia, resumida em 40 palavras por um LLM barato.

Fontes, nesta ordem de confiança:

1. **Newswire da Rockstar** (`rockstargames.com/newswire`) — é a única fonte
   que produz rótulo `oficial`;
2. IGN e GameSpot (RSS público) — produzem `rumor`, salvo quando citam
   Rockstar/Sony/Take-Two no título.

Regras que decidem o que vai ao ar:

- `oficial` (= veio do Newswire) com `nota >= 7` vira o Short do dia, com
  prioridade sobre A/B. Matéria de imprensa que cita Rockstar/Sony/Take-Two
  fica como `imprensa`: é gravada, mas **não** vira Short sozinha;
- `rumor` **só entra** se a fonte for grande E o gancho começar com "Rumor:";
- teto de **8 chamadas de LLM por dia** (`TETO_CHAMADAS`), custo abaixo de
  US$ 0,05/dia. Sem chave de API, o script grava o item com um resumo
  extraído do próprio texto e `nota` conservadora — o pipeline nunca para por
  falta de LLM.

Grava `conteudo/noticias/AAAA-MM-DD.json`; o reabastecedor lê de lá.

Uso: python produzir/noticias.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

PASTA = RAIZ / "conteudo" / "noticias"
TETO_CHAMADAS = 8
MODELO = "claude-haiku-4-5-20251001"     # o mais barato da casa

NEWSWIRE = "https://www.rockstargames.com/newswire"
RSS = [
    ("IGN", "https://feeds.ign.com/ign/games-all"),
    ("GameSpot", "https://www.gamespot.com/feeds/game-news/"),
]
OFICIAIS = ("rockstar", "take-two", "take two", "sony", "playstation", "xbox")
CHAVES = ("gta 6", "gta vi", "grand theft auto vi", "grand theft auto 6")


def _e_do_assunto(texto: str) -> bool:
    t = texto.lower()
    return any(k in t for k in CHAVES)


def do_newswire() -> list[dict]:
    """Scrape do Newswire. Sem RSS confiável, é HTML — e pode voltar vazio."""
    try:
        import requests
        html = requests.get(NEWSWIRE, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; gta6-canais/1.0)"}).text
    except Exception as exc:
        print(f"! newswire indisponível ({exc})")
        return []
    itens = []
    for m in re.finditer(r'href="(/newswire/article/[^"]+)"[^>]*>(.{0,200}?)<',
                         html, re.S):
        url, titulo = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
        if titulo and _e_do_assunto(titulo):
            itens.append({"fonte": "Rockstar Newswire", "titulo": titulo,
                          "url": f"https://www.rockstargames.com{url}",
                          "texto": titulo})
    return itens[:5]


def do_rss() -> list[dict]:
    import requests
    itens = []
    for nome, url in RSS:
        try:
            xml = requests.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0"}).content
            raiz = ElementTree.fromstring(xml)
        except Exception as exc:
            print(f"! {nome} indisponível ({exc})")
            continue
        for item in raiz.iter("item"):
            titulo = (item.findtext("title") or "").strip()
            desc = re.sub(r"<[^>]+>", " ", item.findtext("description") or "")
            if not _e_do_assunto(titulo + " " + desc):
                continue
            itens.append({"fonte": nome, "titulo": titulo,
                          "url": (item.findtext("link") or "").strip(),
                          "texto": re.sub(r"\s+", " ", desc).strip()[:900]})
    return itens[:8]


def _rotulo(item: dict) -> str:
    """`oficial` é sobre a FONTE, não sobre quem o título cita.

    A primeira versão marcava como `oficial` qualquer matéria da IGN que
    tivesse "Rockstar" no título — e é exatamente assim que uma matéria de
    especulação com a palavra Rockstar viraria o Short do dia. Só o Newswire
    da Rockstar produz `oficial`; imprensa citando Rockstar/Sony/Take-Two vira
    `imprensa` (fica gravada, mas não vira Short sozinha); o resto é `rumor`.
    """
    if item["fonte"] == "Rockstar Newswire":
        return "oficial"
    t = (item["titulo"] + " " + item["texto"]).lower()
    return "imprensa" if any(o in t for o in OFICIAIS) else "rumor"


def _sem_llm(item: dict) -> dict:
    """Resumo de emergência: o próprio título e a primeira frase da descrição.

    Existe para o pipeline não depender de LLM nenhum, e a nota fica em 6 —
    abaixo do corte de 7 do reabastecedor. Publicar resumo não conferido sobre
    lançamento de jogo é o caminho mais curto para o canal virar fonte de
    boato, então imprensa e rumor ficam gravados mas NÃO viram Short.

    ⚠ **O Newswire é a exceção, desde 23/09/2026.** `noticia_do_dia` já exige
    `rotulo == "oficial"`, que só o Newswire da Rockstar produz — e ali o texto
    é o comunicado da própria Rockstar. Repetir a primeira frase de um
    comunicado oficial não é boato; é citação. Barrar isso por falta de LLM
    significava perder a notícia oficial no dia em que ela viesse, que é
    justamente o que rende às vésperas de 19/11. Medido nos dois dias
    coletados: o Newswire não publicou nada e as quatro notícias eram IGN e
    GameSpot — ou seja, a chave de LLM nunca foi o gargalo do formato C.
    """
    oficial = _rotulo(item) == "oficial"
    frase = (item["texto"].split(". ")[0] or item["titulo"])[:260]
    return {**item, "gancho": item["titulo"][:70], "resumo": frase,
            "nota": 7 if oficial else 6, "rotulo": _rotulo(item),
            "por": "sem-llm"}


def _com_llm(itens: list[dict]) -> list[dict]:
    chave = os.environ.get("ANTHROPIC_API_KEY", "")
    if not chave:
        print("sem ANTHROPIC_API_KEY — usando o resumo de emergência")
        return [_sem_llm(i) for i in itens]
    try:
        import anthropic
    except ImportError:
        print("pacote anthropic ausente — usando o resumo de emergência")
        return [_sem_llm(i) for i in itens]
    cliente = anthropic.Anthropic(api_key=chave)
    saida = []
    for item in itens[:TETO_CHAMADAS]:
        prompt = (
            "Você resume notícia de videogame para um canal brasileiro sobre "
            "GTA 6. Responda SÓ um JSON com as chaves gancho (≤ 10 palavras, "
            "sem ponto final), resumo (35 a 55 palavras em pt-BR, factual, sem "
            "opinião e sem CTA) e nota (1 a 10: quanto isso é FATO confirmado, "
            "não rumor).\n\n"
            f"Fonte: {item['fonte']}\nTítulo: {item['titulo']}\n"
            f"Texto: {item['texto']}")
        try:
            r = cliente.messages.create(model=MODELO, max_tokens=500,
                                        messages=[{"role": "user",
                                                   "content": prompt}])
            bruto = r.content[0].text
            dados = json.loads(re.search(r"\{.*\}", bruto, re.S).group(0))
            rotulo = _rotulo(item)
            gancho = dados["gancho"]
            if rotulo == "rumor" and not gancho.lower().startswith("rumor"):
                gancho = f"Rumor: {gancho}"
            saida.append({**item, "gancho": gancho[:70],
                          "resumo": dados["resumo"], "nota": int(dados["nota"]),
                          "rotulo": rotulo, "por": MODELO})
        except Exception as exc:
            print(f"! LLM falhou em '{item['titulo'][:50]}' ({exc})")
            saida.append(_sem_llm(item))
    return saida


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    brutos = do_newswire() + do_rss()
    vistos, unicos = set(), []
    for i in brutos:
        if i["url"] in vistos:
            continue
        vistos.add(i["url"])
        unicos.append(i)
    print(f"{len(unicos)} notícias candidatas")
    if not unicos:
        return

    itens = _com_llm(unicos)
    # rumor só passa com fonte grande E gancho rotulado
    itens = [i for i in itens
             if i["rotulo"] in ("oficial", "imprensa")
             or (i["fonte"] in ("IGN", "GameSpot")
                 and i["gancho"].lower().startswith("rumor"))]
    itens.sort(key=lambda i: (-i["nota"], i["rotulo"] != "oficial"))

    if a.dry_run:
        for i in itens:
            print(f"[{i['rotulo']} {i['nota']}] {i['gancho']} — {i['fonte']}")
        return
    PASTA.mkdir(parents=True, exist_ok=True)
    (PASTA / f"{date.today().isoformat()}.json").write_text(
        json.dumps(itens, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")
    print(f"gravado: {len(itens)} itens "
          f"({sum(1 for i in itens if i['rotulo'] == 'oficial')} oficiais)")


if __name__ == "__main__":
    main()
