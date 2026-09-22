# -*- coding: utf-8 -*-
"""Publicador do canal GTA 6 — roda no GitHub Actions duas vezes por hora.

Decide o que está devido NESTA execução (longo, Short do YouTube, cartão do
Instagram ou Story) e publica no máximo UM item por rede por execução. O render
acontece aqui, na hora: a fila guarda só metadados (o repo não carrega MP4).

Herdado do motor Palavra-Viva-3x, com os defeitos já pagos lá:

- **o gap do longo não cala o canal** (03/09/2026): quando o longo espera, a
  execução cai para a avaliação do Short em vez de devolver None;
- **o gap entre Shorts é ALVO, não veto** (`gap_efetivo`): o cron do GitHub
  coalesce e entrega ~6 execuções por dia, não 24; exigir o gap cheio joga o
  último Short para fora do dia;
- **estado versionado**: o runner é descartado, e sem commit o disparo
  seguinte republicaria;
- **channel_id do token conferido** antes de qualquer upload.

Novo aqui:

- **contagem regressiva**: `N = 19/11/2026 - hoje`. Com N ≤ 0 o formato A é
  desligado e a esteira troca para E (gameplay CC BY) e F (guia), conforme
  `fase_pos_lancamento`. Sem cena CC colhida, cai para B e registra o fallback;
- **três redes no mesmo laço**, cada uma com a sua hora e o seu contador.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from nucleo import canal, fabrica, playlists  # noqa: E402

CONFIG = Path(__file__).parent / "config.json"
STATE = Path(__file__).parent / "state.json"
LOCK = Path(__file__).parent / "publicador.lock"
REGISTRO = RAIZ / "publicacoes.md"
SAIDA = RAIZ / "saida"
LOCK_VELHO_S = 3 * 3600

PISO_GAP_MIN = 60


def log(msg: str) -> None:
    print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}",
          flush=True)


def carregar(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def gravar(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


# ------------------------------------------------------------------ fila ----

def pacotes_de_hoje(fila: Path) -> list[tuple[Path, dict]]:
    hoje = datetime.now(timezone.utc).date().isoformat()
    if not fila.is_dir():
        return []
    achados = []
    for p in sorted(fila.iterdir()):
        if p.is_dir() and p.name.startswith(hoje):
            meta = carregar(p / "pacote.json", None)
            if meta:
                achados.append((p, meta))
    return achados


# --------------------------------------------------------------- agenda ----

def estado_canal(state: dict, chave: str) -> dict:
    return state.setdefault("canais", {}).setdefault(chave, {
        "publicados": [], "ultimo_short": None, "ultimo_longo": None,
        "shorts_dia": {"data": "", "n": 0}, "longos_dia": {"data": "", "n": 0},
    })


def estado_rede(state: dict, rede: str) -> dict:
    return state.setdefault("redes", {}).setdefault(rede, {
        "publicados": [], "ultimo": None, "dia": {"data": "", "n": 0},
        "story_dia": {"data": "", "n": 0},
    })


def gap_efetivo(gap: int, faltam: int, agora: datetime) -> float:
    """O gap é ALVO de espaçamento, não veto: tem de caber no que resta do dia.

    Lição de 02/09/2026 no canal ES: com o cron coalescido, exigir o gap cheio
    fez o 2º Short do dia cair fora do dia em 6 de 8 dias — um deles perdido
    por 29 minutos.
    """
    if faltam <= 0:
        return gap
    restam_min = 24 * 60 - (agora.hour * 60 + agora.minute)
    return max(min(gap, restam_min / faltam), PISO_GAP_MIN)


def decidir(cfg: dict, ec: dict, agora: datetime) -> str | None:
    """'longo', 'short' ou None — o que está devido nesta hora no YouTube."""
    hoje = agora.date().isoformat()

    hora_longo = cfg.get("hora_longo_utc")
    ld = ec["longos_dia"]
    n_longos = ld["n"] if ld["data"] == hoje else 0
    if (hora_longo is not None and agora.hour >= hora_longo
            and n_longos < cfg.get("longos_por_dia", 1)):
        gap = cfg.get("gap_longos_min", 0)
        travado = False
        if n_longos and gap and ec.get("ultimo_longo"):
            decorrido = (agora - datetime.fromisoformat(ec["ultimo_longo"])
                         ).total_seconds() / 60
            travado = decorrido < gap
        if not travado:
            return "longo"
        # O longo espera o gap — mas o canal NÃO fica mudo (defeito de 03/09).

    sd = ec["shorts_dia"]
    n_hoje = sd["n"] if sd["data"] == hoje else 0
    faltam = cfg["shorts_por_dia"] - n_hoje
    if faltam <= 0:
        return None
    hora_short = cfg.get("hora_short_utc")
    if hora_short is not None and agora.hour < hora_short:
        return None
    if ec.get("ultimo_short"):
        decorrido = (agora - datetime.fromisoformat(ec["ultimo_short"])
                     ).total_seconds() / 60
        if decorrido < gap_efetivo(cfg["gap_shorts_min"], faltam, agora):
            return None
    return "short"


def decidir_instagram(cfg: dict, er: dict, agora: datetime) -> str | None:
    """'cartao', 'story' ou None. O Story fecha o dia, depois dos cartões."""
    hoje = agora.date().isoformat()
    dia = er["dia"]
    n = dia["n"] if dia["data"] == hoje else 0
    faltam = cfg.get("cartoes_por_dia", 0) - n
    if faltam > 0 and agora.hour >= cfg.get("hora_cartao_utc", 0):
        if not er.get("ultimo"):
            return "cartao"
        decorrido = (agora - datetime.fromisoformat(er["ultimo"])
                     ).total_seconds() / 60
        if decorrido >= gap_efetivo(cfg.get("gap_cartoes_min", 150),
                                    faltam, agora):
            return "cartao"
        return None
    sd = er["story_dia"]
    n_story = sd["n"] if sd["data"] == hoje else 0
    if (n_story < cfg.get("stories_por_dia", 0)
            and agora.hour >= cfg.get("hora_story_utc", 23)):
        return "story"
    return None


def pos_lancamento(cfg: dict, hoje: date) -> bool:
    return hoje >= date.fromisoformat(cfg["lancamento"])


def tipo_de_short(cfg: dict, pacote: dict, idx: int, hoje: date) -> str:
    """Qual formato o Short desta posição usa hoje (A/B/C antes, E/C depois).

    Depois de 19/11 a esteira troca para gameplay CC BY. Se `colher_cc.py`
    ainda não entregou cena nenhuma, cai para B (trailer oficial) e o pacote
    registra `fallback: sem_cc` — nunca fica sem publicar por causa disso.
    """
    if not pos_lancamento(cfg, hoje):
        return pacote["shorts"][idx].get("formato", "B")
    plano = cfg.get("fase_pos_lancamento", {}).get("shorts", ["E"])
    desejado = plano[idx % len(plano)]
    disponivel = pacote["shorts"][idx].get("formato", "B")
    if desejado == "E" and not pacote["shorts"][idx].get("credito_cc"):
        return disponivel
    return desejado


# ----------------------------------------------------------- publicação ----

def registrar(cfg: dict, item: dict, video_id: str) -> None:
    with REGISTRO.open("a", encoding="utf-8") as fh:
        fh.write(
            f"\n## {video_id} — {item['titulo']}\n\n"
            f"- URL: https://youtu.be/{video_id}\n"
            f"- Canal: {cfg['titulo_canal']}\n"
            f"- Item: {item['tipo_item']} — {item['referencia']}\n"
            f"- Duração: {item['duracao_s']}s\n"
            f"- Publicado em: "
            f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}\n")


def registrar_no_estado(state: dict, cfg: dict, item: dict, video_id: str,
                        pasta: Path, tipo: str, formato: str) -> None:
    agora = datetime.now(timezone.utc)
    hoje = agora.date().isoformat()
    ec = estado_canal(state, "gta")
    if any(p["video_id"] == video_id for p in ec["publicados"]):
        return
    ec["publicados"].append({
        "pacote": pasta.name, "item": item["tipo_item"], "formato": formato,
        "video_id": video_id, "titulo": item["titulo"],
        "em": agora.isoformat(timespec="seconds"),
    })
    chave = "longos_dia" if tipo == "longo" else "shorts_dia"
    d = ec[chave]
    ec[chave] = {"data": hoje, "n": (d["n"] if d["data"] == hoje else 0) + 1}
    ec["ultimo_longo" if tipo == "longo" else "ultimo_short"] = \
        agora.isoformat(timespec="seconds")
    gravar(STATE, state)
    registrar(cfg, item, video_id)


def publicar_no_youtube(cfg: dict, config: dict, item: dict, pasta: Path,
                        tipo: str, state: dict, formato: str) -> None:
    from nucleo import youtube_api
    cred_dir = RAIZ / "credenciais" / "gta"
    youtube = youtube_api.servico(cred_dir)
    cid, ctitulo = youtube_api.canal_do_token(youtube)
    if cfg.get("channel_id") and cid != cfg["channel_id"]:
        raise SystemExit(f"token é do canal {cid} ({ctitulo}); "
                         f"esperado {cfg['channel_id']}")
    if not cfg.get("channel_id"):
        log(f"channel_id vazio no config; token é de {cid} ({ctitulo}). "
            f"Grave o id em publicador/config.json.")

    existente = youtube_api.ja_publicado(youtube, item["titulo"])
    if existente:
        log(f"JÁ EXISTE no canal: https://youtu.be/{existente} — registrando.")
        registrar_no_estado(state, cfg, item, existente, pasta, tipo, formato)
        return

    log(f"subindo {item['tipo_item']}: {item['titulo']}")
    video_id = youtube_api.upload(youtube, item["arquivo"], item["titulo"],
                                  item["descricao"], item["tags"], canal.BCP47)
    espera = (config["espera_longo_s"] if tipo == "longo"
              else config["espera_short_s"])
    info = youtube_api.esperar_processamento(youtube, video_id, espera)
    if item.get("thumb"):
        try:
            youtube_api.definir_thumbnail(youtube, video_id, item["thumb"])
        except Exception as exc:
            log(f"thumbnail não aplicada ({exc}); seguindo. O canal precisa "
                f"de verificação por telefone em youtube.com/verify")
    if item.get("legenda_srt"):
        try:
            youtube_api.enviar_legenda(youtube, video_id, item["legenda_srt"],
                                       canal.BCP47)
        except Exception as exc:
            log(f"legenda não enviada ({str(exc)[:120]}); seguindo.")
    youtube_api.tornar_publico(youtube, video_id, info)
    log(f"PUBLICADO: https://youtu.be/{video_id}")

    if tipo == "longo":
        titulo_pl = canal.PLAYLISTS.get(formato)
        if titulo_pl:
            try:
                pl = youtube_api.playlist_por_titulo(youtube, titulo_pl,
                                                     cfg.get("bio", ""))
                playlists.definir(formato, pl)
                youtube_api.adicionar_na_playlist(youtube, pl, video_id)
                log(f"adicionado à playlist '{titulo_pl}'")
            except Exception as exc:
                log(f"playlist falhou ({exc}); seguindo.")

    registrar_no_estado(state, cfg, item, video_id, pasta, tipo, formato)


def longo_do_dia(ec: dict, pacote_nome: str, formato: str) -> str:
    """Ponte do Short para o longo, DENTRO da playlist (`&list=`).

    95% das views do canal vêm do feed de Shorts, e é esse tráfego que morre
    se o Short não apontar para lugar nenhum. Se o longo de hoje falhou, cai
    no último do mesmo formato: link de ontem é melhor que Short sem ponte.
    """
    vid = ""
    for p in reversed(ec.get("publicados", [])):
        if p["item"] != "longo":
            continue
        if p["pacote"] == pacote_nome:
            vid = p["video_id"]
            break
        if not vid and p.get("formato") == formato:
            vid = p["video_id"]
    if not vid:
        return ""
    lista = playlists.obter(formato)
    return (f"https://www.youtube.com/watch?v={vid}&list={lista}" if lista
            else f"https://youtu.be/{vid}")


# ------------------------------------------------------------------ main ----

def main() -> None:
    ap = argparse.ArgumentParser(description="Publica o que está devido agora")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--render-apenas", action="store_true",
                    help="Renderiza em saida/ sem publicar (dispensa token)")
    ap.add_argument("--forcar-tipo",
                    choices=["short", "longo", "cartao", "story"])
    ap.add_argument("--rede", choices=["youtube", "instagram"], default=None)
    args = ap.parse_args()

    config = carregar(CONFIG, None)
    if config is None:
        raise SystemExit(f"Config ausente: {CONFIG}")
    state = carregar(STATE, {})
    agora = datetime.now(timezone.utc)
    hoje = agora.date()
    dias = canal.dias_para_lancamento(hoje)

    cfg = config["canais"]["gta"]
    fila = RAIZ / cfg.get("fila", "fila")
    achados = pacotes_de_hoje(fila)
    if not achados:
        log("SEM PACOTE para hoje — o reabastecedor precisa rodar.")
        return
    pasta_pacote, pacote = achados[0]

    if LOCK.exists() and time.time() - LOCK.stat().st_mtime < LOCK_VELHO_S:
        log("Outra execução em andamento (lock). Saindo.")
        return
    LOCK.write_text(str(os.getpid()), encoding="utf-8")
    falhas: list[str] = []
    try:
        if args.rede in (None, "youtube"):
            try:
                _rodar_youtube(config, cfg, state, agora, dias, achados, args)
            except KeyboardInterrupt:
                raise
            except BaseException as exc:
                log(f"YOUTUBE FALHOU ({exc!r}); seguindo para o Instagram.")
                falhas.append("youtube")
        if args.rede in (None, "instagram"):
            try:
                _rodar_instagram(config, state, agora, pasta_pacote, pacote,
                                 args)
            except KeyboardInterrupt:
                raise
            except BaseException as exc:
                log(f"INSTAGRAM FALHOU ({exc!r}).")
                falhas.append("instagram")
    finally:
        LOCK.unlink(missing_ok=True)

    if falhas:
        raise SystemExit("Falhou em: " + ", ".join(falhas))


def _rodar_youtube(config, cfg, state, agora, dias, achados, args) -> None:
    if not cfg.get("ativo") and not args.render_apenas:
        log("canal inativo; pulando o YouTube.")
        return
    pasta_pacote, pacote = achados[0]
    ec = estado_canal(state, "gta")
    tipo = args.forcar_tipo if args.forcar_tipo in ("short", "longo") \
        else decidir(cfg, ec, agora)
    if tipo is None:
        log("YouTube: nada devido nesta hora.")
        return

    cred = RAIZ / "credenciais" / "gta" / "token.json"
    if not args.render_apenas and not args.dry_run and not cred.exists():
        log("sem credenciais do YouTube no runner; pulando.")
        return

    pasta_longo, pacote_longo = pasta_pacote, pacote
    if tipo == "longo":
        feitos = {p["pacote"] for p in ec["publicados"] if p["item"] == "longo"}
        escolha = next(((p, m) for p, m in achados if p.name not in feitos), None)
        if escolha is None:
            log("todos os longos de hoje já saíram.")
            return
        pasta_longo, pacote_longo = escolha

    if args.dry_run:
        alvo = pasta_longo if tipo == "longo" else pasta_pacote
        log(f"[dry-run] publicaria: {tipo} do pacote {alvo.name}")
        return

    formato_longo = pacote_longo.get("longo", {}).get("formato", "tudo")

    def render_e_publica(t: str) -> None:
        if t == "longo":
            item = fabrica.montar_longo(
                pacote_longo, SAIDA / f"{pasta_longo.name}-longo",
                oferta=cfg.get("oferta_longo", ""), dias=dias)
            origem, formato = pasta_longo, formato_longo
        else:
            idx = (ec["shorts_dia"]["n"]
                   if ec["shorts_dia"]["data"] == agora.date().isoformat()
                   else 0)
            idx = min(idx, len(pacote["shorts"]) - 1)
            item = fabrica.montar_short(
                pacote, idx, SAIDA / f"{pasta_pacote.name}-short{idx}",
                url_longo=longo_do_dia(ec, pasta_pacote.name, formato_longo),
                oferta=cfg.get("oferta_short", ""), dias=dias)
            origem, formato = pasta_pacote, pacote["shorts"][idx].get(
                "formato", "B")
        log(f"render ok: {item['arquivo']} "
            f"({item['arquivo'].stat().st_size / 1e6:.1f} MB, "
            f"{item['duracao_s']}s)")
        if args.render_apenas:
            return
        publicar_no_youtube(cfg, config, item, origem, t, state, formato)

    # O longo é a peça frágil (20 min, centenas de MB). Ele NUNCA pode deixar o
    # canal mudo: render E publicação sob o mesmo try, com queda para o Short.
    try:
        render_e_publica(tipo)
    except KeyboardInterrupt:
        raise
    except BaseException as exc:
        if tipo != "longo":
            raise
        log(f"LONGO FALHOU ({exc!r}); caindo para Short nesta execução.")
        render_e_publica("short")


def _rodar_instagram(config, state, agora, pasta_pacote, pacote, args) -> None:
    ig_cfg = config.get("instagram", {})
    if not ig_cfg.get("ativo"):
        log("Instagram inativo; pulando.")
        return
    er = estado_rede(state, "instagram")
    tipo = args.forcar_tipo if args.forcar_tipo in ("cartao", "story") \
        else decidir_instagram(ig_cfg, er, agora)
    if tipo is None:
        log("Instagram: nada devido nesta hora.")
        return
    if args.dry_run:
        log(f"[dry-run] Instagram publicaria: {tipo}")
        return

    from publicador import instagram
    instagram.rodar(tipo, ig_cfg, state, er, pacote, pasta_pacote,
                    render_apenas=args.render_apenas, gravar=lambda: gravar(
                        STATE, state))


if __name__ == "__main__":
    main()
