#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/*
TRABALHO 3 - PROCESSAMENTO IMAGEM PILHA
Programação de Sistemas / 14138

PROFESSORES:
Airton Marco Polidorio
Nelson Tenório

EQUIPE:
RA 137304 - Ana Paula Loureiro Crippa
RA 134678 - Julia Marques Sanches
RA 134539 - Maria Eduarda de Mello Policante
RA 134241 - Pâmela Camilo Chalegre
*/

typedef struct TpDADO {
    int L, C;
} TpDADO;

typedef struct TpNODE {  /// estrutura da "caixa" do nodo
    TpDADO dado;
    struct TpNODE *prox; /// permite encadear caixas
} TpNODE;

typedef struct TpPILHA {   /// cabecalho (ou descritor) da estrutura de dados
    TpNODE *topo;
} TpPILHA;

typedef unsigned char Tpixel; // tipo Tpixel para valores em [0, 255]

typedef struct pgm {
    int w;     //LARGURA da imagem (total de COLUNAS)
    int h;     //ALTURA da imagem (total de LINHAS)
    int max;   //BRANCO
    Tpixel* pData; // ponteiro para o reticulado (matriz) da immagem alocada como um vetor.
} pgm;

void InicializaPilha(TpPILHA *pilha){
    /*
    Aloca o espaco de memoria para a pilha e aponta o topo para NULL (está vazia)
    */
    pilha->topo = NULL;
}

int push(TpDADO x, TpPILHA *p) {
    /*
    Empilha o dado x na pilha p
    */
    TpNODE *paux;
    /// Aloca a memoria para o novo NODE da pilha.
    paux = (TpNODE*) malloc(sizeof(TpNODE));

    if(!paux) {
        printf("\n ERRO na alocacao de um novo NODO na pilha.");
        return -1;
    }

    paux->dado = x;
    paux->prox = p->topo;
    p->topo = paux;

    return 1;/// sucesso
}

int pop(TpDADO *x, TpPILHA *p) {
    /*
    Desempilha o dado x do topo da pilha p
    */
    if(!p->topo) {
        printf("\n ERRO no desempilhamento. Pilha vazia.");
        return -2;// nao se pode desempilhar em pilha vazia
    }
    /// tem dados empilhados
    TpNODE *paux;
    paux = p->topo;
    /// copiar o valor do dado armazenado no topo da pilha
    *x = paux->dado;
    p->topo = paux->prox;
    paux->prox = NULL; /// desligar do encadeamento a caixa do topo.

    free(paux); /// desalocar da mem�ria o NODO desempihado
    return 2;
}


int WritePGM(const char* arq, const char* tipoPGM, pgm* pPgm) {
    /*
    GRAVA OS DADOS DO DESCRITOR pPgm NO ARQUIVO arq
    */
    FILE *f;

    f = fopen(arq, "w");  /// modo "w" --> abrir para escrita
    if (!f) {
        printf("\n ERRO: Incapaz de abrir arquivo: %s.", arq);
        return -1;  // algum c�digo de erro - Arquivo nao existe.
    }

    fprintf(f, "%s\n", tipoPGM); /// verifica o tipo de pgm que será escrito - colorido "P3", cinza "P2" ou binario "P1"
    if (!strcmp(tipoPGM, "P3")) {/// Se eh P3 a largura está multiplicada por 3 -> 3 colunas por pixel
        fprintf(f,"%d %d\n", pPgm->w/3, pPgm->h); // divide a largura por 3
    }else { // P1 ou P2
        fprintf(f,"%d %d\n", pPgm->w, pPgm->h);
    }
    fprintf(f,"255\n"); // valor BRANCO

    /// gravar no arquivo os valores dos pixels da imagem computada
    for (int k = 0; k < (pPgm->w * pPgm->h); k++) {
        fprintf(f,"%d ", pPgm->pData[k]);
    }

    fclose(f);

    printf("\nARQUIVO GRAVADO --> %s", arq);
    return(1);
}


