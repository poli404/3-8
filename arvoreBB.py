import struct
from dataclasses import dataclass
import io
from sys import argv
#CONSTANTE GLOBAL:
ORDEM = 8
MODELO = f"i{ORDEM - 1}i{ORDEM - 1}i{ORDEM}i"
TAM_PAG = struct.calcsize(MODELO)
TAM_CAB = 4
TAM_REG = 2

@dataclass
class Pagina:
    def __init__(self) -> None:
        self.numChaves: int = 0
        self.chaves: list = [-1] * (ORDEM - 1) #todos os valores são números inteiros.
        self.offsets = [-1] * (ORDEM - 1) #ARMAZENA OS OFFSETS DOS REGISTROS ARMAZENADOS EM CHAVES -> RELAÇÃO DIRETA (CHAVE EM i COM OFFSET EM i).
        self.filhos: list = [-1] * (ORDEM) #numero das paginas.

def novo_rrn(arvore: io.BytesIO) -> int:
    '''Calcula o novo RRN de uma página'''
    arvore.seek(0, 2) # a nova página é escrita no fim do arquivo
    rrn = (arvore.tell() - TAM_CAB) // TAM_PAG #cálculo do RRN (a partir do offstdo fim do arquivo)
    return rrn

def leia_reg(arq_dados: io.BytesIO) -> tuple[str, int]:
    '''Le um registro apos ler seu tamanho, retornando os dois.'''
    tam = int.from_bytes(arq_dados.read(TAM_REG), byteorder='little') #pega o tamanho do registro
    if tam > 0: #se não chegar ao fim do arquivo
        reg = arq_dados.read(tam).decode() #le o restante do tamanho
        return reg, tam #retorna todo o registro (incluindo o primeiro byte) e o tamanho.
    else:
        return '', 0 #retorna a string vazia (fim do arquivo) e tamanho 0.

def lePagina(rrn: int, arvore: io.BytesIO) -> Pagina:
    '''Le a pagina de RRN "rrn" do arquivo da árvore, retornando-a.'''
    byte_offset = (rrn * TAM_PAG) + TAM_CAB # RRN * (tamanho de uma página) + tamcabecalho.
    arvore.seek(byte_offset) #vai ao offset da pagina
    dados_pagina: tuple = struct.unpack(MODELO, arvore.read(TAM_PAG)) #le a pagina e desempacota-a -> retorno é uma tupla com todos os dados SEPARADOS
    pagina = Pagina()
    #CONDENSAÇÃO DOS DADOS:
    pagina.numChaves = dados_pagina[0] #primeiro dado da tupla é o numero de chaves -> i
    pagina.chaves[:ORDEM - 1] = dados_pagina[1 : ORDEM] # os proximos ORDEM-1 dados da tupla são as chaves -> {ORDEM - 1}i -> [1 : ORDEM] -> ORDEM - 1 elementos (do índice 1 a ORDEM-1)
    pagina.offsets[:ORDEM - 1] = dados_pagina[ORDEM:(ORDEM+(ORDEM - 1))] # os proximos ORDEM-1 dados são offsets -> {ORDEM - 1}i -> [ORDEM : ORDEM + (ORDEM - 1)] -> ORDEM-1 elementos (do índice inicial até inicial + ORDEM-1 elementos).
    #[:ORDEM - 1] -> elementos de 0 até o índice ORDEM-2, ou seja, ORDEM-1 elementos
    pagina.filhos[:ORDEM] = dados_pagina[(ORDEM + (ORDEM - 1)):] # o restante dos dados da tupla são os filhos -> [: ORDEM + (ORDEM - 1)] -> a partir do índice final dos offsets
    #[:ORDEM] -> elementos de 0 até o índice ORDEM-1, ou seja, ORDEM elementos
    return pagina #retorna a pagina criada

