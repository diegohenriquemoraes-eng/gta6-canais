# -*- coding: utf-8 -*-
"""Testes da AGENDA — quem decide o que sai em cada execução do cron.

Os dois primeiros casos são defeitos REAIS do motor bíblico, transplantados
para cá como teste antes de acontecerem de novo:

- o gap do longo calava o canal inteiro (26/08 a 02/09/2026: o ES publicou 9
  Shorts de 16 e nenhum alarme tocou);
- o gap entre Shorts era veto, e o cron do GitHub coalesce — entrega ~6
  execuções por dia, não 24.

Os outros são novos e cobrem a contagem regressiva e a troca pós-19/11.

Rodar: python -m unittest discover -s testes
"""

import json
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from nucleo import canal  # noqa: E402
from publicador.publicar import (PISO_GAP_MIN, decidir,  # noqa: E402
                                 decidir_instagram, gap_efetivo,
                                 pos_lancamento, tipo_de_short)

UTC = timezone.utc
CFG = {"hora_longo_utc": 21, "longos_por_dia": 1, "shorts_por_dia": 3,
       "hora_short_utc": 10, "gap_shorts_min": 300,
       "lancamento": "2026-11-19",
       "fase_pos_lancamento": {"shorts": ["E", "E", "C"], "longos": ["guia"]}}
IG = {"cartoes_por_dia": 5, "hora_cartao_utc": 11, "gap_cartoes_min": 150,
      "stories_por_dia": 1, "hora_story_utc": 23}

# As execuções que o cron REALMENTE entrega, medidas na API do repo do motor
# bíblico em 03/09/2026: ~6 por dia, em intervalos de 2 a 7 horas.
EXECUCOES_REAIS = ["01:59", "06:54", "11:51", "15:37", "19:05", "22:08"]


def estado(dia="", n_longos=0, n_shorts=0, ultimo_longo=None,
           ultimo_short=None):
    return {"publicados": [], "ultimo_short": ultimo_short,
            "ultimo_longo": ultimo_longo,
            "shorts_dia": {"data": dia, "n": n_shorts},
            "longos_dia": {"data": dia, "n": n_longos}}


class TestGapNaoCalaOCanal(unittest.TestCase):
    def test_short_sai_mesmo_com_longo_devido_mais_tarde(self):
        agora = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
        self.assertEqual(decidir(CFG, estado("2026-10-01"), agora), "short")

    def test_longo_tem_prioridade_na_sua_hora(self):
        agora = datetime(2026, 10, 1, 21, 5, tzinfo=UTC)
        ec = estado("2026-10-01", n_shorts=3,
                    ultimo_short="2026-10-01T19:00:00+00:00")
        self.assertEqual(decidir(CFG, ec, agora), "longo")

    def test_gap_do_longo_nao_devolve_none(self):
        """O defeito de 03/09: com o longo travado pelo gap, a execução tem de
        cair para a avaliação do Short, nunca devolver None."""
        cfg = {**CFG, "longos_por_dia": 2, "gap_longos_min": 480,
               "hora_longo_utc": 0, "hora_short_utc": 0}
        agora = datetime(2026, 10, 1, 6, 54, tzinfo=UTC)
        ec = estado("2026-10-01", n_longos=1,
                    ultimo_longo="2026-10-01T01:59:00+00:00")
        self.assertEqual(decidir(cfg, ec, agora), "short")

    def test_nada_devido_com_o_dia_completo(self):
        agora = datetime(2026, 10, 1, 23, 30, tzinfo=UTC)
        ec = estado("2026-10-01", n_longos=1, n_shorts=3,
                    ultimo_short="2026-10-01T22:00:00+00:00")
        self.assertIsNone(decidir(CFG, ec, agora))

    def test_respeita_hora_short_utc(self):
        ec = estado("2026-10-01")
        self.assertIsNone(decidir(CFG, ec, datetime(2026, 10, 1, 9, 30,
                                                    tzinfo=UTC)))


class TestGapEfetivo(unittest.TestCase):
    def test_gap_cheio_com_o_dia_longo(self):
        self.assertEqual(gap_efetivo(300, 2, datetime(2026, 10, 1, 9, 0,
                                                      tzinfo=UTC)), 300)

    def test_encolhe_quando_o_dia_acaba(self):
        agora = datetime(2026, 10, 1, 22, 8, tzinfo=UTC)   # restam 112 min
        self.assertEqual(gap_efetivo(300, 1, agora), 112)

    def test_nunca_abaixo_do_piso(self):
        agora = datetime(2026, 10, 1, 23, 40, tzinfo=UTC)
        self.assertEqual(gap_efetivo(300, 2, agora), PISO_GAP_MIN)


