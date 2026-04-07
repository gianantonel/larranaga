import { useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Users, UserCheck, ClipboardList,
  BarChart2, ReceiptText, ChevronRight, Shield, Zap, TrendingUp
} from 'lucide-react'

const SECTIONS = [
  {
    id: 'dashboard',
    title: 'Dashboard',
    icon: LayoutDashboard,
    color: 'violet',
    description: 'Visión 360° de tu estudio en tiempo real. KPIs clave, gráficos de actividad mensual, estado de tareas por colaborador y evolución de IVA — todo en una pantalla.',
    img: '/screenshots/ss_dashboard.png',
  },
  {
    id: 'clientes',
    title: 'Clientes',
    icon: Users,
    color: 'sky',
    description: 'Gestión completa de tu cartera de clientes. CUIT, condición fiscal, credenciales ARCA encriptadas, colaboradores asignados y acceso a todo el historial fiscal por cliente.',
    img: '/screenshots/ss_clientes.png',
  },
  {
    id: 'colaboradores',
    title: 'Colaboradores',
    icon: UserCheck,
    color: 'emerald',
    description: 'Administrá tu equipo con métricas de productividad por colaborador. Visualizá carga de trabajo, tareas completadas vs. pendientes y distribución por estado en tiempo real.',
    img: '/screenshots/ss_colaboradores.png',
  },
  {
    id: 'tareas',
    title: 'Tareas',
    icon: ClipboardList,
    color: 'amber',
    description: 'Sistema completo de gestión de tareas con subtareas, filtros por estado, tipo y colaborador. Detectá cuellos de botella, evitá burn-outs y mantené todo bajo control.',
    img: '/screenshots/ss_tareas.png',
  },
  {
    id: 'iva',
    title: 'Balance IVA',
    icon: BarChart2,
    color: 'rose',
    description: 'Seguimiento mensual del IVA de cada cliente. Débito, crédito, saldo, estado de presentación y número de VEP. Marcá las DDJJ como presentadas directamente desde la plataforma.',
    img: '/screenshots/ss_iva.png',
  },
  {
    id: 'facturas',
    title: 'Facturación',
    icon: ReceiptText,
    color: 'cyan',
    description: 'Registro y emisión de comprobantes electrónicos ARCA. Facturas A, B, C con auto-numeración por punto de venta, CAE, gráfico mensual y filtros por cliente y tipo.',
    img: '/screenshots/ss_facturas.png',
  },
]

