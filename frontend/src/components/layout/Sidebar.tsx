import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/chat', label: 'ProjectAgent (AI)', icon: '🤖' },
  { to: '/projects', label: 'Projects' },
  { to: '/engineers', label: 'Engineers' },
  { to: '/documents', label: 'Documents' },
]

export default function Sidebar() {
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="flex h-16 items-center gap-2 border-b border-slate-200 px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-slate-900 text-sm font-semibold text-white">
          S
        </div>
        <span className="text-base font-semibold text-slate-900">StratOS AI</span>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              [
                'rounded-md px-3 py-2 text-sm font-medium transition-colors flex items-center gap-2',
                isActive
                  ? 'bg-purple-600 text-white'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
              ].join(' ')
            }
          >
            {item.icon && <span>{item.icon}</span>}
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-200 px-6 py-4 text-xs text-slate-400">
        v1.0.0 &middot; MVP
      </div>
    </aside>
  )
}
