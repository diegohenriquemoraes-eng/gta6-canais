# -*- coding: utf-8 -*-
"""O RANQUEADOR — a réplica do "Vice Scrap" do ViceScale, com uma diferença.

O original cola o @ de um perfil, lista os posts por views e **baixa os 10 mais
vistos para republicar**. Aqui a lista sai igual e o download **não acontece**:

> **Baixa para MEDIR, não para postar.** Arquivo só entra no pipeline se a
> licença for Creative Commons (`status.license == creativeCommon`), e aí com
> crédito (ver `produzir/colher_cc.py`).

Republicar arquivo de terceiro não entrega em 2026 — YouTube não monetiza
"reused content", o TikTok tira do For You desde 15/09/2025 e o Instagram
parou de recomendar repost em Reels (2024) e em foto/carrossel (30/04/2026) —
e um strike de copyright atinge todos os canais da mesma conta Google.

O que a ferramenta serve, então: **medir o FORMATO que rende**. Que duração,
que tipo de frase, que cena. O relatório sai em `benchmark/RESUMO.md`.

Redes:

| rede | como | precisa de |
|---|---|---|
| `yt` | Data API: `search.list` por `viewCount` + `videos.list` | token (roda no Actions) |
| `ig` | GraphQL replay no Chrome — cola o JSON de `xdt_api__v1__feed__user_timeline_graphql_connection` em `--colar arquivo.json`; roda LOCAL, porque o runner não tem Chrome logado | nada |
| `tt` | página pública, JSON `__UNIVERSAL_DATA_FOR_REHYDRATION__`; best-effort, quebra quando o TikTok muda | nada |

Uso:
    python produzir/ranquear_perfil.py --rede yt --consulta "gta 6" --top 50
    python produzir/ranquear_perfil.py --rede yt --nosso           # nossa casa
    python produzir/ranquear_perfil.py --rede ig --perfil gta6club --colar ig.json
    python produzir/ranquear_perfil.py --rede tt --perfil gta6
    python produzir/ranquear_perfil.py --resumo                    # só o relatório
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

BENCH = RAIZ / "conteudo" / "benchmark.json"
PASTA = RAIZ / "benchmark"
RESUMO = PASTA / "RESUMO.md"


def _dur_iso(txt: str) -> int:
    """PT1M23S -> 83."""
    m = re.match(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", txt or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def do_youtube(consulta: str, top: int, dias: int = 30,
               canal_id: str = "") -> list[dict]:
    """`search.list` por viewCount + `videos.list`. Custa 100 + 1 por 50 vídeos."""
    from nucleo import youtube_api
    yt = youtube_api.servico(RAIZ / "credenciais" / "gta")
    depois = (datetime.now(timezone.utc) - timedelta(days=dias)
              ).isoformat(timespec="seconds").replace("+00:00", "Z")
    params = dict(part="id", type="video", order="viewCount",
                  maxResults=min(50, top), publishedAfter=depois)
    if canal_id:
        params["channelId"] = canal_id
    else:
        params["q"] = consulta
    ids = [it["id"]["videoId"]
           for it in yt.search().list(**params).execute().get("items", [])]
    if not ids:
        return []
    det = yt.videos().list(part="snippet,statistics,contentDetails,status",
                           id=",".join(ids)).execute().get("items", [])
    saida = []
    for v in det:
        st = v.get("statistics", {})
        saida.append({
            "id": v["id"],
            "url": f"https://youtu.be/{v['id']}",
            "views": int(st.get("viewCount", 0)),
            "likes": int(st.get("likeCount", 0)),
            "comentarios": int(st.get("commentCount", 0)),
            "duracao_s": _dur_iso(v["contentDetails"].get("duration", "")),
            "publicado_em": v["snippet"]["publishedAt"][:10],
            "legenda": v["snippet"]["title"],
            "canal": v["snippet"]["channelTitle"],
            "licenca": v.get("status", {}).get("license", ""),
        })
    return sorted(saida, key=lambda x: -x["views"])[:top]


def do_instagram_colado(caminho: Path, top: int) -> list[dict]:
    """Lê o JSON capturado no Chrome (memória `varrer-instagram-pelo-chrome`).

    Roda LOCAL de propósito: o GraphQL do Instagram exige sessão logada, e o
    runner do Actions não tem navegador nem deve ter a sessão do Diego.
    """
    bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))
    def _achar(no):
        if isinstance(no, dict):
            if "edges" in no and isinstance(no["edges"], list):
                yield from no["edges"]
            for v in no.values():
                yield from _achar(v)
        elif isinstance(no, list):
            for v in no:
                yield from _achar(v)
    saida = []
    for e in _achar(bruto):
        n = (e or {}).get("node") or {}
        if not n.get("code"):
            continue
        legenda = ((n.get("caption") or {}).get("text") or "").strip()
        saida.append({
            "id": n["code"],
            "url": f"https://www.instagram.com/reel/{n['code']}/",
            "views": int(n.get("play_count") or n.get("view_count") or 0),
            "likes": int(n.get("like_count") or 0),
            "comentarios": int(n.get("comment_count") or 0),
            "duracao_s": round(float(n.get("video_duration") or 0), 1),
            "publicado_em": datetime.fromtimestamp(
                n.get("taken_at", 0), timezone.utc).date().isoformat(),
            "legenda": legenda,
            "frase_frame0": legenda.split("\n")[0][:120],
            "licenca": "",
        })
    return sorted(saida, key=lambda x: -x["views"])[:top]


def do_tiktok(perfil: str, top: int) -> list[dict]:
    import requests
    html = requests.get(f"https://www.tiktok.com/@{perfil}", timeout=40,
                        headers={"User-Agent": "Mozilla/5.0"}).text
    m = re.search(r'id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
                  html, re.S)
    if not m:
        print("! TikTok mudou o HTML; nada colhido")
        return []
    dados = json.loads(m.group(1))
    itens = []
    def _achar(no):
        if isinstance(no, dict):
            if "stats" in no and "video" in no:
                itens.append(no)
            for v in no.values():
                _achar(v)
        elif isinstance(no, list):
            for v in no:
                _achar(v)
    _achar(dados)
    saida = []
    for it in itens:
        s = it.get("stats", {})
        saida.append({
            "id": it.get("id", ""),
            "url": f"https://www.tiktok.com/@{perfil}/video/{it.get('id')}",
            "views": int(s.get("playCount", 0)),
            "likes": int(s.get("diggCount", 0)),
            "comentarios": int(s.get("commentCount", 0)),
            "duracao_s": int(it.get("video", {}).get("duration", 0)),
            "publicado_em": datetime.fromtimestamp(
                int(it.get("createTime", 0)), timezone.utc).date().isoformat(),
            "legenda": (it.get("desc") or "")[:200],
            "licenca": "",
        })
    return sorted(saida, key=lambda x: -x["views"])[:top]


def gravar(rede: str, perfil: str, videos: list[dict]) -> None:
    dados = json.loads(BENCH.read_text(encoding="utf-8")) if BENCH.exists() else []
    dados = [d for d in dados
             if not (d["rede"] == rede and d["perfil"] == perfil)]
    dados.append({
        "rede": rede, "perfil": perfil,
        "coletado_em": datetime.now(timezone.utc).date().isoformat(),
        "videos": videos,
    })
    BENCH.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")


FAIXAS = [(0, 10), (10, 20), (20, 30), (30, 60), (60, 10 ** 6)]


def resumo() -> str:
    if not BENCH.exists():
        return "Sem benchmark.json ainda.\n"
    dados = json.loads(BENCH.read_text(encoding="utf-8"))
    linhas = ["# RESUMO do benchmark — o que rende no nicho de GTA 6", "",
              "Gerado por `produzir/ranquear_perfil.py --resumo`. **Nada aqui "
              "foi baixado para reuso**: são metadados públicos.", ""]
    for bloco in dados:
        vs = bloco["videos"]
        if not vs:
            continue
        linhas.append(f"## {bloco['rede']} · {bloco['perfil']} "
                      f"({bloco['coletado_em']}, {len(vs)} itens)")
        linhas.append("")
        linhas.append(f"- mediana de views: "
                      f"{statistics.median(v['views'] for v in vs):,.0f}")
        for a, b in FAIXAS:
            faixa = [v for v in vs if a <= v["duracao_s"] < b]
            if faixa:
                linhas.append(
                    f"- {a}-{b if b < 10**6 else '∞'} s: {len(faixa)} itens, "
                    f"mediana {statistics.median(v['views'] for v in faixa):,.0f}")
        cc = [v for v in vs if v.get("licenca") == "creativeCommon"]
        if cc:
            linhas.append(f"- **{len(cc)} com licença Creative Commons** "
                          f"(esses sim podem virar arquivo, com crédito)")
        top = vs[0]
        linhas.append(f"- mais visto: {top['views']:,} — “{top['legenda'][:90]}”")
        linhas.append("")
    return "\n".join(linhas) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rede", choices=["yt", "ig", "tt"])
    ap.add_argument("--perfil", default="")
    ap.add_argument("--consulta", default="gta 6")
    ap.add_argument("--colar", type=Path, help="JSON do GraphQL do Instagram")
    ap.add_argument("--nosso", action="store_true",
                    help="mede o NOSSO canal em vez da busca")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--dias", type=int, default=30)
    ap.add_argument("--resumo", action="store_true")
    a = ap.parse_args()

    PASTA.mkdir(parents=True, exist_ok=True)
    if a.rede == "yt":
        canal_id = ""
        if a.nosso:
            cfg = json.loads(
                (RAIZ / "publicador" / "config.json").read_text(encoding="utf-8"))
            canal_id = cfg["canais"]["gta"].get("channel_id", "")
            if not canal_id:
                raise SystemExit("channel_id vazio no config — o canal ainda "
                                 "não existe (ver PENDENCIAS-DIEGO.md)")
        vs = do_youtube(a.consulta, a.top, a.dias, canal_id)
        gravar("yt", canal_id or a.consulta, vs)
    elif a.rede == "ig":
        if not a.colar:
            raise SystemExit("--colar com o JSON capturado no Chrome "
                             "(ver a memória varrer-instagram-pelo-chrome)")
        vs = do_instagram_colado(a.colar, a.top)
        gravar("ig", a.perfil or a.colar.stem, vs)
    elif a.rede == "tt":
        vs = do_tiktok(a.perfil, a.top)
        gravar("tt", a.perfil, vs)
    else:
        vs = []

    if vs:
        print(f"{len(vs)} itens colhidos; mediana "
              f"{statistics.median(v['views'] for v in vs):,.0f} views")
    RESUMO.write_text(resumo(), encoding="utf-8")
    print(f"resumo em {RESUMO}")


if __name__ == "__main__":
    main()
