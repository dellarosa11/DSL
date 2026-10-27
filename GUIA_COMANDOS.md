# Guia Completo e Roteiro de Testes: DSL EmState

> **EmState: Uma Linguagem Específica de Domínio para a Descrição de Máquinas de Estados em Sistemas Embarcados**  
> **Autores do Trabalho Acadêmico:**  
> - Matheus Della Rosa (RA: 113209)  
> - Guilherme Marolla Tesch (RA: 113800)  

---

Este documento serve como **manual de instruções e roteiro passo a passo** para qualquer pessoa (avaliador, professor ou desenvolvedor) testar todas as funcionalidades do compilador, do analisador e do simulador da linguagem **EmState**.

---

## 📌 0. Resumo Executivo: Para que serve esse projeto?

O **EmState** é uma **Linguagem de Programação Específica de Domínio (DSL)** acompanhada de seu próprio **compilador completo**, desenvolvida para simplificar a criação de máquinas de estados em **sistemas embarcados** (microcontroladores, motores, robôs, sensores e atuadores).

### 1. O Problema que ele resolve
Tradicionalmente, para implementar máquinas de estados em C ou C++ em sistemas embarcados (ex: controle de motor com proteção contra sobrecorrente), o desenvolvedor precisa escrever manualmente dezenas de linhas de código com variáveis de controle soltas, múltiplos `switch-case`, `if/else` aninhados e chamadas dispersas de pinos. Esse processo é repetitivo, difícil de manter e propenso a falhas.

### 2. A Solução (O que ele faz)
Em vez de programar tudo manualmente em C, o usuário descreve o comportamento do sistema de forma declarativa, limpa e próxima ao domínio:
```emstate
sistema ControleMotor
estado PARADO
estado FUNCIONANDO
estado ERRO

PARADO -> FUNCIONANDO quando botao pressionado
FUNCIONANDO -> ERRO quando corrente > 2

estado FUNCIONANDO:
    motor velocidade 70
```

A partir dessa descrição simples, o compilador EmState:
1. **Valida a lógica e a sintaxe:** Detecta erros antes de qualquer gravação na placa (ex: estados inexistentes, declarações duplicadas ou comandos com valores fora de faixa).
2. **Gera código C99 e Arduino (.ino) automaticamente:** Cria a implementação otimizada com `switch (estadoAtual)`, enums tipados e stubs de hardware, eliminando a codificação manual da máquina de estados.
3. **Simula o sistema no terminal:** Permite acionar botões virtuais e injetar valores de sensores em tempo real para verificar transições e atuadores antes de ligar o circuito físico.
4. **Exporta diagramas visuais:** Gera gráficos de estados em formato Mermaid e Graphviz DOT.

### 3. Objetivo Acadêmico
O projeto serve como implementação prática completa para as disciplinas de **Compiladores** e **Teoria da Computação**, contemplando todo o pipeline clássico de tradução de linguagens:
$$\text{Código EmState (.ems)} \;\longrightarrow\; \text{Léxico} \;\longrightarrow\; \text{Sintático (AST)} \;\longrightarrow\; \text{Semântico} \;\longrightarrow\; \text{Código C / Arduino}$$

---

## 💻 1. Pré-Requisitos e Ambiente

1. **Python 3.8 ou superior** instalado.
   - Para verificar no terminal:
     ```powershell
     python --version
     ```
2. **Dependências Externas:** **Nenhuma!** O compilador foi desenvolvido em Python puro, utilizando apenas a biblioteca padrão. Não é necessário executar `pip install` de bibliotecas externas para rodar os testes, compilar ou simular.
3. **Diretório de Trabalho:** Abra o terminal (PowerShell, CMD ou terminal do VS Code) diretamente na pasta raiz do projeto (`DSL`):
   ```powershell
   cd c:\Users\mathe\Desktop\DSL
   ```

---

## ⚡ 2. Roteiro de Teste Rápido (Passo a Passo de 3 Minutos)

Se você tem pouco tempo e quer testar tudo de ponta a ponta, siga esta sequência numerada:

### Passo 1: Executar todos os testes automatizados
Valida que todas as etapas do compilador estão íntegras e funcionando 100%:
```powershell
python -m unittest discover -s tests -v
```
*Resultado esperado:* 15 testes executados com status `OK`.

---

### Passo 2: Validar o exemplo oficial do artigo acadêmico
Executa as análises léxica, sintática e semântica com exibição da tabela de símbolos:
```powershell
python emstate.py check examples/controle_motor.ems -v
```
*Resultado esperado:* Mensagem de sucesso, identificação dos 3 estados (`PARADO`, `FUNCIONANDO`, `ERRO`) e a tabela de símbolos de atuadores e sensores.

---

### Passo 3: Visualizar a Árvore Sintática Abstrata (AST)
Exibe a árvore exatamente no modelo proposto na **Seção III-C (página 2 do artigo)**:
```powershell
python emstate.py ast examples/controle_motor.ems
```
*Resultado esperado:* Exibição formatada com nós de transição, condições (`corrente > 2`, `botao pressionado`) e blocos de ações.

