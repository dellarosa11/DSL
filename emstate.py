#!/usr/bin/env python3
"""
Ponto de entrada do Compilador EmState.
Linguagem Específica de Domínio para Máquinas de Estados em Sistemas Embarcados.

Autores do Trabalho Acadêmico:
Matheus Della Rosa (RA: 113209)
Guilherme Marolla Tesch (RA: 113800)
"""

import sys
from pathlib import Path

# Adiciona o diretório 'src' ao sys.path para importações relativas e absolutas
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from emstate.cli import main

if __name__ == "__main__":
    main()