def escrevePagina(rrn: int, pagina: Pagina, arvore: io.BytesIO) -> None:
    '''Escreve uma página no RRN "rrn" do arquivo árvore.'''
    byte_offset = (rrn * TAM_PAG) + TAM_CAB # RRN * (tamanho de uma página) + tamcabecalho.
    arvore.seek(byte_offset)
    #empacotar a página: MODELO = i{ORDEM - 1}i{ORDEM - 1}i{ORDEM}i = i + 2*{ORDEM - 1}i + {ORDEM}i (cada i equivale a 1 elemento a ser passado como parâmetro)
    pag = struct.pack(MODELO, pagina.numChaves, *pagina.chaves, *pagina.offsets, *pagina.filhos)
    # MODELO, 1 elemento, (ORDEM - 1) elementos, (ORDEM - 1) elementos, (ORDEM) elementos -> *Descompactação de argumentos: pega os elementos das listas separadamente e os usa como argumentos
    arvore.write(pag)

def buscaNaPagina(chave: int, pag: Pagina) -> tuple[bool, int]:
    '''Define se uma chave pertence a página "pag" e, se sim, retorna sua posição nela.'''
    pos = 0 #iniciando a esquerda -> na menor chave da página
    while (pos < pag.numChaves) and (chave > pag.chaves[pos]): #enquanto houverem chaves e a chave da página for MENOR que a procurada
        pos += 1 #procura-se mais a direita dela
    if (pos < pag.numChaves) and (chave == pag.chaves[pos]): #se o looping se encerrou e a última chave é a desejada
        return True, pos #achou
    else: #se a última chave da página não é a desejada
        return False, pos #não achou :)

def buscaNaArvore(chave: int, rrn: int, arvore: io.BytesIO) -> tuple[bool, int, int]:
    '''Busca uma chave na arvore página a página, indo da raiz até a folha a qual a chave deveria pertencer.'''
    if rrn == -1: #não há mais páginas para se procurar
        return False, -1, -1 #a chave não está na árvore
    else: 
        pag = lePagina(rrn, arvore) #pega uma página
        achou, pos = buscaNaPagina(chave, pag) #procura a chave naquela página
        if achou: #se ela estava na página
            return True, rrn, pos
        else:
            return buscaNaArvore(chave, pag.filhos[pos], arvore) #vai para a próxima página onde a chave idealmente deveria estar.

def buscar(identificador: int, arq_registros: io.BytesIO, arvore: io.BytesIO, raiz: int) -> str:
    '''Busca a chave "identificador" no arquivo "arvore" e retorna o registro presente "em arq_registros".'''
    achou, rrn, pos = buscaNaArvore(identificador, raiz, arvore) #busca na árvore a página (rrn) que contém a chave e sua posição naquela.
    if achou: #se encontrou
        pagina = lePagina(rrn, arvore) #le a página do arquivo da árvore.
        off_reg = pagina.offsets[pos] #posição da chave correta = posição do offset correto para o arquivo de registros
        arq_registros.seek(off_reg) #vai até o offset daquela chave
        registro, tam = leia_reg(arq_registros) #le o registro
        return f'{registro} ({tam} bytes - offset {off_reg})'
    else:
        return "Erro: Registro não encontrado!"

def insereNaPagina(chave: int, filhoD: int, off_reg: int, pag: Pagina) -> None:
    '''Insere uma chave "chave" e seus correlativos em uma página'''
    if pag.numChaves == (ORDEM - 1): #adiciona um espaço extra na página caso ela esteja cheia
        pag.chaves.append(-1)
        pag.filhos.append(-1)
        pag.offsets.append(-1)
    i = pag.numChaves #estando cheia ou não:
    while i > 0 and (chave < pag.chaves[i - 1]): #encontra o local de inserção da nova chave na página
        pag.chaves[i] = pag.chaves[i - 1]
        pag.offsets[i] = pag.offsets[i - 1]
        pag.filhos[i + 1] = pag.filhos[i]
        i -= 1
    pag.chaves[i] = chave #insere a chave na página no local correto
    pag.offsets[i] = off_reg
    pag.filhos[i + 1] = filhoD
    pag.numChaves += 1 #soma a chave adicionada

