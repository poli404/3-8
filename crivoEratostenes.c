/*
Especificação:
Usando o Crivo de Eratóstenes construa uma tabela de consulta (lockup table) que permita 
dizer se um número inteiro positivo pertencente ao intervalo [2, 6400] é primo ou não.

(1)Deve-se fazer uma função que seja capaz de montar essa tabela com um esforço 
computacional e uso de memória mínimos e;

(2)Deve-se fazer uma função que realize consultas nessa tabela para informar se um 
determinado valor é primo ou não com custo mínimo de processamento;

*/

#include<stdio.h>
#include<math.h>

//Declaracao das funções para serem invocados na main.
void crivo(unsigned int *crivo, int MAX_CRIVO, int partes); // (1)
int primo(unsigned int *crivo, int n); // (2)

int main() {
    int MAX_CRIVO = 6400; //6401 números representados -> 6401/32 = 200.038 -> precisaremos de 201 bytes -> 6431 números.
    int bytes = (MAX_CRIVO + 32)/32; //total de bytes necessários
    unsigned int crivoEras[bytes]; //cria um vetor de inteiros sem sinal com bytes espaços
    
    int num; // o numero que queremos saber se é primo ou não
    printf("Insira o numero: ");
    scanf("%d", &num); //coloca o número digitado no espaço reservado para num.
    
    crivo(crivoEras, MAX_CRIVO, bytes); //forma o crivo

    if((2 <= num) && (num <= 6400)) { //apenas numeros no intervalo de 2 a 6400.
        if(primo(crivoEras, num) != 0) { //verifica se o numero é primo -> se for verdadeiro (!= 0)
            printf("O numero %d eh primo!", num);
        } else {
            printf("O numero %d nao eh primo", num);
        }
    } else {
        printf("O numero %d eh invalido!", num); // outros numeros sao invalidos.
    }
    return 0;
}

int primo(unsigned int *crivoEras, int n) {
    /*
    FUNÇÃO (2) da especificação do trabalho
    Permite a consulta de um número inteiro 'n' na "tabela" de consulta 'crivoEras' para descobrir se o
    número 'n' é primo ou não.
    */
    int parte = n/32; //descobre em que byte está o número
    int bit = n%32; //descobre em que bit está o numero
    return ((crivoEras[parte] & (1 << bit)) != 0); //em 000...001 desloca o 1 para a esquerda até a posição do bit desejado
    // &: compara esse 1 com o bit na posição do número que queremos. Será verdadeiro se for qualquer coisa menos 0.
}

void crivo(unsigned int *crivo, int MAX_CRIVO, int partes) {
    /*
    FUNÇÃO (1) da especificação do trabalho.
    Constrói uma "tabela" de consultas, definindo os números como primos (1) ou não (0). Diz-se "tabela", pois para
    isso, utilizou-se as posições dos bits de um unsigned int.
    */    
    int n = MAX_CRIVO;
    //PREENCHIMENTO DO CRIVO: 
    crivo[0] = 0xAAAAAAAC; // preenche todos os bits que representam números pares como 0 e os ímpares como 1 (tirando os primeiros 4 bits que são marcados 1100 para os números 3210)
    for(int i = 1; i <= partes - 1; i++){ //preenche as demais partes do crivo -> de 1 a 200
        crivo[i] = 0xAAAAAAAA; //seta os bits dos numeros pares como 0 e os ímpares como 1.
    }
    // DECISÃO DOS PRIMOS:
    for(int i = 3; i <= n; i++) { //começando do 1o primo não par até o último número do crivo
        for(int k = (i*2); k <= n; k+=i) { // percorre todos os seus múltiplos
            int pos = k/32; //define em qual parte o múltimo está.
            int j = k%32; //define qual bit representa o múltiplo.
            crivo[pos] &= (~(1 << j)); // aplica a operação E bit a bit e armazena o resulta do crivo.
            // (1 << j): em 000...0001 desloca o bit 1 até a posição j.
            // ~(1 << j): nega o resultado obtido. Como se deslocassemos em 111...1110, o bit 0 até a posição j.
            //para a parte do crivo E a sequência ..111...0...111... obtida, alterando apenas o bit da posição j para 0.
        }
    }
}
