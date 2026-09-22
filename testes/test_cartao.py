# -*- coding: utf-8 -*-
"""O CARTÃO: quebra de linha, filtergraph válido e crédito presente.

O `-f null` valida o filtergraph inteiro contra o ffmpeg de verdade, sem
codificar nada e sem rede — é o que pega erro de sintaxe de filtro antes de
uma publicação, que é onde o erro custaria o slot do dia.
"""

import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from nucleo import canal, cartao  # noqa: E402

IDENT = {"nome": "Rumo a Vice City", "handle": "rumoavicecity"}


def tem_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


class TestQuebraDeLinha(unittest.TestCase):
    def test_nenhuma_linha_passa_do_limite(self):
        for frase in ("Vice City é duas vezes o tamanho de Los Santos",
                      "Faltam 58 dias para GTA 6",
                      "Você encontrou a página que fala tudo sobre GTA 6"):
            for linha in cartao.quebrar(frase):
                with self.subTest(frase=frase, linha=linha):
                    self.assertLessEqual(len(linha), cartao.LARGURA_LINHA + 4)

    def test_nao_perde_palavra(self):
        frase = "A polícia precisa de uma testemunha para te caçar"
        self.assertEqual(" ".join(cartao.quebrar(frase)), frase)

    def test_palavra_gigante_nao_quebra_o_algoritmo(self):
        linhas = cartao.quebrar("Grandtheftautoseisemvicecityagora sim")
        self.assertTrue(linhas)


class TestFiltergraph(unittest.TestCase):
    def _filtro(self, layout, **kw):
        return cartao.filtergraph(
            layout, 0.0, 8.0, 3, cartao.GEOMETRIA[layout]["corpo"],
            kw.get("avatar", True), kw.get("selo", True),
            kw.get("foto", layout == 3), IDENT,
            kw.get("rodape", canal.CREDITO_ROCKSTAR))

    def test_os_tres_layouts_produzem_saida(self):
        for layout in cartao.LAYOUTS:
            with self.subTest(layout=layout):
                f = self._filtro(layout)
                self.assertIn("[vout]", f)
                self.assertIn("[aout]", f)

    def test_o_credito_esta_sempre_no_filtro(self):
        for layout in cartao.LAYOUTS:
            with self.subTest(layout=layout):
                self.assertIn("Rockstar Games", self._filtro(layout))

    def test_credito_cc_entra_quando_a_cena_e_cc_by(self):
        f = self._filtro(1, rodape=canal.credito_cc("Canal Exemplo"))
        self.assertIn("CC BY", f)
        self.assertIn("Canal Exemplo", f)

    def test_blur_vem_antes_do_scale_grande(self):
        """Borrar em 108×192 e ampliar: a lição de custo do Reel cine."""
        f = self._filtro(1)
        self.assertLess(f.index("boxblur"), f.index("scale=1080:1920:flags"))

    def test_layout_invalido_e_recusado(self):
        with self.assertRaises(SystemExit):
            cartao.montar(Path("x.mp4"), 0, 1, "oi", 9, IDENT, Path("."))

    @unittest.skipUnless(tem_ffmpeg(), "ffmpeg ausente")
    def test_o_ffmpeg_aceita_os_tres_filtergraphs(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for i in range(3):
                (tmp / f"linha{i}.txt").write_text("linha", encoding="utf-8")
            for layout in cartao.LAYOUTS:
                with self.subTest(layout=layout):
                    # lavfi no lugar dos arquivos reais: o teste valida a
                    # SINTAXE do filtro, não o conteúdo
                    entradas = ["-f", "lavfi", "-i",
                                "testsrc=size=1920x1080:rate=30:duration=9",
                                "-f", "lavfi", "-i", "color=c=red:s=96x96:d=1"]
                    if layout == 3:
                        entradas += ["-f", "lavfi", "-i",
                                     "color=c=blue:s=1920x1080:d=1"]
                    entradas += ["-f", "lavfi", "-i",
                                 "color=c=cyan:s=48x48:d=1"]
                    filtro = self._filtro(layout).replace(
                        "[0:a]atrim=0.00:8.00,asetpts=PTS-STARTPTS,"
                        "volume=0.7,apad=whole_dur=8.00[aout]",
                        "anullsrc=r=44100:cl=stereo,atrim=0:8[aout]")
                    r = subprocess.run(
                        ["ffmpeg", "-y", "-loglevel", "error", *entradas,
                         "-filter_complex", filtro, "-map", "[vout]",
                         "-map", "[aout]", "-frames:v", "1", "-f", "null", "-"],
                        cwd=tmp, capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0,
                                     f"layout {layout}: {r.stderr[-500:]}")


if __name__ == "__main__":
    unittest.main()
