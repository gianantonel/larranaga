import { useEffect, useState } from 'react'
import { BarChart3, CheckCircle, AlertTriangle, TrendingUp } from 'lucide-react'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { getIvaRecords, getClients, fileIva } from '../utils/api'
import { FiledBadge } from '../components/UI/Badge'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import StatCard from '../components/UI/StatCard'
import { formatCurrency, formatPeriod, formatDate } from '../utils/helpers'

export default function IVA() {
  const [records, setRecords] = useState([])
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterClient, setFilterClient] = useState('')
  const [filterFiled, setFilterFiled] = useState('')
  const [filterPeriod, setFilterPeriod] = useState('')
  const [filingId, setFilingId] = useState(null)
  const [vepInput, setVepInput] = useState('')

  const load = () => {
    const params = {}
    if (filterClient) params.client_id = filterClient
    if (filterFiled !== '') params.filed = filterFiled === 'true'
    if (filterPeriod) params.period = filterPeriod
    Promise.all([getIvaRecords(params), getClients()])
      .then(([r, c]) => { setRecords(r.data); setClients(c.data) })
      .catch(err => console.error('IVA load error:', err))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filterClient, filterFiled, filterPeriod])

  const handleFile = async (id) => {
    try {
      await fileIva(id, vepInput || undefined)
      setFilingId(null)
      setVepInput('')
      load()
    } catch (e) { alert(e.response?.data?.detail || 'Error') }
  }

  if (loading) return <LoadingSpinner text="Cargando registros IVA..." />

  const pending = records.filter(r => !r.filed)
  const filed = records.filter(r => r.filed)
  const totalSaldo = records.reduce((a, r) => a + r.saldo, 0)
  const totalDebito = records.reduce((a, r) => a + r.debito_fiscal, 0)
  const totalCredito = records.reduce((a, r) => a + r.credito_fiscal, 0)

  // Chart: last 12 months aggregate
  const byPeriod = {}
  records.forEach(r => {
    if (!byPeriod[r.period]) byPeriod[r.period] = { debito: 0, credito: 0, saldo: 0, count: 0 }
    byPeriod[r.period].debito += r.debito_fiscal
    byPeriod[r.period].credito += r.credito_fiscal
    byPeriod[r.period].saldo += r.saldo
    byPeriod[r.period].count++
  })
  const chartData = Object.entries(byPeriod)
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-12)
    .map(([period, d]) => ({ period, 'Débito Fiscal': d.debito, 'Crédito Fiscal': d.credito, Saldo: d.saldo }))

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="Balance IVA"
        subtitle="Gestión de declaraciones juradas de IVA — ARCA"
      />

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Pendientes de presentar" value={pending.length} icon={AlertTriangle} color="rose" />
        <StatCard title="Presentados" value={filed.length} icon={CheckCircle} color="emerald" />
        <StatCard title="Saldo total a pagar" value={formatCurrency(totalSaldo)} icon={TrendingUp} color="amber" />
        <StatCard title="Total débito fiscal" value={formatCurrency(totalDebito)} icon={BarChart3} color="violet" />
      </div>

      {/* Chart */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">Evolución IVA — todos los clientes</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="period" tickFormatter={formatPeriod} tick={{ fontSize: 11, fill: '#9ca3af' }} />
            <YAxis tickFormatter={v => `$${(v/1000000).toFixed(1)}M`} tick={{ fontSize: 11, fill: '#9ca3af' }} />
            <Tooltip formatter={v => formatCurrency(v)} contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#f3f4f6' }} labelFormatter={formatPeriod} />
            <Legend formatter={v => <span style={{ color: '#d1d5db', fontSize: 12 }}>{v}</span>} />
            <Bar dataKey="Débito Fiscal" fill="#f43f5e" radius={[3,3,0,0]} />
            <Bar dataKey="Crédito Fiscal" fill="#10b981" radius={[3,3,0,0]} />
            <Bar dataKey="Saldo" fill="#f59e0b" radius={[3,3,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select value={filterClient} onChange={e => setFilterClient(e.target.value)} className="input-field w-auto">
          <option value="">Todos los clientes</option>
          {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select value={filterFiled} onChange={e => setFilterFiled(e.target.value)} className="input-field w-auto">
          <option value="">Todos</option>
          <option value="false">Pendientes</option>
          <option value="true">Presentados</option>
        </select>
        <input value={filterPeriod} onChange={e => setFilterPeriod(e.target.value)} placeholder="Período YYYY-MM" className="input-field w-40 font-mono" />
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700/60 bg-[#0f172a]/60">
                <th className="table-header whitespace-nowrap">Cliente</th>
                <th className="table-header whitespace-nowrap">Período</th>
                <th className="table-header text-right whitespace-nowrap">Ventas gravadas</th>
                <th className="table-header text-right whitespace-nowrap">Débito fiscal</th>
                <th className="table-header text-right whitespace-nowrap">Compras gravadas</th>
                <th className="table-header text-right whitespace-nowrap">Crédito fiscal</th>
                <th className="table-header text-right whitespace-nowrap">Saldo</th>
                <th className="table-header whitespace-nowrap">Vto.</th>
                <th className="table-header text-center whitespace-nowrap">Estado</th>
                <th className="table-header text-center whitespace-nowrap">Acción</th>
              </tr>
            </thead>
            <tbody>
              {records.map(r => (
                <tr key={r.id} className={`table-row ${!r.filed ? 'bg-rose-500/3' : ''}`}>
                  <td className="table-cell font-semibold text-white whitespace-nowrap">{r.client_name}</td>
                  <td className="table-cell font-semibold whitespace-nowrap">{formatPeriod(r.period)}</td>
                  <td className="table-cell text-right text-gray-300 whitespace-nowrap">{formatCurrency(r.ventas_gravadas)}</td>
                  <td className="table-cell text-right text-rose-400 font-semibold whitespace-nowrap">{formatCurrency(r.debito_fiscal)}</td>
                  <td className="table-cell text-right text-gray-300 whitespace-nowrap">{formatCurrency(r.compras_gravadas)}</td>
                  <td className="table-cell text-right text-emerald-400 font-semibold whitespace-nowrap">{formatCurrency(r.credito_fiscal)}</td>
                  <td className={`table-cell text-right font-bold text-lg whitespace-nowrap ${r.saldo > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {formatCurrency(r.saldo)}
                  </td>
                  <td className="table-cell text-sm text-gray-400 whitespace-nowrap">{formatDate(r.due_date)}</td>
                  <td className="table-cell text-center whitespace-nowrap">
                    <FiledBadge filed={r.filed} />
                    {r.filed && r.filed_at && (
                      <p className="text-xs text-gray-500 mt-0.5">{formatDate(r.filed_at)}</p>
                    )}
                    {r.vep_number && <p className="text-xs text-sky-400 font-mono mt-0.5">VEP: {r.vep_number}</p>}
                  </td>
                  <td className="table-cell text-center whitespace-nowrap">
                    {!r.filed && (
                      filingId === r.id ? (
                        <div className="flex items-center gap-2">
                          <input value={vepInput} onChange={e => setVepInput(e.target.value)} placeholder="Nº VEP" className="input-field text-xs py-1.5 w-24 font-mono" />
                          <button onClick={() => handleFile(r.id)} className="btn-success text-xs px-2 py-1.5">Confirmar</button>
                          <button onClick={() => setFilingId(null)} className="text-gray-500 hover:text-gray-300 text-xs">✕</button>
                        </div>
                      ) : (
                        <button onClick={() => setFilingId(r.id)} className="btn-success text-sm px-3 py-1.5">
                          Presentar
                        </button>
                      )
                    )}
                  </td>
                </tr>
              ))}
              {records.length === 0 && (
                <tr><td colSpan={10} className="text-center py-12 text-gray-500">No hay registros IVA con los filtros seleccionados.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
