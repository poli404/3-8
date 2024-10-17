/*
TRABALHO 2 - NEWTON-RAPHSON
PROGRAMAÇÃO DE SISTEMAS / 14138

PROFESSORES:
Airton Marco Polidorio
Nelson Tenório

GRUPO:
RA 137304 - Ana Paula Loureiro Crippa
RA 134678 - Julia Marques Sanches
RA 134539 - Maria Eduarda de Mello Policante
RA 134241 - Pâmela Camilo Chalegre

Especificação:
Simplificação do método matemático de Newton-Raphson para cálculo de raiz quadrada utilizando o modelo
floatIEEE e a manipulação de bits.

*/

#include <stdio.h>
#include <math.h>

#define VAL_MIN 1
#define VAL_MAX 50
#define INCREMENTO 1
#define TOLERANCIA 0.00001
#define VIES 127  // bias
#define RAIZ_2 1.4142135623730950488016887f
#define INV_RAIZ_2 1/RAIZ_2

typedef union {
    float x;
    struct {
        unsigned int mantissa : 23; // para a fração
        unsigned int expoente : 8; // para o expoente com viés
        unsigned int sinal : 1; // para o sinal
    } bits;
} FloatIEEE;

float estimativaInicial(float A) {
    FloatIEEE valor;
    valor.x = A;
    // ajusta o expoente subtraindo 
    int expoente = valor.bits.expoente - VIES;

    if (expoente & 1) { // se o expoente for ímpar
        // ao inves de dividir o valor por 1/sqrt(2), multiplica
        valor.bits.expoente = ((expoente + 1) >> 1) + VIES;
        valor.x *= INV_RAIZ_2;
    }
    else { // se o expoente for par
        // divide por 2
        // adiciona novamente o VIES, para obter o expoente absoluto
        valor.bits.expoente = (expoente >> 1) + VIES;
    }
    return valor.x;
}

float newtonRaphson(float A) {

    FloatIEEE x0 = {estimativaInicial(A)};
    int k = 0;
    // aplicação da fórmula de Newton-Raphson
    FloatIEEE x1 = {(x0.x + A / x0.x)};
    // tira 1 do expoente
    x1.bits.expoente--;

    while (x0.x != x1.x) { 
        // dessa forma, não há erro, a precisão é exata
        // aplicação da fórmula de Newton-Raphson
        x0.x = x1.x;
        x1.x = (x0.x + A / x0.x);
        x1.bits.expoente--;
        k++;
    }
    printf("Qtde iter.: %d | ", k); // mostra a quantidade de iterações feitas para encontrar a raiz
    return x1.x;
}

int main() {
    // imprimindo a tabela
    printf("\t\t\t\tValor de A\t\tNewton-Raphson\t\tSqrt do C\t\t\tErro\n");
    float R, erro;

    for (float A = VAL_MIN; A <= VAL_MAX; A += INCREMENTO) {
        float sqrt_newton = newtonRaphson(A);

        R = (float) sqrt(A);
        erro = (float) fabs(R - sqrt_newton);

        // utilizando 7 casas decimais para imprimir pois é o padrão do float
        printf("%.1f ---------- %.7f --------- %.7f ---------- %.7f\t\t\n", A, sqrt_newton, R, erro);   
    }
    return 0;
}
