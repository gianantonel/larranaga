import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Users, UserCheck, ClipboardList,
  ReceiptText, BarChart3, LogOut, FileSearch, Wrench, Wallet, X,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import Logo from '../UI/Logo'
import ThemeToggle from '../UI/ThemeToggle'
import clsx from 'clsx'

const VISTAS = [
  { to: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard',     end: true },
  { to: '/clientes',      icon: Users,           label: 'Clientes' },
  { to: '/colaboradores', icon: UserCheck,       label: 'Colaboradores' },
  { to: '/tareas',        icon: ClipboardList,   label: 'Tareas' },
]

const ACCIONES = [
  { to: '/cuentas-corrientes', icon: Wallet,      label: 'Cuentas Corrientes' },
  { to: '/iva',                icon: BarChart3,   label: 'Balance IVA' },
  { to: '/facturas',           icon: ReceiptText, label: 'Facturación' },
  { to: '/retenciones',        icon: FileSearch,  label: 'Retenciones' },
  { to: '/herramientas',       icon: Wrench,      label: 'Adaptador IVA' },
]

export default function Sidebar({ open = false, onClose = () => {} }) {
  const { user, logout } = useAuth()

  return (
    <aside
      className={clsx(
        'fixed inset-y-0 left-0 z-40 w-72 max-w-[85vw] flex flex-col',
        'transform transition-transform duration-300 ease-out',
        open ? 'translate-x-0' : '-translate-x-full',
        'lg:static lg:translate-x-0 lg:w-64 lg:max-w-none lg:z-auto'
      )}
      style={{ background: 'var(--surface)', borderRight: '1px solid var(--border)' }}
    >
      <div className="px-6 py-5 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border)' }}>
        <Logo size="md" />
        <button
          onClick={onClose}
          className="lg:hidden p-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5"
          style={{ color: 'var(--text-muted)' }}
          aria-label="Cerrar menú"
        >
          <X size={18} />
        </button>
      </div>

      <nav className="flex-1 px-3 py-4 overflow-y-auto">
        <p className="nav-section">Vistas</p>
        <div className="space-y-1">
          {VISTAS.map(({ to, icon: Icon, label, end }) => (
            <NavLink key={to} to={to} end={end} onClick={onClose}
              className={({ isActive }) => clsx(isActive ? 'nav-link-active' : 'nav-link')}>
              <Icon size={18} className="shrink-0" />
              <span className="truncate">{label}</span>
            </NavLink>
          ))}
        </div>

        <p className="nav-section">Acciones</p>
        <div className="space-y-1">
          {ACCIONES.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} onClick={onClose}
              className={({ isActive }) => clsx(isActive ? 'nav-link-active' : 'nav-link')}>
              <Icon size={18} className="shrink-0" />
              <span className="truncate">{label}</span>
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="px-3 py-4" style={{ borderTop: '1px solid var(--border)' }}>
        <div className="flex items-center gap-3 px-3 py-2 rounded-2xl" style={{ background: 'var(--surface-2)' }}>
          <div className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold shrink-0"
            style={{ background: 'var(--brand-soft)', color: 'var(--brand)' }}>
            {user?.avatar_initials || user?.name?.slice(0, 2).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold truncate" style={{ color: 'var(--text)' }}>{user?.name}</p>
            <p className="text-xs truncate" style={{ color: 'var(--text-muted)' }}>{user?.email}</p>
          </div>
          <ThemeToggle />
          <button
            onClick={logout}
            className="p-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5 shrink-0"
            style={{ color: 'var(--text-muted)' }}
            title="Cerrar sesión"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  )
}
