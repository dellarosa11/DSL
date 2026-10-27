"""
Analisador Sintático (Parser) para a linguagem EmState.
Constrói a Árvore Sintática Abstrata (AST) a partir do fluxo de tokens.
"""

from typing import List, Optional, Union
from .token import Token, TokenType
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


class ParserError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Erro Sintático [L{line}:C{column}]: {message}")
        self.line = line
        self.column = column


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF

    def _peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def _advance(self) -> Token:
        tok = self._current()
        if self.pos < len(self.tokens):
            self.pos += 1
        return tok

    def _check(self, *token_types: TokenType) -> bool:
        return self._current().type in token_types

    def _match(self, *token_types: TokenType) -> bool:
        for tt in token_types:
            if self._check(tt):
                self._advance()
                return True
        return False

    def _consume(self, token_type: TokenType, error_message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        tok = self._current()
        raise ParserError(f"{error_message}. Encontrado '{tok.value}' ({tok.type.name})", tok.line, tok.column)

    def _skip_newlines(self):
        while self._check(TokenType.NEWLINE):
            self._advance()

    def _skip_empty_and_indents(self):
        while self._current().type in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
            self._advance()

    def parse(self) -> ProgramaEmState:
        """
        Ponto de entrada do parser.
        Programa:
            sistema <Nome>
            (DeclaracaoEstado | Transicao | BlocoAcoes)*
        """
        self._skip_empty_and_indents()

        # Reconhecimento obrigatório de 'sistema <Nome>'
        tok_sis = self._consume(TokenType.KW_SISTEMA, "Esperado comando 'sistema' no início do programa")
        tok_nome = self._consume(TokenType.IDENTIFIER, "Esperado identificador com o nome do sistema após 'sistema'")
        nome_sistema = str(tok_nome.value)
        self._match(TokenType.NEWLINE)

        programa = ProgramaEmState(
            line=tok_sis.line,
            column=tok_sis.column,
            nome_sistema=nome_sistema
        )

        while not self._check(TokenType.EOF):
            self._skip_empty_and_indents()
            if self._check(TokenType.EOF):
                break

            # 1. Palavra 'estado' pode ser declaração simples ou bloco de ações
            if self._check(TokenType.KW_ESTADO):
                self._parse_estado_ou_bloco(programa)
            # 2. Identificador seguido de '->' é uma transição: ORIGEM -> DESTINO ...
            elif self._check(TokenType.IDENTIFIER) and self._peek().type == TokenType.ARROW:
                trans = self._parse_transicao()
                programa.transicoes.append(trans)
            else:
                tok = self._current()
                raise ParserError(
                    f"Comando inesperado: '{tok.value}'. Esperado declaração de estado, transição ou bloco de ações.",
                    tok.line, tok.column
                )

        return programa

    def _parse_estado_ou_bloco(self, programa: ProgramaEmState):
        tok_estado = self._advance()  # consome 'estado'
        tok_id = self._consume(TokenType.IDENTIFIER, "Esperado nome do estado após palavra-chave 'estado'")
        nome_estado = str(tok_id.value)

        # Se houver ':' é um bloco de ações
        if self._match(TokenType.COLON):
            bloco = self._parse_bloco_acoes(nome_estado, tok_estado.line, tok_estado.column)
            # Se o mesmo estado tiver múltiplos blocos de ações, podemos fundir ou adicionar
            existente = next((b for b in programa.blocos_acoes if b.nome_estado == nome_estado), None)
            if existente:
                existente.acoes.extend(bloco.acoes)
            else:
                programa.blocos_acoes.append(bloco)
        else:
            # É uma declaração de estado simples: 'estado PARADO'
            self._skip_newlines()
            programa.declaracoes_estados.append(
                DeclaracaoEstado(line=tok_estado.line, column=tok_estado.column, nome=nome_estado)
            )

    def _parse_bloco_acoes(self, nome_estado: str, line: int, column: int) -> BlocoAcoesEstado:
        """
        Analisa o bloco de ações de um estado:
        estado PARADO:
            motor parar
            led ligar
        """
        bloco = BlocoAcoesEstado(line=line, column=column, nome_estado=nome_estado)
        self._skip_newlines()

        # Bloco pode começar com INDENT ou comandos diretos se na mesma linha
        has_indent = self._match(TokenType.INDENT)

        while not self._check(TokenType.EOF):
            self._skip_newlines()

            if has_indent and self._check(TokenType.DEDENT):
                self._advance()
                break

            # Se não usou indentação e encontrou uma nova declaração (estado, transição), encerra o bloco
            if not has_indent:
                if self._check(TokenType.KW_ESTADO) or (self._check(TokenType.IDENTIFIER) and self._peek().type == TokenType.ARROW):
                    break

            if self._check(TokenType.EOF):
                break

            # Uma ação começa com o dispositivo (identificador)
            if self._check(TokenType.IDENTIFIER):
                acao = self._parse_acao()
                bloco.acoes.append(acao)
                self._match(TokenType.NEWLINE)
            else:
                tok = self._current()
                raise ParserError(
                    f"Esperado comando de ação (dispositivo e ação). Encontrado '{tok.value}'",
                    tok.line, tok.column
                )

        return bloco

    def _parse_acao(self) -> Acao:
        """
        Analisa uma ação: <dispositivo> <comando> [<argumentos>...]
        Exemplos:
            motor parar
            motor velocidade 70
            led cor vermelho
            buzzer tocar 1000
        """
        tok_disp = self._advance()
        dispositivo = str(tok_disp.value)

        tok_cmd = self._consume(TokenType.IDENTIFIER, f"Esperado comando de ação para o dispositivo '{dispositivo}'")
        comando = str(tok_cmd.value)

        argumentos: List[Union[int, float, str]] = []
        # Captura argumentos na mesma linha até encontrar NEWLINE, DEDENT, EOF ou outro separador
        while not self._check(TokenType.NEWLINE, TokenType.DEDENT, TokenType.EOF):
            if self._check(TokenType.NUMBER):
                argumentos.append(self._advance().value)
            elif self._check(TokenType.STRING):
                argumentos.append(self._advance().value)
            elif self._check(TokenType.IDENTIFIER):
                argumentos.append(str(self._advance().value))
            elif self._match(TokenType.COMMA):
                continue
            else:
                break

        return Acao(
            line=tok_disp.line,
            column=tok_disp.column,
            dispositivo=dispositivo,
            comando=comando,
            argumentos=argumentos
        )

    def _parse_transicao(self) -> Transicao:
        """
        Analisa uma transição:
        <origem> -> <destino> [quando <condicao>]
        """
        tok_origem = self._advance()  # consome origem
        origem = str(tok_origem.value)

        self._consume(TokenType.ARROW, "Esperado operador '->' após estado de origem")

        tok_destino = self._consume(TokenType.IDENTIFIER, "Esperado estado de destino após '->'")
        destino = str(tok_destino.value)

        condicao = None
        if self._match(TokenType.KW_QUANDO):
            condicao = self._parse_expressao_ou()

        self._match(TokenType.NEWLINE)

        return Transicao(
            line=tok_origem.line,
            column=tok_origem.column,
            origem=origem,
            destino=destino,
            condicao=condicao
        )

    def _parse_expressao_ou(self) -> Condicao:
        """Regra: ExpressaoOu -> ExpressaoE ('ou' ExpressaoE)*"""
        nodo = self._parse_expressao_e()
        while self._match(TokenType.KW_OU):
            direita = self._parse_expressao_e()
            nodo = CondicaoLogica(
                line=nodo.line,
                column=nodo.column,
                operador_logico="ou",
                esquerda=nodo,
                direita=direita
            )
        return nodo

    def _parse_expressao_e(self) -> Condicao:
        """Regra: ExpressaoE -> CondicaoPrimaria ('e' CondicaoPrimaria)*"""
        nodo = self._parse_condicao_primaria()
        while self._match(TokenType.KW_E):
            direita = self._parse_condicao_primaria()
            nodo = CondicaoLogica(
                line=nodo.line,
                column=nodo.column,
                operador_logico="e",
                esquerda=nodo,
                direita=direita
            )
        return nodo

    def _parse_condicao_primaria(self) -> Condicao:
        """
        Analisa uma condição atômica ou entre parênteses:
        - ( expressao )
        - corrente > 2
        - botao pressionado
        """
        if self._match(TokenType.LPAREN):
            cond = self._parse_expressao_ou()
            self._consume(TokenType.RPAREN, "Esperado ')' fechando a condição")
            return cond

        tok_var = self._consume(TokenType.IDENTIFIER, "Esperado nome de variável ou dispositivo na condição")
        identificador = str(tok_var.value)

        # Checa se é operador relacional (==, !=, >, >=, <, <=)
        rel_ops = {
            TokenType.OP_EQ: "==",
            TokenType.OP_NEQ: "!=",
            TokenType.OP_GT: ">",
            TokenType.OP_GTE: ">=",
            TokenType.OP_LT: "<",
            TokenType.OP_LTE: "<="
        }

        curr_type = self._current().type
        if curr_type in rel_ops:
            op_str = rel_ops[curr_type]
            self._advance()
            tok_val = self._current()
            if tok_val.type in (TokenType.NUMBER, TokenType.STRING, TokenType.IDENTIFIER):
                val = self._advance().value
                return CondicaoRelacional(
                    line=tok_var.line,
                    column=tok_var.column,
                    variavel=identificador,
                    operador=op_str,
                    valor=val
                )
            else:
                raise ParserError(
                    f"Esperado valor (número ou texto) após operador relacional '{op_str}'",
                    tok_val.line, tok_val.column
                )

        # Se o próximo token for outro identificador, é um estado/evento de dispositivo:
        # Exemplo: 'botao pressionado', 'sensor ativo', 'chave ligada'
        if self._check(TokenType.IDENTIFIER):
            tok_estado = self._advance()
            return CondicaoEstadoDispositivo(
                line=tok_var.line,
                column=tok_var.column,
                dispositivo=identificador,
                estado=str(tok_estado.value)
            )

        # Se for apenas o identificador isolado (ex: 'quando habilitado' ou 'quando flag')
        return CondicaoEstadoDispositivo(
            line=tok_var.line,
            column=tok_var.column,
            dispositivo=identificador,
            estado="ativo"
        )
