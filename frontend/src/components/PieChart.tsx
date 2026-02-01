interface PieChartItem {
  label: string
  value: number
  percentage: number
  color: string
}

interface PieChartProps {
  title: string
  items: PieChartItem[]
  centerLabel?: string
}

export default function PieChart({ title, items, centerLabel }: PieChartProps) {
  // Build conic gradient
  let gradientStops = ''
  let currentPercent = 0

  items.forEach((item, index) => {
    const startPercent = currentPercent
    const endPercent = currentPercent + item.percentage
    gradientStops += `${item.color} ${startPercent}% ${endPercent}%`
    if (index < items.length - 1) gradientStops += ', '
    currentPercent = endPercent
  })

  return (
    <div className="bg-surface-dark border border-slate-800 rounded-lg p-6">
      <h4 className="text-white font-bold mb-6">{title}</h4>
      <div className="flex flex-col items-center">
        <div
          className="size-40 rounded-full mb-6 relative"
          style={{ background: `conic-gradient(${gradientStops})` }}
        >
          <div className="absolute inset-8 bg-surface-dark rounded-full flex items-center justify-center">
            {centerLabel && (
              <span className="text-white text-xs font-bold text-center">{centerLabel}</span>
            )}
          </div>
        </div>
        <div className="w-full space-y-2">
          {items.map((item) => (
            <div key={item.label} className="flex items-center gap-2 text-xs">
              <div className="size-3 rounded-sm" style={{ backgroundColor: item.color }} />
              <span className="text-slate-300 flex-1">{item.label}</span>
              <span className="text-white font-medium">{item.percentage}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
