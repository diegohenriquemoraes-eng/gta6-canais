# -*- coding: utf-8 -*-
"""Monta os pacotes da fila (hoje até hoje+2) a partir do poço de fatos.

Cada pacote (`fila/AAAA-MM-DD/pacote.json`) traz **só metadados**: quais fatos
viram Short, quais viram o longo, quais cenas × frases viram cartão do
Instagram e qual oferta vai no Story. **Nenhum MP4 entra na fila** — o repo é
público e vídeo commitado incharia o Git para sempre; o render acontece na hora
de publicar (regra herdada do motor bíblico).

Escolha dos fatos:

- um Short de formato **A** (contagem regressiva) por dia enquanto faltarem
  dias; os outros de **B** ("você viu isso no trailer?");
- **C** (notícia) tem prioridade sobre A/B no dia em que `produzir/noticias.py`
  entrega item com `nota >= 7` e rótulo `oficial`;
- o longo é **compilação temática rotativa** e NÃO consome o poço. Medido em
  22/09/2026: com alvo de 18 min, um longo leva ~55 fatos — se ele consumisse o
  poço como o Short, os 150 fatos acabariam em TRÊS dias. "Tudo o que sabemos
  sobre GTA 6" é recap por natureza; o que não pode é o recap de hoje ser igual
  ao de ontem. Por isso cada dia pega um TEMA (`TEMAS_LONGO`), com título,
  ordem e capa próprios, girando em ciclo de 6 dias;
- depois de 19/11 o agendador troca sozinho para E/F; aqui a única mudança é
  parar de gerar o formato A.

O consumo fica em `conteudo/fatos_uso.json`, versionado como o `state.json`:
sem isso, o disparo seguinte reaproveitaria os mesmos fatos.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from nucleo import canal, fabrica  # noqa: E402
from produzir import escalar  # noqa: E402

POCO = RAIZ / "conteudo" / "fatos"
USO = RAIZ / "conteudo" / "fatos_uso.json"
FILA = RAIZ / "fila"
CONFIG = RAIZ / "publicador" / "config.json"
OFERTAS = RAIZ / "conteudo" / "ofertas.json"
NOTICIAS = RAIZ / "conteudo" / "noticias"

DIAS_A_FRENTE = 2
DIAS_DESCANSO_FATO = 60      # um fato só volta ao SHORT depois de dois meses

# Os temas do vídeo longo, em ciclo. Cada um é um recorte do poço por tag, com
# título e capa próprios: é o que impede que o longo de hoje seja o de ontem
# com outra ordem — a impressão digital exata que a análise de conteúdo em
# massa procura. O tema do dia sai de `(dia do ano) % len(TEMAS_LONGO)`.
TEMAS_LONGO = [
    ("historia", "Jason, Lucia e a história de GTA 6: tudo o que a Rockstar mostrou",
     ["personagem", "jason", "lucia", "historia", "historia-serie", "npc",
      "perfil-criminal", "boobie", "satira"], "JASON\nE LUCIA"),
    ("mapa", "O mapa de GTA 6: Vice City, Leonida e tudo o que já foi mostrado",
     ["lugar", "mapa", "tamanho", "vice-city", "animais", "transporte",
      "atividade"], "O MAPA\nDE GTA 6"),
    ("mecanicas", "As mecânicas de GTA 6: polícia, armas, carros e o que muda",
     ["mecanica", "policia", "armas", "combate", "carros", "veiculos",
      "economia", "corpo"], "O QUE\nMUDA"),
    ("lancamento", "GTA 6: data, pré-venda, edições e tudo sobre o lançamento",
     ["lancamento", "data", "prazo", "adiamento", "pre-venda", "pre-load",
      "bonus", "ultimate", "edicoes", "preco", "plataformas", "ps5", "pc",
      "dualsense", "brasil", "idiomas"], "A DATA\nE O PREÇO"),
    ("producao", "GTA 6 por dentro: produção, gráficos, música e os números",
     ["producao", "graficos", "design", "arte", "musica", "album", "numeros",
      "recorde", "take-two", "roupas", "app", "redes", "animacao", "visual", "cores",
      "hud", "camera", "snapmatic", "vendas", "pesquisa",
      "duracao", "memoria", "rdr2", "referencia", "netflix",
      "online", "protagonistas"], "POR\nDENTRO"),
    ("trailers", "Tudo o que os trailers de GTA 6 mostraram, cena por cena",
     ["trailer1", "trailer2", "trailers", "extended", "galeria", "curiosidade",
      "capitulos", "capa", "sinopse", "evento", "classificacao",
      "dupla", "casal", "romance", "lista"], "CENA A\nCENA"),
]


def tema_do_dia(quando: date) -> tuple[str, str, list[str], str]:
    return TEMAS_LONGO[quando.toordinal() % len(TEMAS_LONGO)]


def carregar_poco() -> list[dict]:
    fatos: list[dict] = []
    for arq in sorted(glob.glob(str(POCO / "*.json"))):
        fatos += json.loads(Path(arq).read_text(encoding="utf-8"))
    return fatos


def carregar_uso() -> dict:
    return json.loads(USO.read_text(encoding="utf-8")) if USO.exists() else {}


def gravar_uso(uso: dict) -> None:
    USO.write_text(json.dumps(uso, ensure_ascii=False, indent=1,
                              sort_keys=True) + "\n", encoding="utf-8")


def _prioridade(fato: dict) -> tuple:
    """Rockstar antes de imprensa; depois pela ordem do poço."""
    oficial = 0 if "rockstargames.com" in fato.get("fonte", "") else 1
    return (oficial, fato["id"])


def livres(fatos: list[dict], uso: dict, quando: date,
           formato: str | None = None) -> list[dict]:
    out = []
    for f in fatos:
        if f.get("revisar"):
            continue                      # fato em revisão não vai ao ar
        if formato and f.get("formato") != formato:
            continue
        visto = uso.get(f["id"])
        if visto and (quando - date.fromisoformat(visto)).days < DIAS_DESCANSO_FATO:
            continue
        out.append(f)
    return sorted(out, key=_prioridade)


def noticia_do_dia(quando: date) -> dict | None:
    arq = NOTICIAS / f"{quando.isoformat()}.json"
    if not arq.exists():
        return None
    itens = json.loads(arq.read_text(encoding="utf-8"))
    bons = [n for n in itens
            if n.get("nota", 0) >= 7 and n.get("rotulo") == "oficial"]
    return bons[0] if bons else None


def oferta_do_dia(origem: str, quando: date) -> str:
    """Bloco da oferta PRINCIPAL para esta origem, respeitando a vigência.

    Cada link já carrega o Sub_id da origem (o rastreador nativo da Shopee —
    `?src=` não serve: o campo só aceita alfanumérico e o encurtador descarta
    parâmetro colado). Uma oferta por descrição, a de prioridade 1.
    """
    if not OFERTAS.exists():
        return ""
    itens = json.loads(OFERTAS.read_text(encoding="utf-8"))
    validos = []
    for o in itens if isinstance(itens, list) else itens.get("ofertas", []):
        vig = o.get("vigencia", {})
        if vig.get("ate") and date.fromisoformat(vig["ate"]) < quando:
            continue
        if vig.get("de") and date.fromisoformat(vig["de"]) > quando:
            continue
        validos.append(o)
    if not validos:
        return ""
    # UM LINK SÓ, em toda bio e em todo vídeo (decisão do Diego, 23/09/2026):
    # a vitrine com 4 produtos. Antes ia o link direto de UM produto, e trocar
    # de produto obrigaria a mexer em quatro bios — duas delas só pelo celular.
    # Com a vitrine, trocar vira um commit e o link publicado nunca envelhece.
    # O `?de=` preserva o rastreio: a página escolhe o link daquela origem, que
    # é o mesmo destino com Sub_id diferente.
    vit = itens.get("_VITRINE", {}) if isinstance(itens, dict) else {}
    url = vit.get("url")
    if not url:
        return ""
    return (f"🛒 Os acessórios de GTA 6 que a gente indica:\n{url}?de={origem}"
            "\n\nLinks de afiliado da Shopee: comprando por eles você paga o "
            "mesmo preço e ajuda o canal.")


def montar_pacote(quando: date, fatos: list[dict], uso: dict, cfg: dict,
                  ig_cfg: dict, uso_cartoes: dict) -> dict:
    dias = canal.dias_para_lancamento(quando)
    n_shorts = cfg["shorts_por_dia"]

    escolhidos: list[dict] = []
    noticia = noticia_do_dia(quando)
    if noticia:
        escolhidos.append({
            "id": f"N{quando.strftime('%m%d')}",
            "formato": "C",
            "gancho": noticia["gancho"],
            "narracao": noticia["resumo"],
            "fonte": noticia["url"],
            "cena": noticia.get("cena", "galeria: logo GTA VI"),
            "tags": ["noticia"],
            "rotulo": "NOTÍCIA",
        })
    if dias > 0 and len(escolhidos) < n_shorts:
        for f in livres(fatos, uso, quando, formato="A")[:1]:
            escolhidos.append(f)
    for f in livres(fatos, uso, quando, formato="B"):
        if len(escolhidos) >= n_shorts:
            break
        if f["id"] not in {x["id"] for x in escolhidos}:
            escolhidos.append(f)
    for f in livres(fatos, uso, quando):     # completa com o que houver
        if len(escolhidos) >= n_shorts:
            break
        if f["id"] not in {x["id"] for x in escolhidos}:
            escolhidos.append(f)

    # O longo NÃO consome o poço (ver o cabeçalho): ele é o recap do tema do
    # dia, e todo fato do tema entra, tenha ou não virado Short.
    slug, titulo_tema, tags_tema, capa = tema_do_dia(quando)
    do_tema = [f for f in fatos
               if not f.get("revisar") and set(f.get("tags", [])) & set(tags_tema)]
    do_tema.sort(key=_prioridade)
    if len(do_tema) < fabrica.MIN_FATOS_LONGO:
        # tema magro: completa com os fatos de maior prioridade que sobraram,
        # em vez de deixar o canal sem longo no dia
        resto = [f for f in sorted(fatos, key=_prioridade)
                 if not f.get("revisar") and f not in do_tema]
        do_tema += resto[:fabrica.MIN_FATOS_LONGO - len(do_tema)]
    do_longo = fabrica.fatos_para_alvo(do_tema, "tudo")

    titulo = (f"{titulo_tema} — faltam {dias} dias" if dias > 0 else titulo_tema)
    pacote = {
        "data": quando.isoformat(),
        "handle": cfg.get("handle", ""),
        "dias_para_lancamento": dias,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "shorts": escolhidos[:n_shorts],
        "longo": {
            "formato": "tudo",
            "fatos": do_longo,
            "cena": do_longo[0]["cena"] if do_longo else "",
            "titulo": titulo[:100],
            "thumb_titulo": (f"FALTAM\n{dias} DIAS" if dias > 0
                             else "TUDO SOBRE\nGTA 6"),
            "thumb_sub": (do_longo[0]["gancho"] if do_longo else "GTA 6"),
            "descricao_busca": (
                "Os fatos confirmados sobre GTA 6, um de cada vez, com a fonte "
                "de cada um. Sem rumor sem fonte e sem vazamento."),
            "tags_extra": ["gta 6 tudo o que sabemos", "gta 6 fatos",
                           "gta 6 data de lançamento", "gta 6 novidades",
                           f"gta 6 {slug}"],
            "minutos_estimados": round(fabrica.minutos_estimados(do_longo), 1),
        },
        "cartoes": escalar.montar_fila(ig_cfg.get("cartoes_por_dia", 5),
                                       quando, uso_cartoes),
        "stories": [{"oferta": oferta_do_dia("ig_story", quando)}],
        "oferta_yt_longo": oferta_do_dia("yt_largo", quando),
        "oferta_yt_short": oferta_do_dia("yt_short", quando),
    }
    for f in pacote["shorts"]:
        uso[f["id"]] = quando.isoformat()
    return pacote


def main() -> None:
    ap = argparse.ArgumentParser(description="Monta a fila de hoje até hoje+2")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dias", type=int, default=DIAS_A_FRENTE)
    a = ap.parse_args()

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg = config["canais"]["gta"]
    ig_cfg = config.get("instagram", {})
    fatos = carregar_poco()
    uso = carregar_uso()
    uso_cartoes = escalar.carregar_uso()
    hoje = datetime.now(timezone.utc).date()

    criados = []
    for d in range(a.dias + 1):
        quando = hoje + timedelta(days=d)
        pasta = FILA / quando.isoformat()
        if (pasta / "pacote.json").exists():
            print(f"{quando}: pacote já existe")
            continue
        pacote = montar_pacote(quando, fatos, uso, cfg, ig_cfg, uso_cartoes)
        if len(pacote["shorts"]) < cfg["shorts_por_dia"]:
            print(f"! {quando}: só {len(pacote['shorts'])} Shorts — POÇO SECO")
        if a.dry_run:
            print(f"[dry-run] {quando}: "
                  f"{len(pacote['shorts'])} Shorts, "
                  f"{len(pacote['longo']['fatos'])} fatos no longo "
                  f"(~{pacote['longo']['minutos_estimados']} min), "
                  f"{len(pacote['cartoes'])} cartões")
            continue
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "pacote.json").write_text(
            json.dumps(pacote, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
        criados.append(quando.isoformat())
        print(f"{quando}: pacote criado "
              f"({len(pacote['shorts'])} Shorts, "
              f"{len(pacote['longo']['fatos'])} fatos no longo, "
              f"{len(pacote['cartoes'])} cartões)")

    if not a.dry_run and criados:
        gravar_uso(uso)
        escalar.gravar_uso(uso_cartoes)

    restantes = len(livres(fatos, uso, hoje))
    print(f"poço: {restantes} fatos livres de {len(fatos)}")
    if restantes < cfg["shorts_por_dia"] * 3:
        print("! POÇO QUASE SECO — o vigia vai abrir issue")


if __name__ == "__main__":
    main()
