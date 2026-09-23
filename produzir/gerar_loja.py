# -*- coding: utf-8 -*-
"""Gera a vitrine (docs/loja.html) a partir de conteudo/ofertas.json.

**Por que existe uma vitrine nossa.** O painel de afiliados da Shopee Brasil
não tem vitrine — conferido em 23/09/2026: o menu vai de "Oferta de produto"
a "Link personalizado", e não há showcase nenhum. Como o pedido do Diego é
*um link só, em toda bio e em todo vídeo*, a vitrine é nossa, no GitHub Pages
que já está no ar para o OAuth. Custo zero, e trocar de produto passa a ser um
commit em vez de mexer em quatro bios (duas das quais só o celular edita).

**Por que sem foto do produto.** A foto do anúncio é do vendedor, não nossa.
Republicá-la é conteúdo de terceiro por um ganho estético pequeno, e os cards
da marca do canal ficam coerentes com o resto. A API do portal também não
entrega a imagem sem raspar a busca inteira.

**Como o rastreio sobrevive ao link único.** Cada origem (bio do YouTube, bio
do Instagram, bio do TikTok, descrição de Short, de longo, story) chama a
vitrine com `?de=<origem>`, e a página escolhe o link daquela origem — mesmo
destino, Sub_id diferente. Sem isso o relatório da Shopee diria "vendeu", mas
nunca "vendeu pela bio do TikTok".

Uso:
    python produzir/gerar_loja.py            # regrava docs/loja.html
    python produzir/gerar_loja.py --conferir # só valida, não escreve
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

OFERTAS = RAIZ / "conteudo" / "ofertas.json"
PAGINA = RAIZ / "docs" / "loja.html"
MARCA = "__PRODUTOS__"

# Quais entram na vitrine e com que etiqueta. Escolhidos em 23/09/2026 por
# retorno esperado (vendas × comissão) COM variedade de intenção: não adianta
# quatro quadros. Ficaram de fora os dois quadros redundantes (p4, p5) e a
# capa de 15 % (p6), que o p7 cobre melhor pagando o dobro.
VITRINE = [
    (1, "o mais comprado"),      # chaveiro R$ 13,99 · 16 % · 355 vendas
    (2, "o que decora"),         # quadro 3 peças R$ 27,96 · 17 % · 265 vendas
    (3, "para vestir"),          # camiseta R$ 33,75 · 5 % · 449 vendas
    (7, "para o console"),       # capa PS5 R$ 14,90 · 30 % · 67 vendas
]


def escolhidos() -> list[dict]:
    d = json.loads(OFERTAS.read_text(encoding="utf-8"))
    por_prioridade = {o["prioridade"]: o for o in d["ofertas"]}
    fora = [p for p, _ in VITRINE if p not in por_prioridade]
    if fora:
        raise SystemExit(f"prioridades ausentes em ofertas.json: {fora}")
    itens = []
    for prioridade, tag in VITRINE:
        o = por_prioridade[prioridade]
        if not o.get("links"):
            raise SystemExit(f"oferta p{prioridade} sem links")
        itens.append({
            "tag": tag,
            "nome": o["produto"],
            "preco": o["preco"],
            "links": o["links"],
        })
    return itens


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conferir", action="store_true")
    a = ap.parse_args()

    itens = escolhidos()
    for i in itens:
        print(f"  {i['tag']:<16} R$ {i['preco']:>6} · {i['nome'][:52]}")
    if a.conferir:
        return

    html = PAGINA.read_text(encoding="utf-8")
    dados = json.dumps(itens, ensure_ascii=False, indent=1)
    if MARCA in html:
        html = html.replace(MARCA, dados)
    else:
        # regravação: troca o bloco entre "const PRODUTOS = " e o ";" da linha
        import re
        html = re.sub(r"const PRODUTOS = .*?\n\];",
                      f"const PRODUTOS = {dados};", html, count=1,
                      flags=re.S)
    PAGINA.write_text(html, encoding="utf-8")
    print(f"\n{PAGINA.relative_to(RAIZ)} regravada com {len(itens)} produtos")


if __name__ == "__main__":
    main()
