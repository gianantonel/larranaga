import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Users, UserCheck, ClipboardList,
  ReceiptText, BarChart3, Scale, LogOut, ChevronRight, FileSearch
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/clientes',      icon: Users,           label: 'Clientes' },
  { to: '/colaboradores', icon: UserCheck,       label: 'Colaboradores' },
  { to: '/tareas',        icon: ClipboardList,   label: 'Tareas' },
  { to: '/iva',           icon: BarChart3,       label: 'Balance IVA' },
  { to: '/facturas',      icon: ReceiptText,     label: 'Facturación' },
  { to: '/retenciones',   icon: FileSearch,      label: 'Retenciones' },
]

export default function Sidebar() {
  const { user, logout, isAdmin } = useAuth()

  return (
    <aside className="w-64 min-h-screen bg-[#0f172a] border-r border-gray-700/40 flex flex-col">
      {/* Logo */}
      <div className="px-6 py-6 border-b border-gray-700/40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-violet-600 flex items-center justify-center">
            <Scale size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white leading-tight">Larrañaga</h1>
            <p className="text-xs text-gray-400">Estudio Contable y Legal</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/dashboard'}
            className={({ isActive }) =>
              clsx(isActive ? 'nav-link-active' : 'nav-link', 'w-full')
            }
          >
            <Icon size={20} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User */}
      <div className="px-3 pb-4 border-t border-gray-700/40 pt-4">
        <div className="flex items-center gap-3 px-3 py-2 rounded-xl bg-white/3">
          <div className="w-9 h-9 rounded-full bg-violet-600/30 border border-violet-500/30 flex items-center justify-center text-sm font-bold text-violet-300">
            {user?.avatar_initials || user?.name?.slice(0, 2).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-white truncate">{user?.name}</p>
            <p className="text-xs text-gray-400 truncate">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="text-gray-500 hover:text-rose-400 transition-colors p-1"
            title="Cerrar sesión"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  )
}
