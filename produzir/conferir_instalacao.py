# -*- coding: utf-8 -*-
"""Confere a instalação inteira e diz, em uma tela, o que ainda falta.

Rode isto depois de cada passo de `PENDENCIAS-DIEGO.md`. Ele não muda nada:
só olha o repo, os secrets, a config e as credenciais locais e devolve uma
lista de ✓ e ✗ com o comando exato que resolve cada ✗.

    python produzir/conferir_instalacao.py

Existe porque o custo de um passo esquecido aqui é alto e silencioso: app
OAuth em modo de teste mata o refresh token em 7 dias, `channel_id` vazio faz o
publicador aceitar qualquer canal, e link de oferta sem `src=` só é notado dois
meses depois, quando não dá mais para saber o que converteu.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

CONFIG = RAIZ / "publicador" / "config.json"
OFERTAS = RAIZ / "conteudo" / "ofertas.json"
REPO = "diegohenriquemoraes-eng/gta6-canais"
REPO_MIDIA = "diegohenriquemoraes-eng/gta6-media"

OK, FALTA, AVISO = "✓", "✗", "!"


def _gh(*args: str) -> str:
    try:
        r = subprocess.run(["gh", *args], capture_output=True, text=True,
                           timeout=60)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def secrets_do_repo() -> set[str]:
    bruto = _gh("secret", "list", "-R", REPO, "--json", "name", "-q", ".[].name")
    return set(bruto.splitlines()) if bruto else set()


def linhas() -> list[tuple[str, str, str]]:
    """[(marca, o que é, o que fazer se faltar)]"""
    out: list[tuple[str, str, str]] = []
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    canal_cfg = cfg["canais"]["gta"]
    secrets = secrets_do_repo()

    # --- GitHub -----------------------------------------------------------
    vis = _gh("repo", "view", REPO, "--json", "visibility", "-q", ".visibility")
    out.append((OK if vis == "PUBLIC" else FALTA,
                f"repositório {REPO}: {vis or 'não consegui ler'}",
                "gh repo edit " + REPO + " --visibility public "
                "--accept-visibility-change-consequences  "
                "(privado dá 2.000 min/mês de Actions e o render diário passa "
                "disso na 1ª semana)"))

    vis_m = _gh("repo", "view", REPO_MIDIA, "--json", "visibility",
                "-q", ".visibility")
    out.append((OK if vis_m == "PUBLIC" else FALTA,
                f"repositório de mídia {REPO_MIDIA}: {vis_m or 'não existe'}",
                f"gh repo create {REPO_MIDIA} --public  "
                f"(asset de Release privado o Instagram recusa sem explicar)"))

    # --- YouTube ----------------------------------------------------------
    out.append((OK if canal_cfg.get("channel_id") else FALTA,
                f"channel_id no config: {canal_cfg.get('channel_id') or 'VAZIO'}",
                "Studio → Configurações → Canal → Configurações avançadas; "
                "cole em publicador/config.json. Sem isso o publicador aceita "
                "qualquer canal que o token abrir."))

    for nome in ("YT_CLIENT_SECRET_GTA", "YT_TOKEN_GTA"):
        out.append((OK if nome in secrets else FALTA, f"secret {nome}",
                    "python produzir/autorizar.py --canal gta  →  "
                    f"gh secret set {nome} < credenciais/gta/…"))
    out.append((OK if "YT_TOKEN_ANALYTICS_GTA" in secrets else AVISO,
                "secret YT_TOKEN_ANALYTICS_GTA (opcional)",
                "python produzir/autorizar.py --canal gta --analytics  "
                "(sem ele não há hora contável medida; o resto roda)"))

    token_local = RAIZ / "credenciais" / "gta" / "token.json"
    if token_local.exists():
        try:
            info = json.loads(token_local.read_text(encoding="utf-8-sig"))
            tem_refresh = bool(info.get("refresh_token"))
            out.append((OK if tem_refresh else FALTA,
                        "token local tem refresh_token",
                        "Revogue o acesso do app na conta e rode o autorizar "
                        "de novo: sem refresh_token o canal emudece em 1 hora."))
        except Exception as exc:
            out.append((FALTA, f"token local ilegível ({exc})",
                        "rode produzir/autorizar.py de novo"))

    # --- Instagram --------------------------------------------------------
    for nome in ("IG_USER_ID_GTA", "IG_TOKEN_GTA"):
        out.append((OK if nome in secrets else FALTA, f"secret {nome}",
                    f"gh secret set {nome}  (o USER_ID é o de "
                    f"graph.instagram.com/me, não o número do painel)"))

    # --- TikTok -----------------------------------------------------------
    tt = cfg.get("tiktok", {})
    if tt.get("ativo"):
        out.append((OK if "ZERNIO_KEY_GTA" in secrets else FALTA,
                    "secret ZERNIO_KEY_GTA", "gh secret set ZERNIO_KEY_GTA"))
    else:
        out.append((AVISO, "TikTok desligado no config (tiktok.ativo: false)",
                    'ligue depois de conectar o Zernio: "ativo": true'))

    # --- Notícias ---------------------------------------------------------
    out.append((OK if "ANTHROPIC_API_KEY" in secrets else AVISO,
                "secret ANTHROPIC_API_KEY (opcional)",
                "sem ele o resumo de emergência entra com nota 6 e a notícia "
                "NÃO vira Short sozinha — de propósito"))

    # --- Shopee -----------------------------------------------------------
    ofertas = []
    if OFERTAS.exists():
        d = json.loads(OFERTAS.read_text(encoding="utf-8"))
        ofertas = d if isinstance(d, list) else d.get("ofertas", [])
    com_link = [o for o in ofertas if (o.get("links") or {})]
    out.append((OK if com_link else FALTA,
                f"ofertas da Shopee com link: {len(com_link)} de {len(ofertas)}",
                "affiliate.shopee.com.br → Link personalizado, um por origem, "
                "com ?src=  (ver PENDENCIAS-DIEGO.md §8)"))
    for o in com_link:
        ruins = [k for k, v in (o.get("links") or {}).items() if "src=" not in v]
        if ruins:
            out.append((FALTA, f"oferta '{o['produto']}' sem src= em: "
                               f"{', '.join(ruins)}",
                        "sem src= não dá para saber de onde veio a venda"))
        vig = (o.get("vigencia") or {}).get("ate")
        if vig and date.fromisoformat(vig) < date.today():
            out.append((AVISO, f"oferta '{o['produto']}' venceu em {vig}",
                        "ela sai sozinha das descrições; troque a prioridade"))

    # --- conteúdo ---------------------------------------------------------
    from nucleo import cenas as C
    aptas = [c for c in C.aptas_para_cartao() if not c.get("no_runner")]
    precisa = cfg.get("instagram", {}).get("cartoes_por_dia", 5) * 7
    out.append((OK if len(aptas) >= precisa else FALTA,
                f"cenas aptas para cartão: {len(aptas)} (precisa de {precisa})",
                "python produzir/baixar_oficial.py && "
                "python produzir/cenas_da_galeria.py"))

    filas = sorted(p.name for p in (RAIZ / "fila").iterdir() if p.is_dir())
    hoje = date.today().isoformat()
    out.append((OK if any(f >= hoje for f in filas) else FALTA,
                f"fila: {len(filas)} pacotes, último {filas[-1] if filas else '—'}",
                "python produzir/reabastecer.py"))

    return out


def main() -> None:
    resultado = linhas()
    print("\n=== CONFERÊNCIA DA INSTALAÇÃO — gta6-canais ===\n")
    for marca, oque, comofazer in resultado:
        print(f" {marca}  {oque}")
        if marca != OK:
            print(f"      → {comofazer}")
    faltam = sum(1 for m, _, _ in resultado if m == FALTA)
    avisos = sum(1 for m, _, _ in resultado if m == AVISO)
    print(f"\n{len(resultado) - faltam - avisos} ok · {faltam} faltando · "
          f"{avisos} avisos")
    if faltam == 0:
        print("\nTudo pronto. O canal publica sozinho a partir da próxima "
              "execução do workflow Publicar.")
    else:
        print("\nPasso a passo completo em PENDENCIAS-DIEGO.md.")


if __name__ == "__main__":
    main()
