# -*- coding: utf-8 -*-
"""Publicação no Instagram pela Graph API — copiado do psicologia-fria.

O que veio de lá, inteiro, porque já foi pago em produção:

- **o MP4 precisa de uma URL pública**: a API recusa upload de bytes
  (`upload_type=resumable` é ignorado e a resposta é sempre
  "The parameter video_url is required"). Por isso o arquivo sobe como asset
  de um Release num repo **público** — asset de repo privado exige token e o
  Instagram devolve `status: ERROR` sem explicar;
- **retry do erro transitório** (`is_transient`, code 2): sem ele um soluço do
  lado deles custa o slot inteiro;
- **o Story nunca derruba o Reel**: ele é distribuição extra de 24 h, e
  `_esperar_e_publicar` levanta `SystemExit`, que não é subclasse de
  `Exception` — daí o `except (Exception, SystemExit)`;
- **o estado é salvo ANTES do Story**, para que uma falha lá não republique o
  Reel na execução seguinte.

O que é novo: o item publicado é o CARTÃO (formato G) renderizado na hora por
`nucleo/cartao.py`, e o Story do dia carrega a oferta da Shopee com
`src=ig_story`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from nucleo import canal, cartao, cenas  # noqa: E402

GRAPH = "https://graph.instagram.com"
SAIDA = RAIZ / "saida" / "instagram"
REGISTRO = RAIZ / "publicacoes-ig.md"


def log(msg: str) -> None:
    print(f"[ig {datetime.now(timezone.utc):%H:%M:%S}] {msg}", flush=True)


def conta() -> tuple[str, str]:
    """(IG_USER_ID, token). Vazio = ainda sem secret; o chamador para no render."""
    return os.environ.get("IG_USER_ID_GTA", ""), os.environ.get("IG_TOKEN_GTA", "")


# ------------------------------------------------------------ hospedagem ----

def subir_asset(mp4: Path, cfg: dict) -> str:
    repo = cfg["repo_midia"]
    tag = cfg.get("release_tag", "cartoes")
    if subprocess.run(["gh", "release", "view", tag, "-R", repo],
                      capture_output=True).returncode != 0:
        subprocess.run(["gh", "release", "create", tag, "-R", repo,
                        "--title", "Cartões", "--notes",
                        "Hospedagem dos MP4 para a Graph API"], check=True)
    subprocess.run(["gh", "release", "upload", tag, str(mp4), "-R", repo,
                    "--clobber"], check=True)
    return f"https://github.com/{repo}/releases/download/{tag}/{mp4.name}"


# -------------------------------------------------------------- Graph API ---

def _esperar_e_publicar(ig_id: str, token: str, cid: str) -> str:
    log(f"container {cid} criado; esperando o Instagram processar")
    for i in range(30):
        time.sleep(10)
        s = requests.get(f"{GRAPH}/{cid}", timeout=30, params={
            "fields": "status_code,status", "access_token": token}).json()
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise SystemExit(f"o Instagram recusou o vídeo: {s}")
        log(f"  {s.get('status_code')} ({i + 1}/30)")
    else:
        raise SystemExit("timeout esperando o processamento")
    p = requests.post(f"{GRAPH}/{ig_id}/media_publish", timeout=60, data={
        "creation_id": cid, "access_token": token}).json()
    if "id" not in p:
        raise SystemExit(f"falha no media_publish: {p}")
    return p["id"]


def publicar_reel(ig_id: str, token: str, video_url: str, legenda: str) -> str:
    for tentativa in range(4):
        r = requests.post(f"{GRAPH}/{ig_id}/media", timeout=120, data={
            "media_type": "REELS", "video_url": video_url, "caption": legenda,
            "share_to_feed": "true", "access_token": token}).json()
        if "id" in r:
            break
        erro = r.get("error", {})
        if not erro.get("is_transient") or tentativa == 3:
            raise SystemExit(f"falha ao criar container: {r}")
        espera = 20 * (tentativa + 1)
        log(f"erro transitório do Instagram; de novo em {espera}s")
        time.sleep(espera)
    return _esperar_e_publicar(ig_id, token, r["id"])


def publicar_story(ig_id: str, token: str, video_url: str) -> str | None:
    """Nunca derruba a publicação — o Reel é o produto, o Story é bônus."""
    try:
        r = requests.post(f"{GRAPH}/{ig_id}/media", timeout=120, data={
            "media_type": "STORIES", "video_url": video_url,
            "access_token": token}).json()
        if "id" not in r:
            log(f"! story: container recusado ({r})")
            return None
        sid = _esperar_e_publicar(ig_id, token, r["id"])
        log(f"story no ar (24 h): {sid}")
        return sid
    except (Exception, SystemExit) as e:
        log(f"! story falhou ({e}) — sigo")
        return None


# ------------------------------------------------------------------ render --

def identidade(cfg: dict) -> dict:
    marca = RAIZ / "marca"
    return {
        "nome": cfg.get("nome", "Rumo a Vice City"),
        "handle": cfg.get("handle", "rumoavicecity"),
        "avatar": marca / "avatar-96.png",
        "selo": marca / "selo.png",
    }


def render_cartao(item: dict, cfg: dict, outdir: Path) -> Path:
    """Renderiza o cartão do item da fila. Sem arquivo local, não há cartão.

    A origem pode ser um clipe do trailer ou uma FOTO da galeria oficial
    (`cenas.e_foto`); no segundo caso a imagem ganha zoom lento e a trilha
    procedural da casa, porque foto parada e muda não entrega em feed de vídeo.
    """
    cena = item["cena"]
    origem = cenas.arquivo_da_cena(cena)
    if not origem:
        raise SystemExit(
            f"origem de {cena['id']} ausente em marca/oficial — "
            f"rode produzir/baixar_oficial.py antes")
    rodape = (canal.credito_cc(cena["credito"]) if cena.get("licenca") == "cc-by"
              else canal.CREDITO_ROCKSTAR)
    return cartao.montar(origem, cena["inicio"], cena["fim"], item["frase"],
                         item["layout"], identidade(cfg), outdir,
                         rodape=rodape, zoom=item.get("zoom", 1.0),
                         dx=item.get("dx", 0),
                         saida=f"{item['id']}.mp4",
                         estatico=cenas.e_foto(cena),
                         seed=abs(hash(cena["id"])) % 99991)


def legenda_do_cartao(item: dict, cfg: dict) -> str:
    """Legenda do post. Sem link (o Instagram não clica): o link é a bio."""
    hashtags = "#gta6 #gtavi #gta6brasil #vicecity #rockstargames #gta6news"
    fonte = item.get("fonte", "")
    linhas = [item["frase"]]
    if item.get("contexto"):
        linhas.append(item["contexto"])
    linhas.append(f"Fonte: {fonte}" if fonte else canal.CREDITO_ROCKSTAR)
    linhas.append(f"Link da pré-venda na bio · @{cfg.get('handle')}")
    linhas.append(hashtags)
    return "\n\n".join(linhas)


# ------------------------------------------------------------------ rodar ---

def rodar(tipo: str, cfg: dict, state: dict, er: dict, pacote: dict,
          pasta_pacote: Path, render_apenas: bool = False,
          gravar=lambda: None) -> None:
    agora = datetime.now(timezone.utc)
    hoje = agora.date().isoformat()

    if tipo == "story":
        item = (pacote.get("stories") or [None])[0]
        if not item:
            log("sem story no pacote de hoje.")
            return
        feitos = {p["id"] for p in er["publicados"]}
        base = next((c for c in pacote["cartoes"] if c["id"] in feitos), None)
        if base is None:
            log("nenhum cartão publicado hoje ainda; o story espera.")
            return
        url = base.get("url_midia")
        if not url:
            log("cartão do dia sem URL guardada; o story espera.")
            return
        ig_id, token = conta()
        if not token:
            log("sem IG_TOKEN_GTA — story não sai.")
            return
        sid = publicar_story(ig_id, token, url)
        sd = er["story_dia"]
        er["story_dia"] = {"data": hoje,
                           "n": (sd["n"] if sd["data"] == hoje else 0) + 1}
        if sid:
            er.setdefault("stories", []).append(
                {"story_id": sid, "oferta": item.get("oferta", ""),
                 "em": agora.isoformat(timespec="seconds")})
        gravar()
        return

    feitos = {p["id"] for p in er["publicados"]}
    item = next((c for c in pacote.get("cartoes", []) if c["id"] not in feitos),
                None)
    if item is None:
        log("todos os cartões de hoje já saíram.")
        return

    outdir = SAIDA / pasta_pacote.name
    mp4 = render_cartao(item, cfg, outdir)
    log(f"cartão renderizado: {mp4} ({mp4.stat().st_size / 1e6:.1f} MB)")
    if render_apenas:
        return

    ig_id, token = conta()
    if not token:
        log("sem IG_TOKEN_GTA — parei depois do render.")
        return

    url = subir_asset(mp4, cfg)
    log(f"asset publicado: {url}")
    media_id = publicar_reel(ig_id, token, url, legenda_do_cartao(item, cfg))
    log(f"NO AR: https://www.instagram.com/reel/{media_id}/")

    item["url_midia"] = url
    (pasta_pacote / "pacote.json").write_text(
        json.dumps(pacote, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")

    d = er["dia"]
    er["dia"] = {"data": hoje, "n": (d["n"] if d["data"] == hoje else 0) + 1}
    er["ultimo"] = agora.isoformat(timespec="seconds")
    er["publicados"].append({
        "id": item["id"], "media_id": media_id, "cena": item["cena"]["id"],
        "frase": item["frase"], "layout": item["layout"], "url_midia": url,
        "em": agora.isoformat(timespec="seconds"),
    })
    gravar()
    with REGISTRO.open("a", encoding="utf-8") as fh:
        fh.write(f"\n## {media_id} — {item['frase']}\n\n"
                 f"- https://www.instagram.com/reel/{media_id}/\n"
                 f"- cena: `{item['cena']['id']}` · layout {item['layout']}\n"
                 f"- {agora.isoformat(timespec='seconds')}\n")
