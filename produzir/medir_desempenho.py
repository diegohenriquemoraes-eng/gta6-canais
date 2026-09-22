# -*- coding: utf-8 -*-
"""Medição do canal: coorte 2-7 dias, mediana por formato, histórico.

A coorte 2-7 dias existe porque a mediana do acervo inteiro mistura vídeo de
ontem (que ainda não entregou) com vídeo de dois meses (que já entregou tudo) —
e aí nenhuma mudança de formato aparece no número. A janela de 2 a 7 dias é o
que o motor da casa usa para comparar semana contra semana.

⚠ O que este arquivo NÃO mede, e é o que decide a entrega do Short:
**"continuaram assistindo vs. pularam"**, que só existe no Studio (Analytics →
Conteúdo → Shorts → Engajamento). A `averageViewPercentage` da API conta só
quem ficou e passa de 100 % em vídeo que dá a segunda passada — foi o número
errado da casa de 22/08 a 16/09/2026. Régua do canal é o Studio.

Grava `conteudo/desempenho_historico.json` (uma linha por rodada) e imprime o
quadro.

Uso: python produzir/medir_desempenho.py [--dias 30]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

HIST = RAIZ / "conteudo" / "desempenho_historico.json"
STATE = RAIZ / "publicador" / "state.json"


def medir(dias: int = 30) -> dict:
    from nucleo import youtube_api
    yt = youtube_api.servico(RAIZ / "credenciais" / "gta")
    canais = yt.channels().list(part="snippet,statistics,contentDetails",
                                mine=True).execute()["items"][0]
    uploads = canais["contentDetails"]["relatedPlaylists"]["uploads"]
    est = canais["statistics"]

    ids, pagina = [], None
    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=uploads,
                                    maxResults=50, pageToken=pagina).execute()
        parar = False
        for it in r.get("items", []):
            quando = it["contentDetails"].get("videoPublishedAt")
            if not quando:
                continue
            if datetime.fromisoformat(quando.replace("Z", "+00:00")) < corte:
                parar = True
                continue
            ids.append(it["contentDetails"]["videoId"])
        pagina = r.get("nextPageToken")
        if parar or not pagina:
            break

    videos = []
    for i in range(0, len(ids), 50):
        det = yt.videos().list(part="snippet,statistics,contentDetails",
                               id=",".join(ids[i:i + 50])
                               ).execute().get("items", [])
        for v in det:
            from produzir.ranquear_perfil import _dur_iso
            dur = _dur_iso(v["contentDetails"].get("duration", ""))
            pub = datetime.fromisoformat(
                v["snippet"]["publishedAt"].replace("Z", "+00:00"))
            idade = (datetime.now(timezone.utc) - pub).days
            videos.append({
                "id": v["id"], "titulo": v["snippet"]["title"],
                "views": int(v.get("statistics", {}).get("viewCount", 0)),
                "duracao_s": dur, "idade_dias": idade,
                "tipo": "short" if dur <= 180 else "longo",
            })

    coorte = [v for v in videos if 2 <= v["idade_dias"] <= 7]
    def _med(lista):
        return round(statistics.median(v["views"] for v in lista)) if lista else 0

    return {
        "medido_em": datetime.now(timezone.utc).date().isoformat(),
        "canal": canais["snippet"]["title"],
        "inscritos": int(est.get("subscriberCount", 0)),
        "views_totais": int(est.get("viewCount", 0)),
        "videos_publicados": int(est.get("videoCount", 0)),
        "longos_publicados": sum(1 for v in videos if v["tipo"] == "longo"),
        "shorts_publicados": sum(1 for v in videos if v["tipo"] == "short"),
        "mediana_short_2a7d": _med([v for v in coorte if v["tipo"] == "short"]),
        "mediana_longo_2a7d": _med([v for v in coorte if v["tipo"] == "longo"]),
        "n_coorte": len(coorte),
        "janela_dias": dias,
    }


def portoes(m: dict) -> list[str]:
    """Os dois portões de monetização, ditos sem rodeio.

    **Portão A (volume)**: 1.000 inscritos + 4.000 h em 12 meses, OU 1.000
    inscritos + 10 mi de views de Shorts em 90 dias. As trilhas não somam, e
    hora de exibição só vem de vídeo LONGO.

    **Portão B (formato)**: `answer/1311392` lista como inelegível "readings of
    other materials you did not originally create" e slideshow com narrativa
    mínima. Este canal tem narração própria de fato em todo Short e abertura
    falada no longo — nasceu do lado certo desse portão, ao contrário dos
    canais bíblicos da casa.
    """
    linhas = []
    insc = m["inscritos"]
    linhas.append(f"Portão A · inscritos: {insc} de 1.000 "
                  f"({'OK' if insc >= 1000 else 'falta ' + str(1000 - insc)})")
    if m["longos_publicados"] == 0:
        linhas.append("Portão A · horas: SEM TRILHA — nenhum vídeo longo "
                      "publicado ainda, e hora de exibição só vem de longo.")
    else:
        linhas.append(f"Portão A · horas: {m['longos_publicados']} longos na "
                      f"janela; a hora contável só sai da Analytics (token "
                      f"YT_TOKEN_ANALYTICS_GTA).")
    linhas.append("Portão A · Shorts: a trilha de 10 mi de views em 90 dias "
                  "exige ~111 mil views/dia. Não é a aposta deste canal.")
    linhas.append("Portão B · formato: APTO — narração própria de fato em todo "
                  "Short e abertura falada no longo (camada autoral).")
    return linhas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=30)
    a = ap.parse_args()
    if not (RAIZ / "credenciais" / "gta" / "token.json").exists():
        print("sem credenciais do canal — o canal ainda não existe. "
              "Ver PENDENCIAS-DIEGO.md.")
        return
    m = medir(a.dias)
    hist = json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else []
    hist = [h for h in hist if h["medido_em"] != m["medido_em"]] + [m]
    HIST.write_text(json.dumps(hist, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    print(json.dumps(m, ensure_ascii=False, indent=1))
    print("\n".join(portoes(m)))


if __name__ == "__main__":
    main()