def divide(chave: int, filhoD: int, off_reg: int, pag: Pagina, arvore: io.BytesIO) -> tuple[int, int, int, Pagina, Pagina]:
    '''Divide uma página "pag" em duas páginas "pAtual" e "pNova", igualmente ao meio.'''
    insereNaPagina(chave, filhoD, off_reg, pag) #insere a chave na página -> sobrecarrega ela
    meio = ORDEM // 2
    chavePro = pag.chaves[meio] #chave promovida
    offsetPro = pag.offsets[meio]
    filhoDPro = novo_rrn(arvore) #seu filho direito será a nova página criada
    pAtual = Pagina() # nova configuração de pag -> pAtual
    pAtual.numChaves = meio # Uma pagina fica com metade das chaves = MEIO elementos
    pAtual.chaves[:meio] = pag.chaves[:meio] # elementos de chaves[0] até chaves[meio - 1] -> MEIO elementos
    pAtual.offsets[:meio] = pag.offsets[:meio]
    pAtual.filhos[:meio + 1] = pag.filhos[:meio + 1] #até o filho esquerdo de chaves[meio] -> filhos[meio] -> [0 : meio + 1] -> MEIO + 1 ELEMENTOS
    pNova = Pagina() #filho direito -> novoRRN -> recebe os dados APÓS chaves[meio]
    pNova.numChaves = pag.numChaves - meio - 1 # A outra terá MEIO - 1 elementos -> metade restante - chave promovida (é tirada dela).
    pNova.chaves = pag.chaves[meio + 1:] + ([-1] * (ORDEM - 1 - pNova.numChaves)) # a partir de chaves[meio + 1], pega todos as chaves restantes na original.
    pNova.offsets = pag.offsets[meio + 1:] + ([-1] * (ORDEM - 1 - pNova.numChaves))
    pNova.filhos = pag.filhos[meio + 1:] + ([-1] * (ORDEM - 1 - pNova.numChaves)) # a partir do filho direito de chaves[meio] -> filhos[meio + 1] -> pega todos os elementos restantes da lista de filhos.
    #[-1] * N : preenche a lista com elementos -1 N vezes -> LIMITE - numeroDeChaves = completa a lista ATÉ o limite a partir das chaves já existentes. LIMITE = ordem ou ordem - 1
    return chavePro, filhoDPro, offsetPro, pAtual, pNova

def insereNaArvore(chave: int, off_reg: int, rrnAtual: int, arvore: io.BytesIO)-> tuple[int, int, int, bool]: 
    '''Insere uma chave "chave" na árvore.'''
    if rrnAtual == -1: # condicao de parada: achou a folha de inserção correta
        chavePro = chave 
        offsetPro = off_reg
        filhoDPro = -1
        return chavePro, filhoDPro, offsetPro, True
    else: #procura a chave na página
        pag = lePagina(rrnAtual, arvore)
        achou, pos = buscaNaPagina(chave, pag) #determina onde ela DEVERIA estar.
    if achou: #se achou a chave não pode ser inserida novamente -> sai da função.
        return -1, -1, -1, False
    #continua descendo na árvore até encontrar a folha de inserção:
    chavePro, filhoDPro, offsetPro, promo = insereNaArvore(chave, off_reg, pag.filhos[pos], arvore)
    
    if promo == False: #se não houve promoção, o processo acabou -> a chave já foi inserida
        return -1, -1, -1, False
    else: #se houve:
        if pag.numChaves < (ORDEM - 1): #se o número de chaves é menor que o total máximo de chaves
            insereNaPagina(chavePro, filhoDPro, offsetPro, pag) #insere a chave promovida na página pai
            escrevePagina(rrnAtual, pag, arvore) #atualiza a página no arquivo da árvore
            return -1, -1, -1, False
        else: #se o número máximo estourou
            chavePro, filhoDPro, offsetPro, pag, novapag = divide(chavePro, filhoDPro, offsetPro, pag, arvore) #divide a página pai
            escrevePagina(rrnAtual, pag, arvore) #atualiza a página
            escrevePagina(filhoDPro, novapag, arvore) #escreve a nova página
            return chavePro, filhoDPro, offsetPro, True 

