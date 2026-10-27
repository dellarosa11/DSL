"""
Tabela de Símbolos para a linguagem EmState.
Armazena informações sobre o sistema, estados declarados, transições, variáveis e dispositivos.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


class SymbolCategory:
    SISTEMA = "sistema"
    ESTADO = "estado"
    DISPOSITIVO = "dispositivo"
    VARIAVEL = "variavel"


@dataclass
class Symbol:
    name: str
    category: str
    line: int
    column: int
    metadata: Dict = field(default_factory=dict)


class SymbolTable:
    def __init__(self):
        self.symbols: Dict[str, Symbol] = {}
        self.estados_declarados: Dict[str, Symbol] = {}
        self.dispositivos: Dict[str, Symbol] = {}
        self.variaveis_sensores: Dict[str, Symbol] = {}
        self.nome_sistema: Optional[str] = None

    def set_sistema(self, name: str, line: int, column: int):
        self.nome_sistema = name
        sym = Symbol(name=name, category=SymbolCategory.SISTEMA, line=line, column=column)
        self.symbols[name] = sym

    def add_estado(self, name: str, line: int, column: int) -> bool:
        """Retorna True se adicionado com sucesso, False se já existir."""
        if name in self.estados_declarados:
            return False
        sym = Symbol(name=name, category=SymbolCategory.ESTADO, line=line, column=column)
        self.estados_declarados[name] = sym
        self.symbols[f"estado:{name}"] = sym
        return True

    def has_estado(self, name: str) -> bool:
        return name in self.estados_declarados

    def register_dispositivo(self, name: str, line: int, column: int, tipo: str = "atuador"):
        if name not in self.dispositivos:
            sym = Symbol(
                name=name,
                category=SymbolCategory.DISPOSITIVO,
                line=line,
                column=column,
                metadata={"tipo": tipo, "comandos": set()}
            )
            self.dispositivos[name] = sym
        return self.dispositivos[name]

    def register_comando_dispositivo(self, name: str, comando: str):
        if name in self.dispositivos:
            self.dispositivos[name].metadata["comandos"].add(comando)

    def register_variavel_sensor(self, name: str, line: int, column: int):
        if name not in self.variaveis_sensores:
            sym = Symbol(name=name, category=SymbolCategory.VARIAVEL, line=line, column=column)
            self.variaveis_sensores[name] = sym
        return self.variaveis_sensores[name]

    def dump(self) -> str:
        """Gera relatório legível da tabela de símbolos."""
        lines = ["=== TABELA DE SÍMBOLOS ==="]
        lines.append(f"Sistema: {self.nome_sistema}")
        lines.append("\nEstados:")
        for name, sym in self.estados_declarados.items():
            lines.append(f"  - {name} (L{sym.line}:C{sym.column})")

        lines.append("\nDispositivos/Atuadores:")
        for name, sym in self.dispositivos.items():
            cmds = ", ".join(sorted(sym.metadata.get("comandos", [])))
            lines.append(f"  - {name} [comandos: {cmds or 'nenhum'}] (L{sym.line}:C{sym.column})")

        lines.append("\nVariáveis / Sensores monitorados:")
        for name, sym in self.variaveis_sensores.items():
            lines.append(f"  - {name} (L{sym.line}:C{sym.column})")

        return "\n".join(lines)