---

### Passo 4: Compilar para C99 (Padrão para Sistemas Embarcados)
Gera os arquivos C correspondentes ao exemplo:
```powershell
python emstate.py compile examples/controle_motor.ems -o build -t c
```
*Arquivos gerados em `build/`:*
- `build/ControleMotor.h`: Declaração dos enums de estado e protótipos de funções de controle e periféricos.
- `build/ControleMotor.c`: Implementação da FSM com `switch (estadoAtual)` conforme a **Seção III-E**.
- `build/simulacao_ControleMotor.c`: Executável com `main()` e stubs de hardware para testes no PC.

---

### Passo 5: Compilar para Arduino (.ino)
Gera um sketch pronto para gravação em microcontroladores ou simuladores online (como Wokwi):
```powershell
python emstate.py compile examples/controle_motor.ems -o build -t arduino
```
*Arquivo gerado:* `build/ControleMotor.ino` contendo `setup()`, `loop()`, pinagem e chamadas de hardware (`analogWrite`, `digitalRead`, `tone`).

---

### Passo 6: Rodar o Simulador Interativo em Tempo Real
Permite testar as transições e saídas sem precisar de microcontrolador ou de compilar C:
```powershell
python emstate.py simulate examples/controle_motor.ems
```
*Dentro do simulador, digite exatamente esta sequência para ver as transições em ação:*
```text
step
event botao pressionado
step
clear botao
step
set corrente 3.5
step
status
exit
```

---

