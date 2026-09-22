# -*- coding: utf-8 -*-
"""Aplica a marca no canal por API: banner, bio, keywords e idioma.

O que a YouTube Data API REALMENTE grava (medido na casa em 19-20/08/2026):

| item | API | observação |
|---|---|---|
| banner | ✅ `channelBanners.insert` + `channels.update` | funciona |
| descrição (bio) | ✅ `brandingSettings.channel.description` | funciona |
| keywords | ✅ `brandingSettings.channel.keywords` | ancoram o canal no tema |
| `defaultLanguage` | ✅ | pt-BR |
| **nome do canal** | ❌ | devolve **200 gravando nada**; só o Studio |
| **handle** | ❌ | só o Studio |
| **trailer para não inscritos** | ❌ | aceita o campo e ignora; só o Studio |
| **avatar** | ❌ | não existe endpoint; só o Studio/app |
| **seção Links** | ❌ | só o Studio |

Por isso o avatar e o handle estão em PENDENCIAS-DIEGO.md: não é falta de
código, é falta de API. E é por isso que `channels.update` com
`part=localizations` devolve 400 `failedPrecondition` — não insistir.

Uso: python produzir/aplicar_marca.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from nucleo import canal  # noqa: E402
from produzir.reabastecer import oferta_do_dia  # noqa: E402

CONFIG = RAIZ / "publicador" / "config.json"
BANNER = RAIZ / "marca" / "banner.png"

KEYWORDS = ("\"gta 6\" \"gta vi\" \"grand theft auto vi\" \"gta 6 brasil\" "
            "\"vice city\" \"jason e lucia\" leonida \"gta 6 notícias\" "
            "\"gta 6 lançamento\" \"contagem regressiva gta 6\"")


def bio(cfg: dict) -> str:
    from datetime import date
    oferta = oferta_do_dia("yt_bio", date.today())
    base = cfg.get("bio", "")
    return (base + ("\n\n" + oferta if oferta else "")).strip()[:1000]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))["canais"]["gta"]
    texto = bio(cfg)
    if a.dry_run:
        print(f"bio ({len(texto)} chars):\n{texto}\n\nkeywords:\n{KEYWORDS}")
        return
    if not (RAIZ / "credenciais" / "gta" / "token.json").exists():
        print("sem credenciais do canal — nada aplicado. "
              "Ver PENDENCIAS-DIEGO.md.")
        return

    from googleapiclient.http import MediaFileUpload

    from nucleo import youtube_api
    yt = youtube_api.servico(RAIZ / "credenciais" / "gta")
    cid, titulo = youtube_api.canal_do_token(yt)
    print(f"canal: {titulo} ({cid})")

    if BANNER.exists():
        r = yt.channelBanners().insert(
            media_body=MediaFileUpload(str(BANNER), mimetype="image/png")
        ).execute()
        yt.channels().update(part="brandingSettings", body={
            "id": cid,
            "brandingSettings": {"image": {"bannerExternalUrl": r["url"]}},
        }).execute()
        print("banner aplicado")

    yt.channels().update(part="brandingSettings", body={
        "id": cid,
        "brandingSettings": {"channel": {
            "description": texto,
            "keywords": KEYWORDS,
            "defaultLanguage": canal.BCP47,
        }},
    }).execute()
    print("bio, keywords e idioma aplicados")
    print("\nFalta pelo Studio (não tem API): nome do canal, handle, avatar, "
          "trailer para não inscritos e a seção Links.")


if __name__ == "__main__":
    main()