int ReadPGMP2(const char* arq, pgm* pPgm) {
    /*
    Le um arquivo PGM - P2.
    */
    int word; // inteiro de proposito geral
    unsigned int pixelsLidos = 0; // indice para o tamanho do vetor/matriz de dados (pixels) da imagem
    char readChars[256]; // buffer para ler caracteres do arquivo (proposito geral)

    FILE* fd;  /// descritor para um arquivo

    fd = fopen(arq, "r");  // "r" --> abrir somente para leitura
    if(!fd) { // se ele ta vazio
        printf("\n ERRO: Incapaz de abrir arquivo: %s.\n\n", arq);
        exit(1);  // Nao conseguiu abrir -> encerra a execucao do programa
    }
    
    fscanf (fd, "%s", readChars); // leia a primeira linha (string) do arquivo fd

    if ((strcmp(readChars, "P2"))) { // se nao for "P2" -> strcmp retorna a posicao do caractere diferente (!= 0)
        printf ("\n\nErro em PGM: %s Formato nao suportado em:  ", readChars); /// eh a imagem errada
        fclose(fd); // fecha o arquivo
        exit(2); // encerra o programa
    }
    // se eh "P2" -> strcmp retorna 0.

    fscanf (fd, "%s", readChars); // leia a segunda linha
    while (readChars[0] == '#') {   // se comeca com "#", eh um comentario
        fgets (readChars, 255, fd);
        fscanf (fd, "%s", readChars); // Pula a linha e le a proxima -> continua enquanto for uma linha de comentario
    }

    sscanf (readChars, "%d", &pPgm->w);  // pega as informacoes para preencher os campos do struct pgm que vai armazenar os dados da imagem
    fscanf (fd, "%d", &pPgm->h);
    fscanf (fd, "%d", &pPgm->max);

    unsigned int totalPixels = (pPgm->w) * (pPgm->h);

    pPgm->pData = (Tpixel*)malloc(sizeof(Tpixel) * (totalPixels)); // pData : vetor alocado dinamicamente para armazenar os dados dos pixels da imagem

    for (pixelsLidos = 0; pixelsLidos < totalPixels; pixelsLidos++) { // le todos os pixels do arquivo
        fscanf(fd, "%d" ,&word); // le o valor de um pixel do arquivo
        pPgm->pData[pixelsLidos] = word; // armazena o valor deste pixel no vetor alocado -> mesma posicao que ele foi lido na imagem
    }

    fclose(fd); // fecha o arquivo
    printf("\nDADOS LIDOS do ARQUIVO --> %s", arq);

    return 0;
}


int MemImgZero(pgm* atual, pgm* zeropgm) {
    /*
    PREENCHE UM pgm zeropgm DE MESMAS DIMENSÕES QUE O atual COM ZEROS.
    */
    zeropgm->w = atual->w;
    zeropgm->h = atual->h;
    zeropgm->max = atual->max;

    unsigned int totalPixels = (zeropgm->w) * (zeropgm->h);

    zeropgm->pData = (Tpixel*)malloc(sizeof(Tpixel) * (totalPixels));
    ///pData armazena os dados da imagem criada -> dinamicamento alocado -> totalPixels dados Tpixel

    if (!(zeropgm->pData)) {
        printf("ERRO na alocacao de matriz de zeros.");
        return -1;
    }

    const Tpixel ZERO = 0;
    for (unsigned int tp = 0; tp < totalPixels; tp++) {
        zeropgm->pData[tp] = ZERO;
    }

    printf("\nCriada Matriz ZEROS[%d, %d]", zeropgm->h, zeropgm->w);

    return 1;
}


Tpixel GetPixel(pgm* img, int L, int C){
    /*
    PEGA O PIXEL NA POSICAO (L, C) DO DESCRITOR img -> ENTENDE-SE COMO UMA MATRIZ
    */
    if ((L >= img->h) ||  (C >= img->w) || ( L < 0) || (C < 0)) {
        printf("\n ..... Coordenada de imagem esta fora dos limites da grade da imagem.");
        exit(0);
    }
    Tpixel K;
    K = *((img->pData) + L*img->w + C);

    return (K);
}

int PutPixel(pgm* img, int L, int C, Tpixel v){
    /*
    COLOCA O PIXEL v NAS CORDENADAS (L, C) NO DESCRITOR img DA IMAGEM -> ENTENDE-SE COMO UMA MATRIZ.
    */
    if ((L >= img->h) ||  (C >= img->w) || ( L < 0) || (C < 0)) {
        printf("\n ..... Coordenada de imagem esta fora dos limites da grade da imagem.");
        exit(0);
    }
    Tpixel *K;
    K = (img->pData) + L*img->w + C;
    *K = v;

    return 1;
}

