"""
Pacote EmState - Linguagem Específica de Domínio para Máquinas de Estados em Sistemas Embarcados.
"""

from .token import Token, TokenType
from .lexer import Lexer, LexerError
from .parser import Parser, ParserError
from .semantic import SemanticAnalyzer, SemanticError, SemanticWarning
from .symbol_table import SymbolTable, Symbol
from .simulator import Simulator
from .visualizer import StateMachineVisualizer
from .codegen import CCodeGenerator, ArduinoGenerator

__version__ = "1.0.0"
__all__ = [
    "Token",
    "TokenType",
    "Lexer",
    "LexerError",
    "Parser",
    "ParserError",
    "SemanticAnalyzer",
    "SemanticError",
    "SemanticWarning",
    "SymbolTable",
    "Symbol",
    "Simulator",
    "StateMachineVisualizer",
    "CCodeGenerator",
    "ArduinoGenerator",
]
