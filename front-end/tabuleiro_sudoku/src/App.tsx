import { useCallback, useEffect, useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import Footer from './components/Footer/Footer'
import Menu from './components/Menu/Menu'
import Home from './pages/Home/Home'
import Ranking from './pages/Ranking/Ranking'
import {
  carregarSessao,
  EVENTO_SESSAO_EXPIRADA,
  removerSessao,
  salvarSessao,
  type Sessao,
} from './services/sudokuApi'

export default function App() {
  const [sessao, setSessao] = useState<Sessao | null>(carregarSessao)
  const token = sessao?.token ?? null
  const usuario = sessao?.usuario ?? null

  useEffect(() => {
    const encerrarSessaoExpirada = () => setSessao(null)
    window.addEventListener(EVENTO_SESSAO_EXPIRADA, encerrarSessaoExpirada)
    return () => window.removeEventListener(EVENTO_SESSAO_EXPIRADA, encerrarSessaoExpirada)
  }, [])

  const aoEntrar = useCallback((novoToken: string, nome: string) => {
    const novaSessao = { token: novoToken, usuario: nome }
    salvarSessao(novaSessao)
    setSessao(novaSessao)
  }, [])
  const aoSair = useCallback(() => {
    removerSessao()
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
