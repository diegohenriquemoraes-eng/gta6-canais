# -*- coding: utf-8 -*-
"""Realinha descrição e tags do acervo já publicado — idempotente e retomável.

Serve para uma coisa só: quando a oferta muda (a pré-venda morre em 20/11 e o
link principal vira o DualSense), os vídeos antigos continuam com o link velho.
Este script reescreve a linha da oferta no acervo, 19 vídeos por rodada.

Três travas herdadas do motor bíblico, todas pagas caro lá:

1. **compara antes de gastar**: só chama `videos.update` (50 unidades) quando
   algo mudou de verdade. Em dia sem mudança a rodada custa ~40 unidades;
2. **tags são comparadas por CONJUNTO**, não posição a posição — a API devolve
   as tags em ordem alfabética, e comparar listas ordenadas dava "diferente"
   sempre, reescrevendo o acervo inteiro toda rodada;
3. **`--limite`** teta a rodada: estourar a cota deixa o canal mudo até a
   virada do dia UTC.

Uso:
    python produzir/realinhar_publicados.py --dry-run
    python produzir/realinhar_publicados.py --limite 19
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from nucleo import canal  # noqa: E402
from produzir.reabastecer import oferta_do_dia  # noqa: E402

CONFIG = RAIZ / "publicador" / "config.json"
LIMITE_PADRAO = 19

# A oferta ocupa um bloco delimitado na descrição. Sem marca, não dá para
# trocar só ela sem reescrever a descrição inteira (e perder o que o vídeo
# tem de único, que é o que faz cada descrição ser diferente da outra).
INICIO = "<!--oferta-->"
FIM = "<!--/oferta-->"


def bloco(texto: str) -> str:
    return f"{INICIO}\n{texto.strip()}\n{FIM}" if texto.strip() else ""


def trocar_oferta(descricao: str, nova: str) -> str:
    novo_bloco = bloco(nova)
    if INICIO in descricao and FIM in descricao:
        return re.sub(re.escape(INICIO) + r".*?" + re.escape(FIM),
                      novo_bloco.replace("\\", "\\\\"), descricao, flags=re.S)
    if not novo_bloco:
        return descricao
    # sem marca ainda (vídeo publicado antes desta rotina): entra no topo, que
    # é onde converte — o YouTube corta a descrição depois de ~3 linhas
    return f"{novo_bloco}\n\n{descricao}"


def precisa(atual: dict, alvo: dict) -> bool:
    if atual["descricao"] != alvo["descricao"]:
        return True
    return set(atual["tags"]) != set(alvo["tags"])   # CONJUNTO, não lista


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=LIMITE_PADRAO)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not (RAIZ / "credenciais" / "gta" / "token.json").exists():
        print("sem credenciais do canal; nada a realinhar.")
        return
    from nucleo import youtube_api
    yt = youtube_api.servico(RAIZ / "credenciais" / "gta")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))["canais"]["gta"]

    uploads = yt.channels().list(part="contentDetails", mine=True).execute()[
        "items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, pagina = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=uploads,
                                    maxResults=50, pageToken=pagina).execute()
        ids += [it["contentDetails"]["videoId"] for it in r.get("items", [])]
        pagina = r.get("nextPageToken")
        if not pagina:
            break

    hoje = date.today()
    mexidos = 0
    for i in range(0, len(ids), 50):
        if mexidos >= a.limite:
            break
        det = yt.videos().list(part="snippet", id=",".join(ids[i:i + 50])
                               ).execute().get("items", [])
        for v in det:
            if mexidos >= a.limite:
                break
            sn = v["snippet"]
            curto = sn.get("categoryId") and "#shorts" in sn["title"].lower()
            origem = "yt_short" if curto else "yt_largo"
            nova = oferta_do_dia(origem, hoje)
            alvo = {
                "descricao": trocar_oferta(sn.get("description", ""), nova),
                "tags": list(dict.fromkeys(
                    (sn.get("tags") or []) + canal.CONFIG["tags"]))[:60],
            }
            atual = {"descricao": sn.get("description", ""),
                     "tags": sn.get("tags") or []}
            if not precisa(atual, alvo):
                continue
            mexidos += 1
            if a.dry_run:
                print(f"[dry-run] mudaria {v['id']} — {sn['title'][:60]}")
                continue
            sn["description"] = youtube_api.limpar_texto(alvo["descricao"])
            sn["tags"] = alvo["tags"]
            yt.videos().update(part="snippet",
                               body={"id": v["id"], "snippet": sn}).execute()
            print(f"realinhado {v['id']} — {sn['title'][:60]}")
    print(f"{mexidos} vídeos tocados (limite {a.limite}); "
          f"{len(ids)} no acervo")


if __name__ == "__main__":
    main()
