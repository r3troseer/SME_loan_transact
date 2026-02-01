interface BarChartItem {
  label: string
  value: number
  color?: string
}

interface BarChartProps {
  title: string
  items: BarChartItem[]
  icon?: string
  maxValue?: number
}

const defaultColors = [
  'bg-primary',
  'bg-accent-teal',
  'bg-indigo-400',
  'bg-sky-400',
  'bg-slate-600',
  'bg-purple-400',
  'bg-pink-400',
]

export default function BarChart({ title, items, icon, maxValue }: BarChartProps) {
  const max = maxValue || Math.max(...items.map((i) => i.value))

  return (
    <div className="bg-surface-dark border border-slate-800 rounded-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h4 className="text-white font-bold">{title}</h4>
        {icon && <span className="material-symbols-outlined text-slate-500">{icon}</span>}
      </div>
      <div className="space-y-4">
        {items.map((item, index) => (
          <div key={item.label} className="space-y-1.5">
            <div className="flex justify-between text-xs text-slate-300">
              <span>{item.label}</span>
              <span>{item.value}</span>
            </div>
            <div className="w-full bg-slate-800 h-2 rounded-full">
              <div
                className={`h-full rounded-full ${item.color || defaultColors[index % defaultColors.length]}`}
                style={{ width: `${(item.value / max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
