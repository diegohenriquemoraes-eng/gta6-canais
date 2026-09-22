# -*- coding: utf-8 -*-
"""Cenas do material oficial: detecção de corte, leitura do poço, extração.

Três trabalhos:

1. `detectar()` roda o `scdet` do ffmpeg num vídeo oficial e devolve os pontos
   de corte; `montar_cenas()` junta os cortes em cenas de 6 a 12 s (a janela
   que o formato G usa). É o que gera `conteudo/cenas.json`.
2. `quadro()` extrai um frame para servir de fundo do Short narrado. Aceita as
   três formas de `cena` do poço: `trailer2@0:31`, `galeria: Jason` e
   `cc:<videoId>@1:20`.
3. `arquivo_de()` resolve o MP4 de origem em `marca/oficial/` (gitignorado: o
   workflow o reconstrói com `produzir/baixar_oficial.py`).

Tudo aqui falha para `None`/`False` em vez de levantar: render que não acha a
cena cai no gradiente da casa, e isso é sempre melhor que uma publicação
perdida (regra herdada do motor bíblico).
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
OFICIAL = RAIZ / "marca" / "oficial"
GALERIA = OFICIAL / "galeria"
CC = RAIZ / "marca" / "cc"
CENAS_JSON = RAIZ / "conteudo" / "cenas.json"

# Os três vídeos oficiais. Os ids ficam em fontes/PROVENIENCIA.md; aqui só o
# nome do arquivo que `baixar_oficial.py` grava.
VIDEOS = {
    "trailer1": OFICIAL / "trailer1.mp4",
    "trailer2": OFICIAL / "trailer2.mp4",
    "extended": OFICIAL / "extended.mp4",
}

MIN_CENA_S = 6.0
MAX_CENA_S = 12.0


def carregar() -> list[dict]:
    if not CENAS_JSON.exists():
        return []
    return json.loads(CENAS_JSON.read_text(encoding="utf-8"))


def gravar(lista: list[dict]) -> None:
    CENAS_JSON.parent.mkdir(parents=True, exist_ok=True)
    CENAS_JSON.write_text(
        json.dumps(lista, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def segundos(txt: str) -> float:
    """'1:23' ou '0:07.5' ou '83' -> segundos."""
    txt = txt.strip()
    if ":" not in txt:
        return float(txt)
    m, s = txt.rsplit(":", 1)
    horas = 0.0
    if ":" in m:
        h, m = m.split(":", 1)
        horas = float(h) * 3600
    return horas + float(m) * 60 + float(s)


def arquivo_de(video_origem: str) -> Path | None:
    """`trailer2` -> marca/oficial/trailer2.mp4; `cc:ABC123` -> marca/cc/ABC123.mp4."""
    if video_origem.startswith("cc:"):
        p = CC / f"{video_origem[3:]}.mp4"
        return p if p.exists() else None
    p = VIDEOS.get(video_origem)
    return p if p and p.exists() else None


def arquivo_da_cena(cena: dict) -> Path | None:
    """O arquivo de origem de uma cena, seja clipe de vídeo ou foto da galeria.

    A galeria entrou como fonte de cartão em 22/09/2026, e por um motivo de
    aritmética: os trailers 1 e 2 somam 257 s, o que dá **28 cenas aptas**, e
    com a regra de uma frase por cena a cada 7 dias isso limita o Instagram a
    4 cartões/dia sem folga nenhuma. A galeria oficial tem 306 imagens. Foto
    parada com zoom lento é exatamente o que as páginas do nicho postam, e é
    material de divulgação da própria Rockstar.
    """
    if cena.get("video_origem") == "galeria":
        p = GALERIA / cena["arquivo"]
        return p if p.exists() else None
    return arquivo_de(cena.get("video_origem", ""))


def e_foto(cena: dict) -> bool:
    return cena.get("video_origem") == "galeria"


# Palavras que aparecem em quase todo nome de arquivo da galeria e não
# distinguem nada. Sem esta lista, `galeria: logo GTA VI` casava com
# `gta-plus-logo.jpg` e o Short de contagem regressiva saía com a marca do
# GTA+ ocupando a tela inteira (visto no primeiro render, 22/09/2026).
VAZIAS = {"gta", "vi", "logo", "the", "art", "cover", "official", "oficial",
          "imagem", "screenshot", "wallpaper", "jpg", "png"}


def _da_galeria(rotulo: str) -> Path | None:
    """Casa o rótulo do poço com um arquivo da galeria oficial.

    O poço escreve `galeria: Jason`; a galeria traz `jason-duval-07.jpg`. O
    casamento é por palavra DISTINTIVA (ver `VAZIAS`) e **exige pelo menos uma**
    — rótulo genérico não casa com nada, de propósito: quando não casa, quem
    resolve é `fundo_para_fato`, e no fim da fila está o gradiente da casa.
    Melhor liso e limpo que errado.
    """
    if not GALERIA.is_dir():
        return None
    termos = [t for t in re.split(r"\W+", rotulo.lower())
              if len(t) > 2 and t not in VAZIAS]
    if not termos:
        return None
    melhor, pontos = None, 0
    for p in sorted(GALERIA.iterdir()):
        if p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        nome = p.stem.lower()
        n = sum(1 for t in termos if t in nome)
        if n > pontos:
            melhor, pontos = p, n
    return melhor if pontos else None


def fundo_para_fato(fato: dict, destino: Path, seed: int = 0,
                    largura: int = 1080) -> bool:
    """A imagem de fundo de um Short, em ordem de preferência.

    1. a `cena` declarada no poço (quadro do trailer ou foto da galeria);
    2. uma foto da galeria que compartilhe TAG com o fato — é o que salva os
       fatos cujo rótulo de galeria é genérico ("logo GTA VI");
    3. qualquer foto da galeria, sorteada pelo seed do item;
    4. False — e aí o chamador usa o gradiente da casa.

    Sortear por seed no passo 3 não é preguiça: a alternativa é a MESMA imagem
    em todo Short sem cena declarada, que é a impressão digital de produção em
    massa que a política de conteúdo procura.
    """
    if quadro(fato.get("cena", ""), destino, largura):
        return True
    da_galeria = [c for c in carregar() if c.get("video_origem") == "galeria"]
    if not da_galeria:
        return False
    tags = set(fato.get("tags", []))
    combinam = [c for c in da_galeria if tags & set(c.get("tags", []))]
    escolha = (combinam or da_galeria)[seed % len(combinam or da_galeria)]
    return quadro(f"galeria: {Path(escolha['arquivo']).stem}", destino, largura)


def quadro(cena: str, destino: Path, largura: int = 1080) -> bool:
    """Extrai um quadro da cena para `destino`. False = não deu, use o gradiente."""
    cena = (cena or "").strip()
    if not cena:
        return False
    if cena.lower().startswith("galeria:"):
        origem = _da_galeria(cena.split(":", 1)[1])
        if not origem:
            return False
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(origem),
             "-vf", f"scale={largura}:-2", "-frames:v", "1", str(destino)],
            check=True)
        return destino.exists()

    if "@" not in cena:
        return False
    origem_nome, ts = cena.split("@", 1)
    mp4 = arquivo_de(origem_nome.strip())
    if not mp4:
        return False
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{segundos(ts):.2f}",
         "-i", str(mp4), "-vf", f"scale={largura}:-2", "-frames:v", "1",
         str(destino)],
        check=True)
    return destino.exists()


def duracao(mp4: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(mp4)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def detectar(mp4: Path, limiar: float = 0.10) -> list[float]:
    """Pontos de corte (segundos) via `scdet` do ffmpeg.

    Limiar 0.10 (= `threshold=10`, o padrão do filtro). Medido em 22/09/2026:
    com 0.35 o scdet achou **1 corte no Trailer 1 inteiro e nenhum no
    Trailer 2** — e o resultado eram "cenas" de 12 s fatiadas no relógio, sem
    relação com o corte de montagem. Com 0.10 os cortes reais aparecem.
    """
    out = subprocess.run(
        ["ffmpeg", "-i", str(mp4), "-vf", f"scdet=threshold={limiar * 100}",
         "-f", "null", "-"],
        capture_output=True, text=True)
    pontos = []
    for linha in out.stderr.splitlines():
        m = re.search(r"lavfi\.scd\.time:\s*([0-9.]+)", linha)
        if not m:
            m = re.search(r"scene score:.*time:([0-9.]+)", linha)
        if m:
            pontos.append(float(m.group(1)))
    return sorted(set(pontos))


def montar_cenas(origem: str, cortes: list[float], fim: float,
                 licenca: str = "rockstar_oficial",
                 credito: str = "") -> list[dict]:
    """Cortes -> cenas de MIN_CENA_S a MAX_CENA_S segundos.

    Planos curtos são AGRUPADOS até passar do mínimo (trailer de ação corta a
    cada 1-2 s; cena de 2 s no cartão não dá tempo de ler a frase) e planos
    longos são FATIADOS no máximo.
    """
    marcas = [0.0] + [c for c in cortes if 0 < c < fim] + [fim]
    cenas, ini = [], marcas[0]
    for m in marcas[1:]:
        if m - ini < MIN_CENA_S:
            continue
        while m - ini > MAX_CENA_S:
            cenas.append((ini, ini + MAX_CENA_S))
            ini += MAX_CENA_S
        if m - ini >= MIN_CENA_S:
            cenas.append((ini, m))
            ini = m
    saida = []
    for i, (a, b) in enumerate(cenas, start=1):
        saida.append({
            "id": f"{origem}-{i:03d}",
            "video_origem": origem,
            "inicio": round(a, 2),
            "fim": round(b, 2),
            "descricao": "",          # preenchida à mão/pelo poço; cena sem
            "tags": [],               # descrição NÃO entra no formato G
            "licenca": licenca,
            "credito": credito,
        })
    return saida


def aptas_para_cartao(lista: list[dict] | None = None) -> list[dict]:
    """Cenas que podem virar cartão: com descrição e com licença declarada."""
    return [c for c in (lista if lista is not None else carregar())
            if c.get("descricao") and c.get("licenca")
            and (c["licenca"] != "cc-by" or c.get("credito"))]
