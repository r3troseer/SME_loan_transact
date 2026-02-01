import { ReactNode } from 'react'

interface HeaderProps {
  title: string
  subtitle?: string
  actions?: ReactNode
}

export default function Header({ title, subtitle, actions }: HeaderProps) {
  return (
    <header className="w-full border-b border-slate-800 bg-background-dark/80 backdrop-blur-sm z-10 px-8 py-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-white text-xl font-bold">{title}</h2>
          {subtitle && <p className="text-slate-400 text-xs mt-0.5">{subtitle}</p>}
        </div>
        {actions && <div className="flex gap-2">{actions}</div>}
      </div>
    </header>
  )
}
