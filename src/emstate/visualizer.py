"""
Visualizador de Máquinas de Estados da linguagem EmState.
Gera representações em formato Mermaid (para Markdown e diagramas interativos) e Graphviz DOT.
"""

from .ast_nodes import (
    ProgramaEmState,
    Transicao,
    Condicao,
    CondicaoRelacional,
    CondicaoEstadoDispositivo,
    CondicaoLogica,
)


class StateMachineVisualizer:
    def __init__(self, ast: ProgramaEmState):
        self.ast = ast

    def _condicao_str(self, cond: Condicao) -> str:
        if isinstance(cond, CondicaoRelacional):
            return f"{cond.variavel} {cond.operador} {cond.valor}"
        elif isinstance(cond, CondicaoEstadoDispositivo):
            return f"{cond.dispositivo} {cond.estado}"
        elif isinstance(cond, CondicaoLogica):
            return f"{self._condicao_str(cond.esquerda)} {cond.operador_logico} {self._condicao_str(cond.direita)}"
        return ""

    def to_mermaid(self) -> str:
        """Gera um diagrama de estados Mermaid (stateDiagram-v2)."""
        lines = [
            "stateDiagram-v2",
            f"    [*] --> {self.ast.declaracoes_estados[0].nome if self.ast.declaracoes_estados else 'PARADO'}"
        ]

        # Ações em cada estado
        for bloco in self.ast.blocos_acoes:
            if bloco.acoes:
                acoes_desc = "<br>".join(
                    f"{a.dispositivo} {a.comando}" + (f" ({', '.join(str(x) for x in a.argumentos)})" if a.argumentos else "")
                    for a in bloco.acoes
                )
                lines.append(f"    state {bloco.nome_estado} {{")
                lines.append(f"        {bloco.nome_estado} : {acoes_desc}")
                lines.append(f"    }}")

        # Transições
        for trans in self.ast.transicoes:
            label = f" : {self._condicao_str(trans.condicao)}" if trans.condicao else ""
            lines.append(f"    {trans.origem} --> {trans.destino}{label}")

        return "\n".join(lines)

    def to_dot(self) -> str:
        """Gera uma descrição Graphviz DOT."""
        lines = [
            f'digraph "{self.ast.nome_sistema}" {{',
            '    rankdir=LR;',
            '    node [shape=rectangle, style="rounded,filled", fillcolor="#f0f4f8", fontname="Helvetica"];',
            '    edge [fontname="Helvetica", fontsize=10];',
            '',
            '    __start__ [shape=point, width=0.3];',
        ]

        if self.ast.declaracoes_estados:
            primeiro = self.ast.declaracoes_estados[0].nome
            lines.append(f'    __start__ -> "{primeiro}";')

        for trans in self.ast.transicoes:
            label = self._condicao_str(trans.condicao) if trans.condicao else ""
            lines.append(f'    "{trans.origem}" -> "{trans.destino}" [label="{label}"];')

        lines.append("}")
        return "\n".join(lines)
