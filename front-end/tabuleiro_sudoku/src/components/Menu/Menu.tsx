import { useEffect, useRef, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { entrarComGoogle } from '../../services/sudokuApi'

type GoogleIdentity = {
  accounts: {
    id: {
      initialize: (opcoes: { client_id: string; callback: (resposta: { credential: string }) => void }) => void
      renderButton: (elemento: HTMLElement, opcoes: { theme: string; size: string; text: string }) => void
      disableAutoSelect: () => void
    }
  }
}

function googleIdentity(): GoogleIdentity | undefined {
  return (window as Window & { google?: GoogleIdentity }).google
}

export default function Menu({
  usuario,
  aoEntrar,
  aoSair,
}: {
  usuario: string | null
  aoEntrar: (token: string, nome: string) => void
  aoSair: () => void
}) {
  const botaoGoogle = useRef<HTMLDivElement>(null)
  const [mensagem, setMensagem] = useState('')
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

  useEffect(() => {
    if (!clientId || usuario) return

    function configurarBotao() {
      const google = googleIdentity()
      if (!google || !botaoGoogle.current) return
      google.accounts.id.initialize({
        client_id: clientId,
        callback: ({ credential }) => {
          void entrarComGoogle(credential)
            .then(({ token, nome }) => {
              setMensagem('')
              aoEntrar(token, nome)
            })
            .catch(() => setMensagem('Não foi possível entrar. Confira a configuração da API e do Oracle.'))
        },
      })
      botaoGoogle.current.replaceChildren()
      google.accounts.id.renderButton(botaoGoogle.current, {
        theme: 'outline', size: 'large', text: 'signin_with',
      })
    }

    const existente = document.querySelector<HTMLScriptElement>('script[data-google-identity]')
    if (existente) {
      if (googleIdentity()) configurarBotao()
      else existente.addEventListener('load', configurarBotao, { once: true })
      return () => existente.removeEventListener('load', configurarBotao)
    }

    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.dataset.googleIdentity = 'true'
    script.addEventListener('load', configurarBotao, { once: true })
    document.head.appendChild(script)
    return () => script.removeEventListener('load', configurarBotao)
  }, [clientId, usuario, aoEntrar])

  return (
    <header className="px-4 pt-8 pb-4 text-center">
      <h1 className="text-4xl font-bold tracking-tight text-primaria-escura sm:text-5xl">
        Sudoku
      </h1>
      <p className="mt-2 text-texto-suave">
        Escolha o tamanho, a dificuldade e complete o tabuleiro.
      </p>
      <nav className="mt-4 flex justify-center gap-2" aria-label="Navegação principal">
        <NavLink
          className={({ isActive }) => `rounded-jogo px-4 py-2 font-semibold transition-colors ${isActive ? 'bg-primaria text-white' : 'border border-borda bg-superficie hover:bg-primaria-clara'}`}
          to="/"
          end
        >
          Jogar
        </NavLink>
        <NavLink
          className={({ isActive }) => `rounded-jogo px-4 py-2 font-semibold transition-colors ${isActive ? 'bg-primaria text-white' : 'border border-borda bg-superficie hover:bg-primaria-clara'}`}
          to="/ranking"
        >
          Ranking
        </NavLink>
      </nav>
      <div className="mt-4 flex flex-col items-center gap-2">
        {usuario ? (
          <div className="flex items-center gap-3 text-sm">
            <span>Jogando como {usuario}</span>
            <button
              className="rounded-jogo border border-borda px-3 py-1"
              type="button"
              onClick={() => {
                googleIdentity()?.accounts.id.disableAutoSelect()
                aoSair()
              }}
            >
              Sair
            </button>
          </div>
        ) : clientId ? (
          <div ref={botaoGoogle} aria-label="Entrar com Google" />
        ) : (
          <span className="text-sm text-texto-suave">Jogue sem login. O login Google ainda não foi configurado.</span>
        )}
        {mensagem && <p className="text-sm text-red-600" role="status">{mensagem}</p>}
        <p className="text-xs text-texto-suave">Entrar ou sair inicia um novo jogo.</p>
      </div>
    </header>
  )
}
