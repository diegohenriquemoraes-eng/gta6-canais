# -*- coding: utf-8 -*-
"""Coerência da config, das ofertas e das regras que não podem ser quebradas.

Cada caso aqui protege uma regra que, se quebrada, não dá erro nenhum — só
custa dinheiro, alcance ou o canal inteiro:

- link de oferta sem `src=`: dois meses depois ninguém sabe se a oferta gerou
  um clique, e trocar de produto vira achismo;
- oferta sem `vigencia.ate`: a pré-venda morre em 20/11 e o canal continua
  mandando gente para uma página que não existe mais;
- divulgação de afiliado ausente: é exigência da Shopee e da lei;
- crédito da Rockstar fora do rodapé: é a linha que separa uso de material de
  divulgação de apropriação.
"""

import json
import sys
import unittest
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from nucleo import canal  # noqa: E402

CONFIG = RAIZ / "publicador" / "config.json"
OFERTAS = RAIZ / "conteudo" / "ofertas.json"

ORIGENS = {"yt_short", "yt_largo", "ig_bio", "ig_story", "tt_bio", "yt_bio"}


class TestConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_canal_ativo_tem_identidade_e_fila(self):
        for nome, c in self.cfg["canais"].items():
            if not c.get("ativo"):
                continue
            with self.subTest(canal=nome):
                self.assertTrue(c.get("handle"), "sem handle")
                self.assertTrue(c.get("titulo_canal"), "sem título")
                self.assertTrue((RAIZ / c.get("fila", "fila")).is_dir(),
                                "fila ausente")

    def test_a_data_do_lancamento_bate_em_todo_lugar(self):
        for nome, c in self.cfg["canais"].items():
            with self.subTest(canal=nome):
                self.assertEqual(date.fromisoformat(c["lancamento"]),
                                 canal.LANCAMENTO)

    def test_o_rodape_de_credito_nomeia_a_rockstar(self):
        self.assertIn("Rockstar Games", canal.CREDITO_ROCKSTAR)

    def test_credito_cc_nomeia_o_canal_e_a_licenca(self):
        t = canal.credito_cc("Canal X")
        self.assertIn("Canal X", t)
        self.assertIn("CC BY", t)

    def test_a_voz_nao_e_nenhuma_das_ja_usadas_na_casa(self):
        """Antonio é do psicologia-fria; Francisca é do Palavra Viva Diária.
        Duas contas da mesma casa com a mesma voz é assinatura de fábrica."""
        self.assertNotIn(canal.VOZ, ("pt-BR-AntonioNeural",
                                     "pt-BR-FranciscaNeural"))


class TestOfertas(unittest.TestCase):
    """Só roda de verdade quando `conteudo/ofertas.json` existe (passo da
    Shopee). Enquanto não existe, o teste passa vazio de propósito: o motor
    tem de rodar sem oferta nenhuma."""

    def ofertas(self):
        if not OFERTAS.exists():
            return []
        d = json.loads(OFERTAS.read_text(encoding="utf-8"))
        return d if isinstance(d, list) else d.get("ofertas", [])

    def test_todo_link_leva_rastreador(self):
        for o in self.ofertas():
            for origem, link in (o.get("links") or {}).items():
                with self.subTest(produto=o.get("produto"), origem=origem):
                    self.assertIn("src=", link,
                                  "sem src= não dá para saber de onde veio a "
                                  "venda")

    def test_origem_conhecida(self):
        for o in self.ofertas():
            for origem in (o.get("links") or {}):
                with self.subTest(origem=origem):
                    self.assertIn(origem, ORIGENS)

    def test_toda_oferta_tem_vigencia_ate(self):
        for o in self.ofertas():
            with self.subTest(produto=o.get("produto")):
                self.assertTrue((o.get("vigencia") or {}).get("ate"),
                                "a pré-venda morre em 20/11; sem `ate` o canal "
                                "segue apontando para página vencida")

    def test_o_bloco_de_oferta_se_declara_afiliado(self):
        from produzir.reabastecer import oferta_do_dia
        if not self.ofertas():
            return
        bloco = oferta_do_dia("yt_largo", date.today())
        if bloco:
            self.assertIn("afiliado", bloco.lower())

    def test_prioridade_e_numero(self):
        for o in self.ofertas():
            with self.subTest(produto=o.get("produto")):
                self.assertIsInstance(o.get("prioridade", 0), int)


if __name__ == "__main__":
    unittest.main()
