import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Users, UserCheck, ClipboardList,
  ReceiptText, BarChart3, Scale, LogOut, FileSearch, Wrench, Wallet, X,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/clientes',      icon: Users,           label: 'Clientes' },
  { to: '/colaboradores', icon: UserCheck,       label: 'Colaboradores' },
  { to: '/tareas',        icon: ClipboardList,   label: 'Tareas' },
  { to: '/cuentas-corrientes', icon: Wallet,   label: 'Cuentas Corrientes' },
  { to: '/iva',           icon: BarChart3,       label: 'Balance IVA' },
  { to: '/facturas',      icon: ReceiptText,     label: 'Facturación' },
  { to: '/retenciones',   icon: FileSearch,      label: 'Retenciones' },
  { to: '/herramientas',  icon: Wrench,          label: 'Herramientas IVA' },
]

export default function Sidebar({ open = false, onClose = () => {} }) {
  const { user, logout, isAdmin } = useAuth()

  return (
    <aside
      className={clsx(
        'fixed inset-y-0 left-0 z-40 w-72 max-w-[85vw] bg-[#0f172a] border-r border-gray-700/40 flex flex-col',
        'transform transition-transform duration-300 ease-out',
        open ? 'translate-x-0' : '-translate-x-full',
        'lg:static lg:translate-x-0 lg:w-64 lg:max-w-none lg:z-auto'
      )}
    >
      {/* Logo + close (mobile) */}
      <div className="px-6 py-5 border-b border-gray-700/40 flex items-center justify-between">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-xl bg-violet-600 flex items-center justify-center shrink-0">
            <Scale size={20} className="text-white" />
          </div>
          <div className="min-w-0">
            <h1 className="text-lg font-bold text-white leading-tight truncate">Larrañaga</h1>
            <p className="text-xs text-gray-400 truncate">Estudio Contable y Legal</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="lg:hidden p-1.5 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
          aria-label="Cerrar menú"
        >
          <X size={20} />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/dashboard'}
            onClick={onClose}
            className={({ isActive }) =>
              clsx(isActive ? 'nav-link-active' : 'nav-link', 'w-full')
            }
          >
            <Icon size={20} />
            <span className="truncate">{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User */}
      <div className="px-3 pb-4 border-t border-gray-700/40 pt-4">
        <div className="flex items-center gap-3 px-3 py-2 rounded-xl bg-white/3">
          <div className="w-9 h-9 rounded-full bg-violet-600/30 border border-violet-500/30 flex items-center justify-center text-sm font-bold text-violet-300 shrink-0">
            {user?.avatar_initials || user?.name?.slice(0, 2).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-white truncate">{user?.name}</p>
            <p className="text-xs text-gray-400 truncate">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="text-gray-500 hover:text-rose-400 transition-colors p-1 shrink-0"
            title="Cerrar sesión"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  )
}
