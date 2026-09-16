import type { ReactNode } from 'react'

type ContentProps = {
  children: ReactNode
}

export default function Content({ children }: ContentProps) {
  return <main className="mx-auto w-[calc(100%_-_2rem)] max-w-[1040px] flex-1">{children}</main>
}
