"""
Analisador Léxico para a linguagem EmState.
Converte o código-fonte em um fluxo de tokens com rastreamento de linha e coluna.
"""

from typing import List, Optional
from .token import Token, TokenType


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Erro Léxico [L{line}:C{column}]: {message}")
        self.line = line
        self.column = column


class Lexer:
    KEYWORDS = {
        "sistema": TokenType.KW_SISTEMA,
        "estado": TokenType.KW_ESTADO,
        "quando": TokenType.KW_QUANDO,
        "e": TokenType.KW_E,
        "ou": TokenType.KW_OU,
        "nao": TokenType.KW_NAO,
    }

    def __init__(self, source_code: str):
        self.source = source_code
        self.pos = 0
        self.line = 1
        self.column = 1
        self.length = len(source_code)
        self.indent_stack = [0]
        self.tokens: List[Token] = []

    def _peek(self, offset: int = 0) -> Optional[str]:
        target = self.pos + offset
        if target < self.length:
            return self.source[target]
        return None

    def _advance(self) -> Optional[str]:
        if self.pos >= self.length:
            return None
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self.pos >= self.length or self.source[self.pos] != expected:
            return False
        self._advance()
        return True

    def tokenize(self) -> List[Token]:
        self.tokens = []
        at_line_start = True

        while self.pos < self.length:
            start_col = self.column
            start_line = self.line

            # Processamento de indentação no início da linha
            if at_line_start:
                spaces = 0
                while self._peek() in (' ', '\t'):
                    ch = self._advance()
                    spaces += 4 if ch == '\t' else 1

                # Se a linha for vazia ou comentário, ignora indentação
                if self._peek() in ('\n', '\r') or (self._peek() == '#') or (self._peek() == '/' and self._peek(1) == '/'):
                    at_line_start = False
                    continue

                if self._peek() is None:
                    break

                current_indent = self.indent_stack[-1]
                if spaces > current_indent:
                    self.indent_stack.append(spaces)
                    self.tokens.append(Token(TokenType.INDENT, spaces, self.line, self.column))
                elif spaces < current_indent:
                    while self.indent_stack and spaces < self.indent_stack[-1]:
                        self.indent_stack.pop()
                        self.tokens.append(Token(TokenType.DEDENT, spaces, self.line, self.column))
                    if spaces != self.indent_stack[-1]:
                        raise LexerError(
                            f"Nível de indentação inconsistente: {spaces} espaços",
                            self.line, self.column
                        )
                at_line_start = False

            ch = self._peek()

            # Pular espaços em branco no meio da linha
            if ch in (' ', '\t'):
                self._advance()
                continue

            # Quebra de linha
            if ch in ('\n', '\r'):
                if ch == '\r' and self._peek(1) == '\n':
                    self._advance()
                self._advance()
                # Adiciona NEWLINE apenas se o último token não for NEWLINE ou INDENT/DEDENT
                if self.tokens and self.tokens[-1].type not in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
                    self.tokens.append(Token(TokenType.NEWLINE, "\n", start_line, start_col))
                at_line_start = True
                continue

            # Comentários de linha (# ou //)
            if ch == '#' or (ch == '/' and self._peek(1) == '/'):
                while self._peek() not in ('\n', '\r', None):
                    self._advance()
                continue

            # Seta ->
            if ch == '-' and self._peek(1) == '>':
                self._advance()
                self._advance()
                self.tokens.append(Token(TokenType.ARROW, "->", start_line, start_col))
                continue

            # Operadores relacionais
            if ch == '=':
                self._advance()
                if self._match('='):
                    self.tokens.append(Token(TokenType.OP_EQ, "==", start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.OP_ASSIGN, "=", start_line, start_col))
                continue

            if ch == '!':
                self._advance()
                if self._match('='):
                    self.tokens.append(Token(TokenType.OP_NEQ, "!=", start_line, start_col))
                else:
                    raise LexerError("Esperado '=' após '!'", start_line, start_col)
                continue

            if ch == '>':
                self._advance()
                if self._match('='):
                    self.tokens.append(Token(TokenType.OP_GTE, ">=", start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.OP_GT, ">", start_line, start_col))
                continue

            if ch == '<':
                self._advance()
                if self._match('='):
                    self.tokens.append(Token(TokenType.OP_LTE, "<=", start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.OP_LT, "<", start_line, start_col))
                continue

            # Pontuação
            if ch == ':':
                self._advance()
                self.tokens.append(Token(TokenType.COLON, ":", start_line, start_col))
                continue

            if ch == ',':
                self._advance()
                self.tokens.append(Token(TokenType.COMMA, ",", start_line, start_col))
                continue

            if ch == '(':
                self._advance()
                self.tokens.append(Token(TokenType.LPAREN, "(", start_line, start_col))
                continue

            if ch == ')':
                self._advance()
                self.tokens.append(Token(TokenType.RPAREN, ")", start_line, start_col))
                continue

            # Números (inteiros e decimais, inclusive negativos com -)
            if ch.isdigit() or (ch == '-' and self._peek(1) and self._peek(1).isdigit()):
                num_str = self._advance()
                while self._peek() and self._peek().isdigit():
                    num_str += self._advance()
                if self._peek() == '.' and self._peek(1) and self._peek(1).isdigit():
                    num_str += self._advance()  # consome '.'
                    while self._peek() and self._peek().isdigit():
                        num_str += self._advance()
                    val = float(num_str)
                else:
                    val = int(num_str)
                self.tokens.append(Token(TokenType.NUMBER, val, start_line, start_col))
                continue

            # Strings delimitadas por aspas simples ou duplas
            if ch in ('"', "'"):
                quote_type = self._advance()
                str_val = ""
                while self._peek() and self._peek() != quote_type:
                    if self._peek() in ('\n', '\r'):
                        raise LexerError("String não terminada antes do fim da linha", start_line, start_col)
                    str_val += self._advance()
                if self._peek() != quote_type:
                    raise LexerError(f"String não finalizada com {quote_type}", start_line, start_col)
                self._advance()  # consome a aspas de fechamento
                self.tokens.append(Token(TokenType.STRING, str_val, start_line, start_col))
                continue

            # Identificadores e Palavras-chave
            if ch.isalpha() or ch == '_':
                ident = ""
                while self._peek() and (self._peek().isalnum() or self._peek() == '_'):
                    ident += self._advance()

                lower_ident = ident.lower()
                if lower_ident in self.KEYWORDS:
                    tok_type = self.KEYWORDS[lower_ident]
                    self.tokens.append(Token(tok_type, lower_ident, start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, ident, start_line, start_col))
                continue

            # Caractere desconhecido
            unknown = self._advance()
            raise LexerError(f"Caractere inesperado: '{unknown}'", start_line, start_col)

        # Desempilha qualquer indentação pendente no final do arquivo
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, 0, self.line, self.column))

        # Adiciona NEWLINE final se necessário
        if self.tokens and self.tokens[-1].type not in (TokenType.NEWLINE, TokenType.EOF):
            self.tokens.append(Token(TokenType.NEWLINE, "\n", self.line, self.column))

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens
