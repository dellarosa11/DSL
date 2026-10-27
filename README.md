# EmState: Uma Linguagem Específica de Domínio para a Descrição de Máquinas de Estados em Sistemas Embarcados

**Autores:**
- **Matheus Della Rosa** (RA: 113209)
- **Guilherme Marolla Tesch** (RA: 113800)

---

## 📖 Visão Geral

A **EmState** é uma Linguagem Específica de Domínio (DSL) projetada para simplificar a modelagem, validação e implementação de máquinas de estados finitos (FSM) em sistemas embarcados. 

Ao invés de codificar manualmente variáveis de controle de estado, cadeias complexas de `if-else` ou `switch-case` com lógica dispersa, a EmState permite descrever o comportamento do sistema de forma declarativa e concisa, próxima aos conceitos do domínio (estados, transições condicionais, sensores e atuadores).

O compilador processa a descrição através de um pipeline completo de compilação e gera automaticamente implementações otimizadas em **C padrão (ISO C99)** e sketches para **Arduino (C++)**, além de fornecer um **simulador interativo** em tempo real e visualizadores em **Mermaid** e **Graphviz DOT**.

---

## 📐 Fluxo de Processamento do Compilador

Conforme especificado no artigo acadêmico (Figura 1):

```
Código-fonte EmState (.ems)
            ↓
     Análise Léxica (Lexer)
            ↓
          Tokens
            ↓
    Análise Sintática (Parser)
            ↓
  Árvore Sintática Abstrata (AST)
            ↓
    Análise Semântica (Semantic)
            ↓
       AST Validada
            ↓
 Gerador de Código (Codegen)
     ↙                     ↘
Código C/C++          Sketch Arduino (.ino)
     ↓                     ↓
Microcontrolador / Simulação em PC
```

---

## 📁 Estrutura do Repositório

```text
DSL/
├── README.md                      # Documentação completa do projeto
├── grammar.ebnf                   # Gramática formal da linguagem em EBNF
├── pyproject.toml                 # Metadados e empacotamento do compilador
├── emstate.py                     # Ponto de entrada CLI direto na raiz
├── src/
│   └── emstate/
│       ├── __init__.py            # Módulo principal
│       ├── token.py               # Definições de tokens e tipos léxicos
│       ├── lexer.py               # Analisador Léxico com rastreio de linha/coluna
│       ├── ast_nodes.py           # Nós da AST com formatador em árvore
│       ├── parser.py              # Analisador Sintático descendente recursivo
│       ├── symbol_table.py        # Tabela de Símbolos
│       ├── semantic.py            # Analisador Semântico e regras de domínio
│       ├── simulator.py           # Simulador / Interpretador interativo FSM
│       ├── visualizer.py          # Gerador de diagramas Mermaid e DOT
│       ├── cli.py                 # Interface de linha de comando (argparse)
│       └── codegen/
│           ├── __init__.py
│           ├── c_generator.py     # Gerador de C99 (.h, .c e simulação PC)
│           └── arduino_generator.py # Gerador de sketches Arduino (.ino)
├── examples/
│   ├── controle_motor.ems         # Exemplo oficial do artigo
│   ├── semaforo.ems               # Semáforo inteligente com pedestre
│   ├── alarme_residencial.ems     # Alarme com sensor de presença e sirene
│   ├── estufa_inteligente.ems     # Controle térmico com cooler e aquecedor
│   └── erros/
│       ├── estado_nao_declarado.ems
│       ├── estado_duplicado.ems
│       ├── sintaxe_invalida.ems
│       └── valor_invalido.ems
└── tests/
    ├── __init__.py
    ├── test_lexer.py              # Testes unitários do Léxico
    ├── test_parser.py             # Testes unitários do Sintático
    ├── test_semantic.py           # Testes unitários do Semântico
    ├── test_codegen.py            # Testes unitários da Geração de Código
    └── test_simulator.py          # Testes unitários da Simulação
```

---

## 📝 Sintaxe da Linguagem

A sintaxe da EmState foi desenhada para ser limpa e direta:

### Exemplo Oficial do Artigo: `ControleMotor.ems`

```emstate
sistema ControleMotor

estado PARADO
estado FUNCIONANDO
estado ERRO

PARADO -> FUNCIONANDO quando botao pressionado
FUNCIONANDO -> PARADO quando botao pressionado
FUNCIONANDO -> ERRO quando corrente > 2

estado PARADO:
    motor parar

estado FUNCIONANDO:
    motor velocidade 70

estado ERRO:
    motor parar
```

### Elementos Principais:
1. **Declaração do Sistema:** `sistema NomeDoSistema`
2. **Declaração de Estados:** `estado NOME_DO_ESTADO`
3. **Transições entre Estados:**
   - Transição com condição de sensor: `PARADO -> FUNCIONANDO quando botao pressionado`
   - Transição com comparação relacional: `FUNCIONANDO -> ERRO quando corrente > 2`
   - Operadores relacionais: `>`, `<`, `>=`, `<=`, `==`, `!=`
   - Conectivos lógicos: `e`, `ou` (ex: `quando botao pressionado e temperatura > 50`)
4. **Ações dos Estados:**
   ```emstate
   estado NOME:
       dispositivo comando [argumentos...]
   ```
   - Motores: `motor parar`, `motor velocidade 70`
   - LEDs: `led ligar`, `led desligar`, `led piscar 500`
   - Buzzer: `buzzer tocar 1000`, `buzzer bipar`, `buzzer parar`
   - Sensores / Atuadores customizados: `rele ligar`, `cooler velocidade 100`

