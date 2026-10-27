"""
Analisador Semântico para a linguagem EmState.
Valida regras semânticas descritas na Seção III-D do artigo:
- Existência dos estados de origem e destino
- Identificação de declarações duplicadas
- Validade dos comandos de ação
- Validade dos valores em condições e comandos
- Tabela de símbolos e verificação de alcance dos estados
"""

from typing import List, Dict, Set, Optional
from .ast_nodes import (
    ProgramaEmState,
    DeclaracaoEstado,
    Transicao,
    Condicao,
    CondicaoRelacional,
    CondicaoEstadoDispositivo,
    CondicaoLogica,
    BlocoAcoesEstado,
    Acao,
)
from .symbol_table import SymbolTable


class SemanticError(Exception):
    def __init__(self, message: str, line: int = 1, column: int = 1):
        super().__init__(f"Erro Semântico [L{line}:C{column}]: {message}")
        self.line = line
        self.column = column


class SemanticWarning:
    def __init__(self, message: str, line: int = 1, column: int = 1):
        self.message = message
        self.line = line
        self.column = column

    def __str__(self) -> str:
        return f"Aviso Semântico [L{self.line}:C{self.column}]: {self.message}"


class SemanticAnalyzer:
    # Catálogo de comandos e restrições para dispositivos padrão de sistemas embarcados
    DISPOSITIVOS_PADRAO = {
        "motor": {
            "comandos": {"parar", "ligar", "velocidade", "reverso", "frente", "direcao"},
            "regras": {
                "velocidade": lambda args, line, col: SemanticAnalyzer._validar_velocidade_motor(args, line, col),
                "parar": lambda args, line, col: None,
                "ligar": lambda args, line, col: None,
            }
        },
        "led": {
            "comandos": {"ligar", "desligar", "alternar", "cor", "piscar"},
            "regras": {
                "piscar": lambda args, line, col: SemanticAnalyzer._validar_positivo(args, "tempo de piscar", line, col),
            }
        },
        "buzzer": {
            "comandos": {"ligar", "desligar", "parar", "bipar", "tocar"},
            "regras": {
                "tocar": lambda args, line, col: SemanticAnalyzer._validar_positivo(args, "frequência/duração do buzzer", line, col),
            }
        },
        "rele": {
            "comandos": {"ligar", "desligar", "ativar", "desativar"}
        },
        "valvula": {
            "comandos": {"abrir", "fechar"}
        }
    }

    @staticmethod
    def _validar_velocidade_motor(args: List, line: int, col: int):
        if not args:
            raise SemanticError("Comando 'motor velocidade' exige um valor de velocidade", line, col)
        val = args[0]
        if isinstance(val, (int, float)):
            if val < 0 or val > 100:
                raise SemanticError(f"Velocidade do motor deve estar entre 0 e 100%. Recebido: {val}", line, col)

    @staticmethod
    def _validar_positivo(args: List, nome_param: str, line: int, col: int):
        if args and isinstance(args[0], (int, float)):
            if args[0] <= 0:
                raise SemanticError(f"Valor de {nome_param} deve ser maior que zero. Recebido: {args[0]}", line, col)

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: List[SemanticError] = []
        self.warnings: List[SemanticWarning] = []

    def analyze(self, ast: ProgramaEmState) -> SymbolTable:
        self.symbol_table = SymbolTable()
        self.errors = []
        self.warnings = []

        # 1. Registrar Sistema
        if not ast.nome_sistema:
            self.errors.append(SemanticError("Nome do sistema não foi definido", ast.line, ast.column))
        else:
            self.symbol_table.set_sistema(ast.nome_sistema, ast.line, ast.column)

        # 2. Registrar e validar declarações de estados (identificação de duplicatas)
        if not ast.declaracoes_estados:
            self.errors.append(SemanticError("O sistema deve conter ao menos um estado declarado", ast.line, ast.column))

        for decl in ast.declaracoes_estados:
            if not self.symbol_table.add_estado(decl.nome, decl.line, decl.column):
                self.errors.append(
                    SemanticError(f"Estado '{decl.nome}' declarado mais de uma vez (declaração duplicada)", decl.line, decl.column)
                )

        # 3. Validar transições (existência de origem e destino, validade das condições)
        for trans in ast.transicoes:
            # Checa estado de origem
            if not self.symbol_table.has_estado(trans.origem):
                self.errors.append(
                    SemanticError(f"Estado de origem '{trans.origem}' não foi declarado", trans.line, trans.column)
                )
            # Checa estado de destino
            if not self.symbol_table.has_estado(trans.destino):
                self.errors.append(
                    SemanticError(f"Estado de destino '{trans.destino}' não foi declarado", trans.line, trans.column)
                )

            # Analisa condição da transição
            if trans.condicao:
                self._analisar_condicao(trans.condicao)

        # 4. Validar blocos de ações por estado
        for bloco in ast.blocos_acoes:
            if not self.symbol_table.has_estado(bloco.nome_estado):
                self.errors.append(
                    SemanticError(f"Bloco de ações faz referência ao estado não declarado '{bloco.nome_estado}'", bloco.line, bloco.column)
                )

            for acao in bloco.acoes:
                self._analisar_acao(acao)

        # 5. Análise de acessibilidade e estados da máquina (Warnings)
        self._analisar_alcance_estados(ast)

        # Se houver erros semânticos, levanta o primeiro (ou todos)
        if self.errors:
            # Levanta a primeira exceção para compatibilidade, com resumo
            raise self.errors[0]

        return self.symbol_table

    def _analisar_condicao(self, cond: Condicao):
        if isinstance(cond, CondicaoRelacional):
            self.symbol_table.register_variavel_sensor(cond.variavel, cond.line, cond.column)
            # Validação do operador
            if cond.operador not in (">", ">=", "<", "<=", "==", "!="):
                self.errors.append(SemanticError(f"Operador relacional inválido: '{cond.operador}'", cond.line, cond.column))

        elif isinstance(cond, CondicaoEstadoDispositivo):
            self.symbol_table.register_dispositivo(cond.dispositivo, cond.line, cond.column, tipo="sensor")
            self.symbol_table.register_comando_dispositivo(cond.dispositivo, cond.estado)

        elif isinstance(cond, CondicaoLogica):
            self._analisar_condicao(cond.esquerda)
            self._analisar_condicao(cond.direita)

    def _analisar_acao(self, acao: Acao):
        disp = acao.dispositivo.lower()
        cmd = acao.comando.lower()

        self.symbol_table.register_dispositivo(acao.dispositivo, acao.line, acao.column, tipo="atuador")
        self.symbol_table.register_comando_dispositivo(acao.dispositivo, acao.comando)

        # Se for um dispositivo padrão reconhecido
        if disp in self.DISPOSITIVOS_PADRAO:
            info = self.DISPOSITIVOS_PADRAO[disp]
            cmds_permitidos = info.get("comandos", set())
            if cmd not in cmds_permitidos:
                self.warnings.append(
                    SemanticWarning(
                        f"Comando '{cmd}' não é usual para o dispositivo '{disp}'. Comandos padrão: {', '.join(sorted(cmds_permitidos))}",
                        acao.line, acao.column
                    )
                )

            regras = info.get("regras", {})
            if cmd in regras:
                try:
                    regras[cmd](acao.argumentos, acao.line, acao.column)
                except SemanticError as e:
                    self.errors.append(e)
        else:
            # Dispositivo customizado pelo usuário (ex: cooler, porta, sirene)
            self.warnings.append(
                SemanticWarning(
                    f"Dispositivo customizado '{acao.dispositivo}' detectado. Será gerado protótipo de função C/C++ externa.",
                    acao.line, acao.column
                )
            )

    def _analisar_alcance_estados(self, ast: ProgramaEmState):
        if not ast.declaracoes_estados:
            return

        estado_inicial = ast.declaracoes_estados[0].nome
        estados_alcancaveis: Set[str] = {estado_inicial}
        mudou = True

        while mudou:
            mudou = False
            for trans in ast.transicoes:
                if trans.origem in estados_alcancaveis and trans.destino not in estados_alcancaveis:
                    estados_alcancaveis.add(trans.destino)
                    mudou = True

        for decl in ast.declaracoes_estados:
            if decl.nome not in estados_alcancaveis:
                self.warnings.append(
                    SemanticWarning(
                        f"Estado '{decl.nome}' é inalcançável a partir do estado inicial '{estado_inicial}'",
                        decl.line, decl.column
                    )
                )

        # Checa estados sem saída (exceto se for estado final/erro intencional)
        estados_com_saida = {t.origem for t in ast.transicoes}
        for decl in ast.declaracoes_estados:
            if decl.nome not in estados_com_saida:
                self.warnings.append(
                    SemanticWarning(
                        f"Estado '{decl.nome}' não possui transições de saída (estado final ou de parada)",
                        decl.line, decl.column
                    )
                )
