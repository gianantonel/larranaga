import { NavLink } from 'react-router-dom'
import { useState } from 'react'
import {
  LayoutDashboard, Users, UserCheck, ClipboardList,
  ReceiptText, BarChart3, Scale, LogOut, ChevronRight, FileSearch, Wrench, Wallet,
  PiggyBank, Calculator, Briefcase
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import clsx from 'clsx'

const VISTAS_ITEMS = [
  { to: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/clientes',      icon: Users,           label: 'Clientes' },
  { to: '/colaboradores', icon: UserCheck,       label: 'Colaboradores' },
  { to: '/tareas',        icon: ClipboardList,   label: 'Tareas' },
]

const ACCIONES_ITEMS = [
  { to: '/cuentas-corrientes', icon: Wallet,      label: 'Cuentas Corrientes', req: 'R-07' },
  { to: '/iva',                icon: BarChart3,    label: 'Balance IVA', req: 'R-05, R-06, R-16' },
  { to: '/facturas',           icon: ReceiptText,  label: 'Facturación', req: 'R-03, R-04' },
  { to: '/retenciones',        icon: FileSearch,   label: 'Retenciones', req: 'R-05+' },
  { to: '/honorarios',         icon: Calculator,   label: 'Honorarios', req: 'R-03, R-04' },
  { to: '/profesionales',      icon: Briefcase,    label: 'Profesionales', req: 'ADM' },
  { icon: PiggyBank, label: 'Tesorería', req: 'R-08, R-14', disabled: true },
]

const OTRAS_ACCIONES_ITEMS = [
  { to: '/herramientas', icon: Wrench, label: 'Herramientas', req: 'R-01, R-02, R-10' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const [openGroups, setOpenGroups] = useState({ vistas: true, acciones: true, otras: true })

  const toggleGroup = (key) => {
    setOpenGroups(prev => ({ ...prev, [key]: !prev[key] }))
  }

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
      <nav className="flex-1 px-3 py-4 space-y-4 overflow-y-auto">

        {/* VISTAS Group */}
        <div>
          <button
            onClick={() => toggleGroup('vistas')}
            className="nav-group-header w-full gap-2"
          >
            <span>Vistas</span>
            <ChevronRight
              size={14}
              className={clsx('transition-transform duration-200', openGroups.vistas && 'rotate-90')}
            />
          </button>
          {openGroups.vistas && (
            <div className="space-y-1 mt-2">
              {VISTAS_ITEMS.map(({ to, icon: Icon, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/dashboard'}
                  className={({ isActive }) =>
                    clsx(isActive ? 'nav-link-child-active' : 'nav-link-child', 'w-full')
                  }
                >
                  <Icon size={18} />
                  <span>{label}</span>
                </NavLink>
              ))}
            </div>
          )}
        </div>

        {/* ACCIONES Group */}
        <div>
          <button
            onClick={() => toggleGroup('acciones')}
            className="nav-group-header w-full gap-2"
          >
            <span>Acciones</span>
            <ChevronRight
              size={14}
              className={clsx('transition-transform duration-200', openGroups.acciones && 'rotate-90')}
            />
          </button>
          {openGroups.acciones && (
            <div className="space-y-1 mt-2">
              {ACCIONES_ITEMS.map((item, idx) => (
                <div key={item.label || idx}>
                  {item.disabled ? (
                    // Disabled item
                    <span className="nav-link-child opacity-50 cursor-not-allowed">
                      <item.icon size={18} />
                      <span className="flex-1">{item.label}</span>
                      <span className="badge-gray text-xs px-1.5 py-0.5">Próx.</span>
                    </span>
                  ) : (
                    // Active navlink
                    <NavLink
                      to={item.to}
                      end={item.to === '/dashboard'}
                      className={({ isActive }) =>
                        clsx(isActive ? 'nav-link-child-active' : 'nav-link-child', 'w-full')
                      }
                    >
                      <item.icon size={18} />
                      <span>{item.label}</span>
                    </NavLink>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* OTRAS ACCIONES Group */}
        <div>
          <button
            onClick={() => toggleGroup('otras')}
            className="nav-group-header w-full gap-2"
          >
            <span>Otras Acciones</span>
            <ChevronRight
              size={14}
              className={clsx('transition-transform duration-200', openGroups.otras && 'rotate-90')}
            />
          </button>
          {openGroups.otras && (
            <div className="space-y-1 mt-2">
              {OTRAS_ACCIONES_ITEMS.map((item, idx) => (
                <NavLink
                  key={item.to || idx}
                  to={item.to}
                  className={({ isActive }) =>
                    clsx(isActive ? 'nav-link-child-active' : 'nav-link-child', 'w-full')
                  }
                >
                  <item.icon size={18} />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          )}
        </div>

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
