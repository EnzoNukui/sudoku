type TabuleiroProps = {
  valores: number[][]
  celulasFixas: boolean[][]
  blocoLinhas: number
  blocoColunas: number
  celulaSelecionada: [number, number] | null
  aoSelecionar: (linha: number, coluna: number) => void
  aoDigitar: (linha: number, coluna: number, numero: number) => void
}

function Tabuleiro({
  valores,
  celulasFixas,
  blocoLinhas,
  blocoColunas,
  celulaSelecionada,
  aoSelecionar,
  aoDigitar,
}: TabuleiroProps) {
  const tamanho = valores.length

  return (
    <div
      className="tabuleiro"
      style={{ gridTemplateColumns: `repeat(${tamanho}, 1fr)` }}
      aria-label={`Tabuleiro de Sudoku ${tamanho} por ${tamanho}`}
    >
      {valores.map((linha, indiceLinha) =>
        linha.map((numero, indiceColuna) => {
          const fixa = celulasFixas[indiceLinha][indiceColuna]
          const selecionada =
            celulaSelecionada?.[0] === indiceLinha &&
            celulaSelecionada?.[1] === indiceColuna

          const classes = [
            'celula',
            fixa ? 'celula--fixa' : '',
            selecionada ? 'celula--selecionada' : '',
            indiceLinha % blocoLinhas === 0 ? 'bloco--topo' : '',
            indiceColuna % blocoColunas === 0 ? 'bloco--esquerda' : '',
            (indiceLinha + 1) % blocoLinhas === 0 ? 'bloco--base' : '',
            (indiceColuna + 1) % blocoColunas === 0 ? 'bloco--direita' : '',
          ]
            .filter(Boolean)
            .join(' ')

          return (
            <input
              aria-label={`Linha ${indiceLinha + 1}, coluna ${indiceColuna + 1}`}
              className={classes}
              inputMode="numeric"
              key={`${indiceLinha}-${indiceColuna}`}
              maxLength={1}
              readOnly={fixa}
              value={numero === 0 ? '' : numero}
              onFocus={() => aoSelecionar(indiceLinha, indiceColuna)}
              onChange={(evento) => {
                const valor = evento.target.value

                if (valor === '') {
                  aoDigitar(indiceLinha, indiceColuna, 0)
                  return
                }

                const novoNumero = Number(valor)

                if (Number.isInteger(novoNumero) && novoNumero >= 1 && novoNumero <= tamanho) {
                  aoDigitar(indiceLinha, indiceColuna, novoNumero)
                }
              }}
            />
          )
        }),
      )}
    </div>
  )
}

export default Tabuleiro
