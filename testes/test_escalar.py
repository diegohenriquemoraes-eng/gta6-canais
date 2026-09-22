# -*- coding: utf-8 -*-
"""As REGRAS DE REPETIÇÃO do formato G — o que separa este projeto do ViceScale.

A ferramenta original fabrica 10 vídeos × 5 frases = 50 posts, o mesmo clipe
saindo cinco vezes. Isso é a definição literal de conteúdo repetitivo na
atualização de originalidade do Instagram de 30/04/2026. Estes testes são a
garantia de que a regra não se perde numa refatoração.
"""

import json
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from produzir import escalar  # noqa: E402

HOJE = date(2026, 10, 1)
# A cadência real, não um número solto: o teste tem de falhar quando a config
# pedir mais cartões do que o acervo de cenas comporta.
POR_DIA = json.loads((RAIZ / "publicador" / "config.json").read_text(
    encoding="utf-8"))["instagram"]["cartoes_por_dia"]


def uso_vazio():
    return {"cenas": {}, "frases": {}, "pares": []}


def simular(dias: int, por_dia: int = POR_DIA):
    """Roda `dias` dias seguidos e devolve a lista de filas."""
    uso = uso_vazio()
    return [escalar.montar_fila(por_dia, HOJE + timedelta(days=d), uso)
            for d in range(dias)]


class TestUmaFrasePorCenaPorSemana(unittest.TestCase):
    def test_a_cena_nao_volta_dentro_de_sete_dias(self):
        filas = simular(7)
        visto: dict[str, date] = {}
        for d, fila in enumerate(filas):
            dia = HOJE + timedelta(days=d)
            for c in fila:
                cid = c["cena"]["id"]
                if cid in visto:
                    with self.subTest(cena=cid):
                        self.assertGreaterEqual(
                            (dia - visto[cid]).days, escalar.DIAS_REPETICAO,
                            f"{cid} repetiu em {(dia - visto[cid]).days} dias")
                visto[cid] = dia

    def test_a_mesma_cena_nao_sai_duas_vezes_no_mesmo_dia(self):
        fila = escalar.montar_fila(POR_DIA, HOJE, uso_vazio())
        ids = [c["cena"]["id"] for c in fila]
        self.assertEqual(len(ids), len(set(ids)))

    def test_o_par_cena_mais_frase_nao_repete_em_sete_dias(self):
        """A trava de 7 dias é da CENA e do PAR, não da frase sozinha: são 40
        frases-base para 35 cartões por semana."""
        visto: dict[tuple[str, str], date] = {}
        for d, fila in enumerate(simular(7)):
            dia = HOJE + timedelta(days=d)
            for c in fila:
                par = (c["cena"]["id"], c["frase_base"])
                if par in visto:
                    with self.subTest(par=par):
                        self.assertGreaterEqual((dia - visto[par]).days,
                                                escalar.DIAS_REPETICAO)
                visto[par] = dia

    def test_a_frase_nao_repete_no_mesmo_dia(self):
        for fila in simular(7):
            frases = [c["frase_base"] for c in fila]
            self.assertEqual(len(frases), len(set(frases)))


class TestSequenciaDoDia(unittest.TestCase):
    def test_nunca_duas_cenas_do_mesmo_minuto_seguidas(self):
        for fila in simular(5):
            minutos = [escalar._minuto(c["cena"]) for c in fila]
            for a, b in zip(minutos, minutos[1:]):
                with self.subTest(par=(a, b)):
                    self.assertNotEqual(a, b)

    def test_identidade_no_maximo_uma_a_cada_quatro(self):
        for fila in simular(5):
            cats = [c["categoria"] for c in fila]
            for i in range(len(cats)):
                janela = cats[i:i + escalar.MAX_IDENTIDADE_EM]
                with self.subTest(janela=janela):
                    self.assertLessEqual(janela.count("identidade"), 1)

    def test_contagem_no_maximo_duas_por_dia(self):
        for fila in simular(5):
            n = sum(1 for c in fila if c["categoria"] == "contagem")
            self.assertLessEqual(n, escalar.MAX_CONTAGEM_DIA)

    def test_os_tres_layouts_giram(self):
        fila = escalar.montar_fila(POR_DIA, HOJE, uso_vazio())
        self.assertEqual(set(c["layout"] for c in fila), {1, 2, 3})


class TestConteudoDoCartao(unittest.TestCase):
    def test_toda_frase_vem_do_arquivo_de_frases(self):
        frases = escalar.carregar_frases()
        todas = {f for lista in frases.values() for f in lista}
        for fila in simular(3):
            for c in fila:
                with self.subTest(frase=c["frase_base"]):
                    self.assertIn(c["frase_base"], todas)

    def test_o_placeholder_da_contagem_e_substituido(self):
        for fila in simular(3):
            for c in fila:
                with self.subTest(frase=c["frase"]):
                    self.assertNotIn("{N}", c["frase"])

    def test_depois_do_lancamento_nao_ha_contagem(self):
        fila = escalar.montar_fila(POR_DIA, date(2026, 12, 1), uso_vazio())
        self.assertNotIn("contagem", [c["categoria"] for c in fila])

    def test_toda_cena_da_fila_tem_descricao_e_licenca(self):
        for fila in simular(3):
            for c in fila:
                with self.subTest(cena=c["cena"]["id"]):
                    self.assertTrue(c["cena"]["descricao"])
                    self.assertTrue(c["cena"]["licenca"])

    def test_cena_indisponivel_no_runner_fica_de_fora(self):
        """O Extended Look tem restrição de idade e o runner não o baixa."""
        for fila in simular(3):
            for c in fila:
                with self.subTest(cena=c["cena"]["id"]):
                    self.assertFalse(c["cena"].get("no_runner"))


if __name__ == "__main__":
    unittest.main()
