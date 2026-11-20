# Como funciona o EmState

O EmState permite descrever o comportamento de um equipamento em um arquivo de texto e testar o resultado no computador. No exemplo do semáforo, você escolhe o valor do tempo ou aperta um botão virtual. O simulador usa as regras do arquivo para decidir qual será a próxima cor.

## Abra o programa e complete uma volta do semáforo

No Windows, dê dois cliques em **Abrir EmState.pyw**, na pasta do projeto. Você também pode abrir o PowerShell nessa pasta e executar `py emstate.py gui`. A janela usa o Tkinter, incluído na instalação padrão do Python para Windows.

À esquerda está o código de `semaforo.ems`. À direita aparecem o estado atual, as condições de saída e as entradas que você pode mudar. O semáforo começa em **VERDE**, no ciclo **0**. Faça uma linha da tabela por vez e clique em **Avançar um ciclo** após ajustar os campos.

| Ciclo | Campo `tempo` | Campo `botao` | Estado após o clique | O que aconteceu |
|---|---|---|---|---|
| 1 | 0 | Sem evento | VERDE | O botão está solto e o tempo ainda é menor que 30. |
| 2 | 0 | pressionado | AMARELO | O botão acionou a passagem para amarelo. |
| 3 | 5 | Sem evento | VERMELHO | O estado amarelo sai quando o tempo chega a 5. |
| 4 | 2 | Sem evento | PEDESTRE | A condição de saída do vermelho foi atendida. |
| 5 | 15 | Sem evento | VERDE | O semáforo executou as ações de pedestre, incluindo o buzzer, e voltou ao verde. |

**Como ler o histórico.** Cada clique executa primeiro as ações do estado que estava ativo. Em seguida, o simulador percorre as regras de saída na ordem em que foram escritas e aplica a primeira condição verdadeira. Por isso, no ciclo 2 o histórico mostra as ações de **VERDE** e o painel já mostra **AMARELO**. As ações de **AMARELO** aparecem no ciclo 3.

No simulador, `tempo` é um valor que você informa. Ele e o evento do botão conservam o último valor escolhido até você alterá-los ou clicar em **Reiniciar**. Reiniciar também zera o ciclo e limpa o histórico.

## Entenda e altere um arquivo .ems

Leia o exemplo em quatro partes.

| Trecho do semáforo | Significado |
|---|---|
| `sistema SemaforoInteligente` | Dá nome ao sistema e aos arquivos de código que serão gerados. |
| `estado VERDE` | Declara um estado possível. O primeiro estado declarado é o inicial. |
| `VERDE -> AMARELO quando tempo >= 30 ou botao pressionado` | Indica origem, destino e condição. Basta o tempo chegar a 30 ou o botão estar pressionado. |
| `estado PEDESTRE:` | Abre o bloco de ações de PEDESTRE. As linhas recuadas abaixo dele, como `buzzer bipar`, são executadas a cada ciclo nesse estado. |

As condições aceitam comparações numéricas (`==`, `!=`, `<`, `<=`, `>`, `>=`) e eventos como `botao pressionado`. Combine condições com `e` ou `ou`. Uma regra como `A -> B` permite a mudança de A para B a cada avaliação, sem exigir uma entrada. Use `#` para escrever comentários.

**Experimente uma alteração.** No editor, troque `tempo >= 30` por `tempo >= 10` na saída de VERDE. Clique em **Verificar programa**. A simulação volta ao início com as novas regras. Coloque `10` em **tempo**, deixe **botao** em **Sem evento** e avance um ciclo. Agora o semáforo chega a **AMARELO** só pelo tempo. Use **Salvar como…** e escolha `meu_semaforo.ems` para guardar sua versão. Depois, use **Abrir arquivo…** para retomá-la.

Em **Exemplos** você também encontra o controle de motor, a estufa inteligente e o alarme residencial. Ao trocar de programa, os campos de entrada passam a corresponder aos sensores usados nas condições daquele arquivo.

## Entenda uma mensagem de erro

**Verificar programa** destaca a linha do erro no editor. Na mensagem, `L7:C1` significa linha 7, coluna 1. Corrija o trecho indicado e verifique outra vez.

