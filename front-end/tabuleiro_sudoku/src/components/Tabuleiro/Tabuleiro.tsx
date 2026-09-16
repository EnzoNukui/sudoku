type TabuleiroProps = {
  valores: number[][]
  celulasFixas: boolean[][]
  situacoes: (boolean | null)[][]
  bloqueado: boolean
  blocoLinhas: number
  blocoColunas: number
  celulaSelecionada: [number, number] | null
  aoSelecionar: (linha: number, coluna: number) => void
  aoDigitar: (linha: number, coluna: number, numero: number) => void
  aoConfirmar: (linha: number, coluna: number) => void
}

export default function Tabuleiro({
  valores,
  celulasFixas,
  situacoes,
  bloqueado,
  blocoLinhas,
  blocoColunas,
  celulaSelecionada,
  aoSelecionar,
  aoDigitar,
  aoConfirmar,
}: TabuleiroProps) {
  const tamanho = valores.length

  return (
    <div
      className="grid aspect-square w-full max-w-[620px] border-[3px] border-primaria-escura bg-superficie shadow-painel"
      style={{ gridTemplateColumns: `repeat(${tamanho}, 1fr)` }}
      aria-label={`Tabuleiro de Sudoku ${tamanho} por ${tamanho}`}
    >
      {valores.map((linha, indiceLinha) =>
        linha.map((numero, indiceColuna) => {
          const fixa = celulasFixas[indiceLinha][indiceColuna]
          const situacao = situacoes[indiceLinha]?.[indiceColuna]
          const selecionada =
            celulaSelecionada?.[0] === indiceLinha &&
            celulaSelecionada?.[1] === indiceColuna
          const estadoVisual = fixa
            ? 'bg-celula-fixa font-bold text-texto'
            : situacao === true
              ? 'bg-correta-fundo font-semibold text-correta'
              : situacao === false
                ? 'bg-errada-fundo font-semibold text-errada'
                : selecionada
                  ? 'bg-primaria-clara text-primaria'
                  : 'bg-superficie text-primaria'

          const classes = [
            'min-w-0 border border-borda text-center text-[clamp(1rem,4vw,2rem)] outline-none transition-colors focus:z-10',
            estadoVisual,
            indiceLinha !== 0 && indiceLinha % blocoLinhas === 0
              ? 'border-t-[3px] border-t-primaria-escura'
              : '',
            indiceColuna !== 0 && indiceColuna % blocoColunas === 0
              ? 'border-l-[3px] border-l-primaria-escura'
              : '',
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
              readOnly={fixa || bloqueado}
              value={numero === 0 ? '' : numero}
              onFocus={(evento) => {
                aoSelecionar(indiceLinha, indiceColuna)
                if (!fixa && !bloqueado) evento.target.select()
              }}
              onClick={(evento) => {
                if (!fixa && !bloqueado) evento.currentTarget.select()
              }}
              onKeyDown={(evento) => {
                if (evento.key === 'Enter' && !fixa && !bloqueado) {
                  evento.preventDefault()
                  aoConfirmar(indiceLinha, indiceColuna)
                }
              }}
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
