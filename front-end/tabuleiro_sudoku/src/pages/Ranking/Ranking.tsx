import { useEffect, useState } from 'react'
import Content from '../../components/Content/Content'
import {
  buscarRanking,
  type Dificuldade,
  type PosicaoRanking,
  type TamanhoSudoku,
} from '../../services/sudokuApi'

const nomesDificuldade: Record<Dificuldade, string> = {
  facil: 'Fácil',
  medio: 'Médio',
  dificil: 'Difícil',
}

function formatarTempo(tempoMs: number) {
  const segundosTotais = Math.floor(tempoMs / 1000)
  const minutos = Math.floor(segundosTotais / 60)
  const segundos = segundosTotais % 60
  return `${String(minutos).padStart(2, '0')}:${String(segundos).padStart(2, '0')}`
}

export default function Ranking() {
  const [tamanho, setTamanho] = useState<TamanhoSudoku>(9)
  const [dificuldade, setDificuldade] = useState<Dificuldade>('facil')
  const [posicoes, setPosicoes] = useState<PosicaoRanking[]>([])
  const [carregando, setCarregando] = useState(true)
  const [mensagem, setMensagem] = useState('')
  const classeSelecao = 'rounded-jogo border border-borda bg-superficie px-3 py-2 outline-none focus:border-borda-forte focus:ring-2 focus:ring-primaria-clara'

  useEffect(() => {
    let ativo = true

    void buscarRanking(tamanho, dificuldade)
      .then((resultado) => {
        if (ativo) setPosicoes(resultado)
      })
      .catch(() => {
        if (ativo) {
          setPosicoes([])
          setMensagem('Não foi possível carregar o ranking. Verifique se a API está ligada.')
        }
      })
      .finally(() => {
        if (ativo) setCarregando(false)
      })

    return () => {
      ativo = false
    }
  }, [tamanho, dificuldade])

  return (
    <Content>
      <section className="mx-auto w-full max-w-3xl" aria-labelledby="titulo-ranking">
        <h2 id="titulo-ranking" className="text-center text-2xl font-bold text-primaria-escura">Ranking</h2>
        <p className="mt-2 text-center text-sm text-texto-suave">
          Melhores tempos de partidas sem dicas e sem vidas extras.
        </p>

        <div className="my-6 flex flex-col justify-center gap-3 sm:flex-row sm:gap-6">
          <label className="flex items-center justify-between gap-2 font-bold sm:justify-start">
            Tamanho
            <select className={classeSelecao} value={tamanho} onChange={(evento) => {
              setCarregando(true)
              setMensagem('')
              setTamanho(Number(evento.target.value) as TamanhoSudoku)
            }}>
              <option value={4}>4 × 4</option>
              <option value={6}>6 × 6</option>
              <option value={9}>9 × 9</option>
            </select>
          </label>
          <label className="flex items-center justify-between gap-2 font-bold sm:justify-start">
            Dificuldade
            <select className={classeSelecao} value={dificuldade} onChange={(evento) => {
              setCarregando(true)
              setMensagem('')
              setDificuldade(evento.target.value as Dificuldade)
            }}>
              {(Object.keys(nomesDificuldade) as Dificuldade[]).map((valor) => (
                <option key={valor} value={valor}>{nomesDificuldade[valor]}</option>
              ))}
            </select>
          </label>
        </div>

        {carregando ? (
          <p className="py-10 text-center text-texto-suave">Carregando ranking...</p>
        ) : mensagem ? (
          <p className="py-10 text-center font-semibold text-errada" role="status">{mensagem}</p>
        ) : posicoes.length === 0 ? (
          <p className="rounded-jogo border border-borda bg-superficie px-4 py-10 text-center text-texto-suave">
            Ainda não há partidas classificadas para esta configuração.
          </p>
        ) : (
          <div className="overflow-x-auto rounded-jogo border border-borda bg-superficie shadow-painel">
            <table className="w-full border-collapse text-left">
              <thead className="bg-primaria-clara text-primaria-escura">
                <tr>
                  <th className="px-4 py-3" scope="col">Posição</th>
                  <th className="px-4 py-3" scope="col">Jogador</th>
                  <th className="px-4 py-3 text-right" scope="col">Tempo</th>
                  <th className="px-4 py-3 text-right" scope="col">Erros</th>
                </tr>
              </thead>
              <tbody>
                {posicoes.map((posicao) => (
                  <tr className="border-t border-borda" key={`${posicao.posicao}-${posicao.finalizada_em}`}>
                    <td className="px-4 py-3 font-bold">{posicao.posicao}º</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {posicao.foto_url ? (
                          <img className="size-9 rounded-full" src={posicao.foto_url} alt="" referrerPolicy="no-referrer" />
                        ) : (
                          <span className="flex size-9 items-center justify-center rounded-full bg-primaria-clara font-bold" aria-hidden="true">
                            {posicao.nome.charAt(0).toUpperCase()}
                          </span>
                        )}
                        <span className="font-medium">{posicao.nome}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-semibold">{formatarTempo(posicao.tempo_ms)}</td>
                    <td className="px-4 py-3 text-right">{posicao.erros}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </Content>
  )
}
