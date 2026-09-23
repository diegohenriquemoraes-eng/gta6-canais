# -*- coding: utf-8 -*-
"""Integridade do POÇO de fatos, das frases e das cenas.

Existe porque toda armadilha deste projeto foi descoberta em produção, dias
depois. Um fato com gancho de 15 palavras não quebra nada: ele sai no ar, come
os 3 primeiros segundos do Short e a entrega morre sem nenhum erro no log.
"""

import glob
import json
import re
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from nucleo import cenas as C  # noqa: E402

POCO = RAIZ / "conteudo" / "fatos"
FRASES = RAIZ / "conteudo" / "frases.json"

MAX_GANCHO = 10
MIN_NARRACAO, MAX_NARRACAO = 35, 55
FORMATOS = {"A", "B", "C", "E"}
# CTA é trabalho do fabricante (`fabrica._cta`), não do poço: escrito no fato,
# ele sairia repetido no meio da narração de todo vídeo.
PROIBIDAS = ("clique", "link na bio", "link na descrição", "se inscreva")


def carregar() -> list[dict]:
    fatos = []
    for arq in sorted(glob.glob(str(POCO / "*.json"))):
        fatos += json.loads(Path(arq).read_text(encoding="utf-8"))
    return fatos


def _palavras(texto: str) -> set[str]:
    """Palavras de conteúdo: 5+ letras, sem acento, minúsculas."""
    import unicodedata
    sem = unicodedata.normalize("NFKD", texto.lower())
    sem = "".join(c for c in sem if not unicodedata.combining(c))
    return {p for p in re.findall(r"[a-z]{5,}", sem)}


def _todos_os_fatos() -> list[dict]:
    fatos = []
    for p in sorted((RAIZ / "conteudo" / "fatos").glob("*.json")):
        fatos += json.loads(p.read_text(encoding="utf-8"))
    return fatos


