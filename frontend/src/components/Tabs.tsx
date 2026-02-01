import { clsx } from 'clsx'

interface Tab {
  id: string
  label: string
  icon?: string
}

interface TabsProps {
  tabs: Tab[]
  activeTab: string
  onChange: (tabId: string) => void
}

export default function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="flex gap-1 bg-slate-800/50 p-1 rounded-lg">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all',
            activeTab === tab.id
              ? 'bg-primary text-white'
              : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
          )}
        >
          {tab.icon && <span className="material-symbols-outlined text-lg">{tab.icon}</span>}
          {tab.label}
        </button>
      ))}
    </div>
  )
}
