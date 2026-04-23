import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Plus, Eye, EyeOff, UserPlus, UserMinus, Key } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import {
  getClient, getIvaRecords, getFacturas, getTasks,
  getClientCredentials, assignCollaborator, removeCollaboratorFromClient,
  getCollaborators
} from '../utils/api'
import { useAuth } from '../context/AuthContext'
import { StatusBadge, TypeBadge, FiledBadge } from '../components/UI/Badge'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import RetencionesPanel from '../components/RetencionesPanel'
import { formatCurrency, formatDate, formatPeriod } from '../utils/helpers'

export default function ClientDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isAdmin } = useAuth()
  const [client, setClient] = useState(null)
  const [ivaRecords, setIvaRecords] = useState([])
  const [facturas, setFacturas] = useState([])
  const [tasks, setTasks] = useState([])
  const [allCollabs, setAllCollabs] = useState([])
  const [credentials, setCredentials] = useState(null)
  const [showClave, setShowClave] = useState(false)
  const [activeTab, setActiveTab] = useState('iva')
  const [loading, setLoading] = useState(true)

  const load = () => {
    Promise.all([
      getClient(id),
      getIvaRecords({ client_id: id }),
      getFacturas({ client_id: id }),
      getTasks({ client_id: id }),
      getCollaborators(),
    ]).then(([c, iva, f, t, col]) => {
      setClient(c.data)
      setIvaRecords(iva.data)
      setFacturas(f.data)
      setTasks(t.data)
      setAllCollabs(col.data)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [id])

  const loadCredentials = async () => {
    if (credentials) { setShowClave(v => !v); return }
    try {
      const res = await getClientCredentials(id)
      setCredentials(res.data)
      setShowClave(true)
    } catch { alert('No se pudo obtener credenciales') }
  }

  const handleAssign = async (collabId) => {
    try {
      await assignCollaborator(id, collabId)
      load()
    } catch (e) { alert(e.response?.data?.detail || 'Error') }
  }

  const handleUnassign = async (collabId) => {
    if (!confirm('¿Desasignar este colaborador?')) return
    try {
      await removeCollaboratorFromClient(id, collabId)
      load()
    } catch (e) { alert(e.response?.data?.detail || 'Error') }
  }

  if (loading) return <LoadingSpinner text="Cargando cliente..." />
  if (!client) return <div className="p-6 text-gray-400">Cliente no encontrado.</div>

  // IVA chart data
  const ivaChartData = [...ivaRecords].reverse().map(r => ({
    period: r.period,
    'Débito Fiscal': r.debito_fiscal,
    'Crédito Fiscal': r.credito_fiscal,
    Saldo: r.saldo,
  }))

  const tabs = [
    { id: 'iva', label: `IVA (${ivaRecords.length})` },
    { id: 'facturas', label: `Facturas (${facturas.length})` },
    { id: 'tareas', label: `Tareas (${tasks.length})` },
    { id: 'retenciones', label: 'Retenciones' },
  ]

  const assignedIds = client.collaborators.map(c => c.id)
  const unassignedCollabs = allCollabs.filter(c => !assignedIds.includes(c.id))

  return (
    <div className="p-6 space-y-6">
      <button onClick={() => navigate('/clientes')} className="flex items-center gap-2 text-gray-400 hover:text-white text-base transition-colors">
        <ArrowLeft size={18} /> Volver a clientes
      </button>

      {/* Header card */}
      <div className="card">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white">{client.name}</h1>
            {client.business_name && <p className="text-gray-400 mt-0.5">{client.business_name}</p>}
            <div className="flex flex-wrap gap-3 mt-3">
              {client.cuit && <span className="badge-blue font-mono">{client.cuit}</span>}
              {client.fiscal_condition && <span className="badge-purple">{client.fiscal_condition}</span>}
              {client.category && <span className="badge-gray">{client.category}</span>}
              <span className={client.is_active ? 'badge-green' : 'badge-red'}>
                {client.is_active ? 'Activo' : 'Inactivo'}
              </span>
            </div>
          </div>
          <div className="flex gap-2 flex-wrap">
            {client.phone && <div className="text-sm text-gray-400">{client.phone}</div>}
            {client.email && <div className="text-sm text-gray-400">{client.email}</div>}
          </div>
        </div>

        {/* Credentials */}
        <div className="mt-4 p-4 bg-[#0f172a] rounded-xl border border-gray-700/40">
          <div className="flex items-center gap-3 flex-wrap">
            <Key size={16} className="text-amber-400" />
            <span className="text-sm text-gray-400 font-medium">Acceso ARCA:</span>
            <span className="font-mono text-gray-300 text-sm">CUIT: {client.cuit}</span>
            {showClave && credentials && (
              <span className="font-mono text-amber-300 text-sm">Clave: {credentials.clave_fiscal}</span>
            )}
            <button onClick={loadCredentials} className="ml-auto flex items-center gap-1.5 text-amber-400 hover:text-amber-300 text-sm font-medium transition-colors">
              {showClave ? <EyeOff size={15} /> : <Eye size={15} />}
              {showClave ? 'Ocultar' : 'Ver clave fiscal'}
            </button>
          </div>
        </div>
      </div>

      {/* Collaborators */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Colaboradores asignados</h2>
        <div className="flex flex-wrap gap-3">
          {client.collaborators.map(col => (
            <div key={col.id} className="flex items-center gap-2 px-3 py-2 bg-[#1f2937] rounded-xl border border-gray-600/40">
              <div className="w-7 h-7 rounded-full bg-violet-600/30 flex items-center justify-center text-xs font-bold text-violet-300">
                {col.name.slice(0,1)}
              </div>
              <span className="text-sm font-medium text-gray-200">{col.name}</span>
              {isAdmin && (
                <button onClick={() => handleUnassign(col.id)} className="text-gray-500 hover:text-rose-400 transition-colors ml-1">
                  <UserMinus size={14} />
                </button>
              )}
            </div>
          ))}
          {isAdmin && unassignedCollabs.length > 0 && (
            <div className="relative group">
              <button className="flex items-center gap-2 px-3 py-2 bg-emerald-600/10 rounded-xl border border-emerald-500/20 text-emerald-400 text-sm hover:bg-emerald-600/20 transition-colors">
                <UserPlus size={14} /> Asignar
              </button>
              <div className="absolute left-0 top-full mt-1 bg-[#1f2937] border border-gray-600 rounded-xl shadow-xl z-10 hidden group-hover:block min-w-40">
                {unassignedCollabs.map(c => (
                  <button key={c.id} onClick={() => handleAssign(c.id)}
                    className="w-full text-left px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-700/50 hover:text-white transition-colors first:rounded-t-xl last:rounded-b-xl">
                    {c.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* IVA Chart */}
      {ivaChartData.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Evolución IVA — últimos 12 meses</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={ivaChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="period" tickFormatter={formatPeriod} tick={{ fontSize: 11, fill: '#9ca3af' }} />
              <YAxis tickFormatter={v => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 11, fill: '#9ca3af' }} />
              <Tooltip formatter={v => formatCurrency(v)} contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#f3f4f6' }} labelFormatter={formatPeriod} />
              <Legend formatter={v => <span style={{ color: '#d1d5db', fontSize: 12 }}>{v}</span>} />
              <Line type="monotone" dataKey="Débito Fiscal" stroke="#f43f5e" strokeWidth={2} dot={{ r: 2 }} />
              <Line type="monotone" dataKey="Crédito Fiscal" stroke="#10b981" strokeWidth={2} dot={{ r: 2 }} />
              <Line type="monotone" dataKey="Saldo" stroke="#f59e0b" strokeWidth={2.5} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Tabs */}
      <div>
        <div className="flex gap-1 bg-[#0f172a] p-1 rounded-xl w-fit mb-4 border border-gray-700/40">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              className={`px-5 py-2 rounded-lg text-base font-medium transition-all ${activeTab === t.id ? 'bg-violet-600 text-white shadow-lg' : 'text-gray-400 hover:text-gray-200'}`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* IVA Table */}
        {activeTab === 'iva' && (
          <div className="card p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700/60 bg-[#0f172a]/60">
                  <th className="table-header">Período</th>
                  <th className="table-header text-right">Ventas gravadas</th>
                  <th className="table-header text-right">Débito fiscal</th>
                  <th className="table-header text-right">Compras gravadas</th>
                  <th className="table-header text-right">Crédito fiscal</th>
                  <th className="table-header text-right">Saldo</th>
                  <th className="table-header text-center">Estado</th>
                </tr>
              </thead>
              <tbody>
                {ivaRecords.map(r => (
                  <tr key={r.id} className="table-row">
                    <td className="table-cell font-semibold text-white">{formatPeriod(r.period)}</td>
                    <td className="table-cell text-right text-gray-300">{formatCurrency(r.ventas_gravadas)}</td>
                    <td className="table-cell text-right text-rose-400 font-semibold">{formatCurrency(r.debito_fiscal)}</td>
                    <td className="table-cell text-right text-gray-300">{formatCurrency(r.compras_gravadas)}</td>
                    <td className="table-cell text-right text-emerald-400 font-semibold">{formatCurrency(r.credito_fiscal)}</td>
                    <td className={`table-cell text-right font-bold ${r.saldo > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {formatCurrency(r.saldo)}
                    </td>
                    <td className="table-cell text-center"><FiledBadge filed={r.filed} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Facturas Table */}
        {activeTab === 'facturas' && (
          <div className="card p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700/60 bg-[#0f172a]/60">
                  <th className="table-header">Fecha</th>
                  <th className="table-header">Tipo</th>
                  <th className="table-header">Número</th>
                  <th className="table-header">Receptor</th>
                  <th className="table-header text-right">Neto</th>
                  <th className="table-header text-right">IVA 21%</th>
                  <th className="table-header text-right">Total</th>
                  <th className="table-header">Colaborador</th>
                </tr>
              </thead>
              <tbody>
                {facturas.map(f => (
                  <tr key={f.id} className="table-row">
                    <td className="table-cell text-gray-300">{formatDate(f.date)}</td>
                    <td className="table-cell"><span className="badge-blue font-mono">F. {f.invoice_type}</span></td>
                    <td className="table-cell font-mono text-gray-400">{String(f.punto_venta).padStart(5,'0')}-{String(f.number).padStart(8,'0')}</td>
                    <td className="table-cell">
                      <p className="text-sm font-medium text-gray-200">{f.receptor_name}</p>
                      <p className="text-xs text-gray-500 font-mono">{f.receptor_cuit}</p>
                    </td>
                    <td className="table-cell text-right text-gray-300">{formatCurrency(f.neto_gravado)}</td>
                    <td className="table-cell text-right text-gray-400">{formatCurrency(f.iva_21)}</td>
                    <td className="table-cell text-right font-bold text-white">{formatCurrency(f.total)}</td>
                    <td className="table-cell text-sm text-gray-400">{f.collaborator_name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Tasks Table */}
        {activeTab === 'retenciones' && (
          <RetencionesPanel clientId={Number(id)} />
        )}

        {activeTab === 'tareas' && (
          <div className="card p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700/60 bg-[#0f172a]/60">
                  <th className="table-header">Tarea</th>
                  <th className="table-header">Tipo</th>
                  <th className="table-header">Período</th>
                  <th className="table-header">Colaborador</th>
                  <th className="table-header text-center">Subtareas</th>
                  <th className="table-header">Estado</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map(t => (
                  <tr key={t.id} className="table-row">
                    <td className="table-cell font-medium text-gray-200">{t.title}</td>
                    <td className="table-cell"><TypeBadge type={t.task_type} /></td>
                    <td className="table-cell text-gray-400">{t.period ? formatPeriod(t.period) : '—'}</td>
                    <td className="table-cell text-gray-300 text-sm">{t.collaborator_name || '—'}</td>
                    <td className="table-cell text-center">
                      <span className="text-gray-400 text-sm">{t.subtasks?.length || 0}</span>
                    </td>
                    <td className="table-cell"><StatusBadge status={t.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
