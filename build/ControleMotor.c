/**
 * Implementacao da Maquina de Estados gerada pelo compilador EmState
 * Sistema: ControleMotor
 */
#include "ControleMotor.h"
#include <stdio.h>

/* Estado Atual da Maquina */
static ControleMotor_Estado_t estadoAtual = ESTADO_PARADO;

void ControleMotor_init(void) {
    estadoAtual = ESTADO_PARADO;
}

ControleMotor_Estado_t ControleMotor_getEstadoAtual(void) {
    return estadoAtual;
}

const char* ControleMotor_getNomeEstado(ControleMotor_Estado_t estado) {
    switch (estado) {
        case ESTADO_PARADO: return "PARADO";
        case ESTADO_FUNCIONANDO: return "FUNCIONANDO";
        case ESTADO_ERRO: return "ERRO";
        default: return "DESCONHECIDO";
    }
}

void ControleMotor_update(void) {
    switch (estadoAtual) {
        case ESTADO_PARADO:
            /* Acoes do estado PARADO */
            motorParar();
            /* Avaliacao de transicoes */
            if (botaoPressionado()) {
                estadoAtual = ESTADO_FUNCIONANDO;
                break;
            }
            break;

        case ESTADO_FUNCIONANDO:
            /* Acoes do estado FUNCIONANDO */
            motorVelocidade(70);
            /* Avaliacao de transicoes */
            if (botaoPressionado()) {
                estadoAtual = ESTADO_PARADO;
                break;
            }
            if ((obter_corrente() > 2)) {
                estadoAtual = ESTADO_ERRO;
                break;
            }
            break;

        case ESTADO_ERRO:
            /* Acoes do estado ERRO */
            motorParar();
            break;

        default:
            /* Estado indefinido */
            break;
    }
}