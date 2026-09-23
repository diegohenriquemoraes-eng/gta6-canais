# -*- coding: utf-8 -*-
"""O espelho do TikTok — as regras que, quebradas, publicam duas vezes.

O espelho é a única peça que republica um arquivo que JÁ está no ar em outra
rede. Isso muda o que dá errado: aqui o prejuízo não é ficar mudo, é postar o
mesmo vídeo duas vezes na mesma conta — que é exatamente o que o TikTok lê como
spam e o que fez o @vendanaobra pagar caro em 20/09/2026.
"""

import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from publicador import tiktok  # noqa: E402

CFG = {"ativo": True, "espelhos_por_dia": 3, "atraso_min": 30,
       "hashtags_fixas": ["gta6", "gtavi", "vicecity"],
       "conta_id": "conta1"}
AGORA = datetime(2026, 9, 23, 18, 0, tzinfo=timezone.utc)


def cartao(cid: str, minutos_atras: int, url="https://x/y.mp4") -> dict:
    return {"id": cid, "frase": "frase", "url_midia": url,
            "em": (AGORA - timedelta(minutes=minutos_atras)).isoformat()}


def estado(publicados=(), n_hoje=0) -> dict:
    return {"publicados": [{"cartao": c} for c in publicados],
            "dia": {"data": AGORA.date().isoformat(), "n": n_hoje}}


class TestQuandoEspelhar(unittest.TestCase):
    def test_cartao_quente_espera(self):
        """Publicar nas duas redes no mesmo minuto é assinatura de automação."""
        er = {"publicados": [cartao("c1", minutos_atras=5)]}
        self.assertIsNone(tiktok.a_espelhar(CFG, er, estado(), AGORA))

    def test_cartao_frio_vai(self):
        er = {"publicados": [cartao("c1", minutos_atras=45)]}
        item = tiktok.a_espelhar(CFG, er, estado(), AGORA)
        self.assertEqual(item["id"], "c1")

    def test_nao_espelha_duas_vezes(self):
        er = {"publicados": [cartao("c1", 60), cartao("c2", 50)]}
        item = tiktok.a_espelhar(CFG, er, estado(publicados=["c1"]), AGORA)
        self.assertEqual(item["id"], "c2")

    def test_teto_do_dia(self):
        """3/dia é leitura de spam do TikTok, não cota."""
        er = {"publicados": [cartao(f"c{i}", 60) for i in range(5)]}
        self.assertIsNone(
            tiktok.a_espelhar(CFG, er, estado(n_hoje=3), AGORA))

    def test_teto_de_ontem_nao_conta_hoje(self):
        er = {"publicados": [cartao("c1", 60)]}
        et = {"publicados": [], "dia": {"data": "2026-09-22", "n": 3}}
        self.assertIsNotNone(tiktok.a_espelhar(CFG, er, et, AGORA))

    def test_cartao_sem_url_e_pulado(self):
        """Sem MP4 hospedado não há o que espelhar — e não se renderiza de novo."""
        er = {"publicados": [cartao("c1", 60, url=""), cartao("c2", 60)]}
        item = tiktok.a_espelhar(CFG, er, estado(), AGORA)
        self.assertEqual(item["id"], "c2")


class TestLegenda(unittest.TestCase):
    def test_tira_url_e_arroba(self):
        """URL em texto é penalizada no TikTok; @ do Instagram viraria menção
        a um perfil qualquer de lá, que não é o nosso."""
        saida = tiktok.legenda_do_cartao(
            "Olha isso @rumoavicecity\nhttps://s.shopee.com.br/abc\n#gta6", CFG)
        self.assertNotIn("http", saida)
        self.assertNotIn("@", saida)
        self.assertIn("rumoavicecity", saida)

    def test_hashtags_fixas_primeiro_e_sem_repetir(self):
        saida = tiktok.legenda_do_cartao("texto #gta6 #vicecity #outra", CFG)
        tags = [t for t in saida.split() if t.startswith("#")]
        self.assertEqual(tags[:3], ["#gta6", "#gtavi", "#vicecity"])
        self.assertEqual(len(tags), len(set(tags)))
        self.assertLessEqual(len(tags), tiktok.MAX_HASHTAGS)

    def test_corpo_cortado_em_palavra_inteira(self):
        saida = tiktok.legenda_do_cartao("palavra " * 400, CFG)
        corpo = saida.split("\n\n")[0]
        self.assertLessEqual(len(corpo), tiktok.MAX_LEGENDA)
        self.assertTrue(corpo.endswith("…"))


class TestRespostaDoZernio(unittest.TestCase):
    """207 não é falha — e tratá-lo como falha duplica o post.

    O teto do TikTok no Zernio é de 15 numa janela MÓVEL de 24 h, não por dia
    UTC. Quando ela fecha, o Zernio responde 207 com o post enfileirado e
    publica sozinho depois. Em 20/09/2026, no @vendanaobra, ler isso como erro
    levou a reenviar o mesmo vídeo.
    """

    def _com_resposta(self, status, corpo):
        original = tiktok._zernio
        tiktok._zernio = lambda m, c, b=None: (status, corpo)
        self.addCleanup(lambda: setattr(tiktok, "_zernio", original))

    def test_207_enfileirado_conta_como_sucesso(self):
        self._com_resposta(207, {"post": {"_id": "p1", "status": "pending",
                                          "platforms": [{"platform": "tiktok"}]}})
        ok, info = tiktok.publicar({"_id": "c"}, "u", "l")
        self.assertTrue(ok)
        self.assertEqual(info["estado"], "pending")

    def test_failed_e_falha(self):
        self._com_resposta(200, {"post": {"_id": "p1", "status": "failed",
                                          "platforms": []}})
        ok, _ = tiktok.publicar({"_id": "c"}, "u", "l")
        self.assertFalse(ok)

    def test_declaracao_legal_vai_em_todo_post(self):
        """A auditoria do TikTok exige essa declaração por post; sem ela o
        Zernio recusa e o vídeo não sai público."""
        vistos = {}

        def falso(metodo, caminho, corpo=None):
            vistos.update(corpo or {})
            return 201, {"post": {"_id": "p", "status": "published",
                                  "platforms": []}}
        original = tiktok._zernio
        tiktok._zernio = falso
        self.addCleanup(lambda: setattr(tiktok, "_zernio", original))
        tiktok.publicar({"_id": "c"}, "u", "l")
        s = vistos["tiktokSettings"]
        self.assertTrue(s["content_preview_confirmed"])
        self.assertTrue(s["express_consent_given"])
        self.assertEqual(s["privacy_level"], "PUBLIC_TO_EVERYONE")


class TestConfig(unittest.TestCase):
    def test_a_conta_esta_travada_no_config(self):
        """Sem `conta_id`, uma segunda conta ligada no Zernio publicaria no
        perfil errado — o mesmo motivo do `channel_id` conferido no YouTube."""
        cfg = json.loads((RAIZ / "publicador" / "config.json")
                         .read_text(encoding="utf-8")).get("tiktok", {})
        if not cfg.get("ativo"):
            self.skipTest("TikTok desligado")
        self.assertTrue(cfg.get("conta_id"), "tiktok.conta_id vazio")
        self.assertTrue(cfg.get("conta"), "tiktok.conta (nome) vazio")


if __name__ == "__main__":
    unittest.main()