const COLOR_MAP = {
  violet: { badge: 'bg-violet-600/20 text-violet-300 border-violet-500/30', dot: 'bg-violet-500', line: 'border-violet-500/40' },
  sky:    { badge: 'bg-sky-600/20 text-sky-300 border-sky-500/30',         dot: 'bg-sky-500',    line: 'border-sky-500/40' },
  emerald:{ badge: 'bg-emerald-600/20 text-emerald-300 border-emerald-500/30', dot: 'bg-emerald-500', line: 'border-emerald-500/40' },
  amber:  { badge: 'bg-amber-600/20 text-amber-300 border-amber-500/30',   dot: 'bg-amber-500',  line: 'border-amber-500/40' },
  rose:   { badge: 'bg-rose-600/20 text-rose-300 border-rose-500/30',      dot: 'bg-rose-500',   line: 'border-rose-500/40' },
  cyan:   { badge: 'bg-cyan-600/20 text-cyan-300 border-cyan-500/30',      dot: 'bg-cyan-500',   line: 'border-cyan-500/40' },
}

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[#070b14] text-white">

      {/* ── Navbar ──────────────────────────────────────────────── */}
      <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4
                         bg-[#070b14]/80 backdrop-blur-md border-b border-white/5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center font-bold text-sm">L</div>
          <span className="font-semibold text-white tracking-tight">Larrañaga</span>
          <span className="text-gray-500 text-sm hidden sm:inline">· Estudio Contable &amp; Legal</span>
        </div>
        <button
          onClick={() => navigate('/login')}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500
                     text-white text-sm font-medium transition-colors shadow-lg shadow-violet-900/40">
          Iniciar sesión <ChevronRight size={15} />
        </button>
      </header>

      {/* ── Hero ────────────────────────────────────────────────── */}
      <section className="pt-40 pb-24 px-6 text-center max-w-4xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-600/15
                        border border-violet-500/25 text-violet-300 text-xs font-medium mb-6">
          <Zap size={12} /> Data Driven Management
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight tracking-tight mb-6
                       bg-gradient-to-br from-white via-gray-100 to-gray-400 bg-clip-text text-transparent">
          Gestioná tu estudio contable<br className="hidden sm:block" />
          <span className="text-violet-400"> basándote en datos</span>
        </h1>
        <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Data Driven Management es la nueva forma de gestionar tus clientes, equipos de colaboradores,
          tareas, prioridades y pendientes — encontrá problemas, detectá cuellos de botella,
          evitá burn-outs y tomá decisiones con información real.
        </p>
        <div className="flex flex-wrap gap-4 justify-center">
          <button
            onClick={() => navigate('/login')}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-violet-600 hover:bg-violet-500
                       text-white font-semibold transition-colors shadow-xl shadow-violet-900/50 text-base">
            Acceder a la plataforma <ChevronRight size={18} />
          </button>
        </div>

        {/* Feature pills */}
        <div className="flex flex-wrap gap-3 justify-center mt-10">
          {[
            { icon: Shield, text: 'Credenciales ARCA encriptadas' },
            { icon: TrendingUp, text: 'Gráficos en tiempo real' },
            { icon: Zap, text: 'Facturación electrónica ARCA' },
          ].map(({ icon: Icon, text }) => (
            <span key={text} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full
                                        bg-white/5 border border-white/10 text-gray-400 text-sm">
              <Icon size={13} className="text-violet-400" /> {text}
            </span>
          ))}
        </div>
      </section>

      {/* ── Module sections ─────────────────────────────────────── */}
      <div className="max-w-5xl mx-auto px-6 pb-24 space-y-24">
        {SECTIONS.map((section) => {
          const Icon = section.icon
          const colors = COLOR_MAP[section.color]
          return (
            <section key={section.id} id={section.id}>
              {/* Section header */}
              <div className="flex items-center gap-3 mb-6">
                <div className={`w-10 h-10 rounded-xl border flex items-center justify-center ${colors.badge}`}>
                  <Icon size={20} />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white">{section.title}</h2>
                  <p className="text-gray-400 text-sm mt-0.5 max-w-2xl">{section.description}</p>
                </div>
              </div>

              {/* Screenshot — full width, scrollable vertically */}
              <div className={`rounded-2xl border ${colors.line} overflow-hidden shadow-2xl`}
                   style={{ background: '#0a0f1e' }}>
                <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-white/5 bg-white/[0.02]">
                  <div className="w-2.5 h-2.5 rounded-full bg-rose-500/70" />
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-500/70" />
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/70" />
                  <span className="ml-2 text-xs text-gray-600 font-mono">localhost:5173/{section.id}</span>
                </div>
                <div className="overflow-y-auto max-h-[70vh]">
                  <img
                    src={section.img}
                    alt={`Módulo ${section.title}`}
                    className="w-full block"
                    loading="lazy"
                  />
                </div>
              </div>
            </section>
          )
        })}
      </div>

      {/* ── Footer CTA ──────────────────────────────────────────── */}
      <section className="border-t border-white/5 bg-gradient-to-b from-transparent to-violet-950/20 py-20 px-6 text-center">
        <h2 className="text-3xl font-bold text-white mb-3">¿Listo para empezar?</h2>
        <p className="text-gray-400 mb-8 max-w-md mx-auto">
          Accedé a la plataforma y gestioná tu estudio con información en tiempo real.
        </p>
        <button
          onClick={() => navigate('/login')}
          className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-violet-600 hover:bg-violet-500
                     text-white font-semibold text-base transition-colors shadow-xl shadow-violet-900/50">
          Iniciar sesión <ChevronRight size={18} />
        </button>
      </section>

      <footer className="border-t border-white/5 py-6 text-center text-gray-600 text-sm">
        © {new Date().getFullYear()} Larrañaga Estudio Contable y Legal · Plataforma interna
      </footer>
    </div>
  )
}
