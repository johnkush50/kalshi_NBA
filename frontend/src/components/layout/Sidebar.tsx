import { NavLink } from 'react-router-dom'
import {
  Gamepad2,
  Brain,
  ArrowLeftRight,
  DollarSign,
  ShieldAlert,
  ChevronRight
} from 'lucide-react'

const navItems = [
  { path: '/', icon: Gamepad2, label: 'Games', description: 'Load & monitor games' },
  { path: '/strategies', icon: Brain, label: 'Strategies', description: 'Trading algorithms' },
  { path: '/trading', icon: ArrowLeftRight, label: 'Trading', description: 'Positions & orders' },
  { path: '/pnl', icon: DollarSign, label: 'P&L', description: 'Portfolio performance' },
  { path: '/risk', icon: ShieldAlert, label: 'Risk', description: 'Risk management' },
]

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-16 bottom-0 w-64 bg-terminal-surface/80 backdrop-blur-sm border-r border-terminal-border overflow-y-auto">
      <nav className="p-4 space-y-2">
        <div className="px-3 py-2 mb-4">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">Navigation</span>
        </div>

        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                isActive
                  ? 'bg-neon-cyan/10 border border-neon-cyan/30 shadow-neon-cyan'
                  : 'border border-transparent hover:bg-terminal-hover hover:border-terminal-border'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <div className={`p-2 rounded-md ${
                  isActive ? 'bg-neon-cyan/20' : 'bg-terminal-bg group-hover:bg-terminal-border'
                }`}>
                  <item.icon className={`w-5 h-5 ${
                    isActive ? 'text-neon-cyan' : 'text-slate-400 group-hover:text-slate-300'
                  }`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className={`font-medium text-sm ${
                    isActive ? 'text-neon-cyan' : 'text-slate-300 group-hover:text-white'
                  }`}>
                    {item.label}
                  </div>
                  <div className="text-[11px] text-slate-500 truncate">
                    {item.description}
                  </div>
                </div>
                <ChevronRight className={`w-4 h-4 transition-transform ${
                  isActive ? 'text-neon-cyan translate-x-0.5' : 'text-slate-600 group-hover:text-slate-400'
                }`} />
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-terminal-border bg-terminal-surface/50">
        <div className="text-center">
          <div className="text-[10px] font-mono text-slate-600 uppercase tracking-wider">Paper Trading Mode</div>
          <div className="text-xs font-mono text-neon-yellow mt-1">No Real Money</div>
        </div>
      </div>
    </aside>
  )
}