def gerenciadorDeInsercao(raiz: int, chave: int, offset: int, arvore: io.BytesIO) -> int:
    '''Gerencia a inserção -> em caso de promoção na raiz ou troca'''
    chavePro, filhoDpro, offsetPro, promocao = insereNaArvore(chave, offset, raiz, arvore)
    if promocao: 
        pNova = Pagina() #nova página raiz
        pNova.chaves[0] = chavePro #nova chave da raiz
        pNova.offsets[0] = offsetPro
        pNova.filhos[0] = raiz #filho esquerdo -> antiga raiz 
        pNova.filhos[1] = filhoDpro #filho direito -> da chave promovida a raiz
        pNova.numChaves += 1
        rrnNova = novo_rrn(arvore) #calcula o novo rrn
        escrevePagina(rrnNova, pNova, arvore) #escreve a nova página raiz no arquivo da árvore
        if rrnNova != raiz: #se houve uma atualização da raiz
            arvore.seek(0)
            arvore.write(rrnNova.to_bytes(TAM_CAB, byteorder='little')) #atualiza-se no cabecalho do arquivo da árvore
        raiz = rrnNova #atualiza a raiz para o RRN da nova pagina raiz
    return raiz 

def inserir(registro: str, raiz: int, arq_registros: io.BytesIO, arvore: io.BytesIO) -> str:
    '''Insere um novo registro ao arquivo de registros E adiciona sua chave à árvore de identificadores.'''
    identificador = registro.split(sep='|')[0]
    print(f"\nInserção do registro de chave: {identificador}")
    achou, p, n = buscaNaArvore(int(identificador), raiz, arvore) #procura a chave na árvore
    if achou: #se achou retorna erro -> não pode inserir de novo.
        return f'Erro: chave \"{identificador}\" já existente'
    else: # se não, insere
        total_reg = int.from_bytes(arq_registros.read(TAM_CAB), byteorder='little') + 1 #adição de um registro ao total de registros anterior (cabecalho)
        reg = registro.encode()
        tam = len(reg) #manipulação do registro novo para bytes e seu tamanho
        arq_registros.seek(0, 2) #vai ao fim do arquivo de registros
        offset = arq_registros.tell() #offset do novo registro -> o do fim do arquivo
        arq_registros.write(tam.to_bytes(TAM_REG, byteorder='little'))
        arq_registros.write(reg) #escreve o tamanho e o novo registro no arquivo de registros
        arq_registros.seek(0) #volta ao cabecalho
        arq_registros.write(total_reg.to_bytes(TAM_CAB, byteorder='little')) #atualiza o cabecalho -> novo número de registros
        raizNova = gerenciadorDeInsercao(raiz, int(identificador), offset, arvore) #insere a nova chave na árvore
        return f'{registro} ({tam} bytes - offset {offset})'

def criar() -> None:
    '''Cria um novo arquivo (ou sobrescreve) btree.dat para armazenar um índice de árvore binária dos registros do arquivo games.dat.'''
    try:
        arq_arvore = open("btree.dat", 'w+b') #cria um arquivo para a árvore (ou sobrescreve)
        arq_registros = open("games.dat", 'rb') #le o arquivo de registros
        raiz = -1 
        arq_arvore.write(raiz.to_bytes(TAM_CAB, byteorder='little', signed=True)) #escreve a raiz no cabecalho do arquivo arvore
        total_reg = int.from_bytes(arq_registros.read(TAM_CAB), byteorder='little') #le o cabecalho -> numero de registros a seren inseridos
        offset = TAM_CAB #pulando o cabecalho do arquivo de registros -> offset do primeiro registro
        for i in range(total_reg): #para todos os registros.
            reg, tam = leia_reg(arq_registros) #le o registro
            identificador = int(reg.split('|')[0]) #pega o identificador -> primeiro campo do registro
            raizNova = gerenciadorDeInsercao(raiz, identificador, offset, arq_arvore) #insere o identificador na árvore
            raiz = raizNova
            offset += tam + TAM_REG #atualiza o offset para o próximo registro -> tam_do_ultimo + 2

        print("\nÍndice criado com sucesso!\n")
        arq_arvore.close()
        arq_registros.close()
    except FileNotFoundError:
        print("Não foi possível abrir o arquivo de registros e/ou o arquivo da árvore!")

