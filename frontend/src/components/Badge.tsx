import { clsx } from 'clsx'
import { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'neutral'
  size?: 'sm' | 'md'
}

export default function Badge({ children, variant = 'neutral', size = 'sm' }: BadgeProps) {
  const variantStyles = {
    success: 'bg-accent-teal/20 text-accent-teal border-accent-teal/30',
    warning: 'bg-orange-400/20 text-orange-400 border-orange-400/30',
    danger: 'bg-red-400/20 text-red-400 border-red-400/30',
    info: 'bg-primary/20 text-primary border-primary/30',
    neutral: 'bg-slate-700/50 text-slate-300 border-slate-600',
  }

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-xs',
  }

  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium rounded border',
        variantStyles[variant],
        sizeStyles[size]
      )}
    >
      {children}
    </span>
  )
}