int MorphGrad33(pgm* img, pgm* grad) {
    /*
    Computa  o gradiente morfonlógico a partir dos dados de img e armazena em grad -> derivada da diferenca.
    */
    MemImgZero(img, grad); /// preenche a imagem com ZEROS

    int L, C, k, j;
    Tpixel max, p;
    for (L = 1; L < img->h - 1; L++) {
        for (C = 1; C < img->w - 1; C++) {
            max = 0;
            for (k = -1; k<=1; k++) { /// Elemento estruturante 3x3
                for (j = -1; j<=1; j++){
                    p = GetPixel(img, L + k, C + j);
                    if (p > max) max = p;  /// valor de cinza maximo coberto pelo EE
                }
            }
            p = max - GetPixel(img, L , C);
            PutPixel(grad, L, C, p);
        }
    }
    return 0;
}

int regiao_lago(const char* arquivoLAGO, int criterio, int LS, int CS, pgm* imgOR, pgm* imgBORDA) {
    /*
    ALGORITMO REGION GROW PARA DELIMITAR A ÁREA DO LAGO.
    */
    pgm *imgLAGO; ///descritor para dados da imagem da silhueta do lago

    imgLAGO = malloc (sizeof(pgm)); // Alocaçao de memoria para o descritor do lago
    MemImgZero(imgOR, imgLAGO); // preenche o descritor da imagem do lago com ZEROS na mesma proporção do descritor da imagem original

    int VS = GetPixel(imgOR, LS, CS); /// VS - valor de brilho do pixel do ponto semente escolhido na imagem original

    TpPILHA *pilha;
    TpDADO  pixelAtual, proxPixel;

    ///Aloca o espaco para a pilha
    pilha = (TpPILHA*) malloc(sizeof(TpPILHA));
    if (!pilha) {
        printf("\n ERRO de alocacao da PILHA:\n");
        exit(0);
    }

    InicializaPilha(pilha); /// Inicia o topo da pilha como NULL

    pixelAtual.L = LS; /// copia as coordenadas do ponto semente para
    pixelAtual.C = CS;
    printf("\n Valor do Ponto Semente  =  %d \n", VS);

    push(pixelAtual, pilha); // empilhar a coordenada do ponto semente na pilha
    PutPixel(imgLAGO, pixelAtual.L, pixelAtual.C, 1); // Marca o ponto semente como pertencente ao lago

    int k, j; /// elementos estruturantes 3x3: auxiliares para visitar os 8-vizinhos de um pixel
    int pertence;
              
    Tpixel valorPixel, Growpix; // auxiliar para definir se um pixel j� foi pocessado ou n�o

    while(pilha->topo) {  /// enquanto existir coordenada na pilha
        pop(&pixelAtual, pilha);    /// desempilhar uma coordenada do topo
        for (k = -1; k<=1; k++) {
            proxPixel.L = pixelAtual.L + k;
            for (j = -1; j<=1; j++){
                proxPixel.C = pixelAtual.C + j ;

                valorPixel = GetPixel(imgOR, proxPixel.L, proxPixel.C); /// recupera o valor pixel visitado na imagem original (valor de brilho real)
                Growpix = GetPixel(imgLAGO, proxPixel.L, proxPixel.C); /// recupera o valor do pixel na imagem do lago (1 : pertence | 0: nao pertence/nao analisado)
                pertence = (abs(VS - valorPixel) <= criterio); // verifica se o pixel pertence ao intervalo permitido pelo criterio de similaridade do Pixel

                if (!Growpix && pertence) { /// se o pixel nao foi visitado E cumpre o criterio de similaridade do lago
                    push(proxPixel, pilha);  /// empilha o pixel -> para visitar seus vizinhos posteriormente
                    PutPixel(imgLAGO, proxPixel.L, proxPixel.C, 1); // Marca o pixel como pertencente ao lago (1) na imagem do Lago
                }
            }
        }
    }

    MorphGrad33(imgLAGO, imgBORDA);  /// gera a borda da regiao obtida do lago -> derivada marca a diferenca entre 0 e 1.

    //Escreve os dados do descritor do lago no arquivo (binário)
    WritePGM(arquivoLAGO, "P1", imgLAGO);

    ///DESALOCA O DESCRITOR DO LAGO E O ESPACO DA PILHA
    free(imgLAGO->pData);    free(imgLAGO);
    free(pilha);

    return 0;
}