def executar(arquivo_operacoes: str) -> None:
    '''Executa o arquivo de operacoes.'''
    try: #tenta abrir os arquivos e executa-los.
        arq_registros = open('games.dat', 'r+b')
        arq_instrucoes = open(arquivo_operacoes, 'r')
        arq_arvore = open('btree.dat', 'r+b')

        raiz = int.from_bytes(arq_arvore.read(TAM_CAB), byteorder='little', signed=True) #le o cabecalho do arquivo arvore
        
        opera = arq_instrucoes.readline() #le uma linha do arquivo de instrucoes

        while opera != '': #enquanto não EOF
            if opera[:2] == 'b ': #buscar
                identificador = int(opera[2:]) #pega o restante da linha e transforma em inteiro -> identificador do registro
                print(f"\nBuscando o registro de identificador: {identificador}")
                registro = buscar(identificador, arq_registros, arq_arvore, raiz) #busca do registro pelo identificador
                print(registro)
            elif opera[:2] == 'i ': #inserir
                registro = opera[2:].strip('\n')
                insercao = inserir(registro, raiz, arq_registros, arq_arvore)
                print(insercao)
            else: #alguma outra letra ou outra coisa
                print(f"\nOPERAÇÃO INVÁLIDA: {opera}.")

            arq_registros.seek(0) #reinicia o arquivo de registros
            arq_arvore.seek(0) #reinicia o arquivo da árvore
            raiz = int.from_bytes(arq_arvore.read(TAM_CAB), byteorder='little', signed=True)
            opera = arq_instrucoes.readline() #le a proxima linha

        print(f"\nAs operações do arquivo \"{arquivo_operacoes}\" foram executadas com sucesso!\n")
        arq_registros.close()
        arq_instrucoes.close()
        arq_arvore.close()
    except FileNotFoundError: #caso nao consiga abrir os arquivos
        print("Não foi possível abrir o arquivo de registros e/ou o arquivo da árvore!")

def imprimir() -> None:
    '''Imprime as páginas da árvore binária armazenada em btree.dat em ordem crescente'''
    try:
        arvore = open('btree.dat', 'rb')
        raiz = int.from_bytes(arvore.read(TAM_CAB), byteorder='little', signed=True)
        rrnMax = novo_rrn(arvore) #qual seria o proximo rrn criado na árvore
        i = 0
        for i in range(rrnMax): #até atingir o rrn que ainda não existe
            pagina = lePagina(i, arvore) #le a página
            if i == raiz: #se for a raiz
                print("\n- - - - - - - - - - Raiz  - - - - - - - - - -") #avisa que é ela
                print(f"Pagina {i}:\nChaves = {pagina.chaves}\nOffsets = {pagina.offsets}\nFilhos = {pagina.filhos}")
                print("- - - - - - - - - - - - - - - - - - - - - - -")
            else: #se não, normal
                print(f"\nPagina {i}:\nChaves = {pagina.chaves}\nOffsets = {pagina.offsets}\nFilhos = {pagina.filhos}") #impressão
            i += 1
        print("\nO índice \"btree.dat\" foi impresso com sucesso!\n")
        arvore.close()
    except FileNotFoundError:
        print("Não foi possível abrir o arquivo da árvore!")

def main() -> None:
    if len(argv) == 2 and argv[1] == '-c': #PROGRAMA.PY -c
        criar()
    elif len(argv) == 3 and argv[1] == '-e': #PROGRAMA.PY -e ARQUIVO_OPERAÇÕES.TXT
        executar(argv[2]) #nome do arquivo de operações
    elif len(argv) == 2 and argv[1] == '-p': #PROGRAMA.PY -p
        imprimir()
    else:
        raise ValueError("Número incorreto de argumentos!")

if __name__ == '__main__':
    main()