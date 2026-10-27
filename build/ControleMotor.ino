/**
 * Sketch Arduino gerado automaticamente pelo compilador EmState
 * Sistema: ControleMotor
 */

// Definições de Estados
enum Estado {
  ESTADO_PARADO,
  ESTADO_FUNCIONANDO,
  ESTADO_ERRO
};

Estado estadoAtual = ESTADO_PARADO;
Estado estadoAnterior = ESTADO_PARADO;

// Mapeamento de pinos do microcontrolador (Ajuste conforme sua placa)
#define PINO_BOTAO     2
#define PINO_LED       13
#define PINO_MOTOR_PWM 9
#define PINO_BUZZER    8

// Funções de leitura de sensores e condições
float obter_corrente() {
  // Simulação de leitura analógica ou sensor real
  int valorRaw = analogRead(A0);
  return (valorRaw * 5.0) / 1023.0; // Exemplo de conversão
}
bool botaoPressionado() {
  return (digitalRead(PINO_BOTAO) == LOW); // Ativo em nível lógico baixo com PULLUP
}

// Funções de comando de atuadores
void motorParar() {
  analogWrite(PINO_MOTOR_PWM, 0);
  Serial.println("[ATUADOR] motorParar");
}
void motorVelocidade(int valor) {
  int pwm = map(valor, 0, 100, 0, 255);
  analogWrite(PINO_MOTOR_PWM, pwm);
  Serial.print("[ATUADOR] motorVelocidade: ");
  Serial.println(valor);
}

void setup() {
  Serial.begin(115200);
  pinMode(PINO_BOTAO, INPUT_PULLUP);
  pinMode(PINO_LED, OUTPUT);
  pinMode(PINO_MOTOR_PWM, OUTPUT);
  pinMode(PINO_BUZZER, OUTPUT);
  Serial.println("=== Sistema EmState Inicializado: ControleMotor ===");
}

void loop() {
  switch (estadoAtual) {
    case ESTADO_PARADO:
      if (estadoAtual != estadoAnterior) {
        Serial.println("-> Entrando no estado: PARADO");
        estadoAnterior = estadoAtual;
      }
      motorParar();
      if (botaoPressionado()) {
        estadoAtual = ESTADO_FUNCIONANDO;
        break;
      }
      break;

    case ESTADO_FUNCIONANDO:
      if (estadoAtual != estadoAnterior) {
        Serial.println("-> Entrando no estado: FUNCIONANDO");
        estadoAnterior = estadoAtual;
      }
      motorVelocidade(70);
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
      if (estadoAtual != estadoAnterior) {
        Serial.println("-> Entrando no estado: ERRO");
        estadoAnterior = estadoAtual;
      }
      motorParar();
      break;

  }
  delay(100); // Taxa de amostragem da FSM
}