---

## 🚀 Como Usar o Compilador

Você pode executar o compilador diretamente via Python:

### 1. Verificação Léxica, Sintática e Semântica (`check`)
Valida o programa e exibe a tabela de símbolos e avisos:
```bash
python emstate.py check examples/controle_motor.ems -v
```

### 2. Exibição da Árvore Sintática Abstrata (`ast`)
Renderiza a AST exatamente no formato especificado na Seção III-C do artigo:
```bash
python emstate.py ast examples/controle_motor.ems
```

Saída:
```text
=== ÁRVORE SINTÁTICA ABSTRATA (AST) ===
Sistema: ControleMotor
|-- Estados Declarados:
|   |-- Estado declarado: PARADO
|   |-- Estado declarado: FUNCIONANDO
|   `-- Estado declarado: ERRO
|-- Transições:
|   |-- Transição
|   |   |-- origem: PARADO
|   |   |-- destino: FUNCIONANDO
|   |   `-- condição (dispositivo)
|   |       |-- dispositivo: botao
|   |       `-- estado esperado: pressionado
|   |-- Transição
|   |   |-- origem: FUNCIONANDO
|   |   |-- destino: PARADO
|   |   `-- condição (dispositivo)
|   |       |-- dispositivo: botao
|   |       `-- estado esperado: pressionado
|   `-- Transição
|       |-- origem: FUNCIONANDO
|       |-- destino: ERRO
|       `-- condição (relacional)
|           |-- variável: corrente
|           |-- operador: >
|           `-- valor: 2
`-- Blocos de Ações por Estado:
    |-- Bloco de Ações: estado PARADO
    |   `-- Ação
    |       |-- dispositivo: motor
    |       `-- comando: parar
    |-- Bloco de Ações: estado FUNCIONANDO
    |   `-- Ação
    |       |-- dispositivo: motor
    |       `-- comando: velocidade 70
    `-- Bloco de Ações: estado ERRO
        `-- Ação
            |-- dispositivo: motor
            `-- comando: parar
```

### 3. Compilação para C / C++ (`compile`)
Gera o cabeçalho (`.h`), a implementação em switch-case (`.c`) e um arquivo de simulação para desktop (`simulacao_*.c`):
```bash
python emstate.py compile examples/controle_motor.ems -o build -t c
```

Arquivos gerados em `build/`:
- `build/ControleMotor.h`: Definição de `enum Estado_t`, protótipos de `ControleMotor_update()` e drivers.
- `build/ControleMotor.c`: Implementação da FSM em switch-case com tratamento de ações e transições.
- `build/simulacao_ControleMotor.c`: Executável de simulação em desktop com stubs para rodar no PC.

### 4. Compilação para Arduino (`compile -t arduino`)
Gera um sketch `.ino` completo pronto para ser gravado em um Arduino Uno, Nano, ESP32 ou testado no simulador [Wokwi](https://wokwi.com):
```bash
python emstate.py compile examples/controle_motor.ems -o build -t arduino
```

### 5. Simulador Interativo em Terminal (`simulate`)
Permite interagir com a máquina de estados em tempo real sem precisar de compilador C ou hardware externo:
```bash
python emstate.py simulate examples/controle_motor.ems
```
Comandos dentro do simulador:
- `step`: Executa um ciclo da máquina de estados.
- `event botao pressionado`: Dispara o evento de pressionar o botão.
- `set corrente 3.5`: Altera o valor da leitura do sensor de corrente.
- `status`: Exibe o estado atual e valores dos sensores.
- `exit`: Sai do simulador.

### 6. Geração de Diagramas (`diagram`)
Gera diagramas para inclusão em relatórios ou documentação:
```bash
# Formato Mermaid:
python emstate.py diagram examples/controle_motor.ems -f mermaid -o diagrama.mmd

# Formato Graphviz DOT:
python emstate.py diagram examples/controle_motor.ems -f dot -o diagrama.dot
```

---

## 🧪 Suíte de Testes Automatizados

O projeto conta com testes unitários para cada etapa do compilador:

```bash
python -m unittest discover -s tests
```

Resultado:
```text
...............
----------------------------------------------------------------------
Ran 15 tests in 0.007s

OK
```

Casos cobertos:
- Reconhecimento de palavras-chave, identificadores, números e comentários pelo Lexer.
- Construção correta da AST e expressões lógicas pelo Parser.
- Detecção e relatório de erros semânticos (estados não declarados, declarações duplicadas, parâmetros fora de faixa).
- Validação do código C e Arduino gerado.
- Validação do fluxo de execução do Simulador em tempo real.

---

## 📚 Referências

1. M. Mernik, J. Heering, and A. M. Sloane, “When and how to develop domain-specific languages,” *ACM Computing Surveys*, vol. 37, no. 4, pp. 316–344, 2005.
2. A. van Deursen, P. Klint, and J. Visser, “Domain-specific languages: An annotated bibliography,” *ACM SIGPLAN Notices*, vol. 35, no. 6, pp. 26–36, 2000.
3. L. Nascimento et al., “A systematic mapping study on domain-specific languages,” in *ICSEA*, 2012.
4. I. Rodrigues, M. Campos, and A. Zorzo, “Usability evaluation of domain-specific languages: A systematic literature review,” in *International Conference on Human-Computer Interaction*, 2017.
