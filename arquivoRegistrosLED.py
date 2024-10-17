from sys import argv
import io

TAM_REG: int = 2
MINIMO_REG: int = 15
TAM_ENDERECO_LED: int = 4

def leia_reg(arq_dados: io.BytesIO) -> tuple[str, int]:
    '''Le um registro apos ler seu tamanho, retornando os dois.'''
    tam = int.from_bytes(arq_dados.read(TAM_REG)) #pega o tamanho do registro
    if tam > 0: #se não chegar ao fim do arquivo
        marca = arq_dados.read(1).decode() #le o primeiro byte do registro e o decodifica
        if marca == '*': #se for o *, indica um espaco removido:
            arq_dados.read(tam - 1) #le o restante do tamanho
            return '', tam #retorna uma string vazia (espaco removido) e o tamanho do campo.
        else: #se houver um registro
            reg = arq_dados.read(tam - 1).decode() #le o restante do registro e o decodifica
        return (marca + reg), tam #retorna todo o registro (incluindo o primeiro byte) e o tamanho.
    else:
        return '', 0 #retorna a string vazia (fim do arquivo) e tamanho 0.

def lerCabLed(arq_dados: io.BytesIO) -> tuple[int, int]:
    '''Le um offset armazenado em 4 bytes, o busca e le seu tamanho. Retorna o offset e o tamanho.'''
    cabecalho = arq_dados.read(TAM_ENDERECO_LED) #le o cabecalho -> cabeca da LED
    cabeca = int.from_bytes(cabecalho, signed= True) #transforma em inteiro com sinal
    cab = int.from_bytes(cabecalho) #transforma em inteiro sem sinal
    if cabeca == -1: #se o inteiro com sinal for -1:
        return cabeca, 0 #retorna o -1 e 0 para indicar o fim do arquivo
    else:
        arq_dados.seek(cab) #vai ate o byte offset
        tam = int.from_bytes(arq_dados.read(TAM_REG)) #pega o tamanho do espaco
        return cab, tam #retorna o offset lido e o tamanho do seu espaco

def buscar(arq_dados: io.BytesIO, identificador: int) -> str:
    '''Busca o registro do 'identificador'.'''
    registro, tam = leia_reg(arq_dados) #transforma em string
    if tam != 0: #se nao EOF
        if registro != '': #exclui o retorno de leia_reg quando passa por um espaco vazio na LED (*).
            reg = registro.split(sep='|') #transforma o registro em uma lista de campos
            if int(reg[0]) == identificador: #o primeiro campo é o identificador do registro
                return f"{registro} ({tam} bytes)" #registro (bytes)
            else:
                return buscar(arq_dados, identificador) #se não for o registro correto, busca o proximo registro
        else:
            return buscar(arq_dados, identificador) #pula pro proximo registro
    else:
        return "IDENTIFICADOR NÃO ENCONTRADO" #chagou ao fim, o identificador nao existe

def atualizaled(arq_dados: io.BytesIO, offset: int) -> None:
    '''Escreve o 'offset' em formato de 4 bytes (na LED).'''
    if offset == -1:
        arq_dados.write(offset.to_bytes(TAM_ENDERECO_LED, signed=True))
    else:
        arq_dados.write(offset.to_bytes(TAM_ENDERECO_LED))

def arrumaled(arq_dados: io.BytesIO, offset: int, tam: int, cabeca: int, tamCabec: int) -> None:
    '''Insere o espaco de offset 'offset' e tamanho 'tam' na LED, procurando sua posicao pela LED a partir do cabecalho 'cabeca' de tamanho 'tamCabec'.'''
    anterior = 0 #iniciando as comparacoes a partir do cabecalho
    tamLed = tamCabec #armazena o tamanho do espaco 
    while cabeca != -1 and tamLed > tam: #enquanto não chegar ao fim da LED e o tamanho do espaco daquele endereco nao for maior o novo:
        arq_dados.seek(cabeca + 3) #vai até o offset do cabecalho, pulando os bytes de tamanho e o *
        anterior = cabeca + 3 #armazena esse endereco como o ultimo offset de espaco maior ou ultimo diferente de -1
        cabeca, tamLed = lerCabLed(arq_dados) #le o proximo endereco da LED e pega seu tamanho

    arq_dados.seek(anterior) #vai ate o ultimo espaco (maior ou diferente de -1).
    atualizaled(arq_dados, offset) #escreve o novo offset na LED
    arq_dados.seek(offset + 3) #pular os bytes de tamanho e asterisco *
    atualizaled(arq_dados, cabeca) #escreve o offset do ultimo espaco (maior ou -1) no novo espaco.

