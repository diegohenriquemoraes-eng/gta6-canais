# -*- coding: utf-8 -*-
"""A ESCALA do formato G: cena × frase → fila de cartões.

É a réplica da aba "Scale" do ViceScale (10 vídeos × 5 frases = 50 posts), com
a regra que ele **não** tem e que decide se o perfil vive ou morre:

> **Uma cena recebe UMA frase por 7 dias.**

Repetir o mesmo vídeo cinco vezes com frase diferente é a definição literal de
conteúdo repetitivo na atualização de originalidade do Instagram de
30/04/2026 — quem faz isso perde Explorar, aba de Reels e sugeridos. A
variação aqui é ENTRE cenas, não do mesmo clipe.

⚠ A trava de 7 dias é da **CENA** e do **PAR cena+frase**, não da frase
sozinha. São 40 frases-base e 35 cartões por semana: exigir descanso de 7 dias
também da frase é aritmeticamente impossível, e seria a regra errada de
qualquer jeito — o que a política do Instagram chama de repetitivo é o
ARQUIVO repetido, não a legenda parecida. A frase segue o critério do motor da
casa: **rebaixar, nunca excluir** — a menos usada há mais tempo vem primeiro, e
nenhuma frase sai duas vezes no mesmo dia.

As outras quatro regras (ARQUITETURA.md §C.7), todas com caso de teste:

1. nunca duas cenas do mesmo trecho do trailer (mesmo minuto) em posts
   consecutivos — é o que faz o feed parecer o mesmo post duas vezes;
2. frase de `identidade` no máximo 1 a cada 4 cartões (ela não informa nada;
   em excesso vira spam de autopromoção);
3. `contagem` no máximo 2 por dia (o `{N}` muda todo dia, mas cinco contagens
   no mesmo dia é uma página só de número);
4. `fato` e `pergunta` preferem a cena cujas TAGS casam com as da frase —
   frase de polícia sobre cena de praia é o erro clássico da página dark.

O uso de cada frase e de cada cena fica em `conteudo/frases_uso.json`, que é
versionado como o `state.json`: o runner é descartado e sem isso a regra dos
7 dias não sobreviveria a uma execução.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from nucleo import canal, cenas as C  # noqa: E402

FRASES = RAIZ / "conteudo" / "frases.json"
USO = RAIZ / "conteudo" / "frases_uso.json"

DIAS_REPETICAO = 7
MAX_IDENTIDADE_EM = 4      # 1 identidade a cada 4 cartões
MAX_CONTAGEM_DIA = 2
LAYOUTS = (1, 2, 3)

# Vocabulário que liga frase a cena. A chave é a palavra que aparece na frase;
# o valor, as tags de cena que combinam.
AFINIDADE = {
    "polícia": ["policia", "perseguicao"],
    "procurado": ["policia", "perseguicao"],
    "testemunha": ["policia"],
    "carro": ["carro", "direcao"],
    "controle": ["carro"],
    "jason": ["jason", "dupla"],
    "lucia": ["lucia", "dupla"],
    "vice city": ["cidade", "vice-city", "mapa"],
    "cidade": ["cidade", "vice-city"],
    "mapa": ["mapa", "cidade"],
    "los santos": ["cidade", "mapa"],
    "história": ["personagem", "dupla"],
    "romance": ["dupla", "jason", "lucia"],
    "animações": ["personagem"],
    "noite": ["noite"],
    "praia": ["praia"],
    "leonida": ["leonida", "pantano", "natureza"],
}


def carregar_frases() -> dict[str, list[str]]:
    d = json.loads(FRASES.read_text(encoding="utf-8"))
    return {k: v for k, v in d.items() if not k.startswith("_")}


def carregar_uso() -> dict:
    if not USO.exists():
        return {"cenas": {}, "frases": {}, "pares": []}
    return json.loads(USO.read_text(encoding="utf-8"))


def gravar_uso(uso: dict) -> None:
    USO.write_text(json.dumps(uso, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")


def _minuto(cena: dict) -> str:
    """Chave de 'mesmo trecho': origem + minuto de início."""
    return f"{cena['video_origem']}-{int(cena['inicio']) // 60}"


def _recente(quando: str | None, hoje: date, dias: int) -> bool:
    if not quando:
        return False
    return (hoje - date.fromisoformat(quando)).days < dias


def _idade(uso: dict, frase: str, quando: date) -> int:
    """Há quantos dias a frase não é usada. Frase nunca usada vale o máximo."""
    visto = uso["frases"].get(frase)
    if not visto:
        return 10_000
    return (quando - date.fromisoformat(visto)).days


def _afinidade(frase: str, cena: dict) -> int:
    """Quantos gatilhos da frase batem com as tags da cena."""
    f = frase.lower()
    tags = set(cena.get("tags", []))
    return sum(1 for gatilho, alvos in AFINIDADE.items()
               if gatilho in f and tags & set(alvos))


def escolher_categoria(pos: int, contagens_hoje: int, dias: int) -> str:
    """Qual categoria de frase o cartão da posição `pos` usa.

    `identidade` só na posição 0 de cada bloco de 4; `contagem` até o teto do
    dia e só enquanto o jogo não saiu; o resto alterna fato e pergunta.
    """
    if pos % MAX_IDENTIDADE_EM == 0:
        return "identidade"
    if dias > 0 and contagens_hoje < MAX_CONTAGEM_DIA and pos % 2 == 1:
        return "contagem"
    return "fato" if pos % 2 == 0 else "pergunta"


def montar_fila(quantos: int, quando: date, uso: dict | None = None,
                aptas: list[dict] | None = None,
                frases: dict[str, list[str]] | None = None) -> list[dict]:
    """Devolve `quantos` cartões para a data `quando`, respeitando as regras."""
    uso = carregar_uso() if uso is None else uso
    aptas = C.aptas_para_cartao() if aptas is None else aptas
    aptas = [c for c in aptas if not c.get("no_runner")]
    frases = carregar_frases() if frases is None else frases
    if not aptas:
        return []

    dias = canal.dias_para_lancamento(quando)
    fila: list[dict] = []
    contagens = 0
    minuto_anterior = ""
    for pos in range(quantos):
        cat = escolher_categoria(pos, contagens, dias)
        opcoes = frases.get(cat) or frases["fato"]

        # cenas elegíveis: não usadas nos últimos 7 dias e não do mesmo trecho
        # do cartão anterior
        candidatas = [c for c in aptas
                      if not _recente(uso["cenas"].get(c["id"]), quando,
                                      DIAS_REPETICAO)
                      and _minuto(c) != minuto_anterior
                      and c["id"] not in {f["cena"]["id"] for f in fila}]
        if not candidatas:
            # rebaixar, nunca excluir: sem candidata limpa, usa a cena usada há
            # mais tempo. O motor não pode parar por falta de cena.
            candidatas = sorted(
                (c for c in aptas if c["id"] not in
                 {f["cena"]["id"] for f in fila}),
                key=lambda c: uso["cenas"].get(c["id"], "0000-01-01"))
        if not candidatas:
            break

        # frases elegíveis: nenhuma repete no mesmo dia; fora isso, a menos
        # usada há mais tempo vem primeiro (rebaixar, nunca excluir)
        usadas_hoje = {f["frase_base"] for f in fila}
        frases_ok = [f for f in opcoes if f not in usadas_hoje] or list(opcoes)
        pares_recentes = {(p["cena"], p["frase"]) for p in uso.get("pares", [])
                          if _recente(p["em"], quando, DIAS_REPETICAO)}

        melhor = max(
            ((c, f) for c in candidatas for f in frases_ok
             if (c["id"], f) not in pares_recentes),
            key=lambda par: (_afinidade(par[1], par[0]),
                             _idade(uso, par[1], quando),
                             par[0]["id"]),
            default=None)
        if melhor is None:
            melhor = max(((c, f) for c in candidatas for f in frases_ok),
                         key=lambda par: (_afinidade(par[1], par[0]),
                                          par[0]["id"]))
        cena, frase = melhor
        texto = frase.replace("{N}", str(max(dias, 0)))
        fila.append({
            "id": f"{quando.isoformat()}-c{pos + 1}",
            "cena": cena,
            "frase": texto,
            "frase_base": frase,
            "categoria": cat,
            "layout": LAYOUTS[pos % len(LAYOUTS)],
            "contexto": cena["descricao"],
            "fonte": "rockstargames.com/VI",
            "zoom": 1.0,
            "dx": 0,
        })
        uso["cenas"][cena["id"]] = quando.isoformat()
        uso["frases"][frase] = quando.isoformat()
        uso["pares"] = (uso.get("pares", []) +
                        [{"cena": cena["id"], "frase": frase,
                          "em": quando.isoformat()}])[-400:]
        minuto_anterior = _minuto(cena)
        if cat == "contagem":
            contagens += 1
    return fila


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Mostra a fila de cartões de um dia")
    ap.add_argument("--quantos", type=int, default=5)
    ap.add_argument("--data", default=date.today().isoformat())
    ap.add_argument("--gravar-uso", action="store_true")
    a = ap.parse_args()
    uso = carregar_uso()
    fila = montar_fila(a.quantos, date.fromisoformat(a.data), uso)
    for c in fila:
        print(f"{c['id']} · layout {c['layout']} · {c['categoria']:10s} · "
              f"{c['cena']['id']} · “{c['frase']}”")
    if a.gravar_uso:
        gravar_uso(uso)


if __name__ == "__main__":
    main()
