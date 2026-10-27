"""
Interface de Linha de Comando (CLI) para o Compilador da DSL EmState.
Suporta checagem, visualização da AST, compilação para C/Arduino, simulação e diagramas.
"""

import argparse
import sys
import os
from pathlib import Path

from .lexer import Lexer, LexerError
from .parser import Parser, ParserError
from .semantic import SemanticAnalyzer, SemanticError
from .codegen import CCodeGenerator, ArduinoGenerator
from .simulator import Simulator
from .visualizer import StateMachineVisualizer


def processar_arquivo(caminho_arquivo: str):
    """Lê e processa um arquivo EmState pelas etapas de Léxico, Sintático e Semântico."""
    if not os.path.exists(caminho_arquivo):
        print(f"[ERRO] Arquivo não encontrado: {caminho_arquivo}", file=sys.stderr)
        sys.exit(1)

    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        codigo = f.read()

    # 1. Análise Léxica
    lexer = Lexer(codigo)
    try:
        tokens = lexer.tokenize()
    except LexerError as e:
        print(f"[ERRO LÉXICO] {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Análise Sintática
    parser = Parser(tokens)
    try:
        ast = parser.parse()
    except ParserError as e:
        print(f"[ERRO SINTÁTICO] {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Análise Semântica
    analyzer = SemanticAnalyzer()
    try:
        symbol_table = analyzer.analyze(ast)
    except SemanticError as e:
        print(f"[ERRO SEMÂNTICO] {e}", file=sys.stderr)
        sys.exit(1)

    return ast, symbol_table, analyzer.warnings


def cmd_check(args):
    print(f"-> Verificando programa EmState: {args.arquivo}")
    ast, symbol_table, warnings = processar_arquivo(args.arquivo)

    print(f"[SUCESSO] Código léxica, sintática e semanticamente válido!")
    print(f"Sistema: {ast.nome_sistema}")
    print(f"Estados ({len(ast.declaracoes_estados)}): {', '.join(d.nome for d in ast.declaracoes_estados)}")
    print(f"Transições ({len(ast.transicoes)})")

    if warnings:
        print("\n--- Avisos Semânticos ---")
        for w in warnings:
            print(f"  [AVISO] {w}")

    if args.verbose:
        print("\n" + symbol_table.dump())


def cmd_ast(args):
    ast, _, _ = processar_arquivo(args.arquivo)
    print("\n=== ÁRVORE SINTÁTICA ABSTRATA (AST) ===")
    print(ast.to_tree())
    print("=======================================\n")


def cmd_compile(args):
    ast, symbol_table, warnings = processar_arquivo(args.arquivo)

    if warnings:
        for w in warnings:
            print(f"[AVISO] {w}")

    target = args.target.lower()
    base_name = ast.nome_sistema or "SistemaEmState"
    out_dir = Path(args.output) if args.output else Path(".")

    if out_dir.is_dir() or not out_dir.suffix:
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir.parent.mkdir(parents=True, exist_ok=True)

    if target == "c":
        c_gen = CCodeGenerator(ast, symbol_table)
        h_code = c_gen.generate_header()
        c_code = c_gen.generate_source()
        sim_code = c_gen.generate_simulation_main()

        h_path = out_dir / f"{base_name}.h" if out_dir.is_dir() else out_dir.with_suffix(".h")
        c_path = out_dir / f"{base_name}.c" if out_dir.is_dir() else out_dir.with_suffix(".c")
        sim_path = out_dir / f"simulacao_{base_name}.c" if out_dir.is_dir() else out_dir.parent / f"sim_{out_dir.stem}.c"

        with open(h_path, "w", encoding="utf-8") as f:
            f.write(h_code)
        with open(c_path, "w", encoding="utf-8") as f:
            f.write(c_code)
        with open(sim_path, "w", encoding="utf-8") as f:
            f.write(sim_code)

        print(f"[COMPILADO COM SUCESSO]")
        print(f"  - Header C:       {h_path}")
        print(f"  - Implementação: {c_path}")
        print(f"  - Simulação PC:   {sim_path}")

    elif target in ("arduino", "cpp"):
        ard_gen = ArduinoGenerator(ast, symbol_table)
        ino_code = ard_gen.generate_sketch()
        ino_path = out_dir / f"{base_name}.ino" if out_dir.is_dir() else out_dir.with_suffix(".ino")

        with open(ino_path, "w", encoding="utf-8") as f:
            f.write(ino_code)

        print(f"[COMPILADO COM SUCESSO]")
        print(f"  - Sketch Arduino: {ino_path}")
    else:
        print(f"[ERRO] Alvo desconhecido: '{target}'. Use 'c' ou 'arduino'.", file=sys.stderr)
        sys.exit(1)


def cmd_simulate(args):
    ast, _, _ = processar_arquivo(args.arquivo)
    sim = Simulator(ast)
    sim.run_interactive()


def cmd_diagram(args):
    ast, _, _ = processar_arquivo(args.arquivo)
    viz = StateMachineVisualizer(ast)
    fmt = args.format.lower()

    if fmt == "mermaid" or (args.output and args.output.endswith(".mmd")):
        content = viz.to_mermaid()
    else:
        content = viz.to_dot()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[DIAGRAMA GERADO]: {args.output}")
    else:
        print(content)


def main():
    parser = argparse.ArgumentParser(
        prog="emstate",
        description="Compilador e Ferramentas para a DSL EmState (Máquinas de Estados para Sistemas Embarcados)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Subcomando 'check'
    p_check = subparsers.add_parser("check", help="Executa análises léxica, sintática e semântica")
    p_check.add_argument("arquivo", help="Caminho para o arquivo .ems")
    p_check.add_argument("-v", "--verbose", action="store_true", help="Exibe tabela de símbolos detalhada")
    p_check.set_defaults(func=cmd_check)

    # Subcomando 'ast'
    p_ast = subparsers.add_parser("ast", help="Exibe a Árvore Sintática Abstrata (AST)")
    p_ast.add_argument("arquivo", help="Caminho para o arquivo .ems")
    p_ast.set_defaults(func=cmd_ast)

    # Subcomando 'compile'
    p_comp = subparsers.add_parser("compile", help="Compila o código EmState para linguagem de destino (C/Arduino)")
    p_comp.add_argument("arquivo", help="Caminho para o arquivo .ems")
    p_comp.add_argument("-o", "--output", default="build", help="Diretório ou arquivo de saída")
    p_comp.add_argument("-t", "--target", default="c", choices=["c", "arduino", "cpp"], help="Linguagem alvo (padrão: c)")
    p_comp.set_defaults(func=cmd_compile)

    # Subcomando 'simulate'
    p_sim = subparsers.add_parser("simulate", help="Inicia o simulador interativo no terminal")
    p_sim.add_argument("arquivo", help="Caminho para o arquivo .ems")
    p_sim.set_defaults(func=cmd_simulate)

    # Subcomando 'diagram'
    p_diag = subparsers.add_parser("diagram", help="Gera diagrama de estados (Mermaid ou Graphviz DOT)")
    p_diag.add_argument("arquivo", help="Caminho para o arquivo .ems")
    p_diag.add_argument("-f", "--format", default="mermaid", choices=["mermaid", "dot"], help="Formato do diagrama")
    p_diag.add_argument("-o", "--output", help="Arquivo de saída (opcional, imprime na tela se omitido)")
    p_diag.set_defaults(func=cmd_diagram)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
