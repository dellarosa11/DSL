"""
Definição dos nós da Árvore Sintática Abstrata (AST) da linguagem EmState.
Suporta visualização em árvore hierárquica e conversão para formatos intermediários.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Union


@dataclass
class ASTNode:
    """Nó base da Árvore Sintática Abstrata."""
    line: int = 1
    column: int = 1

    def to_tree(self, prefix: str = "", is_last: bool = True) -> str:
        """Renderiza o nó e seus filhos em formato textual de árvore."""
        raise NotImplementedError


@dataclass
class Condicao(ASTNode):
    """Nó base para condições em transições."""
    pass


@dataclass
class CondicaoRelacional(Condicao):
    """
    Condição do tipo: corrente > 2, temperatura <= 50, etc.
    Exemplo do artigo:
        Transição
        |-- origem: FUNCIONANDO
        |-- destino: ERRO
        `-- condição
            |-- variável: corrente
            |-- operador: >
            `-- valor: 2
    """
    variavel: str = ""
    operador: str = ""
    valor: Union[int, float, str] = 0

    def to_tree(self, prefix: str = "", is_last: bool = True) -> str:
        marker = "`-- " if is_last else "|-- "
        sub_prefix = prefix + ("    " if is_last else "|   ")
        lines = [
            f"{prefix}{marker}condição (relacional)",
            f"{sub_prefix}|-- variável: {self.variavel}",
            f"{sub_prefix}|-- operador: {self.operador}",
            f"{sub_prefix}`-- valor: {self.valor}"
        ]
        return "\n".join(lines)


@dataclass
class CondicaoEstadoDispositivo(Condicao):
    """
    Condição de estado/evento de dispositivo:
    Exemplo do artigo: 'botao pressionado', 'sensor ativo', 'chave ligada'
    """
    dispositivo: str = ""
    estado: str = ""  # ex: pressionado, solto, ativo, detectado

    def to_tree(self, prefix: str = "", is_last: bool = True) -> str:
        marker = "`-- " if is_last else "|-- "
        sub_prefix = prefix + ("    " if is_last else "|   ")
        lines = [
            f"{prefix}{marker}condição (dispositivo)",
            f"{sub_prefix}|-- dispositivo: {self.dispositivo}",
            f"{sub_prefix}`-- estado esperado: {self.estado}"
        ]
        return "\n".join(lines)


@dataclass
class CondicaoLogica(Condicao):
    """
    Condição composta lógica: <cond1> e <cond2>, <cond1> ou <cond2>
    """
    operador_logico: str = "e"  # 'e' ou 'ou'
    esquerda: Condicao = field(default_factory=lambda: Condicao())
    direita: Condicao = field(default_factory=lambda: Condicao())

    def to_tree(self, prefix: str = "", is_last: bool = True) -> str:
        marker = "`-- " if is_last else "|-- "
        sub_prefix = prefix + ("    " if is_last else "|   ")
        lines = [
            f"{prefix}{marker}condição lógica ({self.operador_logico})",
            self.esquerda.to_tree(sub_prefix, is_last=False),
            self.direita.to_tree(sub_prefix, is_last=True)
        ]
        return "\n".join(lines)


@dataclass
class Acao(ASTNode):
    """
    Ação executada em um estado:
    Exemplo:
        motor parar
        motor velocidade 70
        led ligar
        buzzer tocar 1000
    """
    dispositivo: str = ""
    comando: str = ""
    argumentos: List[Union[int, float, str]] = field(default_factory=list)

    def to_tree(self, prefix: str = "", is_last: bool = True) -> str:
        marker = "`-- " if is_last else "|-- "
        sub_prefix = prefix + ("    " if is_last else "|   ")
        args_str = f" {', '.join(str(a) for a in self.argumentos)}" if self.argumentos else ""
        lines = [
            f"{prefix}{marker}Ação",
            f"{sub_prefix}|-- dispositivo: {self.dispositivo}",
            f"{sub_prefix}`-- comando: {self.comando}{args_str}"
        ]
        return "\n".join(lines)


@dataclass
class Transicao(ASTNode):
    """
    Transição entre estados:
    Exemplo:
        PARADO -> FUNCIONANDO quando botao pressionado
        FUNCIONANDO -> ERRO quando corrente > 2
    """
    origem: str = ""
    destino: str = ""
    condicao: Optional[Condicao] = None

    def to_tree(self, prefix: str = "", is_last: bool = True) -> str:
        marker = "`-- " if is_last else "|-- "
        sub_prefix = prefix + ("    " if is_last else "|   ")
        lines = [
            f"{prefix}{marker}Transição",
            f"{sub_prefix}|-- origem: {self.origem}",
            f"{sub_prefix}|-- destino: {self.destino}"
        ]
        if self.condicao:
            lines.append(self.condicao.to_tree(sub_prefix, is_last=True))
        else:
            lines.append(f"{sub_prefix}`-- condição: (sempre / incondicional)")
        return "\n".join(lines)


@dataclass
class DeclaracaoEstado(ASTNode):
    """
    Declaração explícita de um estado:
    estado PARADO
    """
    nome: str = ""

    def to_tree(self, prefix: str = "", is_last: bool = True) -> str:
        marker = "`-- " if is_last else "|-- "
        return f"{prefix}{marker}Estado declarado: {self.nome}"


@dataclass
class BlocoAcoesEstado(ASTNode):
    """
    Bloco de ações associadas a um estado:
    estado FUNCIONANDO:
        motor velocidade 70
    """
    nome_estado: str = ""
    acoes: List[Acao] = field(default_factory=list)

    def to_tree(self, prefix: str = "", is_last: bool = True) -> str:
        marker = "`-- " if is_last else "|-- "
        sub_prefix = prefix + ("    " if is_last else "|   ")
        lines = [
            f"{prefix}{marker}Bloco de Ações: estado {self.nome_estado}"
        ]
        if not self.acoes:
            lines.append(f"{sub_prefix}`-- (nenhuma ação)")
        else:
            for idx, acao in enumerate(self.acoes):
                last = (idx == len(self.acoes) - 1)
                lines.append(acao.to_tree(sub_prefix, is_last=last))
        return "\n".join(lines)


@dataclass
class ProgramaEmState(ASTNode):
    """
    Nó raiz do programa EmState:
    sistema ControleMotor
    ...
    """
    nome_sistema: str = ""
    declaracoes_estados: List[DeclaracaoEstado] = field(default_factory=list)
    transicoes: List[Transicao] = field(default_factory=list)
    blocos_acoes: List[BlocoAcoesEstado] = field(default_factory=list)

    def to_tree(self, prefix: str = "", is_last: bool = True) -> str:
        lines = [
            f"Sistema: {self.nome_sistema}",
            "|-- Estados Declarados:"
        ]
        total_decls = len(self.declaracoes_estados)
        if total_decls == 0:
            lines.append("|   `-- (nenhum estado declarado)")
        else:
            for idx, decl in enumerate(self.declaracoes_estados):
                last = (idx == total_decls - 1)
                lines.append(decl.to_tree("|   ", is_last=last))

        lines.append("|-- Transições:")
        total_trans = len(self.transicoes)
        if total_trans == 0:
            lines.append("|   `-- (nenhuma transição definida)")
        else:
            for idx, trans in enumerate(self.transicoes):
                last = (idx == total_trans - 1)
                lines.append(trans.to_tree("|   ", is_last=last))

        lines.append("`-- Blocos de Ações por Estado:")
        total_blocos = len(self.blocos_acoes)
        if total_blocos == 0:
            lines.append("    `-- (nenhum bloco de ações)")
        else:
            for idx, bloco in enumerate(self.blocos_acoes):
                last = (idx == total_blocos - 1)
                lines.append(bloco.to_tree("    ", is_last=last))

        return "\n".join(lines)
