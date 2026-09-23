# -*- coding: utf-8 -*-
"""Colhe gameplay com licença Creative Commons — formatos E e F, pós 19/11/2026.

Este é o único caminho pelo qual arquivo de vídeo de terceiro entra no
pipeline, e ele tem quatro travas:

1. a busca pede `videoLicense=creativeCommon` na Data API;
2. o `videos.list` **reconfirma** `status.license == "creativeCommon"` antes de
   qualquer download (a busca às vezes devolve o que não devia);
3. o crédito nominal ao canal de origem vai no rodapé queimado do vídeo
   (`Gameplay: <canal> · CC BY`) e o link do original vai na descrição — é o
   que a CC BY exige em troca da reutilização;
4. cada `videoId` usado ganha uma linha em `fontes/PROVENIENCIA.md`. Se a API
   deixar de reportar `creativeCommon` para um id já usado, o vigia abre issue
   e o material sai de circulação.

**Só roda a partir de 19/11/2026** — antes disso não existe gameplay público de
GTA 6 que não seja vazamento, e vazamento é a única coisa que a política da
Rockstar derruba sem discussão.

Uso:
    python produzir/colher_cc.py --consulta "GTA 6 gameplay" --quantos 6
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from nucleo import canal, cenas as C  # noqa: E402

CC = RAIZ / "marca" / "cc"
REGISTRO = RAIZ / "conteudo" / "cc_colhidos.json"

MIN_S, MAX_S = 60, 20 * 60


def carregar_registro() -> dict:
    return json.loads(REGISTRO.read_text(encoding="utf-8")) if REGISTRO.exists() else {}


def gravar_registro(reg: dict) -> None:
    REGISTRO.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")


def buscar(consulta: str, quantos: int, ignorar_data: bool = False
           ) -> list[dict]:
    """Gameplay CC BY publicado DEPOIS do lançamento — nunca vazamento.

    ⚠ `publishedAfter` no futuro derruba a chamada com 400 "invalid argument"
    (medido em 23/09/2026, no primeiro ensaio do formato E). O corte é o
    lançamento, mas num ensaio antes dele isso é uma data futura — daí o
    `min(...)`. Em produção a trava continua inteira: é o `main` que decide.
    """
    from nucleo import youtube_api
    yt = youtube_api.servico(RAIZ / "credenciais" / "gta")
    corte = canal.LANCAMENTO
    if ignorar_data:
        corte = min(corte, date.today() - timedelta(days=30))
    depois = datetime.combine(corte, datetime.min.time(),
                              tzinfo=timezone.utc).isoformat(
                                  timespec="seconds").replace("+00:00", "Z")
    r = yt.search().list(part="id", q=consulta, type="video",
                         videoLicense="creativeCommon", order="viewCount",
                         videoDefinition="high", publishedAfter=depois,
                         maxResults=50).execute()
    ids = [it["id"]["videoId"] for it in r.get("items", [])]
    if not ids:
        return []
    det = yt.videos().list(part="snippet,contentDetails,status,statistics",
                           id=",".join(ids)).execute().get("items", [])
    bons = []
    for v in det:
        # trava 2: a busca mente de vez em quando
        if v.get("status", {}).get("license") != "creativeCommon":
            continue
        from produzir.ranquear_perfil import _dur_iso
        dur = _dur_iso(v["contentDetails"].get("duration", ""))
        if not (MIN_S <= dur <= MAX_S):
            continue
        bons.append({
            "id": v["id"], "canal": v["snippet"]["channelTitle"],
            "titulo": v["snippet"]["title"], "duracao_s": dur,
            "url": f"https://www.youtube.com/watch?v={v['id']}",
            "views": int(v.get("statistics", {}).get("viewCount", 0)),
            "licenca_lida": "creativeCommon",
            "colhido_em": date.today().isoformat(),
        })
        if len(bons) >= quantos:
            break
    return bons


def baixar(item: dict) -> Path | None:
    CC.mkdir(parents=True, exist_ok=True)
    destino = CC / f"{item['id']}.mp4"
    if destino.exists():
        return destino
    r = subprocess.run(
        ["yt-dlp", "-f", "bv*[height<=1080]+ba/b[height<=1080]",
         "--merge-output-format", "mp4", "-o", str(destino), item["url"]],
        capture_output=True, text=True)
    if r.returncode != 0 or not destino.exists():
        print(f"! {item['id']} não baixou: {r.stderr.strip()[-200:]}")
        return None
    return destino


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--consulta", default="GTA 6 gameplay")
    ap.add_argument("--quantos", type=int, default=6)
    ap.add_argument("--ignorar-data", action="store_true",
                    help="só para teste; em produção a trava de data vale")
    a = ap.parse_args()

    if date.today() < canal.LANCAMENTO and not a.ignorar_data:
        print(f"Antes de {canal.LANCAMENTO}: não existe gameplay público de "
              f"GTA 6 que não seja vazamento. Nada a colher.")
        return

    reg = carregar_registro()
    novos = [i for i in buscar(a.consulta, a.quantos, a.ignorar_data)
             if i["id"] not in reg]
    print(f"{len(novos)} vídeos CC BY novos")
    lista = C.carregar()
    for item in novos:
        mp4 = baixar(item)
        if not mp4:
            continue
        fim = C.duracao(mp4)
        cortes = C.detectar(mp4)
        cenas_novas = C.montar_cenas(f"cc:{item['id']}", cortes, fim,
                                     licenca="cc-by", credito=item["canal"])
        for c in cenas_novas:
            c["descricao"] = item["titulo"][:120]
            c["tags"] = ["gameplay", "cc"]
        lista += cenas_novas
        reg[item["id"]] = item
        print(f"{item['id']} ({item['canal']}): {len(cenas_novas)} cenas")
    C.gravar(lista)
    gravar_registro(reg)


if __name__ == "__main__":
    main()
