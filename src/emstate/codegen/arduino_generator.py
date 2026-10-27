"""
Gerador de Código Arduino (C++) para a linguagem EmState.
Gera um sketch completo (.ino) com setup(), loop() e mapeamento para hardware Arduino.
"""

from typing import List, Dict, Set
from ..ast_nodes import (
    ProgramaEmState,
    Transicao,
    Condicao,
    CondicaoRelacional,
    CondicaoEstadoDispositivo,
    CondicaoLogica,
    Acao,
)
from ..symbol_table import SymbolTable


class ArduinoGenerator:
    def __init__(self, ast: ProgramaEmState, symbol_table: SymbolTable):
        self.ast = ast
        self.symbol_table = symbol_table
        self.nome_sistema = ast.nome_sistema or "SistemaEmState"

    def _sanitize_name(self, name: str) -> str:
        return "".join(c if c.isalnum() or c == '_' else '_' for c in name)

    def _estado_enum_name(self, estado: str) -> str:
        return f"ESTADO_{self._sanitize_name(estado).upper()}"

    def _func_acao_name(self, acao: Acao) -> str:
        disp = self._sanitize_name(acao.dispositivo).lower()
        cmd = self._sanitize_name(acao.comando).capitalize()
        return f"{disp}{cmd}"

    def _condicao_para_arduino(self, cond: Condicao) -> str:
        if isinstance(cond, CondicaoRelacional):
            var_func = f"obter_{self._sanitize_name(cond.variavel)}()"
            val = cond.valor
            if isinstance(val, str):
                val = f'"{val}"'
            return f"({var_func} {cond.operador} {val})"

        elif isinstance(cond, CondicaoEstadoDispositivo):
            disp = self._sanitize_name(cond.dispositivo).lower()
            estado = self._sanitize_name(cond.estado).capitalize()
            return f"{disp}{estado}()"

        elif isinstance(cond, CondicaoLogica):
            op = "&&" if cond.operador_logico == "e" else "||"
            esq = self._condicao_para_arduino(cond.esquerda)
            dir_ = self._condicao_para_arduino(cond.direita)
            return f"({esq} {op} {dir_})"

        return "true"

    def generate_sketch(self) -> str:
        primeiro_estado = self.ast.declaracoes_estados[0].nome if self.ast.declaracoes_estados else "PARADO"
        enum_inicial = self._estado_enum_name(primeiro_estado)

        lines = [
            f"/**",
            f" * Sketch Arduino gerado automaticamente pelo compilador EmState",
            f" * Sistema: {self.nome_sistema}",
            f" */",
            f"",
            f"// Definições de Estados",
            f"enum Estado {{",
        ]

        estados = [decl.nome for decl in self.ast.declaracoes_estados]
        for idx, est in enumerate(estados):
            comma = "," if idx < len(estados) - 1 else ""
            lines.append(f"  {self._estado_enum_name(est)}{comma}")

        lines.extend([
            f"}};",
            f"",
            f"Estado estadoAtual = {enum_inicial};",
            f"Estado estadoAnterior = {enum_inicial};",
            f"",
            f"// Mapeamento de pinos do microcontrolador (Ajuste conforme sua placa)",
            f"#define PINO_BOTAO     2",
            f"#define PINO_LED       13",
            f"#define PINO_MOTOR_PWM 9",
            f"#define PINO_BUZZER    8",
            f"",
            f"// Funções de leitura de sensores e condições",
        ])

        # Funções de leitura
        for var in self.symbol_table.variaveis_sensores.keys():
            lines.append(f"float obter_{self._sanitize_name(var)}() {{")
            lines.append(f"  // Simulação de leitura analógica ou sensor real")
            lines.append(f"  int valorRaw = analogRead(A0);")
            lines.append(f"  return (valorRaw * 5.0) / 1023.0; // Exemplo de conversão")
            lines.append(f"}}")

        for disp, sym in self.symbol_table.dispositivos.items():
            if sym.metadata.get("tipo") == "sensor":
                for cmd in sym.metadata.get("comandos", []):
                    lines.append(f"bool {disp.lower()}{cmd.capitalize()}() {{")
                    lines.append(f"  return (digitalRead(PINO_BOTAO) == LOW); // Ativo em nível lógico baixo com PULLUP")
                    lines.append(f"}}")

        lines.append(f"\n// Funções de comando de atuadores")

        seen_funcs = set()
        for bloco in self.ast.blocos_acoes:
            for acao in bloco.acoes:
                func = self._func_acao_name(acao)
                if func in seen_funcs:
                    continue
                seen_funcs.add(func)

                disp = acao.dispositivo.lower()
                cmd = acao.comando.lower()

                if acao.argumentos:
                    lines.append(f"void {func}(int valor) {{")
                    if disp == "motor" and cmd == "velocidade":
                        lines.append(f"  int pwm = map(valor, 0, 100, 0, 255);")
                        lines.append(f"  analogWrite(PINO_MOTOR_PWM, pwm);")
                    elif disp == "buzzer" and cmd == "tocar":
                        lines.append(f"  tone(PINO_BUZZER, valor);")
                    lines.append(f'  Serial.print("[ATUADOR] {func}: ");')
                    lines.append(f"  Serial.println(valor);")
                    lines.append(f"}}")
                else:
                    lines.append(f"void {func}() {{")
                    if disp == "motor" and cmd == "parar":
                        lines.append(f"  analogWrite(PINO_MOTOR_PWM, 0);")
                    elif disp == "led" and cmd == "ligar":
                        lines.append(f"  digitalWrite(PINO_LED, HIGH);")
                    elif disp == "led" and cmd == "desligar":
                        lines.append(f"  digitalWrite(PINO_LED, LOW);")
                    elif disp == "buzzer" and cmd == "parar":
                        lines.append(f"  noTone(PINO_BUZZER);")
                    lines.append(f'  Serial.println("[ATUADOR] {func}");')
                    lines.append(f"}}")

        lines.extend([
            f"",
            f"void setup() {{",
            f"  Serial.begin(115200);",
            f"  pinMode(PINO_BOTAO, INPUT_PULLUP);",
            f"  pinMode(PINO_LED, OUTPUT);",
            f"  pinMode(PINO_MOTOR_PWM, OUTPUT);",
            f"  pinMode(PINO_BUZZER, OUTPUT);",
            f'  Serial.println(\"=== Sistema EmState Inicializado: {self.nome_sistema} ===\");',
            f"}}",
            f"",
            f"void loop() {{",
            f"  switch (estadoAtual) {{",
        ])

        # Mapa de ações por estado
        acoes_por_estado: Dict[str, List[Acao]] = {}
        for b in self.ast.blocos_acoes:
            acoes_por_estado[b.nome_estado] = b.acoes

        # Mapa de transições por estado
        transicoes_por_estado: Dict[str, List[Transicao]] = {}
        for t in self.ast.transicoes:
            transicoes_por_estado.setdefault(t.origem, []).append(t)

        for decl in self.ast.declaracoes_estados:
            nome_est = decl.nome
            lines.append(f"    case {self._estado_enum_name(nome_est)}:")

            # Log de mudança de estado
            lines.append(f"      if (estadoAtual != estadoAnterior) {{")
            lines.append(f'        Serial.println("-> Entrando no estado: {nome_est}");')
            lines.append(f"        estadoAnterior = estadoAtual;")
            lines.append(f"      }}")

            # Ações
            acoes = acoes_por_estado.get(nome_est, [])
            for acao in acoes:
                func = self._func_acao_name(acao)
                if acao.argumentos:
                    lines.append(f"      {func}({acao.argumentos[0]});")
                else:
                    lines.append(f"      {func}();")

            # Transições
            trans = transicoes_por_estado.get(nome_est, [])
            for t in trans:
                dest_enum = self._estado_enum_name(t.destino)
                if t.condicao:
                    expr = self._condicao_para_arduino(t.condicao)
                    lines.append(f"      if ({expr}) {{")
                    lines.append(f"        estadoAtual = {dest_enum};")
                    lines.append(f"        break;")
                    lines.append(f"      }}")
                else:
                    lines.append(f"      estadoAtual = {dest_enum};")
                    lines.append(f"      break;")

            lines.append(f"      break;")
            lines.append(f"")

        lines.extend([
            f"  }}",
            f"  delay(100); // Taxa de amostragem da FSM",
            f"}}",
        ])

        return "\n".join(lines)
