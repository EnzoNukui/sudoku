import { useCallback, useEffect, useState } from 'react'
import Content from '../../components/Content/Content'
import Tabuleiro from '../../components/Tabuleiro/Tabuleiro'
import {
  criarNovoJogo,
  verificarJogada,
  verificarTabuleiro,
  type Dificuldade,
  type Jogo,
  type TamanhoSudoku,
} from '../../services/sudokuApi'

export default function Home() {
  const [tamanho, setTamanho] = useState<TamanhoSudoku>(9)
  const [dificuldade, setDificuldade] = useState<Dificuldade>('facil')
  const [jogo, setJogo] = useState<Jogo | null>(null)
  const [tabuleiro, setTabuleiro] = useState<number[][]>([])
  const [celulasFixas, setCelulasFixas] = useState<boolean[][]>([])
  const [situacoes, setSituacoes] = useState<(boolean | null)[][]>([])
  const [celulaSelecionada, setCelulaSelecionada] = useState<[number, number] | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [mensagem, setMensagem] = useState('')
  const classeSelecao =
    'rounded-jogo border border-borda bg-superficie px-3 py-2 text-texto outline-none transition-colors focus:border-borda-forte focus:ring-2 focus:ring-primaria-clara'
  const classeBotao =
    'min-h-12 rounded-jogo border border-borda bg-superficie px-4 py-3 font-medium text-texto transition-colors hover:bg-primaria-clara disabled:opacity-50'

  const carregarJogo = useCallback(async () => {
    try {
      const novoJogo = await criarNovoJogo(tamanho, dificuldade)
      setJogo(novoJogo)
      setTabuleiro(novoJogo.tabuleiro.map((linha) => [...linha]))
      setCelulasFixas(
        novoJogo.tabuleiro.map((linha) => linha.map((numero) => numero !== 0)),
      )
      setSituacoes(
        novoJogo.tabuleiro.map((linha) => linha.map(() => null)),
      )
    } catch {
      setJogo(null)
      setMensagem('Não foi possível carregar o jogo. Verifique se a API está ligada.')
    } finally {
      setCarregando(false)
    }
  }, [tamanho, dificuldade])

  useEffect(() => {
    void carregarJogo()
  }, [carregarJogo])

  async function digitarNumero(linha: number, coluna: number, numero: number) {
    if (celulasFixas[linha]?.[coluna] || !jogo) {
      return
    }

    const novoTabuleiro = tabuleiro.map((valores) => [...valores])
    novoTabuleiro[linha][coluna] = numero
    setTabuleiro(novoTabuleiro)
    setMensagem('')

    const novasSituacoes = situacoes.map((valores) => [...valores])

    if (numero === 0) {
      novasSituacoes[linha][coluna] = null
      setSituacoes(novasSituacoes)
      return
    }

    try {
      const correta = await verificarJogada(jogo.jogo_id, linha, coluna, numero)
      novasSituacoes[linha][coluna] = correta
      setSituacoes(novasSituacoes)
    } catch {
      setMensagem('Não foi possível verificar a jogada.')
      return
    }

    if (novoTabuleiro.every((valores) => valores.every((valor) => valor !== 0))) {
      const completo = await verificarTabuleiro(jogo.jogo_id, novoTabuleiro)
      setMensagem(completo ? 'Parabéns! Você completou o Sudoku.' : 'Ainda existem erros no tabuleiro.')
    }
  }

  function apagarSelecionada() {
    if (!celulaSelecionada) {
      setMensagem('Selecione uma célula para apagar.')
      return
    }

    const [linha, coluna] = celulaSelecionada

    if (celulasFixas[linha][coluna]) {
      setMensagem('Os números iniciais não podem ser apagados.')
      return
    }

    void digitarNumero(linha, coluna, 0)
  }

  return (
    <Content>
      <section
        className="mb-6 flex flex-col justify-center gap-3 sm:flex-row sm:gap-6"
        aria-label="Configurações do jogo"
      >
          <label className="flex items-center justify-between gap-2 font-bold sm:justify-start">
            Tamanho
            <select
              className={classeSelecao}
              value={tamanho}
              onChange={(evento) => {
                setCarregando(true)
                setMensagem('')
                setCelulaSelecionada(null)
                setTamanho(Number(evento.target.value) as TamanhoSudoku)
              }}
            >
              <option value={4}>4 × 4</option>
              <option value={6}>6 × 6</option>
              <option value={9}>9 × 9</option>
            </select>
          </label>

          <label className="flex items-center justify-between gap-2 font-bold sm:justify-start">
            Dificuldade
            <select
              className={classeSelecao}
              value={dificuldade}
              onChange={(evento) => {
                setCarregando(true)
                setMensagem('')
                setCelulaSelecionada(null)
                setDificuldade(evento.target.value as Dificuldade)
              }}
            >
              <option value="facil">Fácil</option>
              <option value="medio">Médio</option>
              <option value="dificil">Difícil</option>
            </select>
          </label>
      </section>

      <section className="grid items-start gap-6 md:grid-cols-[minmax(0,1fr)_minmax(280px,620px)_minmax(0,1fr)]">
          <div className="min-w-0 md:col-start-2">
            {carregando && (
              <p className="py-8 text-center text-texto-suave">Carregando tabuleiro...</p>
            )}

            {!carregando && jogo && (
              <Tabuleiro
                valores={tabuleiro}
                celulasFixas={celulasFixas}
                situacoes={situacoes}
                blocoLinhas={jogo.bloco_linhas}
                blocoColunas={jogo.bloco_colunas}
                celulaSelecionada={celulaSelecionada}
                aoSelecionar={(linha, coluna) => setCelulaSelecionada([linha, coluna])}
                aoDigitar={(linha, coluna, numero) => void digitarNumero(linha, coluna, numero)}
              />
            )}

            {mensagem && (
              <p className="mt-3 min-h-6 text-center font-semibold text-primaria-escura" role="status">
                {mensagem}
              </p>
            )}
          </div>

          <aside
            className="grid grid-cols-3 gap-3 md:col-start-3 md:w-full md:max-w-[170px] md:grid-cols-1"
            aria-label="Controles do jogo"
          >
            <button
              className={`${classeBotao} bg-primaria-clara font-bold text-primaria-escura`}
              type="button"
              onClick={() => {
                setCarregando(true)
                setMensagem('')
                setCelulaSelecionada(null)
                void carregarJogo()
              }}
            >
              Novo jogo
            </button>
            <button className={classeBotao} type="button" onClick={apagarSelecionada}>
              Apagar
            </button>
            <button
              className={classeBotao}
              type="button"
              disabled
              title="A dica será implementada na próxima etapa"
            >
              Dica
            </button>
          </aside>
      </section>
    </Content>
  )
}