### Passo 7: Gerar o Diagrama de Estados Visual (Mermaid)
Exporta a máquina de estados para visualização gráfica:
```powershell
python emstate.py diagram examples/controle_motor.ems -f mermaid -o build/diagrama.mmd
```
*Dica:* Abra o arquivo gerado `build/diagrama.mmd` no VS Code ou visualize direto no [Mermaid Live Editor](https://mermaid.live).

---

## 🛠️ 3. Referência Completa de Comandos da CLI

| Comando | Sintaxe | Descrição |
| :--- | :--- | :--- |
| **`check`** | `python emstate.py check <arq.ems> [-v]` | Análises léxica, sintática e semântica + tabela de símbolos |
| **`ast`** | `python emstate.py ast <arq.ems>` | Exibe a Árvore Sintática Abstrata (AST) em formato de árvore |
| **`compile`** | `python emstate.py compile <arq.ems> [-o <dir>] [-t <c\|arduino>]` | Compila para C99 ou Arduino |
| **`simulate`** | `python emstate.py simulate <arq.ems>` | Inicia o simulador interativo via terminal |
| **`diagram`** | `python emstate.py diagram <arq.ems> [-f <mermaid\|dot>] [-o <arq>]` | Exporta diagrama de estados |

---

## 🧪 4. Bateria de Testes de Erros (Conforme Seção III-G do Artigo)

O artigo acadêmico especifica explicitamente que o compilador deve identificar e reportar adequadamente situações de erro. Foram criados cenários específicos para demonstrar essas verificações:

### Teste de Erro 1: Estado de Destino Não Declarado
```powershell
python emstate.py check examples/erros/estado_nao_declarado.ems
```
*Saída observada:*
```text
[ERRO SEMÂNTICO] Erro Semântico [L7:C1]: Estado de destino 'MANUTENCAO' não foi declarado
```

### Teste de Erro 2: Estado Declarado Mais de uma Vez (Duplicata)
```powershell
python emstate.py check examples/erros/estado_duplicado.ems
```
*Saída observada:*
```text
[ERRO SEMÂNTICO] Erro Semântico [L6:C1]: Estado 'LIGADO' declarado mais de uma vez (declaração duplicada)
```

### Teste de Erro 3: Sintaxe Incorreta na Transição (Falta operador `->`)
```powershell
python emstate.py check examples/erros/sintaxe_invalida.ems
```
*Saída observada:*
```text
[ERRO SINTÁTICO] Erro Sintático [L7:C1]: Comando inesperado: 'A'. Esperado declaração de estado, transição ou bloco de ações.
```

### Teste de Erro 4: Parâmetro Fora da Faixa Física Permitida (Velocidade do motor > 100%)
```powershell
python emstate.py check examples/erros/valor_invalido.ems
```
*Saída observada:*
```text
[ERRO SEMÂNTICO] Erro Semântico [L10:C1]: Velocidade do motor deve estar entre 0 e 100%. Recebido: 250
```

---

## 💡 5. Outros Exemplos Prontos para Testar

Além do exemplo do artigo (`controle_motor.ems`), a pasta `examples/` contém outros sistemas embarcados completos:

1. **Semáforo Inteligente com Pedestre:**
   ```powershell
   python emstate.py check examples/semaforo.ems -v
   python emstate.py diagram examples/semaforo.ems -f mermaid
   python emstate.py compile examples/semaforo.ems -o build -t c
   ```
2. **Sistema de Alarme Residencial (com sensor de presença, buzzer e LED):**
   ```powershell
   python emstate.py check examples/alarme_residencial.ems
   python emstate.py simulate examples/alarme_residencial.ems
   ```
3. **Estufa Inteligente (controle de temperatura com aquecedor e cooler):**
   ```powershell
   python emstate.py check examples/estufa_inteligente.ems
   python emstate.py ast examples/estufa_inteligente.ems
   ```

---

## 🎮 6. Comandos Aceitos no Simulador Interativo (`simulate`)

Quando você inicia o simulador (`python emstate.py simulate <arquivo.ems>`), ele abre um prompt interativo no formato `[NomeDoSistema | ESTADO_ATUAL] > `.

Os comandos disponíveis são:

| Comando | O que faz | Exemplo |
| :--- | :--- | :--- |
| **`step`** | Executa um ciclo de clock: aciona as ações do estado atual e avalia se há transição para outro estado | `step` |
| **`event <disp> <est>`** | Simula um sinal de botão ou sensor booleano | `event botao pressionado` |
| **`set <var> <val>`** | Modifica o valor de uma variável contínua (corrente, temperatura, tempo) | `set corrente 2.5` |
| **`clear <disp>`** | Limpa o evento ativo de um dispositivo | `clear botao` |
| **`status`** | Mostra o estado atual, ciclos decorridos e tabela de sensores ativos | `status` |
| **`reset`** | Retorna a máquina de estados para o estado inicial | `reset` |
| **`exit`** | Sai do simulador | `exit` |

---

## 🗺️ 7. Mapeamento Direto com as Seções do Artigo Acadêmico

Para facilitar a correção e avaliação do trabalho pelos professores, a tabela abaixo mapeia cada requisito do artigo acadêmico para o arquivo implementado no projeto:

| Requisito do Artigo | Seção no Artigo | Arquivo Implementado no Projeto |
| :--- | :--- | :--- |
| **Gramática Formal da DSL** | Seção III-B | [`grammar.ebnf`](file:///c:/Users/mathe/Desktop/DSL/grammar.ebnf) |
| **Análise Léxica (Tokens)** | Seção III-C | [`src/emstate/lexer.py`](file:///c:/Users/mathe/Desktop/DSL/src/emstate/lexer.py), [`src/emstate/token.py`](file:///c:/Users/mathe/Desktop/DSL/src/emstate/token.py) |
| **Análise Sintática e AST** | Seção III-C | [`src/emstate/parser.py`](file:///c:/Users/mathe/Desktop/DSL/src/emstate/parser.py), [`src/emstate/ast_nodes.py`](file:///c:/Users/mathe/Desktop/DSL/src/emstate/ast_nodes.py) |
| **Tabela de Símbolos** | Seção III-D | [`src/emstate/symbol_table.py`](file:///c:/Users/mathe/Desktop/DSL/src/emstate/symbol_table.py) |
| **Análise Semântica (Validações)**| Seção III-D | [`src/emstate/semantic.py`](file:///c:/Users/mathe/Desktop/DSL/src/emstate/semantic.py) |
| **Gerador de Código C/C++** | Seção III-E | [`src/emstate/codegen/c_generator.py`](file:///c:/Users/mathe/Desktop/DSL/src/emstate/codegen/c_generator.py) |
| **Gerador Arduino** | Seção III-E | [`src/emstate/codegen/arduino_generator.py`](file:///c:/Users/mathe/Desktop/DSL/src/emstate/codegen/arduino_generator.py) |
| **Simulador Interativo** | Seção III-G | [`src/emstate/simulator.py`](file:///c:/Users/mathe/Desktop/DSL/src/emstate/simulator.py) |
| **Cenários de Teste Válidos e Erros** | Seção III-G | [`examples/`](file:///c:/Users/mathe/Desktop/DSL/examples/), [`tests/`](file:///c:/Users/mathe/Desktop/DSL/tests/) |

---

## 📂 8. Estrutura dos Arquivos no Repositório

```text
DSL/
├── README.md                      # Documentação geral do projeto
├── GUIA_COMANDOS.md               # Este guia passo a passo para testes
├── grammar.ebnf                   # Especificação formal da gramática em EBNF
├── pyproject.toml                 # Metadados de empacotamento
├── emstate.py                     # Script executável da CLI na raiz
├── src/
│   └── emstate/                   # Código-fonte modular do compilador
│       ├── lexer.py               # Analisador Léxico
│       ├── parser.py              # Analisador Sintático
│       ├── ast_nodes.py           # Nós da AST
│       ├── symbol_table.py        # Tabela de Símbolos
│       ├── semantic.py            # Analisador Semântico
│       ├── simulator.py           # Simulador FSM
│       ├── visualizer.py          # Gerador Mermaid/DOT
│       └── codegen/               # Geradores de Código
├── examples/                      # Exemplos válidos e casos de erro
└── tests/                         # Suíte de testes unitários (unittest)
```
