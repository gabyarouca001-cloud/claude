import json
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ferramentas"))
import cortes_para_xml as c  # noqa: E402

EXEMPLO = os.path.join(os.path.dirname(__file__), "..", "exemplos", "cortes_exemplo.json")


class TestTempo(unittest.TestCase):
    def test_formatos(self):
        fps = c.normalizar_fps(29.97)
        self.assertEqual(fps, Fraction(30000, 1001))
        self.assertEqual(c.tempo_para_frames("00:00:10,000", fps), 300)
        self.assertEqual(c.tempo_para_frames("1:00", Fraction(25)), 1500)
        self.assertEqual(c.tempo_para_frames(2.5, Fraction(24)), 60)
        self.assertEqual(c.tempo_para_frames("00:00:01:12", Fraction(25)), 37)
        with self.assertRaises(ValueError):
            c.tempo_para_frames("abc", fps)

    def test_url_windows(self):
        self.assertEqual(
            c.caminho_para_url("C:\\Meus Videos\\a.mp4"),
            "file://localhost/C:/Meus%20Videos/a.mp4",
        )


class TestXml(unittest.TestCase):
    def gerar(self, dados=None):
        pasta = tempfile.mkdtemp()
        entrada = EXEMPLO
        if dados is not None:
            entrada = os.path.join(pasta, "cortes.json")
            with open(entrada, "w", encoding="utf-8") as f:
                json.dump(dados, f)
        saida = os.path.join(pasta, "saida.xml")
        self.assertEqual(c.main([entrada, "-o", saida, "--sem-ffprobe"]), 0)
        return ET.parse(saida).getroot()

    def test_timeline_do_exemplo(self):
        raiz = self.gerar()
        seq = raiz.find("sequence")
        video = seq.findall("media/video/track/clipitem")
        audio = seq.findall("media/audio/track")
        self.assertEqual(len(video), 4)
        self.assertEqual(len(audio), 2)
        # clipes encostados um no outro, sem buracos
        for anterior, atual in zip(video, video[1:]):
            self.assertEqual(anterior.findtext("end"), atual.findtext("start"))
        self.assertEqual(int(seq.findtext("duration")), int(video[-1].findtext("end")))
        # cada arquivo descrito por completo só uma vez
        completos = [f for f in raiz.iter("file") if f.find("pathurl") is not None]
        self.assertEqual(len(completos), 2)
        self.assertEqual([m.findtext("name") for m in seq.findall("marker")][0], "GANCHO - frase forte")

    def test_corte_invertido(self):
        dados = {"video": "a.mp4", "cortes": [{"inicio": "10", "fim": "5"}]}
        entrada = os.path.join(tempfile.mkdtemp(), "c.json")
        with open(entrada, "w", encoding="utf-8") as f:
            json.dump(dados, f)
        self.assertEqual(c.main([entrada, "--sem-ffprobe"]), 1)


if __name__ == "__main__":
    unittest.main()
