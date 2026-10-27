"""
Definições dos tokens da linguagem EmState.
Linguagem Específica de Domínio para Máquinas de Estados em Sistemas Embarcados.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional


class TokenType(Enum):
    # Palavras-chave
    KW_SISTEMA = auto()       # sistema
    KW_ESTADO = auto()        # estado
    KW_QUANDO = auto()        # quando
    KW_E = auto()             # e (conjunção lógica)
    KW_OU = auto()            # ou (disjunção lógica)
    KW_NAO = auto()           # nao (negação lógica)

    # Identificadores e Literais
    IDENTIFIER = auto()       # nomes de variáveis, estados, dispositivos, comandos
    NUMBER = auto()           # 10, 3.14, 0
    STRING = auto()           # "texto"

    # Operadores e Pontuação
    ARROW = auto()            # ->
    COLON = auto()            # :
    COMMA = auto()            # ,
    LPAREN = auto()           # (
    RPAREN = auto()           # )
    
    # Operadores relacionais
    OP_EQ = auto()            # ==
    OP_NEQ = auto()           # !=
    OP_GT = auto()            # >
    OP_GTE = auto()           # >=
    OP_LT = auto()            # <
    OP_LTE = auto()           # <=
    OP_ASSIGN = auto()        # =

    # Finais e especiais
    NEWLINE = auto()          # quebra de linha significativa
    INDENT = auto()           # aumento de indentação
    DEDENT = auto()           # diminuição de indentação
    EOF = auto()              # fim do arquivo


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.column})"
