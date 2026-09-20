import random

def escolher_tamanho():
    while True:
        print("1 - Sudoku 4x4")
        print("2 - Sudoku 6x6")
        print("3 - Sudoku 9x9")

        entrada = input("Escolha uma opção: ")

        try:
            escolha = int(entrada)

            if escolha == 1:
                return 4, (2, 2)
            elif escolha == 2:
                return 6, (2, 3)
            elif escolha == 3:
                return 9, (3, 3)
            else:
                print("Opção inválida, escolha 1, 2 ou 3.\n")
        except ValueError:
            print("Entrada inválida! Digite apenas o número da opção (não deixe em branco).\n")

def escolher_dificuldade(tamanho_tabuleiro):
    while True:
        print("\n1 - Fácil")
        print("2 - Médio")
        print("3 - Difícil")

        dificuldade = int(input("Escolha a dificuldade: "))

        try:
    
            total_celulas = tamanho_tabuleiro * tamanho_tabuleiro

            if dificuldade == 1:
                return int(total_celulas * 0.4)
            elif dificuldade == 2:
                return int(total_celulas * 0.5)
            elif dificuldade == 3:
                return int(total_celulas * 0.6)
            else:
                print("Opção inválida, escolha 1, 2 ou 3.")
        except ValueError:
            print("Entrada inválida! Digite apenas o número da opção.")

def criar_tabuleiro(tamanho_tabuleiro):
    tabuleiro = []

    for i in range(tamanho_tabuleiro):
        linha = []

        for j in range(tamanho_tabuleiro):
            linha.append(0)

        tabuleiro.append(linha)

    return tabuleiro
    
    

def mostrar_tabuleiro(tabuleiro, tamanho_bloco):
    bloco_linhas, bloco_colunas = tamanho_bloco

    for i in range(len(tabuleiro)):
        for j in range(len(tabuleiro[i])):
            if tabuleiro[i][j] == 0:
                print(".", end=" ")
            else:
                print(tabuleiro[i][j], end=" ")

            if (j + 1) % bloco_colunas == 0 and j != len(tabuleiro[i]) - 1:
                print("|", end=" ")

        print()

        if (i + 1) % bloco_linhas == 0 and i != len(tabuleiro) - 1:
            print("-" * (len(tabuleiro) * 2 + bloco_colunas))



def verificar_linha(tabuleiro, linha, numero):
    for i in range(len(tabuleiro[linha])):
        if tabuleiro[linha][i] == numero:
            return False

    return True
          
def verificar_coluna(tabuleiro, coluna, numero):
    for i in range(len(tabuleiro)):
          if tabuleiro[i][coluna] == numero:
              return False

    return True

