# -*- coding: utf-8 -*-
"""Baixa o material OFICIAL da Rockstar para marca/oficial/ (gitignorado).

Três vídeos do canal @rockstargames (ids conferidos em 22/09/2026 pelo próprio
yt-dlp, listando o canal) e a galeria de screenshots de rockstargames.com/VI.

Por que gitignorado e reobtido no runner: o repo é público e vídeo commitado
incharia o Git para sempre — a mesma regra que fez a fila do motor bíblico não
guardar MP4. O workflow chama este script com cache de Actions; em cache quente
ele não baixa nada.

⚠ A GALERIA não sai por script simples: `rockstargames.com/VI/media` monta as
imagens por JavaScript e devolve HTML sem `<img>`. Conferido em 22/09/2026.
Quando o script não consegue, ele **não falha**: registra a ausência e o render
cai no quadro extraído do trailer (e, em último caso, no gradiente da casa). A
via manual está em PENDENCIAS-DIEGO.md.

Uso:
    python produzir/baixar_oficial.py            # o que faltar
    python produzir/baixar_oficial.py --forcar   # tudo de novo
    python produzir/baixar_oficial.py --so-video trailer2
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

OFICIAL = RAIZ / "marca" / "oficial"
GALERIA = OFICIAL / "galeria"
PROVENIENCIA = RAIZ / "fontes" / "PROVENIENCIA.md"

# id, título oficial, data de publicação — para o registro de proveniência.
VIDEOS = {
    "trailer1": ("QdBZY2fkU-0", "Grand Theft Auto VI Trailer 1", "2023-12-04"),
    "trailer2": ("VQRLujxTm3c", "Grand Theft Auto VI Trailer 2", "2025-05-06"),
    "extended": ("tJbzMqJGH4k", "Grand Theft Auto VI: An Extended Look",
                 "2026-08-27"),
}

# 1080p basta: o cartão é 1080×1920 e o Short é 1080×1920. Baixar 4K triplica
# o tempo de download no runner sem mudar um pixel da saída.
FORMATO = "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b"

GALERIA_PAGINA = "https://www.rockstargames.com/VI/media"


def baixar_video(chave: str, forcar: bool = False) -> Path | None:
    vid, titulo, quando = VIDEOS[chave]
    destino = OFICIAL / f"{chave}.mp4"
    if destino.exists() and destino.stat().st_size > 1_000_000 and not forcar:
        print(f"{chave}: já está em {destino.name} "
              f"({destino.stat().st_size / 1e6:.0f} MB)")
        return destino
    OFICIAL.mkdir(parents=True, exist_ok=True)
    print(f"{chave}: baixando {titulo} ({vid})")
    r = subprocess.run(
        ["yt-dlp", "-f", FORMATO, "--merge-output-format", "mp4",
         "-o", str(destino), f"https://www.youtube.com/watch?v={vid}"],
        capture_output=True, text=True)
    if r.returncode != 0 or not destino.exists():
        print(f"! {chave} falhou: {r.stderr.strip()[-400:]}")
        return None
    return destino


def baixar_galeria() -> int:
    """Tenta a galeria oficial. Devolve quantas imagens ficaram em disco."""
    GALERIA.mkdir(parents=True, exist_ok=True)
    tem = len([p for p in GALERIA.iterdir()
               if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")])
    if tem:
        print(f"galeria: {tem} imagens já em disco")
        return tem
    try:
        import re

        import requests
        html = requests.get(GALERIA_PAGINA, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; gta6-canais/1.0)"}).text
        urls = sorted(set(re.findall(
            r"https://[^\"' ]+?\.(?:jpg|jpeg|png|webp)", html)))
        urls = [u for u in urls if "screenshot" in u.lower()
                or "/VI/" in u or "artwork" in u.lower()]
        for i, u in enumerate(urls[:120], start=1):
            nome = u.rsplit("/", 1)[-1].split("?")[0]
            alvo = GALERIA / f"{i:03d}-{nome}"
            try:
                alvo.write_bytes(requests.get(u, timeout=60).content)
            except Exception as exc:
                print(f"  ! {nome}: {exc}")
        tem = len(list(GALERIA.iterdir()))
    except Exception as exc:
        print(f"! galeria não pôde ser lida por script ({exc})")
    if not tem:
        print("! galeria VAZIA — a página monta por JavaScript. O render cai "
              "no quadro do trailer. Via manual em PENDENCIAS-DIEGO.md.")
    return tem


def escrever_proveniencia(baixados: dict[str, Path | None], n_galeria: int
                          ) -> None:
    PROVENIENCIA.parent.mkdir(parents=True, exist_ok=True)
    linhas = [
        "# PROVENIÊNCIA — de onde vem cada arquivo e sob que licença",
        "",
        "Gerado por `produzir/baixar_oficial.py`. `marca/oficial/` é",
        "gitignorado: o repo é público e vídeo commitado incharia o Git para",
        "sempre. O runner reobtém a cada rodada (com cache de Actions).",
        "",
        "## 1. Vídeos oficiais da Rockstar Games",
        "",
        "Material de **divulgação** publicado pela própria Rockstar no canal",
        "oficial @rockstargames. A \"Policy on posting copyrighted Rockstar",
        "Games material\" libera gameplay, machinima e clipes, inclusive com",
        "receita de anúncio de plataforma, e derruba material vazado ou",
        "pré-lançamento. Trailers e o Extended Look são o uso mais seguro que",
        "existe. **Nunca** o vazamento de 2022.",
        "",
        "| chave | vídeo | id | publicado | arquivo |",
        "|---|---|---|---|---|",
    ]
    for chave, (vid, titulo, quando) in VIDEOS.items():
        p = baixados.get(chave)
        estado = (f"`{p.name}` ({p.stat().st_size / 1e6:.0f} MB)" if p
                  else "**não baixado**")
        linhas.append(f"| `{chave}` | {titulo} | `{vid}` | {quando} | {estado} |")
    linhas += [
        "",
        "Rodapé obrigatório em todo vídeo que usa este material:",
        "`Material oficial © Rockstar Games` (queimado no pixel por",
        "`nucleo/legendas.py`, estilo `Marca`, e repetido na descrição).",
        "",
        "## 2. Galeria oficial (screenshots e artworks)",
        "",
        f"Origem: {GALERIA_PAGINA} — **{n_galeria} imagens** em disco.",
        "",
        "## 3. Gameplay em Creative Commons (formatos E e F, pós-19/11/2026)",
        "",
        "Colhido por `produzir/colher_cc.py` com `videoLicense=creativeCommon`",
        "na YouTube Data API. A CC BY autoriza a reutilização **com crédito**:",
        "o nome do canal de origem vai no rodapé do vídeo",
        "(`Gameplay: <canal> · CC BY`) e o link do original vai na descrição.",
        "Cada `videoId` usado ganha uma linha abaixo, com a licença lida da",
        "API na data da colheita. Se a API deixar de reportar",
        "`creativeCommon` para um id já usado, o vigia abre issue.",
        "",
        "| videoId | canal | colhido em | licença lida |",
        "|---|---|---|---|",
        "| (nenhum ainda — o pipeline E/F só liga em 19/11/2026) | | | |",
        "",
        "## 4. Fontes do repo",
        "",
        "`marca/fontes/Montserrat-Bold.ttf` e `BebasNeue-Regular.ttf` —",
        "SIL Open Font License, copiadas do repo `Palavra-Viva-3x`.",
        "",
        f"_Atualizado em {date.today().isoformat()}._",
        "",
    ]
    PROVENIENCIA.write_text("\n".join(linhas), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forcar", action="store_true")
    ap.add_argument("--so-video", choices=list(VIDEOS))
    ap.add_argument("--sem-galeria", action="store_true")
    a = ap.parse_args()

    alvos = [a.so_video] if a.so_video else list(VIDEOS)
    baixados = {c: baixar_video(c, a.forcar) for c in alvos}
    n = 0 if a.sem_galeria else baixar_galeria()
    escrever_proveniencia(baixados, n)
    faltou = [c for c, p in baixados.items() if p is None]
    print(json.dumps({"baixados": [c for c, p in baixados.items() if p],
                      "faltou": faltou, "galeria": n}, ensure_ascii=False))
    if faltou:
        raise SystemExit(f"não baixou: {', '.join(faltou)}")


if __name__ == "__main__":
    main()