| Mensagem | O que conferir |
|---|---|
| Erro léxico | Procure um caractere que a linguagem não reconhece. |
| Erro sintático | Confira a forma da instrução, como a seta `->` entre dois estados. |
| Erro semântico | Confira o significado. Por exemplo, o destino de uma transição precisa estar declarado, e `motor velocidade` aceita valores numéricos de 0 a 100. |
| Aviso semântico | O programa passou na validação. Leia o aviso no histórico e confira se o comportamento é intencional, como um estado final sem saída. |

Para ver um caso pronto, abra `examples/erros/estado_nao_declarado.ems`. A mensagem aponta para o destino `MANUTENCAO`. Acrescente `estado MANUTENCAO` junto às declarações e clique em **Verificar programa**.

## Escolha o que exportar

No menu **Exportar**, escolha o formato e o local para salvar.

| Opção | O que você recebe | Como usar |
|---|---|---|
| Projeto C | Um ZIP com o cabeçalho `.h`, a implementação da máquina `.c` e um segundo `.c` com a simulação para PC. | Extraia os arquivos. O cabeçalho declara a interface e os dois arquivos C podem ser compilados juntos com um compilador C. |
| Arduino | Um sketch `.ino` com a lógica de estados, `setup()` e `loop()`. | Abra na IDE do Arduino e confira os pinos e as funções de sensores e atuadores de acordo com seu circuito antes de compilar para a placa. |
| Diagrama Mermaid | Uma descrição `.mmd` dos estados e das transições. | Abra em um visualizador compatível com Mermaid para ver o desenho. |
| Diagrama Graphviz | Uma descrição `.dot` da máquina de estados. | Renderize o arquivo com Graphviz para ver o desenho. |

## Use pelo terminal

Execute os comandos abaixo na pasta que contém `emstate.py`. Todos usam o mesmo semáforo da interface.

| Objetivo | Comando no PowerShell |
|---|---|
| Abrir a janela | `py emstate.py gui` |
| Verificar o programa e listar os símbolos encontrados | `py emstate.py check examples/semaforo.ems -v` |
| Ver como o compilador organizou o código em uma árvore | `py emstate.py ast examples/semaforo.ems` |
| Simular por comandos | `py emstate.py simulate examples/semaforo.ems` |
| Gerar os três arquivos C na pasta build | `py emstate.py compile examples/semaforo.ems -t c -o build` |
| Gerar o sketch Arduino na pasta build | `py emstate.py compile examples/semaforo.ems -t arduino -o build` |
| Salvar o diagrama Mermaid | `py emstate.py diagram examples/semaforo.ems -f mermaid -o semaforo.mmd` |
| Salvar o diagrama Graphviz | `py emstate.py diagram examples/semaforo.ems -f dot -o semaforo.dot` |

Dentro de `simulate`, digite `event botao pressionado` e depois `step` para chegar a AMARELO. Digite `clear botao`, `set tempo 5` e `step` para chegar a VERMELHO. Use `status` para consultar as entradas e o estado atual, `reset` para recomeçar e `exit` para sair.

## O que acontece por dentro

1. **Leitura.** A interface obtém o texto do editor. Pelo terminal, o programa lê o arquivo indicado no comando.
2. **Análise léxica.** O módulo `lexer.py` separa o texto em unidades, como nomes, números e a seta `->`, e registra suas posições.
3. **Análise sintática.** O módulo `parser.py` organiza essas unidades em uma árvore de estados, condições, transições e ações. É essa estrutura que o comando `ast` exibe.
4. **Análise semântica.** O módulo `semantic.py` confere as declarações, referências e restrições de valores. A tabela de símbolos reúne estados, dispositivos e variáveis. A interface usa essas informações para montar os campos da simulação.
5. **Execução ou geração.** Com o programa validado, `simulator.py` executa um ciclo por vez, os geradores em `codegen/` produzem C ou Arduino, e `visualizer.py` descreve as transições para os diagramas.

Esses módulos ficam em [src/emstate](src/emstate/). Os [exemplos](examples/) servem para experimentar o comportamento, e os [testes automatizados](tests/) verificam as etapas do compilador e da simulação.
