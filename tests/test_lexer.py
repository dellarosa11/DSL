import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from emstate.lexer import Lexer, LexerError
from emstate.token import TokenType


class TestLexer(unittest.TestCase):
    def test_palavras_chave_e_identificadores(self):
        codigo = "sistema ControleMotor\nestado PARADO\n"
        lexer = Lexer(codigo)
        todos_tokens = lexer.tokenize()
        tokens = [t for t in todos_tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]

        tipos = [t.type for t in tokens]
        self.assertEqual(tipos, [
            TokenType.KW_SISTEMA,
            TokenType.IDENTIFIER,
            TokenType.KW_ESTADO,
            TokenType.IDENTIFIER
        ])
        self.assertEqual(tokens[1].value, "ControleMotor")
        self.assertEqual(tokens[3].value, "PARADO")

    def test_operadores_e_transicoes(self):
        codigo = "PARADO -> FUNCIONANDO quando corrente > 2\n"
        lexer = Lexer(codigo)
        tokens = lexer.tokenize()

        tipos = [t.type for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]
        self.assertEqual(tipos, [
            TokenType.IDENTIFIER,
            TokenType.ARROW,
            TokenType.IDENTIFIER,
            TokenType.KW_QUANDO,
            TokenType.IDENTIFIER,
            TokenType.OP_GT,
            TokenType.NUMBER
        ])
        self.assertEqual(tokens[6].value, 2)

    def test_comentarios_ignorados(self):
        codigo = "# Este é um comentário\nsistema Teste // outro comentario\n"
        lexer = Lexer(codigo)
        tokens = lexer.tokenize()
        tipos = [t.type for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]
        self.assertEqual(tipos, [TokenType.KW_SISTEMA, TokenType.IDENTIFIER])


if __name__ == "__main__":
    unittest.main()
