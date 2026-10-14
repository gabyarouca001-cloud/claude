import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ferramentas"))
import verificar as v  # noqa: E402

FFMPEG = shutil.which("ffmpeg") is not None


def seno(segundos=2.0, freq=440.0, amp=0.3, fase_extra=0.0, salto_em=None):
    t = np.arange(int(segundos * v.SR)) / v.SR
    fase = 2 * np.pi * freq * t
    if salto_em is not None:
        fase[int(salto_em * v.SR):] += fase_extra
    return (np.sin(fase) * amp * 32767).astype(np.int16)


class TestEstalo(unittest.TestCase):
    def test_seno_continuo_nao_tem_estalo(self):
        self.assertIsNone(v.detectar_estalo(seno(), 1.0))

    def test_salto_de_fase_e_estalo(self):
        x = seno(fase_extra=np.pi / 2, salto_em=1.0001)     # (em 1,0 s o seno cruza o zero e o salto some)
        achado = v.detectar_estalo(x, 1.0001)
        self.assertIsNotNone(achado)
        self.assertGreater(achado["salto"], 0.1)

    def test_corte_no_silencio_nao_e_estalo(self):
        x = np.zeros(2 * v.SR, np.int16)
        x[:v.SR // 2] = seno(0.5)
        self.assertIsNone(v.detectar_estalo(x, 1.0))


class TestPontos(unittest.TestCase):
    def test_pontos_do_plano_somam_duracoes(self):
        pasta = tempfile.mkdtemp()
        arq = os.path.join(pasta, "plano.json")
        with open(arq, "w") as f:
            f.write('{"segmentos": [{"ini": 0, "fim": 2.0, "corte_depois": "silencio"},'
                    '{"ini": 5, "fim": 8.5, "corte_depois": "retake"}, {"ini": 9, "fim": 10}]}')
        self.assertEqual(v.pontos_do_plano(arq, 1.0), [(3.0, "silencio"), (6.5, "retake")])

    def test_amostrar_limita_quantidade(self):
        pts = [(float(i), "c") for i in range(100)]
        self.assertEqual(len(v.amostrar(pts, 10)), 10)
        self.assertEqual(v.amostrar(pts[:5], 10), pts[:5])


@unittest.skipUnless(FFMPEG, "precisa de ffmpeg")
class TestVideo(unittest.TestCase):
    def gerar(self, volume):
        pasta = tempfile.mkdtemp()
        arq = os.path.join(pasta, "t.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=640x360:r=25:d=4",
                        "-f", "lavfi", "-i", f"sine=f=440:d=4,volume={volume}", "-c:v", "libx264", "-pix_fmt",
                        "yuv420p", "-c:a", "aac", arq], check=True)
        return pasta, arq

    def status(self, pasta, arq, *extra):
        saida = os.path.join(pasta, "v")
        codigo = v.main([arq, "--saida", saida, "--sem-imagens", *extra])
        import json
        itens = json.load(open(os.path.join(saida, "relatorio.json"), encoding="utf-8"))["itens"]
        return codigo, {i["item"]: i["status"] for i in itens}

    def test_fora_do_alvo_reprova(self):
        pasta, arq = self.gerar(1.0)                      # seno a -22 LUFS
        codigo, st = self.status(pasta, arq)
        self.assertEqual(codigo, 1)
        self.assertEqual(st["Loudness integrado"], v.FALHOU)

    def test_no_alvo_aprova_medicoes_e_pede_escuta_humana(self):
        pasta, arq = self.gerar(2.45)                     # ~ -14 LUFS
        codigo, st = self.status(pasta, arq)
        self.assertEqual(st["True peak"], v.OK)
        self.assertEqual(st["Loudness integrado"], v.OK)
        self.assertEqual(st["Erros de fala"], v.NAO)
        self.assertEqual(st["Escuta completa (voz, SFX, trilha, finais truncados)"], v.NAO)
        self.assertEqual(codigo, 0)

    def test_gera_folhas_com_cortes(self):
        pasta, arq = self.gerar(2.45)
        saida = os.path.join(pasta, "img")
        v.main([arq, "--saida", saida, "--pontos", "1.5,3", "--passo", "1"])
        nomes = os.listdir(saida)
        self.assertIn("folha_01.jpg", nomes)
        self.assertIn("cortes_01.jpg", nomes)


if __name__ == "__main__":
    unittest.main()
