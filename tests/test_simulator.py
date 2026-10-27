import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from emstate.lexer import Lexer
from emstate.parser import Parser
from emstate.simulator import Simulator


class TestSimulator(unittest.TestCase):
    def setUp(self):
        codigo = """
        sistema ControleMotor
        estado PARADO
        estado FUNCIONANDO
        estado ERRO

        PARADO -> FUNCIONANDO quando botao pressionado
        FUNCIONANDO -> PARADO quando botao pressionado
        FUNCIONANDO -> ERRO quando corrente > 2

        estado PARADO:
            motor parar

        estado FUNCIONANDO:
            motor velocidade 70

        estado ERRO:
            motor parar
        """
        tokens = Lexer(codigo).tokenize()
        self.ast = Parser(tokens).parse()
        self.sim = Simulator(self.ast)

    def test_ciclo_inicial_sem_evento(self):
        # Inicialmente deve estar em PARADO e motor parar
        res = self.sim.step()
        self.assertEqual(res["estado_atual"], "PARADO")
        self.assertIn("motor parar", res["acoes"])
        self.assertFalse(res["mudou_de_estado"])

    def test_transicao_com_botao_pressionado(self):
        # Injeta evento de botão pressionado
        self.sim.set_evento_dispositivo("botao", "pressionado")
        res = self.sim.step()
        self.assertEqual(res["estado_atual"], "FUNCIONANDO")
        self.assertTrue(res["mudou_de_estado"])

        # No próximo ciclo em FUNCIONANDO deve executar motor velocidade 70
        res2 = self.sim.step()
        self.assertIn("motor velocidade 70", res2["acoes"])

    def test_transicao_por_corrente_alta(self):
        # Vai para FUNCIONANDO
        self.sim.set_evento_dispositivo("botao", "pressionado")
        self.sim.step()
        self.sim.clear_evento_dispositivo("botao")

        # Injeta corrente > 2
        self.sim.set_variavel("corrente", 2.8)
        res = self.sim.step()
        self.assertEqual(res["estado_atual"], "ERRO")
        self.assertTrue(res["mudou_de_estado"])


if __name__ == "__main__":
    unittest.main()
