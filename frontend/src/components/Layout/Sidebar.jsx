import { NavLink } from 'react-router-dom'
import { 
  Gamepad2, 
  Brain, 
  ShoppingCart, 
  DollarSign, 
  Shield
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/', icon: Gamepad2, label: 'Games' },
  { to: '/strategies', icon: Brain, label: 'Strategies' },
  { to: '/trading', icon: ShoppingCart, label: 'Trading' },
  { to: '/pnl', icon: DollarSign, label: 'P&L' },
  { to: '/risk', icon: Shield, label: 'Risk' },
]

export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-800 border-r border-gray-700 min-h-screen">
      <nav className="p-4">
        <ul className="space-y-2">
          {navItems.map(({ to, icon: Icon, label }) => (
            <li key={to}>
              <NavLink
                to={to}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700'
                  )
                }
              >
                <Icon className="w-5 h-5" />
                <span>{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  )
}
