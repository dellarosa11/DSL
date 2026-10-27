"""
Gerador de Código C (ISO C99) para a linguagem EmState.
Produz arquivos .h e .c baseados em switch-case, conforme Seção III-E do artigo.
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
    BlocoAcoesEstado,
)
from ..symbol_table import SymbolTable


class CCodeGenerator:
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

    def _condicao_para_c(self, cond: Condicao) -> str:
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
            esq = self._condicao_para_c(cond.esquerda)
            dir_ = self._condicao_para_c(cond.direita)
            return f"({esq} {op} {dir_})"

        return "1 /* sempre */"

    def generate_header(self) -> str:
        guard = f"EMSTATE_{self.nome_sistema.upper()}_H"
        lines = [
            "/**",
            f" * Arquivo de Cabecalho gerado automaticamente pelo compilador EmState",
            f" * Sistema: {self.nome_sistema}",
            " */",
            f"#ifndef {guard}",
            f"#define {guard}",
            "",
            "#include <stdbool.h>",
            "#include <stdint.h>",
            "",
            "#ifdef __cplusplus",
            'extern "C" {',
            "#endif",
            "",
            "/* Estados do Sistema */",
            "typedef enum {",
        ]

        estados = [decl.nome for decl in self.ast.declaracoes_estados]
        for idx, est in enumerate(estados):
            comma = "," if idx < len(estados) - 1 else ""
            lines.append(f"    {self._estado_enum_name(est)}{comma}")

        lines.extend([
            f"}} {self.nome_sistema}_Estado_t;",
            "",
            "/* Funcoes de Controle da Maquina de Estados */",
            f"void {self.nome_sistema}_init(void);",
            f"void {self.nome_sistema}_update(void);",
            f"{self.nome_sistema}_Estado_t {self.nome_sistema}_getEstadoAtual(void);",
            f"const char* {self.nome_sistema}_getNomeEstado({self.nome_sistema}_Estado_t estado);",
            "",
            "/* Prototipos de Funcoes de Dispositivos e Sensores */",
        ])

        # Protótipos de sensores/condições
        for var in self.symbol_table.variaveis_sensores.keys():
            lines.append(f"float obter_{self._sanitize_name(var)}(void);")

        for disp, sym in self.symbol_table.dispositivos.items():
            if sym.metadata.get("tipo") == "sensor":
                for cmd in sym.metadata.get("comandos", []):
                    lines.append(f"bool {disp.lower()}{cmd.capitalize()}(void);")

        # Protótipos de atuadores/ações
        for bloco in self.ast.blocos_acoes:
            for acao in bloco.acoes:
                func_name = self._func_acao_name(acao)
                if acao.argumentos:
                    params = []
                    for i, arg in enumerate(acao.argumentos):
                        if isinstance(arg, float):
                            params.append(f"float arg{i+1}")
                        elif isinstance(arg, int):
                            params.append(f"int arg{i+1}")
                        else:
                            params.append(f"const char* arg{i+1}")
                    lines.append(f"void {func_name}({', '.join(params)});")
                else:
                    lines.append(f"void {func_name}(void);")

        # Remover linhas duplicadas preservando ordem
        dedup_lines = []
        seen = set()
        for l in lines:
            if l.startswith("void ") or l.startswith("bool ") or l.startswith("float "):
                if l not in seen:
                    seen.add(l)
                    dedup_lines.append(l)
            else:
                dedup_lines.append(l)

        dedup_lines.extend([
            "",
            "#ifdef __cplusplus",
            "}",
            "#endif",
            "",
            f"#endif /* {guard} */",
        ])

        return "\n".join(dedup_lines)

    def generate_source(self) -> str:
        header_name = f"{self.nome_sistema}.h"
        primeiro_estado = self.ast.declaracoes_estados[0].nome if self.ast.declaracoes_estados else "PARADO"
        enum_inicial = self._estado_enum_name(primeiro_estado)

        lines = [
            "/**",
            f" * Implementacao da Maquina de Estados gerada pelo compilador EmState",
            f" * Sistema: {self.nome_sistema}",
            " */",
            f'#include "{header_name}"',
            "#include <stdio.h>",
            "",
            "/* Estado Atual da Maquina */",
            f"static {self.nome_sistema}_Estado_t estadoAtual = {enum_inicial};",
            "",
            f"void {self.nome_sistema}_init(void) {{",
            f"    estadoAtual = {enum_inicial};",
            "}",
            "",
            f"{self.nome_sistema}_Estado_t {self.nome_sistema}_getEstadoAtual(void) {{",
            "    return estadoAtual;",
            "}",
            "",
            f"const char* {self.nome_sistema}_getNomeEstado({self.nome_sistema}_Estado_t estado) {{",
            "    switch (estado) {",
        ]

        for decl in self.ast.declaracoes_estados:
            lines.append(f'        case {self._estado_enum_name(decl.nome)}: return "{decl.nome}";')

        lines.extend([
            '        default: return "DESCONHECIDO";',
            "    }",
            "}",
            "",
            f"void {self.nome_sistema}_update(void) {{",
            "    switch (estadoAtual) {",
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
            lines.append(f"        case {self._estado_enum_name(nome_est)}:")

            # 1. Executa ações associadas ao estado
            acoes = acoes_por_estado.get(nome_est, [])
            if acoes:
                lines.append(f"            /* Acoes do estado {nome_est} */")
                for acao in acoes:
                    func = self._func_acao_name(acao)
                    if acao.argumentos:
                        args_str = ", ".join(
                            f'"{a}"' if isinstance(a, str) else str(a)
                            for a in acao.argumentos
                        )
                        lines.append(f"            {func}({args_str});")
                    else:
                        lines.append(f"            {func}();")

            # 2. Avalia transições condicionais
            trans = transicoes_por_estado.get(nome_est, [])
            if trans:
                lines.append("            /* Avaliacao de transicoes */")
                for t in trans:
                    dest_enum = self._estado_enum_name(t.destino)
                    if t.condicao:
                        expr_c = self._condicao_para_c(t.condicao)
                        lines.append(f"            if ({expr_c}) {{")
                        lines.append(f"                estadoAtual = {dest_enum};")
                        lines.append("                break;")
                        lines.append("            }")
                    else:
                        lines.append("            /* Transicao incondicional */")
                        lines.append(f"            estadoAtual = {dest_enum};")
                        lines.append("            break;")

            lines.append("            break;")
            lines.append("")

        lines.extend([
            "        default:",
            "            /* Estado indefinido */",
            "            break;",
            "    }",
            "}",
        ])

        return "\n".join(lines)

    def generate_simulation_main(self) -> str:
        """
        Gera um arquivo de simulação executável com implementações mock dos dispositivos.
        """
        header_name = f"{self.nome_sistema}.h"
        lines = [
            "/**",
            f" * Arquivo de Simulacao e Teste para o sistema {self.nome_sistema}",
            " * Implementa stubs com prints para demonstrar o funcionamento da FSM.",
            " */",
            f'#include "{header_name}"',
            "#include <stdio.h>",
            "#include <stdlib.h>",
            "",
            "/* Variaveis de simulacao para sensores */",
        ]

        for var in self.symbol_table.variaveis_sensores.keys():
            lines.append(f"static float sim_{var} = 0.0f;")
            lines.append(f"float obter_{self._sanitize_name(var)}(void) {{ return sim_{var}; }}")

        for disp, sym in self.symbol_table.dispositivos.items():
            if sym.metadata.get("tipo") == "sensor":
                for cmd in sym.metadata.get("comandos", []):
                    lines.append(f"static bool sim_{disp}_{cmd} = false;")
                    lines.append(f"bool {disp.lower()}{cmd.capitalize()}(void) {{ return sim_{disp}_{cmd}; }}")

        # Stubs para atuadores
        seen_funcs = set()
        for bloco in self.ast.blocos_acoes:
            for acao in bloco.acoes:
                func = self._func_acao_name(acao)
                if func in seen_funcs:
                    continue
                seen_funcs.add(func)

                if acao.argumentos:
                    params_decl = []
                    args_print = []
                    for i, arg in enumerate(acao.argumentos):
                        if isinstance(arg, float):
                            params_decl.append(f"float arg{i+1}")
                            args_print.append("%f")
                        elif isinstance(arg, int):
                            params_decl.append(f"int arg{i+1}")
                            args_print.append("%d")
                        else:
                            params_decl.append(f"const char* arg{i+1}")
                            args_print.append("%s")
                    fmt = " ".join(args_print)
                    call_args = ", ".join(f"arg{i+1}" for i in range(len(acao.argumentos)))
                    lines.append(f"void {func}({', '.join(params_decl)}) {{")
                    lines.append(f'    printf("[ATUADOR] {func}({fmt})\\n", {call_args});')
                    lines.append("}")
                else:
                    lines.append(f"void {func}(void) {{")
                    lines.append(f'    printf("[ATUADOR] {func}()\\n");')
                    lines.append("}")

        lines.extend([
            "",
            "int main(void) {",
            f'    printf("=== Iniciando Simulacao do Sistema {self.nome_sistema} ===\\n");',
            f"    {self.nome_sistema}_init();",
            f'    printf("Estado Inicial: %s\\n", {self.nome_sistema}_getNomeEstado({self.nome_sistema}_getEstadoAtual()));',
            "",
            "    for (int ciclo = 1; ciclo <= 5; ciclo++) {",
            f'        printf("\\n--- Ciclo %d (Estado: %s) ---\\n", ciclo, {self.nome_sistema}_getNomeEstado({self.nome_sistema}_getEstadoAtual()));',
            f"        {self.nome_sistema}_update();",
            "    }",
            "",
            '    printf("\\nSimulacao finalizada com sucesso!\\n");',
            "    return 0;",
            "}",
        ])

        return "\n".join(lines)
