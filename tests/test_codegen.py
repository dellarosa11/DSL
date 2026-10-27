import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from emstate.lexer import Lexer
from emstate.parser import Parser
from emstate.semantic import SemanticAnalyzer
from emstate.codegen import CCodeGenerator, ArduinoGenerator


class TestCodeGen(unittest.TestCase):
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
        self.symbol_table = SemanticAnalyzer().analyze(self.ast)

    def test_geracao_c(self):
        c_gen = CCodeGenerator(self.ast, self.symbol_table)
        header = c_gen.generate_header()
        source = c_gen.generate_source()
        sim_main = c_gen.generate_simulation_main()

        # Verifica header
        self.assertIn("ESTADO_PARADO", header)
        self.assertIn("ESTADO_FUNCIONANDO", header)
        self.assertIn("ESTADO_ERRO", header)
        self.assertIn("void ControleMotor_update(void);", header)
        self.assertIn("bool botaoPressionado(void);", header)
        self.assertIn("float obter_corrente(void);", header)

        # Verifica switch case no source
        self.assertIn("switch (estadoAtual)", source)
        self.assertIn("case ESTADO_PARADO:", source)
        self.assertIn("motorParar();", source)
        self.assertIn("if (botaoPressionado())", source)
        self.assertIn("estadoAtual = ESTADO_FUNCIONANDO;", source)
        self.assertIn("motorVelocidade(70);", source)

        # Verifica arquivo de simulação
        self.assertIn("int main(void)", sim_main)

    def test_geracao_arduino(self):
        ard_gen = ArduinoGenerator(self.ast, self.symbol_table)
        sketch = ard_gen.generate_sketch()

        self.assertIn("void setup()", sketch)
        self.assertIn("void loop()", sketch)
        self.assertIn("switch (estadoAtual)", sketch)
        self.assertIn("analogWrite(PINO_MOTOR_PWM", sketch)


if __name__ == "__main__":
    unittest.main()