class TestEsteiraFechaODia(unittest.TestCase):
    """Com as execuções que o cron entrega de verdade, o dia fecha?"""

    def _replay(self, cfg, horas, dias=3):
        ec = estado()
        saiu = {}
        for d in range(dias):
            base = datetime(2026, 10, 1, tzinfo=UTC) + timedelta(days=d)
            for hhmm in horas:
                h, m = (int(x) for x in hhmm.split(":"))
                agora = base.replace(hour=h, minute=m)
                hoje = agora.date().isoformat()
                tipo = decidir(cfg, ec, agora)
                if tipo is None:
                    continue
                chave = "longos_dia" if tipo == "longo" else "shorts_dia"
                if ec[chave]["data"] != hoje:
                    ec[chave] = {"data": hoje, "n": 0}
                ec[chave]["n"] += 1
                ec["ultimo_longo" if tipo == "longo" else "ultimo_short"] = \
                    agora.isoformat()
                saiu.setdefault(hoje, {"longo": 0, "short": 0})[tipo] += 1
        return saiu

    def test_config_real_fecha_o_dia(self):
        cfg = json.loads((RAIZ / "publicador" / "config.json").read_text(
            encoding="utf-8"))["canais"]["gta"]
        saiu = self._replay(cfg, EXECUCOES_REAIS)
        ultimo = list(saiu)[-1]
        self.assertEqual(saiu[ultimo]["short"], cfg["shorts_por_dia"],
                         "os Shorts não fecharam com o cron real")
        if cfg.get("hora_longo_utc") is not None:
            self.assertEqual(saiu[ultimo]["longo"],
                             cfg.get("longos_por_dia", 1),
                             "o longo não saiu com o cron real")


class TestContagemRegressiva(unittest.TestCase):
    def test_dias_batem_com_a_data_do_lancamento(self):
        self.assertEqual(canal.dias_para_lancamento(date(2026, 11, 18)), 1)
        self.assertEqual(canal.dias_para_lancamento(date(2026, 11, 19)), 0)
        self.assertEqual(canal.dias_para_lancamento(date(2026, 9, 22)), 58)

    def test_n_menor_ou_igual_a_zero_desliga_o_formato_A(self):
        from produzir import reabastecer as R
        fatos = R.carregar_poco()
        pac = R.montar_pacote(date(2026, 11, 20), fatos, {}, CFG, IG,
                              {"cenas": {}, "frases": {}, "pares": []})
        self.assertNotIn("A", [s["formato"] for s in pac["shorts"]],
                         "formato A (contagem) continuou depois do lançamento")

    def test_a_contagem_entra_na_narracao_antes_do_lancamento(self):
        from nucleo import fabrica
        fato = {"formato": "A", "narracao": "Teste.", "gancho": "g"}
        self.assertTrue(fabrica.narracao_do_fato(fato, 58).startswith("Faltam 58"))
        self.assertEqual(fabrica.narracao_do_fato(fato, 0), "Teste.")


class TestTrocaPosLancamento(unittest.TestCase):
    def test_antes_do_lancamento_segue_o_poco(self):
        pacote = {"shorts": [{"formato": "B"}, {"formato": "A"}, {"formato": "B"}]}
        self.assertEqual(tipo_de_short(CFG, pacote, 1, date(2026, 10, 1)), "A")
        self.assertFalse(pos_lancamento(CFG, date(2026, 11, 18)))

    def test_depois_do_lancamento_troca_para_E(self):
        pacote = {"shorts": [{"formato": "B", "credito_cc": "Canal X"},
                             {"formato": "B", "credito_cc": "Canal X"},
                             {"formato": "B"}]}
        self.assertTrue(pos_lancamento(CFG, date(2026, 11, 19)))
        self.assertEqual(tipo_de_short(CFG, pacote, 0, date(2026, 11, 19)), "E")

    def test_sem_cena_cc_cai_para_B(self):
        """`colher_cc.py` ainda não entregou nada: publica trailer, não para."""
        pacote = {"shorts": [{"formato": "B"}]}
        self.assertEqual(tipo_de_short(CFG, pacote, 0, date(2026, 11, 20)), "B")


class TestAgendaDoInstagram(unittest.TestCase):
    def _er(self, dia="", n=0, ultimo=None, story=0):
        return {"publicados": [], "ultimo": ultimo,
                "dia": {"data": dia, "n": n},
                "story_dia": {"data": dia, "n": story}}

    def test_cartao_espera_a_hora(self):
        self.assertIsNone(decidir_instagram(
            IG, self._er("2026-10-01"), datetime(2026, 10, 1, 9, 0, tzinfo=UTC)))

    def test_cartao_sai_na_hora(self):
        self.assertEqual(decidir_instagram(
            IG, self._er("2026-10-01"), datetime(2026, 10, 1, 11, 5, tzinfo=UTC)),
            "cartao")

    def test_story_so_depois_dos_cartoes(self):
        er = self._er("2026-10-01", n=5, ultimo="2026-10-01T22:00:00+00:00")
        self.assertEqual(decidir_instagram(
            IG, er, datetime(2026, 10, 1, 23, 10, tzinfo=UTC)), "story")

    def test_um_story_por_dia(self):
        er = self._er("2026-10-01", n=5, ultimo="2026-10-01T22:00:00+00:00",
                      story=1)
        self.assertIsNone(decidir_instagram(
            IG, er, datetime(2026, 10, 1, 23, 40, tzinfo=UTC)))


if __name__ == "__main__":
    unittest.main()