def verificar_quadrado(tabuleiro, linha, coluna, numero, tamanho_bloco):
    bloco_linhas, bloco_colunas = tamanho_bloco
    inicio_linha = (linha // bloco_linhas) * bloco_linhas
    inicio_coluna = (coluna // bloco_colunas) * bloco_colunas
    for i in range(inicio_linha, inicio_linha + bloco_linhas):  
        for j in range(inicio_coluna, inicio_coluna + bloco_colunas):
            if tabuleiro[i][j] == numero:
                return False
    return True  

def verificar_jogada(tabuleiro, linha, coluna, numero, tamanho_bloco):
    if numero < 1 or numero > len(tabuleiro):
        return False
    
    if verificar_linha(tabuleiro, linha, numero) == False:
        return False

    if verificar_coluna(tabuleiro, coluna, numero) == False:
        return False

    if verificar_quadrado(tabuleiro, linha, coluna, numero, tamanho_bloco) == False:
        return False

    return True 

def encontrar_vazio(tabuleiro):
    for i in range(len(tabuleiro)):
        for j in range(len(tabuleiro[i])):
            if tabuleiro[i][j] == 0:
                return i, j

    return None   

def gerar_solucao(tabuleiro, tamanho_bloco):
    posicao = encontrar_vazio(tabuleiro)

    if posicao is None:
        return True

    linha, coluna = posicao                     

    numeros = list(range(1, len(tabuleiro) + 1))
    random.shuffle(numeros)

    for numero in numeros:
        if verificar_jogada(tabuleiro, linha, coluna, numero, tamanho_bloco):
            tabuleiro[linha][coluna] = numero

            if gerar_solucao(tabuleiro, tamanho_bloco):
                return True

            tabuleiro[linha][coluna] = 0

    return False

def copiar_tabuleiro(tabuleiro):
    copia = []

    for linha in tabuleiro:
        copia.append(linha.copy())

    return copia
        
def remover_numeros(tabuleiro, quantidade):
    removidos = 0

    while removidos < quantidade:
        linha = random.randint(0, len(tabuleiro) - 1)
        coluna = random.randint(0, len(tabuleiro) - 1)

        if tabuleiro[linha][coluna] != 0:
            tabuleiro[linha][coluna] = 0
            removidos += 1

def verificar_completo(tabuleiro):
    for i in range(len(tabuleiro)):
        for j in range(len(tabuleiro[i])):
            if tabuleiro[i][j] == 0:
                return False

    return True

def criar_celulas_fixas(tabuleiro):
    celulas_fixas = []

    for i in range(len(tabuleiro)):
        linha = []

        for j in range(len(tabuleiro)):
            if tabuleiro[i][j] != 0:
                linha.append(True)
            else:
                linha.append(False)

        celulas_fixas.append(linha)

    return celulas_fixas

def posicao_valida(tabuleiro, linha, coluna):
    if linha < 0 or linha >= len(tabuleiro):
        return False

    if coluna < 0 or coluna >= len(tabuleiro):
        return False

    return True


def apagar_jogada(tabuleiro, celulas_fixas, linha, coluna):
    if not posicao_valida(tabuleiro, linha, coluna):
        print("Linha ou coluna fora do tabuleiro!")
        return

    if celulas_fixas[linha][coluna]:
        print("Essa célula é fixa e não pode ser apagada!")
        return

    if tabuleiro[linha][coluna] == 0:
        print("Essa célula já está vazia!")
        return

    tabuleiro[linha][coluna] = 0
    print("Jogada apagada com sucesso!")

def menu_principal():
    while True:
        print("\n=== SUDOKU ===")
        print("1 - Jogar")
        print("2 - Sair")

        try:
            opcao = int(input("Escolha uma opção: "))

            if opcao == 1 or opcao == 2:
                return opcao

            print("Opção inválida, escolha 1 ou 2.")
        except ValueError:
            print("Entrada inválida! Digite apenas o número da opção.")

def jogar_sudoku(tabuleiro, celulas_fixas, tamanho_bloco):
    while verificar_completo(tabuleiro) == False:
        mostrar_tabuleiro(tabuleiro, tamanho_bloco)

        print("\n1 - Fazer jogada")
        print("2 - Apagar jogada")
        print("3 - Voltar")

        try:
            opcao = int(input("Escolha uma opção: "))

            if opcao == 3:
                print("Voltando...")
                return

            if opcao != 1 and opcao != 2:
                print("Opção inválida!")
                continue

            linha = int(input(f'Digite a linha (1 a {len(tabuleiro)}): ')) - 1
            coluna = int(input(f'Digite a coluna (1 a {len(tabuleiro)}): ')) - 1

        except ValueError:
            print('Digite apenas números!')
            continue

        if posicao_valida(tabuleiro, linha, coluna) == False:
            print('Linha ou coluna fora do tabuleiro!')
            continue

        if opcao == 2:
            apagar_jogada(tabuleiro, celulas_fixas, linha, coluna)
            continue

        try:
            numero = int(input('Digite o número: '))
        except ValueError:
            print('Digite apenas números!')
            continue

        if celulas_fixas[linha][coluna] == True:
            print('Essa célula é fixa!')
            continue

        elif verificar_jogada(tabuleiro, linha, coluna, numero, tamanho_bloco):
            tabuleiro[linha][coluna] = numero

        else:
            print('Jogada Inválida, tente novamente!')

    print('Parabéns, você conseguiu completar o Sudoku!')
    
       
#Main (menu do Sudoku)


def main_sudoku():
    while True:
        opcao = menu_principal()

        if opcao == 2:
            print("Saindo do jogo...")
            return

        tamanho, tamanho_bloco = escolher_tamanho()
        quantidade_remover = escolher_dificuldade(tamanho)
        tabuleiro = criar_tabuleiro(tamanho)

        gerar_solucao(tabuleiro, tamanho_bloco)

        solucao = copiar_tabuleiro(tabuleiro)

        remover_numeros(tabuleiro, quantidade_remover)

        celulas_fixas = criar_celulas_fixas(tabuleiro)

        jogar_sudoku(tabuleiro, celulas_fixas, tamanho_bloco)


main_sudoku()

    
                
