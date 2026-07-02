import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Users, UserCheck, ClipboardList,
  ReceiptText, BarChart3, LogOut, FileSearch, Wrench, Wallet, X,
  Scale, Calculator, Briefcase, DollarSign, CalendarCheck,
  BookOpen, Banknote, ArrowDownToLine, TrendingUp, Percent,
  Settings, Eye, EyeOff,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useFeatureFlags } from '../../context/FeatureFlagsContext'
import Logo from '../UI/Logo'
import ThemeToggle from '../UI/ThemeToggle'
import RequirementBadge from '../UI/RequirementBadge'
import FeatureGate from '../FeatureGate'
import clsx from 'clsx'

const VISTAS = [
  { to: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard',     end: true },
  { to: '/clientes',      icon: Users,           label: 'Clientes' },
  { to: '/colaboradores', icon: UserCheck,       label: 'Colaboradores' },
  { to: '/tareas',        icon: ClipboardList,   label: 'Tareas' },
]

const ACCIONES = [
  { to: '/cuentas-corrientes',     icon: Wallet,          label: 'Cuentas Corrientes',   req: 'R-07' },
  { to: '/iva',                    icon: BarChart3,       label: 'Balance IVA',          req: 'R-06' },
  { to: '/posicion-iva',           icon: Scale,           label: 'Posición IVA',         req: 'R-06' },
  { to: '/facturas',               icon: ReceiptText,     label: 'Facturación' },
  { to: '/retenciones',            icon: FileSearch,      label: 'Retenciones',          req: 'R-05' },
  { to: '/maestro-proveedores',    icon: BookOpen,        label: 'Maestro Proveedores',  req: 'R-09' },
  { to: '/honorarios',             icon: Calculator,      label: 'Honorarios',           req: 'R-03' },
  { to: '/actualizar-honorarios',  icon: Percent,         label: 'Actualizar Honorarios',req: 'R-13' },
  { to: '/liquidaciones',          icon: CalendarCheck,   label: 'Liquidaciones',        req: 'R-04' },
  { to: '/cobros',                 icon: DollarSign,      label: 'Registrar Cobro',      req: 'R-08' },
  { to: '/retiros',                icon: ArrowDownToLine, label: 'Retiros Socios',       req: 'R-12' },
  { to: '/flujo-fondos',           icon: TrendingUp,      label: 'Flujo de Fondos',      req: 'R-11' },
  { to: '/conciliacion-bancaria',  icon: Banknote,        label: 'Conciliación Bancaria',req: 'R-15' },
  { to: '/herramientas',           icon: Wrench,          label: 'Adaptador IVA',        req: ['R-01', 'R-02'] },
]

export default function Sidebar({ open = false, onClose = () => {} }) {
  const { user, logout, isAdmin } = useAuth()
  const { flagsByCodigo, verificationMode, toggleVerificationMode } = useFeatureFlags()

  const NavItem = ({ to, Icon, label, req, end }) => (
    <NavLink to={to} end={end} onClick={onClose}
      className={({ isActive }) => clsx(isActive ? 'nav-link-active' : 'nav-link')}>
      <Icon size={16} strokeWidth={1.75} className="shrink-0" />
      <span className="truncate flex-1">{label}</span>
      {isAdmin && verificationMode && req && (
        <RequirementBadge
          codigo={Array.isArray(req) ? req[0] : req}
          flag={flagsByCodigo[Array.isArray(req) ? req[0] : req]}
        />
      )}
    </NavLink>
  )

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
      <div className="px-6 py-7 flex items-center justify-between">
        <Logo size="md" />
        <button
          onClick={onClose}
          className="lg:hidden p-1.5 rounded-full"
          style={{ color: 'var(--text-subtle)' }}
          aria-label="Cerrar menú"
        >
          <X size={18} strokeWidth={1.75} />
        </button>
      </div>

      <nav className="flex-1 px-3 pb-4 overflow-y-auto">
        <p className="nav-section">Vistas</p>
        <div className="space-y-0.5">
          {VISTAS.map(({ to, icon: Icon, label, end }) => (
            <NavItem key={to} to={to} Icon={Icon} label={label} end={end} />
          ))}
        </div>

        <p className="nav-section">Acciones</p>
        <div className="space-y-0.5">
          {ACCIONES.map(({ to, icon: Icon, label, req }) => {
            const item = <NavItem to={to} Icon={Icon} label={label} req={req} />
            return req
              ? <FeatureGate key={to} codigo={req}>{item}</FeatureGate>
              : <span key={to}>{item}</span>
          })}
        </div>

        {isAdmin && (
          <>
            <p className="nav-section">Administración</p>
            <div className="space-y-0.5">
              <NavLink to="/gestion-requisitos" onClick={onClose}
                className={({ isActive }) => clsx(isActive ? 'nav-link-active' : 'nav-link')}>
                <Settings size={16} strokeWidth={1.75} className="shrink-0" />
                <span className="truncate">Gestión de Requisitos</span>
              </NavLink>
              <button
                onClick={toggleVerificationMode}
                className="nav-link w-full text-left"
                style={{ cursor: 'pointer' }}
              >
                {verificationMode
                  ? <Eye size={16} strokeWidth={1.75} className="shrink-0" />
                  : <EyeOff size={16} strokeWidth={1.75} className="shrink-0" />}
                <span className="truncate">Modo verificación {verificationMode ? 'ON' : 'OFF'}</span>
              </button>
            </div>
          </>
        )}
      </nav>

      <div className="px-3 py-4 divider">
        <div
          className="flex items-center gap-3 px-3 py-2.5 rounded-2xl"
          style={{ background: 'var(--surface-2)' }}
        >
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-semibold shrink-0"
            style={{ background: 'var(--text)', color: 'var(--bg)' }}
          >
            {user?.avatar_initials || user?.name?.slice(0, 2).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[12px] font-semibold truncate" style={{ color: 'var(--text)' }}>
              {user?.name}
            </p>
            <p className="text-[10px] truncate" style={{ color: 'var(--text-subtle)' }}>
              {user?.email}
            </p>
          </div>
          <ThemeToggle />
          <button
            onClick={logout}
            className="p-1.5 rounded-full shrink-0"
            style={{ color: 'var(--text-subtle)' }}
            title="Cerrar sesión"
          >
            <LogOut size={14} strokeWidth={1.75} />
          </button>
        </div>
      </div>
    </aside>
  )
}
