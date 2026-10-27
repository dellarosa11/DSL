"""
Simulador / Interpretador Interativo para a linguagem EmState.
Permite executar a máquina de estados em tempo real no terminal,
injetar valores de sensores e eventos de botões, e observar as ações dos atuadores.
"""

from typing import Dict, Any, List, Optional
from .ast_nodes import (
    ProgramaEmState,
    Transicao,
    Condicao,
    CondicaoRelacional,
    CondicaoEstadoDispositivo,
    CondicaoLogica,
    Acao,
)


class Simulator:
    def __init__(self, ast: ProgramaEmState):
        self.ast = ast
        self.nome_sistema = ast.nome_sistema
        self.estados = [decl.nome for decl in ast.declaracoes_estados]
        self.estado_atual = self.estados[0] if self.estados else "INDEFINIDO"
        self.estado_anterior = None
        self.ciclo = 0

        # Estado dos sensores e variáveis do ambiente
        self.variaveis: Dict[str, float] = {}
        self.eventos_dispositivos: Dict[str, str] = {}

        # Histórico de execuções de ações
        self.historico_acoes: List[str] = []

        # Indexação de ações e transições por estado
        self.acoes_por_estado: Dict[str, List[Acao]] = {}
        for bloco in ast.blocos_acoes:
            self.acoes_por_estado[bloco.nome_estado] = bloco.acoes

        self.transicoes_por_estado: Dict[str, List[Transicao]] = {}
        for t in ast.transicoes:
            self.transicoes_por_estado.setdefault(t.origem, []).append(t)

    def set_variavel(self, nome: str, valor: float):
        """Define o valor de uma variável analógica (ex: corrente, temperatura, tempo)."""
        self.variaveis[nome] = valor

    def set_evento_dispositivo(self, dispositivo: str, estado: str):
        """Define o estado de um sensor/botão (ex: botao -> pressionado)."""
        self.eventos_dispositivos[dispositivo] = estado

    def clear_evento_dispositivo(self, dispositivo: str):
        if dispositivo in self.eventos_dispositivos:
            del self.eventos_dispositivos[dispositivo]

    def _avaliar_condicao(self, cond: Optional[Condicao]) -> bool:
        if cond is None:
            return True

        if isinstance(cond, CondicaoRelacional):
            val_atual = self.variaveis.get(cond.variavel, 0.0)
            op = cond.operador
            alvo = cond.valor
            if op == "==": return val_atual == alvo
            if op == "!=": return val_atual != alvo
            if op == ">":  return val_atual > alvo
            if op == ">=": return val_atual >= alvo
            if op == "<":  return val_atual < alvo
            if op == "<=": return val_atual <= alvo
            return False

        elif isinstance(cond, CondicaoEstadoDispositivo):
            disp_estado = self.eventos_dispositivos.get(cond.dispositivo, "")
            return disp_estado.lower() == cond.estado.lower()

        elif isinstance(cond, CondicaoLogica):
            esq = self._avaliar_condicao(cond.esquerda)
            dir_ = self._avaliar_condicao(cond.direita)
            if cond.operador_logico == "e":
                return esq and dir_
            else:
                return esq or dir_

        return False

    def step(self) -> Dict[str, Any]:
        """
        Executa um ciclo da máquina de estados:
        1. Executa ações associadas ao estado atual.
        2. Avalia condições de transição para o próximo estado.
        """
        self.ciclo += 1
        estado_inicio = self.estado_atual
        acoes_executadas: List[str] = []

        # 1. Executar ações
        for acao in self.acoes_por_estado.get(self.estado_atual, []):
            args_str = f" {', '.join(str(a) for a in acao.argumentos)}" if acao.argumentos else ""
            msg = f"{acao.dispositivo} {acao.comando}{args_str}"
            acoes_executadas.append(msg)
            self.historico_acoes.append(f"Ciclo {self.ciclo} [{self.estado_atual}]: {msg}")

        # 2. Avaliar transições
        transicao_ocorrida = None
        for trans in self.transicoes_por_estado.get(self.estado_atual, []):
            if self._avaliar_condicao(trans.condicao):
                transicao_ocorrida = trans
                self.estado_anterior = self.estado_atual
                self.estado_atual = trans.destino
                break

        return {
            "ciclo": self.ciclo,
            "estado_anterior": estado_inicio,
            "estado_atual": self.estado_atual,
            "mudou_de_estado": (estado_inicio != self.estado_atual),
            "transicao": transicao_ocorrida,
            "acoes": acoes_executadas,
        }

    def run_interactive(self):
        """Roda a simulação em modo interativo de linha de comando."""
        print(f"\n=======================================================")
        print(f" SIMULADOR INTERATIVO EmState: {self.nome_sistema}")
        print(f"=======================================================")
        print(f"Estado Inicial: {self.estado_atual}")
        print("Comandos disponíveis:")
        print("  step                  - Executa um ciclo da FSM")
        print("  set <var> <valor>     - Ex: set corrente 2.5")
        print("  event <disp> <estado> - Ex: event botao pressionado")
        print("  status                - Mostra estado atual e sensores")
        print("  reset                 - Reinicia para o estado inicial")
        print("  exit / quit           - Encerra o simulador\n")

        while True:
            try:
                line = input(f"[{self.nome_sistema} | {self.estado_atual}] > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nEncerrando simulação.")
                break

            if not line:
                continue

            parts = line.split()
            cmd = parts[0].lower()

            if cmd in ("exit", "quit", "sair"):
                print("Simulação finalizada.")
                break

            elif cmd == "step":
                res = self.step()
                print(f"--- Ciclo {res['ciclo']} ---")
                if res['acoes']:
                    for ac in res['acoes']:
                        print(f"  [ATUADOR] {ac}")
                else:
                    print("  [Nenhuma ação executada]")
                if res['mudou_de_estado']:
                    print(f"  >>> Transição de Estado: {res['estado_anterior']} -> {res['estado_atual']}")
                else:
                    print(f"  Permanecendo no estado: {res['estado_atual']}")

            elif cmd == "set" and len(parts) >= 3:
                var = parts[1]
                try:
                    val = float(parts[2])
                    self.set_variavel(var, val)
                    print(f"  Variável '{var}' definida para {val}")
                except ValueError:
                    print(f"  Valor inválido: '{parts[2]}'")

            elif cmd == "event" and len(parts) >= 3:
                disp = parts[1]
                est = parts[2]
                self.set_evento_dispositivo(disp, est)
                print(f"  Evento registrado: {disp} -> {est}")

            elif cmd == "clear" and len(parts) >= 2:
                self.clear_evento_dispositivo(parts[1])
                print(f"  Evento de {parts[1]} limpo.")

            elif cmd == "status":
                print(f"  Estado Atual: {self.estado_atual}")
                print(f"  Ciclos Executados: {self.ciclo}")
                print(f"  Variáveis/Sensores: {self.variaveis}")
                print(f"  Eventos Ativos: {self.eventos_dispositivos}")

            elif cmd == "reset":
                self.estado_atual = self.estados[0]
                self.ciclo = 0
                self.variaveis.clear()
                self.eventos_dispositivos.clear()
                print(f"  Sistema reiniciado para estado: {self.estado_atual}")

            else:
                print(f"  Comando desconhecido. Digite 'step', 'set <var> <val>', 'event <disp> <est>' ou 'status'.")
