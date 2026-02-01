import { NavLink } from 'react-router-dom'
import { useLenderStore, LENDERS } from '../stores/lenderStore'
import { useCreditsStore } from '../stores/creditsStore'

const navItems = [
  { path: '/portfolio', icon: 'dashboard', label: 'Portfolio Overview' },
  { path: '/company', icon: 'business', label: 'Company Analysis' },
  { path: '/marketplace', icon: 'storefront', label: 'Marketplace' },
  { path: '/swaps', icon: 'swap_horiz', label: 'Loan Swaps' },
  { path: '/market', icon: 'insights', label: 'Market Intelligence' },
  { path: '/simulator', icon: 'calculate', label: 'Transaction Simulator' },
]

export default function Sidebar() {
  const { currentLender, setCurrentLender } = useLenderStore()
  const { balance } = useCreditsStore()

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col bg-background-dark border-r border-slate-800 z-20 overflow-y-auto custom-scrollbar">
      <div className="p-6">
        {/* Logo */}
        <div className="flex items-center gap-2 mb-8">
          <div className="size-8 rounded bg-primary flex items-center justify-center">
            <span className="material-symbols-outlined text-white text-xl">account_balance</span>
          </div>
          <h1 className="text-white text-lg font-bold">GFA Exchange</h1>
        </div>

        {/* Credit Balance */}
        <div className="mb-8 p-3 bg-slate-800/50 rounded-lg border border-slate-700">
          <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Engine Balance</p>
          <div className="flex items-center justify-between">
            <span className="text-white font-mono text-lg font-bold">{balance} Credits</span>
            <span className="material-symbols-outlined text-accent-teal text-sm">bolt</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-1">
          <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-2 px-2">Navigation</p>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${
                  isActive
                    ? 'bg-slate-800 text-white font-medium'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`
              }
            >
              <span className="material-symbols-outlined text-xl">{item.icon}</span>
              <span className="text-sm">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Lender Selector */}
        <div className="mt-8">
          <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-4 px-2">Current Lender</p>
          <div className="px-2">
            <select
              value={currentLender?.id || ''}
              onChange={(e) => {
                const lender = LENDERS.find((l) => l.id === Number(e.target.value))
                if (lender) setCurrentLender(lender)
              }}
              className="w-full bg-slate-900 border-slate-700 text-xs text-white rounded px-2 py-2 focus:ring-primary focus:border-primary"
            >
              {LENDERS.map((lender) => (
                <option key={lender.id} value={lender.id}>
                  {lender.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* User Info */}
      <div className="mt-auto p-6 border-t border-slate-800">
        <div className="flex items-center gap-3">
          <div className="size-8 rounded-full bg-slate-700 flex items-center justify-center">
            <span className="material-symbols-outlined text-slate-400 text-sm">person</span>
          </div>
          <div className="flex-1 overflow-hidden">
            <p className="text-xs font-medium text-white truncate">{currentLender?.name || 'Select Lender'}</p>
            <p className="text-[10px] text-slate-500">Lender View</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
