import random


def criar_tabuleiro(tamanho):
    tabuleiro = []

    for i in range(tamanho):
        linha = []

        for j in range(tamanho):
            linha.append(0)

        tabuleiro.append(linha)

    return tabuleiro


def verificar_linha(tabuleiro, linha, numero):
    for coluna in range(len(tabuleiro)):
        if tabuleiro[linha][coluna] == numero:
            return False

    return True


def verificar_coluna(tabuleiro, coluna, numero):
    for linha in range(len(tabuleiro)):
        if tabuleiro[linha][coluna] == numero:
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

    if not verificar_linha(tabuleiro, linha, numero):
        return False

    if not verificar_coluna(tabuleiro, coluna, numero):
        return False

    if not verificar_quadrado(tabuleiro, linha, coluna, numero, tamanho_bloco):
        return False

    return True


def encontrar_vazio(tabuleiro):
    for i in range(len(tabuleiro)):
        for j in range(len(tabuleiro)):
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


def quantidade_por_dificuldade(tamanho, dificuldade):
    porcentagens = {
        "facil": 0.4,
        "medio": 0.5,
        "dificil": 0.6,
    }

    total_celulas = tamanho * tamanho
    return int(total_celulas * porcentagens[dificuldade])


def obter_tamanho_bloco(tamanho):
    tamanhos = {
        4: (2, 2),
        6: (2, 3),
        9: (3, 3),
    }

    return tamanhos[tamanho]


def criar_jogo(tamanho, dificuldade):
    tabuleiro, solucao = criar_jogo_com_solucao(tamanho, dificuldade)
    return tabuleiro


def criar_jogo_com_solucao(tamanho, dificuldade):
    tamanho_bloco = obter_tamanho_bloco(tamanho)
    tabuleiro = criar_tabuleiro(tamanho)
    gerar_solucao(tabuleiro, tamanho_bloco)
    solucao = copiar_tabuleiro(tabuleiro)

    quantidade = quantidade_por_dificuldade(tamanho, dificuldade)
    remover_numeros(tabuleiro, quantidade)

    return tabuleiro, solucao


def verificar_tabuleiro_completo(tabuleiro, tamanho_bloco):
    tamanho = len(tabuleiro)

    for linha in range(tamanho):
        for coluna in range(tamanho):
            numero = tabuleiro[linha][coluna]

            if numero == 0:
                return False

            tabuleiro[linha][coluna] = 0
            jogada_valida = verificar_jogada(
                tabuleiro, linha, coluna, numero, tamanho_bloco
            )
            tabuleiro[linha][coluna] = numero

            if not jogada_valida:
                return False

    return True