int gerar_borda_colorida(const char* arqBordaColorida, pgm* imgOR, pgm* imgBORDA) {
    /*
    GERA UM ARQUIVO SOBREPONDO A IMAGEM ORIGINAL E A IMAGEM DA BORDA, COLORINDO A BORDA (manipulando a imagem binária e copiando a original)
    */
    //CRIAÇÃO, ALOCAÇÃO DA MEMORIA PARA O DESCRITOR E DEFINIÇÃO DE SUAS CARACTERISTICAS
    pgm *imgCOLOR;
    imgCOLOR = malloc (sizeof(pgm));
    imgCOLOR->h = imgOR->h;
    imgCOLOR->w = 3*(imgOR->w); /// uma imagem colorida tem TRÊS vezes mais colunas (pois cada pixel tem colunaS R, G e B)
    imgCOLOR->max = 255; /// BRANCO

    MemImgZero(imgCOLOR, imgCOLOR); /// Preenche o descritor da imagem colorida com ZEROS.

    int j, k;
    int TotalPix = imgBORDA->w * imgBORDA->h;
    j = -1;
    for (k = 0; k<TotalPix; k++){
        if (imgBORDA->pData[k]) { /// se o pixel EH da bordda (1), ele eh COLORIDO (em RGB)
            imgCOLOR->pData[++j] = 255; /// R (vermelho)
            imgCOLOR->pData[++j] = 0; /// G (verde)
            imgCOLOR->pData[++j] = 238; /// B (azul)
        } else { /// se nao eh da borda (0), ele permanece como na imagem original
            imgCOLOR->pData[++j] = imgOR->pData[k];  /// repetir o o mesmo valor de
            imgCOLOR->pData[++j] = imgOR->pData[k];  /// cinza para completar os valores
            imgCOLOR->pData[++j] = imgOR->pData[k];  /// RGB dos pixels da imagem colorida
        }
    }
    
    WritePGM(arqBordaColorida, "P3", imgCOLOR); /// grava o arquivo da imagem colorida
    
    //DESALOCA O ESPAÇO DO DESCRITOR E SEUS DADOS
    free(imgCOLOR->pData);   
    free(imgCOLOR);

    return 0;
}

int processamento_imagem(const char* imagemOriginal, const char* arquivoLAGO, const char* arquivoBORDA, const char* imagemColorida){
    /*
    PROCESSA A IMAGEM imagemOriginal PARA OBTER A imagemColorida COM O LAGO CONTORNADO EM ROSA.
    */    
    /// Descritores para os dados da imagem original e imagem da borda (P2 e P1)
    pgm *imgOR, *imgBORDA;

    /// Alocação de memória para os descritores
    imgOR = malloc (sizeof(pgm)); // imagem original
    imgBORDA = malloc (sizeof(pgm)); //imagem da borda do lago

    ReadPGMP2(imagemOriginal, imgOR); // transfere os dados do arquivo original para o descritor

    int criterio_lago = 10;   /// CRITÉRIO DE PERTENCIMENTO -> limite para similaridade ao ponto semente do lago
    int LS = 377, CS = 507; /// coordenada linha (LS) e coluna (CS) do ponto semente

    regiao_lago(arquivoLAGO, criterio_lago, LS, CS, imgOR, imgBORDA); /// processa a imagem original para obter a silhueta do lago e borda do lago
    
    WritePGM(arquivoBORDA, "P1", imgBORDA); // Escreve o arquivo da borda da imagem

    gerar_borda_colorida(imagemColorida, imgOR, imgBORDA); /// Cria a imagem colorida

    ///DESALOCA A MEMORIA ALOCADA ANTERIORMENTE
    free(imgOR->pData);      free(imgOR);
    free(imgBORDA->pData);    free(imgBORDA);

    return 0;
}

int main() {
    /*
    SEMPRE ALTERAR OS CAMINHOS DO DIRETÓRIO DAS IMAGENS -> TANTO A ORIGINAL QUANTO A DO LAGO, BORDA E COLORIDA.
    */
    const char* imagemOriginal = "C:\\Users\\home\\OneDrive\\Poli\\PTST\\UmuNirGeoEye.pgm"; //Imagem original - P2
    const char* arquivoLAGO = "C:\\Users\\home\\OneDrive\\Poli\\PTST\\UmuGrow.pbm"; /// imagem da silhueta do lago - P1
    const char* arquivoBORDA = "C:\\Users\\home\\OneDrive\\Poli\\PTST\\UmuBorda.pbm"; ///imagem da borda do lago - P1
    const char* imagemColorida  = "C:\\Users\\home\\OneDrive\\Poli\\PTST\\UmuColorBordEye.ppm"; /// Imagem colorida - P3

    processamento_imagem(imagemOriginal, arquivoLAGO, arquivoBORDA, imagemColorida);

    return 0;
}