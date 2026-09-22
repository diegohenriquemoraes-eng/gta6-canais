"""Cache dos ids de playlist por formato do longo (publicador/playlists.json).

A playlist é o que transforma 1 vídeo assistido em SESSÃO: com o id em mãos, o
link do Short para o longo sai como watch?v=...&list=... (acabando um longo, o
YouTube emenda o próximo da lista) e a descrição do longo aponta a lista
completa. Descobrir o id pela API custa 1 unidade por página de playlists.list
em toda publicação — este arquivo versionado evita isso e, mais importante,
deixa o id disponível no RENDER (fabrica.py), que roda sem token.

Quem escreve: produzir/preencher_playlists.py (auditoria/backfill) e o
publicador, quando cria uma playlist nova. O arquivo entra no commit de estado
do workflow Publicar, como o state.json.
"""

from __future__ import annotations

import json
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parent.parent / "publicador" / "playlists.json"


def mapa() -> dict:
    if not ARQUIVO.exists():
        return {}
    return json.loads(ARQUIVO.read_text(encoding="utf-8"))


def obter(formato: str) -> str:
    return mapa().get(formato, "")


def definir(formato: str, playlist_id: str) -> None:
    m = mapa()
    if m.get(formato) == playlist_id:
        return
    m[formato] = playlist_id
    ARQUIVO.write_text(
        json.dumps(m, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
