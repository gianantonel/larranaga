import { useEffect, useState } from 'react'
import {
  Users, UserCheck, ClipboardList, CheckCircle,
  AlertCircle, Clock, BarChart3, TrendingUp, Activity
} from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import {
  getDashboardStats, getCollaboratorStats, getMonthlyActivity, getTasksByType
} from '../utils/api'
import StatCard from '../components/UI/StatCard'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import PageHeader from '../components/UI/PageHeader'
import { formatCurrency, formatPeriod, taskTypeConfig, CHART_COLORS } from '../utils/helpers'

const STATUS_COLORS = {
  terminada: '#10b981',
  en_curso:  '#0ea5e9',
  pendiente: '#f59e0b',
  bloqueada: '#f43f5e',
  postergada:'#f97316',
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [collabStats, setCollabStats] = useState([])
  const [monthlyData, setMonthlyData] = useState([])
  const [tasksByType, setTasksByType] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getDashboardStats(),
      getCollaboratorStats(),
      getMonthlyActivity(),
      getTasksByType(),
    ]).then(([s, cs, ma, tt]) => {
      setStats(s.data)
      setCollabStats(cs.data)
      setMonthlyData(ma.data.slice(-12))

      // Build pie data from tasks by type
      const pie = Object.entries(tt.data).map(([type, statusMap]) => ({
        name: taskTypeConfig[type]?.label || type,
        value: Object.values(statusMap).reduce((a, b) => a + b, 0),
        color: taskTypeConfig[type]?.color || '#9ca3af',
      }))
      setTasksByType(pie)
    }).catch(err => {
      console.error('Dashboard load error:', err)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner text="Cargando dashboard..." />

  // Collaborator stacked bar data
  const collabBarData = collabStats.map(c => ({
    name: c.collaborator_name.split(' ')[0],
    Terminadas: c.completed,
    'En Curso': c.in_progress,
    Pendientes: c.pending,
    Bloqueadas: c.blocked,
  }))

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    return (
      <div className="bg-[#1f2937] border border-gray-600 rounded-lg p-3 shadow-xl">
        <p className="text-gray-300 font-medium mb-2">{formatPeriod(label) || label}</p>
        {payload.map(p => (
          <p key={p.name} style={{ color: p.color }} className="text-sm">
            {p.name}: {p.name.includes('Monto') ? formatCurrency(p.value) : p.value}
          </p>
        ))}
      </div>
    )
  }

  return (
    <div className="p-6 space-y-8">
      <PageHeader
        title="Dashboard"
        subtitle="Resumen general del estudio Larrañaga"
      />

      {/* Sección: Cartera y Actividad */}
      <div className="space-y-3">
        <p className="section-title">Cartera y Actividad</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Clientes activos" value={stats.active_clients} subtitle={`${stats.total_clients} total`} icon={Users} color="cyan" />
          <StatCard title="Colaboradores" value={stats.total_collaborators} icon={UserCheck} color="violet" />
          <StatCard title="Tareas este mes" value={stats.tasks_this_month} icon={Activity} color="indigo" />
          <StatCard title="Tareas totales" value={stats.total_tasks} icon={ClipboardList} color="amber" />
        </div>
      </div>

      {/* Sección: Estado de Tareas + IVA */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          <p className="section-title">Estado de Tareas</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatCard title="Terminadas" value={stats.completed_tasks} icon={CheckCircle} color="emerald" />
            <StatCard title="En curso" value={stats.in_progress_tasks} icon={Clock} color="cyan" />
            <StatCard title="Pendientes" value={stats.pending_tasks} icon={AlertCircle} color="amber" />
            <StatCard title="Bloqueadas" value={stats.blocked_tasks} icon={AlertCircle} color="rose" />
          </div>
        </div>
        <div className="space-y-3">
          <p className="section-title">Declaraciones IVA</p>
          <div className="space-y-4">
            <StatCard title="DDJJ IVA pendientes" value={stats.iva_pendientes} subtitle="Sin presentar" icon={BarChart3} color="rose" />
            <StatCard title="IVA presentados este mes" value={stats.iva_presentados_mes} subtitle="Declaraciones juradas" icon={CheckCircle} color="emerald" />
          </div>
        </div>
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly billing */}
        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp size={20} className="text-violet-400" />
            Facturación mensual
          </h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="period" tickFormatter={formatPeriod} tick={{ fontSize: 11, fill: '#9ca3af' }} />
              <YAxis tickFormatter={v => `$${(v/1000000).toFixed(1)}M`} tick={{ fontSize: 11, fill: '#9ca3af' }} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="monto_facturas" name="Monto facturado" stroke="#7c3aed" strokeWidth={2.5} dot={{ r: 3, fill: '#7c3aed' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Tasks by type pie */}
        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <ClipboardList size={20} className="text-sky-400" />
            Tareas por tipo
          </h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={tasksByType} cx="50%" cy="50%" outerRadius={90} innerRadius={45}
                dataKey="value" nameKey="name" paddingAngle={3}>
                {tasksByType.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(v, n) => [v, n]} contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#f3f4f6' }} />
              <Legend formatter={v => <span style={{ color: '#d1d5db', fontSize: 12 }}>{v}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Collaborator tasks stacked bar */}
        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <UserCheck size={20} className="text-emerald-400" />
            Tareas por colaborador
          </h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={collabBarData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#9ca3af' }} />
              <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} />
              <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#f3f4f6' }} />
              <Legend formatter={v => <span style={{ color: '#d1d5db', fontSize: 12 }}>{v}</span>} />
              <Bar dataKey="Terminadas" stackId="a" fill="#10b981" radius={[0,0,0,0]} />
              <Bar dataKey="En Curso" stackId="a" fill="#0ea5e9" />
              <Bar dataKey="Pendientes" stackId="a" fill="#f59e0b" />
              <Bar dataKey="Bloqueadas" stackId="a" fill="#f43f5e" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Monthly tasks & IVA */}
        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Activity size={20} className="text-amber-400" />
            Actividad mensual
          </h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="period" tickFormatter={formatPeriod} tick={{ fontSize: 11, fill: '#9ca3af' }} />
              <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend formatter={v => <span style={{ color: '#d1d5db', fontSize: 12 }}>{v}</span>} />
              <Bar dataKey="tareas" name="Tareas" fill="#7c3aed" radius={[3,3,0,0]} />
              <Bar dataKey="facturas" name="Facturas" fill="#0ea5e9" radius={[3,3,0,0]} />
              <Bar dataKey="iva_presentados" name="IVA pres." fill="#10b981" radius={[3,3,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Collaborator detail table */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <UserCheck size={20} className="text-violet-400" />
          Rendimiento de colaboradores
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700/60">
                <th className="table-header">Colaborador</th>
                <th className="table-header text-right">Clientes</th>
                <th className="table-header text-right">Total tareas</th>
                <th className="table-header text-right">Terminadas</th>
                <th className="table-header text-right">En curso</th>
                <th className="table-header text-right">Pendientes</th>
                <th className="table-header text-right">Bloqueadas</th>
                <th className="table-header">% completado</th>
              </tr>
            </thead>
            <tbody>
              {collabStats.map(c => {
                const pct = c.total_tasks > 0 ? Math.round(c.completed / c.total_tasks * 100) : 0
                return (
                  <tr key={c.collaborator_id} className="table-row">
                    <td className="table-cell font-medium text-white">{c.collaborator_name}</td>
                    <td className="table-cell text-right">{c.clients_count}</td>
                    <td className="table-cell text-right font-semibold">{c.total_tasks}</td>
                    <td className="table-cell text-right text-emerald-400">{c.completed}</td>
                    <td className="table-cell text-right text-sky-400">{c.in_progress}</td>
                    <td className="table-cell text-right text-amber-400">{c.pending}</td>
                    <td className="table-cell text-right text-rose-400">{c.blocked}</td>
                    <td className="table-cell">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${pct}%`, background: pct > 70 ? '#10b981' : pct > 40 ? '#f59e0b' : '#f43f5e' }}
                          />
                        </div>
                        <span className="text-sm font-semibold text-gray-300 w-10 text-right">{pct}%</span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
