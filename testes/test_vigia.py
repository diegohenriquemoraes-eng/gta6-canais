# -*- coding: utf-8 -*-
"""O VIGIA: o alarme que faltava e os que já existiam.

O caso central é o de 26/08 a 02/09/2026 no motor bíblico: o canal devia 2
Shorts/dia e publicou 1 durante sete dias. Nenhum alarme tocou, porque o vigia
media SILÊNCIO — e um canal que publica 1 de 2 nunca fica calado.
"""

import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from produzir import vigia  # noqa: E402

UTC = timezone.utc


def _estado(shorts_por_dia_feitos: int, horas_desde_o_ultimo: float = 1.0):
    agora = datetime.now(UTC)
    pubs = []
    for d in range(1, vigia.DIAS_FECHADOS + 1):
        dia = (agora - timedelta(days=d)).date().isoformat()
        for n in range(shorts_por_dia_feitos):
            pubs.append({"item": f"short-{n + 1}", "video_id": f"v{d}{n}",
                         "em": f"{dia}T1{n}:00:00+00:00"})
    return {"canais": {"gta": {
        "publicados": pubs,
        "ultimo_short": (agora - timedelta(hours=horas_desde_o_ultimo)
                         ).isoformat(timespec="seconds"),
        "ultimo_longo": None,
        "shorts_dia": {"data": "", "n": 0},
        "longos_dia": {"data": "", "n": 0}}}}


class TestPublicouMenos(unittest.TestCase):
    def _rodar(self, estado):
        with mock.patch.object(vigia, "_carregar") as carregar:
            def falso(p, default):
                if p == vigia.STATE:
                    return estado
                if p == vigia.CONFIG:
                    return json.loads(
                        vigia.CONFIG.read_text(encoding="utf-8"))
                return default
            carregar.side_effect = falso
            return vigia.alarmes()

    def test_alarme_quando_publica_menos_que_a_config(self):
        titulos = [t for t, _ in self._rodar(_estado(1))]
        self.assertTrue(any("publicou menos" in t for t in titulos),
                        f"nenhum alarme de 'publicou menos' em {titulos}")

    def test_sem_alarme_quando_a_cota_do_dia_fecha(self):
        cfg = json.loads(vigia.CONFIG.read_text(encoding="utf-8"))
        n = cfg["canais"]["gta"]["shorts_por_dia"]
        titulos = [t for t, _ in self._rodar(_estado(n))]
        self.assertFalse(any("publicou menos" in t for t in titulos))

    def test_alarme_de_silencio(self):
        titulos = [t for t, _ in self._rodar(_estado(3, horas_desde_o_ultimo=20))]
        self.assertTrue(any("silêncio" in t for t in titulos))

    def test_sem_alarme_de_silencio_quando_acabou_de_publicar(self):
        titulos = [t for t, _ in self._rodar(_estado(3, horas_desde_o_ultimo=2))]
        self.assertFalse(any("silêncio" in t and "YouTube" in t
                             for t in titulos))


class TestAlarmesDeEstoque(unittest.TestCase):
    def test_poco_cheio_nao_dispara(self):
        titulos = [t for t, _ in vigia.alarmes()]
        self.assertFalse(any("Poço de fatos quase seco" in t for t in titulos),
                         "o poço tem 150 fatos; não devia alarmar")

    def test_cenas_aptas_suficientes(self):
        titulos = [t for t, _ in vigia.alarmes()]
        self.assertFalse(any("Cenas aptas" in t for t in titulos))


if __name__ == "__main__":
    unittest.main()