class TestPoco(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fatos = carregar()

    def test_existe_poco(self):
        self.assertGreaterEqual(len(self.fatos), 150,
                                "o poço nasceu com 150 fatos")

    def test_ids_unicos(self):
        ids = [f["id"] for f in self.fatos]
        repetidos = {i for i in ids if ids.count(i) > 1}
        self.assertFalse(repetidos, f"ids repetidos: {repetidos}")

    def test_formato_valido(self):
        for f in self.fatos:
            with self.subTest(id=f["id"]):
                self.assertIn(f.get("formato"), FORMATOS)

    def test_gancho_ate_dez_palavras(self):
        for f in self.fatos:
            with self.subTest(id=f["id"]):
                n = len(f["gancho"].split())
                self.assertTrue(0 < n <= MAX_GANCHO,
                                f"{n} palavras: “{f['gancho']}”")

    def test_narracao_entre_35_e_55_palavras(self):
        for f in self.fatos:
            with self.subTest(id=f["id"]):
                n = len(f["narracao"].split())
                self.assertTrue(MIN_NARRACAO <= n <= MAX_NARRACAO,
                                f"{n} palavras na narração de {f['id']}")

    def test_narracao_sem_cta(self):
        for f in self.fatos:
            texto = f["narracao"].lower()
            for p in PROIBIDAS:
                with self.subTest(id=f["id"], termo=p):
                    self.assertNotIn(p, texto)

    def test_toda_fonte_e_url(self):
        for f in self.fatos:
            with self.subTest(id=f["id"]):
                self.assertTrue(f.get("fonte", "").startswith("http"),
                                f"{f['id']} sem URL de fonte")

    def test_tem_tags(self):
        for f in self.fatos:
            with self.subTest(id=f["id"]):
                self.assertTrue(f.get("tags"), f"{f['id']} sem tag")

    def test_cena_no_formato_esperado(self):
        padrao = re.compile(r"^(trailer1|trailer2|extended|cc:[\w-]+)@[\d:.]+$")
        for f in self.fatos:
            cena = f.get("cena", "")
            with self.subTest(id=f["id"]):
                self.assertTrue(
                    cena.lower().startswith("galeria:") or padrao.match(cena),
                    f"{f['id']}: cena '{cena}' não é resolvível")

    def test_fato_em_revisao_nao_vai_ao_ar(self):
        """`revisar: true` é uma trava: o reabastecedor tem de ignorar o fato."""
        from produzir import reabastecer as R
        from datetime import date
        marcados = [f["id"] for f in self.fatos if f.get("revisar")]
        livres = {f["id"] for f in R.livres(self.fatos, {}, date(2026, 10, 1))}
        for i in marcados:
            with self.subTest(id=i):
                self.assertNotIn(i, livres)

    def test_f110_foi_resolvido(self):
        """O único fato que nasceu com `revisar: true` (número de vendas com
        fonte secundária). Fonte primária: balanço da Take-Two."""
        f110 = next(f for f in self.fatos if f["id"] == "F110")
        self.assertNotIn("revisar", f110)
        self.assertIn("take2games.com", f110["fonte"])


class TestFrases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(FRASES.read_text(encoding="utf-8"))
        cls.cats = {k: v for k, v in cls.d.items() if not k.startswith("_")}

    def test_quatro_categorias(self):
        self.assertEqual(set(self.cats),
                         {"identidade", "fato", "pergunta", "contagem"})

    def test_frase_curta(self):
        for cat, frases in self.cats.items():
            for f in frases:
                with self.subTest(cat=cat, frase=f):
                    self.assertLessEqual(len(f.split()), 12)

    def test_so_a_contagem_usa_o_placeholder(self):
        for cat, frases in self.cats.items():
            for f in frases:
                with self.subTest(cat=cat, frase=f):
                    if cat == "contagem":
                        self.assertIn("{N}", f)
                    else:
                        self.assertNotIn("{N}", f)


class TestCenas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cenas = C.carregar()

    def test_existem_cenas(self):
        self.assertTrue(self.cenas, "conteudo/cenas.json vazio — rodar "
                                    "produzir/marcar_cenas.py")

    def test_duracao_entre_6_e_12_segundos(self):
        for c in self.cenas:
            with self.subTest(id=c["id"]):
                dur = c["fim"] - c["inicio"]
                self.assertTrue(C.MIN_CENA_S - 0.05 <= dur
                                <= C.MAX_CENA_S + 0.05, f"{dur:.1f}s")

    def test_toda_cena_declara_licenca(self):
        for c in self.cenas:
            with self.subTest(id=c["id"]):
                self.assertIn(c.get("licenca"),
                              {"rockstar_oficial", "cc-by"})

    def test_cc_by_exige_credito(self):
        """Reutilizar CC BY sem creditar é violar a própria licença."""
        for c in self.cenas:
            if c.get("licenca") != "cc-by":
                continue
            with self.subTest(id=c["id"]):
                self.assertTrue(c.get("credito"), f"{c['id']} sem crédito")

    def test_cena_sem_descricao_nao_vira_cartao(self):
        aptas = {c["id"] for c in C.aptas_para_cartao(self.cenas)}
        for c in self.cenas:
            if not c.get("descricao"):
                with self.subTest(id=c["id"]):
                    self.assertNotIn(c["id"], aptas)

    def test_sobram_cenas_para_uma_semana(self):
        cfg = json.loads((RAIZ / "publicador" / "config.json").read_text(
            encoding="utf-8")).get("instagram", {})
        aptas = [c for c in C.aptas_para_cartao(self.cenas)
                 if not c.get("no_runner")]
        self.assertGreaterEqual(
            len(aptas), cfg.get("cartoes_por_dia", 5) * 5,
            "cenas aptas de menos: a regra é uma frase por cena a cada 7 dias")


if __name__ == "__main__":
    unittest.main()


class TestFrasesDeFato(unittest.TestCase):
    """Frase de cartão é queimada no pixel e não tem campo `fonte`.

    Auditoria de 23/09/2026: 7 das 10 frases de `fato` vinham do VAZAMENTO de
    2022 ou de número nunca confirmado (600 mil animações, 80 horas de
    campanha, clonador de chave, "a polícia precisa de uma testemunha"), e uma
    era simplesmente FALSA: "o romance entre Jason e Lucia é opcional" — a
    Rockstar diz que a força dessa relação muda a história e o final. Três
    cartões com ela já estavam na fila.

    Como frase não tem fonte própria, a regra é que ela se apoie num FATO do
    poço, que tem. O teste é uma peneira grossa de vocabulário: não prova a
    afirmação, mas reprova a frase que não fala de nada que o poço sustenta.
    """

    @classmethod
    def setUpClass(cls):
        cls.frases = json.loads(
            (RAIZ / "conteudo" / "frases.json").read_text(encoding="utf-8"))
        cls.vocab_por_fato = [
            (f["id"], _palavras(f"{f['gancho']} {f['narracao']}"))
            for f in _todos_os_fatos()]

    def test_toda_frase_de_fato_se_apoia_num_fato_do_poco(self):
        """Contra UM fato, não contra o poço inteiro.

        Somando os 218 fatos o vocabulário fica tão largo que uma frase de
        vazamento ("carro de luxo só abre com clonador de chave") passa por
        reaproveitar duas palavras banais de fatos diferentes. Exigir que a
        MAIORIA das palavras venha do MESMO fato é o que força a frase a
        espelhar algo que alguém escreveu com fonte.

        ⚠ O que esta peneira NÃO pega: frase que fala do assunto certo e diz o
        contrário ("o romance entre Jason e Lucia é opcional" espelha o
        vocabulário de F157 e afirma o oposto dele). Para isso existe a lista
        de proibidas abaixo, e revisão humana.
        """
        for frase in self.frases["fato"]:
            with self.subTest(frase=frase):
                palavras = _palavras(frase)
                fid, comuns = max(
                    ((i, palavras & v) for i, v in self.vocab_por_fato),
                    key=lambda x: len(x[1]))
                cobertura = len(comuns) / max(len(palavras), 1)
                self.assertTrue(
                    len(comuns) >= 2 and cobertura >= 0.6,
                    f"{frase!r} não espelha nenhum fato do poço (mais "
                    f"próximo: {fid}, {len(comuns)} palavras em comum de "
                    f"{len(palavras)}: {sorted(comuns)}). Escreva o fato com "
                    f"fonte em conteudo/fatos/ antes de virar frase de cartão.")

    def test_nenhuma_afirmacao_de_vazamento_volta(self):
        """As sete que estavam no ar até 23/09/2026, e por que cada uma saiu.

        Vinham do vazamento de 2022 ou de número que a Rockstar nunca
        confirmou. Uma delas ("romance opcional") contradiz o que a Rockstar
        de fato diz: a FORÇA da relação entre Jason e Lucia muda a história e
        o final. Três cartões com ela já estavam na fila quando a auditoria
        aconteceu — por isso isto é teste, e não anotação.
        """
        proibidas = {
            "testemunha": "o vazamento de 2022; o que a Rockstar mostrou é a "
                          "polícia lendo roupa, aparência e veículo",
            "opcional": "a relação Jason/Lucia não é opcional — a força dela "
                        "muda a história e o final",
            "animacoes": "600 mil animações é número de vazamento",
            "clonador": "clonador de chave é vazamento",
            "80 horas": "duração da campanha nunca foi confirmada",
            "perfil criminal": "nome vindo do vazamento; o confirmado é karma",
        }
        import unicodedata
        for cat, lista in self.frases.items():
            if not isinstance(lista, list):
                continue
            for frase in lista:
                s = unicodedata.normalize("NFKD", frase.lower())
                s = "".join(c for c in s if not unicodedata.combining(c))
                for termo, porque in proibidas.items():
                    self.assertNotIn(termo, s, f"{frase!r} ({cat}): {porque}")
