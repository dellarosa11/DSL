import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from emstate.lexer import Lexer
from emstate.parser import Parser
from emstate.semantic import SemanticAnalyzer, SemanticError


class TestSemantic(unittest.TestCase):
    def _analisar(self, codigo: str):
        tokens = Lexer(codigo).tokenize()
        ast = Parser(tokens).parse()
        return SemanticAnalyzer().analyze(ast)

    def test_programa_valido(self):
        codigo = """
        sistema Valido
        estado A
        estado B
        A -> B quando botao pressionado
        B -> A quando tempo > 10
        estado A:
            motor parar
        estado B:
            motor velocidade 50
        """
        sym_tab = self._analisar(codigo)
        self.assertTrue(sym_tab.has_estado("A"))
        self.assertTrue(sym_tab.has_estado("B"))
        self.assertIn("motor", sym_tab.dispositivos)

    def test_estado_origem_nao_declarado(self):
        codigo = """
        sistema Invalido
        estado B
        A -> B quando botao pressionado
        """
        with self.assertRaises(SemanticError) as ctx:
            self._analisar(codigo)
        self.assertIn("Estado de origem 'A' não foi declarado", str(ctx.exception))

    def test_estado_destino_nao_declarado(self):
        codigo = """
        sistema Invalido
        estado A
        A -> B quando botao pressionado
        """
        with self.assertRaises(SemanticError) as ctx:
            self._analisar(codigo)
        self.assertIn("Estado de destino 'B' não foi declarado", str(ctx.exception))

    def test_estado_duplicado(self):
        codigo = """
        sistema Duplicado
        estado A
        estado A
        """
        with self.assertRaises(SemanticError) as ctx:
            self._analisar(codigo)
        self.assertIn("declarado mais de uma vez", str(ctx.exception))

    def test_velocidade_motor_fora_dos_limites(self):
        codigo = """
        sistema Limites
        estado PARADO
        estado RAPIDO
        PARADO -> RAPIDO
        estado RAPIDO:
            motor velocidade 150
        """
        with self.assertRaises(SemanticError) as ctx:
            self._analisar(codigo)
        self.assertIn("Velocidade do motor deve estar entre 0 e 100%", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
