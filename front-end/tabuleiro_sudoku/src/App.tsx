import { useCallback, useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import Footer from './components/Footer/Footer'
import Menu from './components/Menu/Menu'
import Home from './pages/Home/Home'
import Ranking from './pages/Ranking/Ranking'

type Sessao = {
  token: string
  usuario: string
}

const CHAVE_SESSAO = 'sudoku_sessao'

function carregarSessao(): Sessao | null {
  try {
    const sessao = localStorage.getItem(CHAVE_SESSAO)
    if (!sessao) return null
    const dados = JSON.parse(sessao) as Partial<Sessao>
    return typeof dados.token === 'string' && typeof dados.usuario === 'string'
      ? { token: dados.token, usuario: dados.usuario }
      : null
  } catch {
    localStorage.removeItem(CHAVE_SESSAO)
    return null
  }
}

export default function App() {
  const [sessao, setSessao] = useState<Sessao | null>(carregarSessao)
  const token = sessao?.token ?? null
  const usuario = sessao?.usuario ?? null
  const aoEntrar = useCallback((novoToken: string, nome: string) => {
    const novaSessao = { token: novoToken, usuario: nome }
    localStorage.setItem(CHAVE_SESSAO, JSON.stringify(novaSessao))
    setSessao(novaSessao)
  }, [])
  const aoSair = useCallback(() => {
    localStorage.removeItem(CHAVE_SESSAO)
    setSessao(null)
  }, [])

  return (
    <div className="flex min-h-screen flex-col">
      <Menu usuario={usuario} aoEntrar={aoEntrar} aoSair={aoSair} />
      <Routes>
        <Route path="/" element={<Home key={token ?? 'visitante'} token={token} />} />
        <Route path="/ranking" element={<Ranking />} />
      </Routes>
      <Footer />
    </div>
  )
}
