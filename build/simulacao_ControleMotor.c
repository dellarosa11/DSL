/**
 * Arquivo de Simulacao e Teste para o sistema ControleMotor
 * Implementa stubs com prints para demonstrar o funcionamento da FSM.
 */
#include "ControleMotor.h"
#include <stdio.h>
#include <stdlib.h>

/* Variaveis de simulacao para sensores */
static float sim_corrente = 0.0f;
float obter_corrente(void) { return sim_corrente; }
static bool sim_botao_pressionado = false;
bool botaoPressionado(void) { return sim_botao_pressionado; }
void motorParar(void) {
    printf("[ATUADOR] motorParar()\n");
}
void motorVelocidade(int arg1) {
    printf("[ATUADOR] motorVelocidade(%d)\n", arg1);
}

int main(void) {
    printf("=== Iniciando Simulacao do Sistema ControleMotor ===\n");
    ControleMotor_init();
    printf("Estado Inicial: %s\n", ControleMotor_getNomeEstado(ControleMotor_getEstadoAtual()));

    for (int ciclo = 1; ciclo <= 5; ciclo++) {
        printf("\n--- Ciclo %d (Estado: %s) ---\n", ciclo, ControleMotor_getNomeEstado(ControleMotor_getEstadoAtual()));
        ControleMotor_update();
    }

    printf("\nSimulacao finalizada com sucesso!\n");
    return 0;
}