def inserir(registro: str, arq_dados: io.BytesIO, cabeca: int, tamCabeca: int) -> str:
    '''Insere o registro 'registro' no arquivo com a estrategia worst-fit, ou seja, na cabeca da LED 'cabeca' ou no fim do arquivo.'''
    reg = registro.split(sep='|')
    tam = len(registro)
    print(f"\nInserção do registro de chave: {reg[0]} ({tam} bytes)")
    registro = registro.encode()
    if cabeca == -1 or tamCabeca < tam: #se nao houver espacos na LED ou o tamanho do espaco da cabeca for menor que o novo.
        arq_dados.seek(0, 2) # vai para o fim do arquivo
        arq_dados.write(tam.to_bytes(TAM_REG)) #escreve o tamanho em 2 bytes
        arq_dados.write(registro) #escreve o novo registro
        return "Local: fim do arquivo"
    else:
        arq_dados.seek(cabeca)
        sobra = tamCabeca - (tam + 2)
        if sobra >= MINIMO_REG:
            arq_dados.write(sobra.to_bytes(TAM_REG)) #escreve o tamanho da sobra
            arq_dados.seek(sobra, 1) #pula a sobra
            arq_dados.write(tam.to_bytes(TAM_REG)) #escreve o tamanho do novo depois da sobra
            arq_dados.write(registro) #escreve o novo registro
            arq_dados.seek(cabeca + 3) #volta na sobra, pulando os bytes de tamanho e o *
            proxLed, tamProx = lerCabLed(arq_dados) #pega o segundo endereco da LED -> primeiro sem ser o cabecalho
            if sobra < tamProx: #se a sobra for menor que o segundo espaco da LED:
                arq_dados.seek(0)
                atualizaled(arq_dados, proxLed) #coloca o segundo espaco como o cabecalho.
                arrumaled(arq_dados, cabeca, sobra, proxLed, tamProx) #encontra o lugar de insercao da sobra na LED
            #else: nao alteraria a LED.
            return f"Tamanho do espaço reutilizado: {tamCabeca} bytes (Sobra de {sobra} bytes)\nLocal: offset = {cabeca} bytes ({hex(cabeca)})"
        else: #se a sobra for pequena (ou 0).
            arq_dados.read(3) #pula os bytes de tamanho e o *
            proxLed, tamProx = lerCabLed(arq_dados) #pega o segundo espaco da LED
            arq_dados.seek(cabeca + 2) #volta no espaco de insercao (pula o tamanho)
            arq_dados.write(registro.ljust(tamCabeca, b'\0')) #escreve o novo registro, completando a sobra com bytes vazios.
            arq_dados.seek(0)
            atualizaled(arq_dados, proxLed) #segundo espaco vira cabeca da LED
        return f"Tamanho do espaço reutilizado: {tamCabeca} bytes\nLocal: offset = {cabeca} bytes ({hex(cabeca)})"

