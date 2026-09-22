# -*- coding: utf-8 -*-
"""O VIGIA — abre issue quando alguma coisa para de funcionar em silêncio.

Cada alarme aqui existe por causa de uma falha que ficou dias no ar sem
ninguém ver:

1. **silêncio** (`> 12 h sem publicar` numa rede ativa) — o alarme clássico;
2. **publicou MENOS do que a config manda** nos 3 dias UTC fechados. Este é o
   que faltava no motor bíblico: o vigia media silêncio, e um canal que
   publica 1 de 2 nunca fica calado. O ES entregou 9 Shorts de 16 em sete dias
   e ninguém viu (26/08 a 02/09/2026);
3. **poço seco ou quase** — o poço estoico foi de 14 temas a 1 sem aviso;
4. **fila sem pacote para amanhã** — reabastecedor falhou;
5. **cena aptas para cartão abaixo do consumo de uma semana** — o formato G
   para sem isso;
6. **licença CC mudou**: um `videoId` que já virou vídeo nosso deixou de ser
   `creativeCommon` na API. Aí o material tem de sair de circulação.

Uso:
    python produzir/vigia.py            # imprime o relatório
    python produzir/vigia.py --issues   # abre issue no GitHub (usa `gh`)
"""

from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from nucleo import cenas as C  # noqa: E402

CONFIG = RAIZ / "publicador" / "config.json"
STATE = RAIZ / "publicador" / "state.json"
FILA = RAIZ / "fila"
POCO = RAIZ / "conteudo" / "fatos"
USO = RAIZ / "conteudo" / "fatos_uso.json"

HORAS_DE_SILENCIO = 12
DIAS_FECHADOS = 3


