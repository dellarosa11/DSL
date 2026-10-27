/**
 * Arquivo de Cabecalho gerado automaticamente pelo compilador EmState
 * Sistema: ControleMotor
 */
#ifndef EMSTATE_CONTROLEMOTOR_H
#define EMSTATE_CONTROLEMOTOR_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Estados do Sistema */
typedef enum {
    ESTADO_PARADO,
    ESTADO_FUNCIONANDO,
    ESTADO_ERRO
} ControleMotor_Estado_t;

/* Funcoes de Controle da Maquina de Estados */
void ControleMotor_init(void);
void ControleMotor_update(void);
ControleMotor_Estado_t ControleMotor_getEstadoAtual(void);
const char* ControleMotor_getNomeEstado(ControleMotor_Estado_t estado);

/* Prototipos de Funcoes de Dispositivos e Sensores */
float obter_corrente(void);
bool botaoPressionado(void);
void motorParar(void);
void motorVelocidade(int arg1);

#ifdef __cplusplus
}
#endif

#endif /* EMSTATE_CONTROLEMOTOR_H */