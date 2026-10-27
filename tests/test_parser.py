import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from emstate.lexer import Lexer
from emstate.parser import Parser, ParserError
from emstate.ast_nodes import CondicaoRelacional, CondicaoEstadoDispositivo, CondicaoLogica


class TestParser(unittest.TestCase):
    def test_parse_programa_oficial(self):
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
        lexer = Lexer(codigo)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        self.assertEqual(ast.nome_sistema, "ControleMotor")
        self.assertEqual(len(ast.declaracoes_estados), 3)
        self.assertEqual(len(ast.transicoes), 3)
        self.assertEqual(len(ast.blocos_acoes), 3)

        # Verifica primeira transição
        t1 = ast.transicoes[0]
        self.assertEqual(t1.origem, "PARADO")
        self.assertEqual(t1.destino, "FUNCIONANDO")
        self.assertIsInstance(t1.condicao, CondicaoEstadoDispositivo)
        self.assertEqual(t1.condicao.dispositivo, "botao")
        self.assertEqual(t1.condicao.estado, "pressionado")

        # Verifica terceira transição com condição relacional
        t3 = ast.transicoes[2]
        self.assertEqual(t3.origem, "FUNCIONANDO")
        self.assertEqual(t3.destino, "ERRO")
        self.assertIsInstance(t3.condicao, CondicaoRelacional)
        self.assertEqual(t3.condicao.variavel, "corrente")
        self.assertEqual(t3.condicao.operador, ">")
        self.assertEqual(t3.condicao.valor, 2)

    def test_condicao_logica(self):
        codigo = """
        sistema Logica
        estado S1
        estado S2
        S1 -> S2 quando botao pressionado e corrente > 5
        """
        tokens = Lexer(codigo).tokenize()
        ast = Parser(tokens).parse()
        cond = ast.transicoes[0].condicao
        self.assertIsInstance(cond, CondicaoLogica)
        self.assertEqual(cond.operador_logico, "e")


if __name__ == "__main__":
    unittest.main()