def _carregar(p: Path, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def alarmes() -> list[tuple[str, str]]:
    """[(título, corpo)] — vazio significa que está tudo em ordem."""
    cfg = _carregar(CONFIG, {})
    state = _carregar(STATE, {})
    agora = datetime.now(timezone.utc)
    hoje = agora.date()
    saida: list[tuple[str, str]] = []

    cgta = cfg.get("canais", {}).get("gta", {})
    ec = state.get("canais", {}).get("gta", {})
    ig_cfg = cfg.get("instagram", {})
    er = state.get("redes", {}).get("instagram", {})

    # 1. silêncio
    for nome, ativo, ultimo in (
            ("YouTube", cgta.get("ativo"),
             max(filter(None, [ec.get("ultimo_short"), ec.get("ultimo_longo")]),
                 default=None)),
            ("Instagram", ig_cfg.get("ativo"), er.get("ultimo"))):
        if not ativo:
            continue
        if not ultimo:
            saida.append((f"{nome} nunca publicou",
                          f"O {nome} está ativo na config e o estado não tem "
                          f"nenhuma publicação. Falta token/secret? Ver "
                          f"PENDENCIAS-DIEGO.md."))
            continue
        horas = (agora - datetime.fromisoformat(ultimo)).total_seconds() / 3600
        if horas > HORAS_DE_SILENCIO:
            saida.append((f"{nome} em silêncio há {horas:.0f} h",
                          f"Último post: {ultimo}. Ver o workflow Publicar."))

    # 2. publicou menos do que a config manda
    fechados = [(hoje - timedelta(days=d)).isoformat()
                for d in range(1, DIAS_FECHADOS + 1)]
    def _conta(pubs, item, dia):
        return sum(1 for p in pubs
                   if p.get("em", "").startswith(dia)
                   and (p.get("item") == "longo") == (item == "longo"))
    for dia in fechados:
        if cgta.get("ativo"):
            devidos = cgta.get("shorts_por_dia", 0)
            feitos = _conta(ec.get("publicados", []), "short", dia)
            if feitos and feitos < devidos:
                saida.append((
                    f"YouTube publicou menos que a config em {dia}",
                    f"{feitos} de {devidos} Shorts. Este é o alarme que faltou "
                    f"entre 26/08 e 02/09/2026: silêncio não pega canal que "
                    f"publica 1 de 2."))
        if ig_cfg.get("ativo"):
            devidos = ig_cfg.get("cartoes_por_dia", 0)
            feitos = sum(1 for p in er.get("publicados", [])
                         if p.get("em", "").startswith(dia))
            if feitos and feitos < devidos:
                saida.append((f"Instagram publicou menos que a config em {dia}",
                              f"{feitos} de {devidos} cartões."))

    # 3. poço
    fatos = []
    for arq in sorted(glob.glob(str(POCO / "*.json"))):
        fatos += json.loads(Path(arq).read_text(encoding="utf-8"))
    uso = _carregar(USO, {})
    livres = [f for f in fatos
              if not f.get("revisar")
              and (f["id"] not in uso
                   or (hoje - date.fromisoformat(uso[f["id"]])).days >= 60)]
    por_dia = max(1, cgta.get("shorts_por_dia", 3))
    if len(livres) < por_dia * 3:
        saida.append((
            f"Poço de fatos quase seco: {len(livres)} livres",
            f"Dá para {len(livres) // por_dia} dias a {por_dia} Shorts/dia. "
            f"Escrever fatos novos em `conteudo/fatos/` no mesmo esquema "
            f"(gancho ≤ 10 palavras, narração 35-55, fonte, cena, tags) e "
            f"rodar `python produzir/reabastecer.py --dry-run`."))

    # 4. fila
    amanha = (hoje + timedelta(days=1)).isoformat()
    if not (FILA / amanha / "pacote.json").exists():
        saida.append((f"Fila sem pacote para {amanha}",
                      "O workflow Reabastecer falhou ou o poço secou."))

    # 5. cenas aptas
    aptas = [c for c in C.aptas_para_cartao() if not c.get("no_runner")]
    semana = ig_cfg.get("cartoes_por_dia", 5) * 7
    if ig_cfg.get("ativo") and len(aptas) < semana:
        saida.append((
            f"Cenas aptas para cartão abaixo de uma semana: {len(aptas)}",
            f"São {semana} cartões por semana e a regra é uma frase por cena "
            f"a cada 7 dias. Descrever mais cenas em "
            f"`conteudo/descricoes_cenas.json` (a folha de contato sai de "
            f"`python produzir/marcar_cenas.py --contato`)."))

    # 6. licença CC mudou
    colhidos = _carregar(RAIZ / "conteudo" / "cc_colhidos.json", {})
    if colhidos and (RAIZ / "credenciais" / "gta" / "token.json").exists():
        try:
            from nucleo import youtube_api
            yt = youtube_api.servico(RAIZ / "credenciais" / "gta")
            ids = list(colhidos)[:50]
            det = yt.videos().list(part="status", id=",".join(ids)
                                   ).execute().get("items", [])
            vistos = {v["id"]: v["status"].get("license") for v in det}
            for vid in ids:
                lic = vistos.get(vid)
                if lic is not None and lic != "creativeCommon":
                    saida.append((
                        f"Licença mudou em {vid}",
                        f"O vídeo {vid} ({colhidos[vid].get('canal')}) não é "
                        f"mais Creative Commons (agora: {lic}). Tirar as cenas "
                        f"`cc:{vid}` de `conteudo/cenas.json` e conferir o que "
                        f"já foi publicado com elas."))
        except Exception as exc:
            print(f"(não deu para conferir licenças: {exc})")

    return saida


def abrir_issue(titulo: str, corpo: str) -> None:
    existe = subprocess.run(
        ["gh", "issue", "list", "--state", "open", "--search",
         f"{titulo} in:title", "--json", "number", "-q", ".[].number"],
        capture_output=True, text=True).stdout.strip()
    if existe:
        print(f"(issue já aberta: {titulo})")
        return
    subprocess.run(["gh", "issue", "create", "--title", titulo,
                    "--body", corpo], check=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues", action="store_true")
    a = ap.parse_args()
    lista = alarmes()
    if not lista:
        print("tudo em ordem")
        return
    for titulo, corpo in lista:
        print(f"\n!! {titulo}\n   {corpo}")
        if a.issues:
            abrir_issue(titulo, corpo)


if __name__ == "__main__":
    main()
