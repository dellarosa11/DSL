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

    def test_comandos_numericos_exigem_um_numero(self):
        for comando in ("motor velocidade", "led piscar", "buzzer tocar"):
            for argumento in ('"alta"', "alta", "", "10 20"):
                with self.subTest(comando=comando, argumento=argumento):
                    codigo = f"sistema Teste\nestado A\nestado A:\n    {comando} {argumento}\n"
                    with self.assertRaisesRegex(SemanticError, "um argumento numérico"):
                        self._analisar(codigo)

    def test_argumentos_numericos_validos(self):
        self._analisar(
            "sistema Teste\nestado A\nestado A:\n"
            "    motor velocidade 0\n    motor velocidade 100\n"
            "    motor velocidade 12.5\n    led piscar 100\n    buzzer tocar 440\n"
        )

    def test_comandos_com_parametro_positivo_rejeitam_zero(self):
        for comando in ("led piscar", "buzzer tocar"):
            with self.subTest(comando=comando):
                with self.assertRaisesRegex(SemanticError, "maior que zero"):
                    self._analisar(f"sistema Teste\nestado A\nestado A:\n    {comando} 0\n")


if __name__ == "__main__":
    unittest.main()
