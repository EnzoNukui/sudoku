import type { ReactNode } from 'react'

type ContentProps = {
  children: ReactNode
}

function Content({ children }: ContentProps) {
  return <main className="conteudo">{children}</main>
}

export default Content
