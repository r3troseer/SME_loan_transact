interface MetricCardProps {
  label: string
  value: string | number
  suffix?: string
  badge?: string
  badgeColor?: 'teal' | 'orange' | 'red' | 'blue'
  icon?: string
}

export default function MetricCard({ label, value, suffix, badge, badgeColor = 'teal', icon }: MetricCardProps) {
  const badgeColors = {
    teal: 'text-accent-teal',
    orange: 'text-orange-400',
    red: 'text-red-400',
    blue: 'text-blue-400',
  }

  return (
    <div className="bg-surface-dark border border-slate-800 rounded-lg p-5">
      <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-2">{label}</p>
      <div className="flex items-baseline gap-2">
        <h3 className="text-white text-3xl font-bold">{value}</h3>
        {suffix && <span className="text-xs text-slate-500 font-medium">{suffix}</span>}
        {badge && <span className={`text-xs font-medium ${badgeColors[badgeColor]}`}>{badge}</span>}
        {icon && (
          <span className="material-symbols-outlined text-slate-500 text-sm" title="Anonymized">
            {icon}
          </span>
        )}
      </div>
    </div>
  )
}