def remover(arq_dados: io.BytesIO, identificador: int, offset: int, cabeca: int, tamCabec: int) -> str:
    '''Busca e remove o registro do indentificador, adicionando seu espaco a LED.'''
    registro, tam = leia_reg(arq_dados)
    if tam != 0: #se nao EOF.
        if registro != '': #se nao for espaco removido.
            reg = registro.split(sep='|')
            if int(reg[0]) == identificador: #se o registro a ser removido foi encontrado:
                arq_dados.seek(offset + 2) # +2 pula os bytes de tamanho para gravar o *
                arq_dados.write('*'.encode()) #escreve o asterisco pra marcar como removido
                arrumaled(arq_dados, offset, tam, cabeca, tamCabec)
                return f"Registro removido! ({tam} bytes)\nLocal: offset = {offset} bytes ({hex(offset)})" #retorno de remocao
            else:
                offset = offset + tam + 2 #a cada registro errado, pula-se o registro e os bytes de tamanho
                return remover(arq_dados, identificador, offset, cabeca, tamCabec) #ate achar o que vai remover
        else:
            offset = offset + tam + 2 #a cada registro errado, pula-se o registro e os bytes de tamanho
            return remover(arq_dados, identificador, offset, cabeca, tamCabec) #ate achar o que vai remover
    else:
        return "Erro: Registro não encontrado!" #o resgistro nao existe.

def executa(nome_operacoes: str) -> None:
    '''Executa o arquivo de operacoes.'''
    try: #tenta abrir os arquivos e executa-los.
        arq_dados = open('dados.dat', 'r+b')
        arq_instrucoes = open(nome_operacoes, 'r')

        cabecalho, tamCabecalho = lerCabLed(arq_dados)
        arq_dados.seek(4) #coloca o ponteiro logo apos o cabecalho -> primeiro byte do primeiro registro
        
        opera = arq_instrucoes.readline() #le a linha do arquivo de instrucoes

        while opera != '': #enquanto não EOF
            if opera[:2] == 'b ': #buscar
                identificador = int(opera[2:]) #pega o restante da linha e transforma em inteiro -> identificador do registro
                print(f"\nBuscando o registro de identificador: {identificador}")
                registro = buscar(arq_dados, identificador) #busca do registro pelo identificador
                print(registro)
            elif opera[:2] == 'i ': #inserir
                if opera[-1] == '\n':
                    registro = opera[2:-1] #exclui a quebra de linha se tiver.
                else:
                    registro = opera[2:]
                insercao = inserir(registro, arq_dados, cabecalho, tamCabecalho)
                print(insercao)
            elif opera[:2] == 'r ': #remover
                identificador = int(opera[2:])
                print(f"\nRemoção do registro de chave: {identificador}")
                offset = 4 #offset do primeiro registro -> iniciar a busca do registro a ser removido
                remocao = remover(arq_dados, identificador, offset, cabecalho, tamCabecalho)
                print(remocao)
            else: #alguma outra letra ou outra coisa
                print(f"\nOPERAÇÃO INVÁLIDA: {opera}.")

            arq_dados.seek(0)
            cabecalho, tamCabecalho = lerCabLed(arq_dados) #atualiza o cabecalho
            arq_dados.seek(4) #coloca o ponteiro no primeiro registro
            opera = arq_instrucoes.readline() #le a proxima linha

        arq_dados.close()
        arq_instrucoes.close()
    except: #caso nao consiga abrir os arquivos
        print("Não foi possível abrir os arquivos.")

def led() -> None:
    '''Imprime a LED.'''
    try: #tenta abrir o arquivo de dados para percorrer a LED.
        arq_dados = open('dados.dat', 'rb')
        endLed, tam = lerCabLed(arq_dados) #le o cabecalho -> a cabeca da LED.
        print('\nLED', end=' ') #para imprimir tudo na mesma linha
        while endLed != -1 and tam != 0:
            print(f'-> [offset: {endLed}, tam: {tam}]', end=' ')
            arq_dados.read(1) #le o * do espaco vazio
            endLed, tam = lerCabLed(arq_dados)

        print(f'-> [offset: {endLed}]\n') #imprime o ultimo endereco da LED -> o -1 (tam = 0).
        arq_dados.close()
    except: #caso o arquivo de dados nao exista
        print(f"Não foi possível abrir o arquivo dados.")

def main() -> None:
    if len(argv) == 2 and argv[1] == '-p': # PROGRAMA.PY -p
        led()
    elif len(argv) == 3 and argv[1] == '-e': # PROGRAMA.PY -e OPERACOES.TXT
        executa(argv[2]) #argv[2] e o nome do arquivo de operacoes a ser aberto.
    else:
        raise ValueError("Número incorreto de argumentos.")

if __name__ == '__main__':
    main()