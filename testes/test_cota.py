# -*- coding: utf-8 -*-
"""Orçamento de COTA da YouTube Data API.

10.000 unidades por dia no projeto Cloud. Estourar não dá erro visível na
hora: o canal simplesmente para de publicar até a virada do dia UTC.

Este teste transforma em código a conta que, no motor bíblico, vivia em prosa
no CLAUDE.md — e que estava ERRADA (a conta de 25/08/2026 prometia margem de
retry ao canal ES e não incluía o workflow Realinhar nem a legenda e a
playlist dos dois longos).
"""

import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# Custos oficiais (developers.google.com/youtube/v3/determine_quota_cost).
UPLOAD = 1600
UPDATE = 50             # videos.update — tornar público
THUMBNAIL = 50          # thumbnails.set — só no longo
CAPTION = 400           # captions.insert — a faixa .srt do longo
PLAYLIST_INSERT = 50    # playlistItems.insert — só no longo
CHANNELS_LIST = 1       # validação do channel_id do token, por publicação
JA_PUBLICADO = 2        # guarda contra duplicata (channels + playlistItems)

# esperar_processamento chama videos.list de 15 em 15 s, 1 unidade cada
POLL_SHORT = 12
POLL_LONGO = 25

LIMITE = 10_000
REALINHAR_DIARIO = 10 * UPDATE     # workflow Realinhar, `--limite 10`

# Canais em que o dia normal cabe, mas um reenvio não. Vazio de propósito: se
# um dia entrar alguém aqui, que seja decisão registrada, não surpresa.
SEM_MARGEM_DE_RETRY: dict[str, str] = {}


def custo_short() -> int:
    return UPLOAD + UPDATE + POLL_SHORT + CHANNELS_LIST + JA_PUBLICADO


def custo_longo() -> int:
    return (UPLOAD + UPDATE + THUMBNAIL + CAPTION + PLAYLIST_INSERT
            + POLL_LONGO + CHANNELS_LIST + JA_PUBLICADO)


def custo_dia(cfg: dict) -> int:
    shorts = cfg.get("shorts_por_dia", 0) * custo_short()
    longos = (cfg.get("longos_por_dia", 1) * custo_longo()
              if cfg.get("hora_longo_utc") is not None else 0)
    return shorts + longos + REALINHAR_DIARIO


class TestOrcamento(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(
            (RAIZ / "publicador" / "config.json").read_text(encoding="utf-8"))

    def ativos(self):
        return [(k, c) for k, c in self.config["canais"].items()
                if c.get("ativo")]

    def test_o_dia_normal_cabe(self):
        for nome, cfg in self.ativos():
            with self.subTest(canal=nome):
                gasto = custo_dia(cfg)
                self.assertLessEqual(
                    gasto, LIMITE,
                    f"{nome}: {gasto} unidades num dia SEM nenhuma falha — o "
                    f"canal fica mudo até a virada do dia UTC.")

    def test_margem_para_um_reenvio(self):
        for nome, cfg in self.ativos():
            pior = custo_dia(cfg) + max(custo_short(), custo_longo())
            tem = pior <= LIMITE
            with self.subTest(canal=nome):
                if nome in SEM_MARGEM_DE_RETRY:
                    self.assertFalse(tem, f"{nome} ganhou margem: tirar de "
                                          f"SEM_MARGEM_DE_RETRY.")
                    continue
                self.assertTrue(
                    tem, f"{nome}: {custo_dia(cfg)} no dia normal e {pior} com "
                         f"um reenvio. Reduza a agenda ou registre o motivo em "
                         f"SEM_MARGEM_DE_RETRY.")

    def test_nunca_seis_uploads_por_dia(self):
        """Regra da casa: 6 uploads/dia só com aumento de cota aprovado."""
        for nome, cfg in self.ativos():
            n = cfg.get("shorts_por_dia", 0)
            if cfg.get("hora_longo_utc") is not None:
                n += cfg.get("longos_por_dia", 1)
            with self.subTest(canal=nome):
                self.assertLessEqual(n, 5, f"{nome}: {n} uploads por dia")

    def test_instagram_dentro_do_limite_da_graph_api(self):
        """A Graph API aceita 50 publicações por 24 h somando tudo."""
        ig = self.config.get("instagram", {})
        if not ig.get("ativo"):
            return
        total = ig.get("cartoes_por_dia", 0) + ig.get("stories_por_dia", 0)
        self.assertLessEqual(total, 25,
                             f"{total} publicações/dia no Instagram — o plano "
                             f"é 4-6 cartões + 1 story.")


if __name__ == "__main__":
    unittest.main()
