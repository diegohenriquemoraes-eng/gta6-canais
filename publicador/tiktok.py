# -*- coding: utf-8 -*-
"""Espelho do TikTok — republica no TikTok o cartão que já saiu no Instagram.

**Por que espelho e não render próprio.** O cartão do Instagram já é 1080×1920,
já foi renderizado nesta execução ou numa anterior e já está hospedado numa URL
pública (asset de Release deste repo). Renderizar de novo gastaria minuto de
runner para produzir o mesmo arquivo, e publicar arquivo diferente do mesmo
conteúdo em duas redes não traz nada.

**Por que Zernio.** A Content Posting API do TikTok só publica *público* depois
de auditoria do app (2 a 4 semanas, sem garantia); sem ela tudo sai
`SELF_ONLY`. Upload por navegador é blindado e robô é contra os termos. O
Zernio tem app auditado e 2 contas grátis **por conta do Zernio** — o teto é
por conta, não por perfil (medido em 23/09/2026), e por isso este canal tem
conta própria lá.

**Atraso de propósito** (`tiktok.atraso_min`): publicar nas duas redes no mesmo
minuto é assinatura de automação. O espelho espera o cartão "esfriar".

**Teto diário** (`tiktok.espelhos_por_dia`): leitura de spam do TikTok, não
cota. Conta nova que recebe 5 vídeos num dia é robô; 3 escoa o dia e parece
gente. O teto do próprio TikTok no Zernio é 15 numa janela MÓVEL de 24 h — não
por dia UTC (lição paga no @vendanaobra em 20/09/2026, quando o Zernio devolveu
207 com o post enfileirado e publicou sozinho depois).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

ZERNIO = "https://zernio.com/api/v1"

MAX_LEGENDA = 1000          # o TikTok aceita 2.200; acima de ~1.000 ninguém lê
MAX_HASHTAGS = 5


def log(msg: str) -> None:
    print(f"[tt {datetime.now(timezone.utc):%H:%M:%S}] {msg}", flush=True)


def chave() -> str:
    return os.environ.get("ZERNIO_KEY_GTA", "").strip()


def _zernio(metodo: str, caminho: str, corpo: dict | None = None
            ) -> tuple[int, dict]:
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(
        f"{ZERNIO}{caminho}", data=dados, method=metodo, headers={
            "Authorization": f"Bearer {chave()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "RumoAViceCity/1.0",
        })
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try:
            detalhe = json.load(e)
        except Exception:
            detalhe = {"erro": e.read().decode("utf-8", "replace")[:500]}
        return e.code, detalhe


def conta(cfg: dict) -> dict | None:
    """A conta TikTok que recebe o espelho.

    Trava: com mais de uma conta ligada e nenhuma escolhida no config, para.
    Publicar no perfil errado é o erro que não se desfaz — o mesmo motivo pelo
    qual o publicador confere o `channel_id` do token antes de todo upload.
    """
    status, resp = _zernio("GET", "/accounts?platform=tiktok")
    if status != 200:
        log(f"/accounts devolveu {status}: {str(resp)[:200]}")
        return None
    contas = [c for c in resp.get("accounts", [])
              if c.get("platform") == "tiktok"
              and c.get("isActive", True) and c.get("enabled", True)]
    alvo = cfg.get("conta_id", "")
    if alvo:
        return next((c for c in contas if c.get("_id") == alvo), None)
    if not contas:
        log("nenhuma conta TikTok ligada no Zernio.")
        return None
    if len(contas) > 1:
        nomes = ", ".join(f"{c.get('username')} ({c.get('_id')})"
                          for c in contas)
        log(f"mais de uma conta ligada ({nomes}); defina tiktok.conta_id.")
        return None
    return contas[0]


def legenda_do_cartao(legenda_ig: str, cfg: dict) -> str:
    """A legenda do Instagram, adaptada ao que o TikTok penaliza ou ignora.

    Sai a URL em texto (penalizada e não clicável), sai o `@` de arroba do
    Instagram (que aqui viraria menção a outro perfil) e o corpo é cortado.
    As hashtags são remontadas a partir das que já existiam.
    """
    import re
    corpo = re.sub(r"https?://\S+", "", legenda_ig or "")
    corpo = re.sub(r"(?<!\w)@([\w.]+)", r"\1", corpo)
    achadas = [t.lower() for t in re.findall(r"#(\w+)", corpo)]
    corpo = re.sub(r"#\w+", "", corpo)
    corpo = re.sub(r"[ \t]+\n", "\n", corpo)
    corpo = re.sub(r"\n{3,}", "\n\n", corpo).strip()
    if len(corpo) > MAX_LEGENDA:
        corpo = corpo[:MAX_LEGENDA - 1].rsplit(" ", 1)[0] + "…"

    tags, vistas = [], set()
    for t in list(cfg.get("hashtags_fixas", [])) + achadas:
        t = t.lstrip("#").lower()
        if t and t not in vistas and len(tags) < MAX_HASHTAGS:
            vistas.add(t)
            tags.append(t)
    return (corpo + "\n\n" + " ".join(f"#{t}" for t in tags)).strip()


def publicar(alvo: dict, url_video: str, legenda: str) -> tuple[bool, dict]:
    """201 = publicou; 207 = enfileirado pelo teto móvel de 24 h do TikTok.

    O 207 NÃO é falha: o Zernio publica sozinho quando a janela abre. Tratá-lo
    como erro faria o espelho reenviar o mesmo vídeo e duplicar o post.
    """
    corpo = {
        "content": legenda,
        "mediaItems": [{"type": "video", "url": url_video}],
        "platforms": [{"platform": "tiktok", "accountId": alvo["_id"]}],
        # Declaração que a auditoria do TikTok exige de quem publica por API.
        "tiktokSettings": {
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "allow_comment": True,
            "allow_duet": True,
            "allow_stitch": True,
            "content_preview_confirmed": True,
            "express_consent_given": True,
        },
        "publishNow": True,
    }
    status, resp = _zernio("POST", "/posts", corpo)
    post = resp.get("post", resp)
    tk = next((p for p in (post.get("platforms") or [])
               if p.get("platform") == "tiktok"), {})
    if status in (200, 201, 207) and post.get("status") != "failed":
        return True, {"post_id": post.get("_id"),
                      "url": tk.get("platformPostUrl"),
                      "estado": post.get("status")}
    return False, {"status": status, "resposta": str(resp)[:400]}


def a_espelhar(cfg: dict, er_ig: dict, et: dict, agora: datetime) -> dict | None:
    """O cartão mais antigo já publicado no IG que ainda não foi espelhado."""
    hoje = agora.date().isoformat()
    dia = et.get("dia", {"data": "", "n": 0})
    n = dia["n"] if dia["data"] == hoje else 0
    if n >= cfg.get("espelhos_por_dia", 3):
        return None
    feitos = {p["cartao"] for p in et.get("publicados", [])}
    atraso = timedelta(minutes=cfg.get("atraso_min", 30))
    for p in er_ig.get("publicados", []):
        if p["id"] in feitos or not p.get("url_midia"):
            continue
        if agora - datetime.fromisoformat(p["em"]) < atraso:
            continue        # ainda quente: publicar junto é assinatura de robô
        return p
    return None


def rodar(cfg: dict, er_ig: dict, et: dict, legendas: dict,
          gravar=lambda: None, dry_run: bool = False) -> None:
    agora = datetime.now(timezone.utc)
    if not chave():
        log("sem ZERNIO_KEY_GTA; o espelho fica parado.")
        return
    item = a_espelhar(cfg, er_ig, et, agora)
    if item is None:
        log("nada a espelhar nesta hora.")
        return
    if dry_run:
        log(f"[dry-run] espelharia {item['id']}")
        return

    alvo = conta(cfg)
    if alvo is None:
        return
    legenda = legenda_do_cartao(legendas.get(item["id"], item.get("frase", "")),
                                cfg)
    ok, info = publicar(alvo, item["url_midia"], legenda)
    if not ok:
        log(f"o TikTok recusou: {info}")
        return
    log(f"NO AR: {info.get('url') or info.get('estado') or 'enfileirado'}")

    hoje = agora.date().isoformat()
    d = et.get("dia", {"data": "", "n": 0})
    et["dia"] = {"data": hoje, "n": (d["n"] if d["data"] == hoje else 0) + 1}
    et["ultimo"] = agora.isoformat(timespec="seconds")
    et.setdefault("publicados", []).append({
        "cartao": item["id"], "post_id": info.get("post_id"),
        "url": info.get("url"), "estado": info.get("estado"),
        "em": agora.isoformat(timespec="seconds"),
    })
    gravar()
