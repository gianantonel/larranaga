import { useEffect, useState } from 'react'
import { Plus, ReceiptText, TrendingUp, DollarSign, X, Upload } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { getFacturas, getClients, getMonthlyActivity, createFactura } from '../utils/api'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import StatCard from '../components/UI/StatCard'
import { formatCurrency, formatDate, formatPeriod } from '../utils/helpers'
import BulkUploadModal from '../components/UI/BulkUploadModal'

const INVOICE_TYPES = ['A', 'B', 'C', 'M', 'E']

export default function Facturas() {
  const [facturas, setFacturas] = useState([])
  const [clients, setClients] = useState([])
  const [monthlyData, setMonthlyData] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterClient, setFilterClient] = useState('')
  const [filterType, setFilterType] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [showBulkModal, setShowBulkModal] = useState(false)
  const [form, setForm] = useState({
    client_id: '', invoice_type: 'A', punto_venta: 1, date: '',
    receptor_cuit: '', receptor_name: '', concept: 'Servicios',
    neto_gravado: '', iva_21: '', total: ''
  })
  const [saving, setSaving] = useState(false)

  const load = () => {
    const params = {}
    if (filterClient) params.client_id = filterClient
    if (filterType) params.invoice_type = filterType
    Promise.all([getFacturas(params), getClients(), getMonthlyActivity()])
      .then(([f, c, ma]) => {
        setFacturas(f.data)
        setClients(c.data)
        setMonthlyData(ma.data.slice(-12))
      })
      .catch(err => console.error('Facturas load error:', err))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filterClient, filterType])

  const handleNetoChange = (val) => {
    const neto = parseFloat(val) || 0
    const iva = Math.round(neto * 21) / 100
    setForm(f => ({ ...f, neto_gravado: val, iva_21: iva.toFixed(2), total: (neto + iva).toFixed(2) }))
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await createFactura({
        ...form,
        punto_venta: parseInt(form.punto_venta),
        neto_gravado: parseFloat(form.neto_gravado) || 0,
        iva_21: parseFloat(form.iva_21) || 0,
        total: parseFloat(form.total) || 0,
      })
      setShowModal(false)
      load()
    } catch (e) { alert(e.response?.data?.detail || 'Error al crear factura') }
    finally { setSaving(false) }
  }

  useEffect(() => {
    if (!showModal) return
    const handleEsc = e => { if (e.key === 'Escape') setShowModal(false) }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [showModal])

  if (loading) return <LoadingSpinner text="Cargando facturas..." />

  const totalMonto = facturas.reduce((a, f) => a + f.total, 0)
  const totalIVA = facturas.reduce((a, f) => a + f.iva_21 + f.iva_105, 0)
  const countA = facturas.filter(f => f.invoice_type === 'A').length
  const countB = facturas.filter(f => f.invoice_type === 'B').length

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Facturación" subtitle="Comprobantes electrónicos — ARCA">
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={() => setShowBulkModal(true)}>
            <Upload size={18} /> Importar
          </button>
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={18} /> Nueva factura
          </button>
        </div>
      </PageHeader>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total facturas" value={facturas.length} icon={ReceiptText} color="violet" />
        <StatCard title="Monto total" value={formatCurrency(totalMonto)} icon={DollarSign} color="emerald" />
        <StatCard title="IVA total" value={formatCurrency(totalIVA)} icon={TrendingUp} color="amber" />
        <StatCard title="Fact. A / B" value={`${countA} / ${countB}`} icon={ReceiptText} color="cyan" />
      </div>

      {/* Chart */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">Facturación mensual</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="period" tickFormatter={formatPeriod} tick={{ fontSize: 11, fill: '#9ca3af' }} />
            <YAxis tickFormatter={v => `$${(v/1000000).toFixed(1)}M`} tick={{ fontSize: 11, fill: '#9ca3af' }} />
            <Tooltip formatter={(v, n) => [n === 'Monto' ? formatCurrency(v) : v, n]} contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#f3f4f6' }} labelFormatter={formatPeriod} />
            <Legend formatter={v => <span style={{ color: '#d1d5db', fontSize: 12 }}>{v}</span>} />
            <Bar dataKey="monto_facturas" name="Monto" fill="#7c3aed" radius={[3,3,0,0]} />
            <Bar dataKey="facturas" name="Cantidad" fill="#0ea5e9" radius={[3,3,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select value={filterClient} onChange={e => setFilterClient(e.target.value)} className="input-field w-auto">
          <option value="">Todos los clientes</option>
          {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select value={filterType} onChange={e => setFilterType(e.target.value)} className="input-field w-auto">
          <option value="">Todos los tipos</option>
          {INVOICE_TYPES.map(t => <option key={t} value={t}>Factura {t}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700/60 bg-[#0f172a]/60">
                <th className="table-header whitespace-nowrap">Fecha</th>
                <th className="table-header whitespace-nowrap">Tipo</th>
                <th className="table-header whitespace-nowrap">Número</th>
                <th className="table-header">Cliente</th>
                <th className="table-header">Receptor</th>
                <th className="table-header text-right whitespace-nowrap">Neto gravado</th>
                <th className="table-header text-right whitespace-nowrap">IVA 21%</th>
                <th className="table-header text-right whitespace-nowrap">Total</th>
                <th className="table-header whitespace-nowrap">CAE</th>
                <th className="table-header whitespace-nowrap">Colaborador</th>
              </tr>
            </thead>
            <tbody>
              {facturas.map(f => (
                <tr key={f.id} className="table-row">
                  <td className="table-cell text-gray-300 text-sm whitespace-nowrap">{formatDate(f.date)}</td>
                  <td className="table-cell whitespace-nowrap">
                    <span className="badge-blue font-mono font-bold">F. {f.invoice_type}</span>
                  </td>
                  <td className="table-cell font-mono text-gray-400 text-sm whitespace-nowrap">
                    {String(f.punto_venta).padStart(5,'0')}-{String(f.number).padStart(8,'0')}
                  </td>
                  <td className="table-cell font-medium text-white min-w-[200px]">{f.client_name}</td>
                  <td className="table-cell min-w-[200px]">
                    <p className="text-sm text-gray-200 truncate max-w-[200px]" title={f.receptor_name}>{f.receptor_name}</p>
                    <p className="text-xs text-gray-500 font-mono">{f.receptor_cuit}</p>
                  </td>
                  <td className="table-cell text-right text-gray-300 whitespace-nowrap">{formatCurrency(f.neto_gravado)}</td>
                  <td className="table-cell text-right text-gray-400 whitespace-nowrap">{formatCurrency(f.iva_21)}</td>
                  <td className="table-cell text-right font-bold text-white text-lg whitespace-nowrap">{formatCurrency(f.total)}</td>
                  <td className="table-cell font-mono text-xs text-sky-400 whitespace-nowrap">{f.cae?.slice(-8) || '—'}</td>
                  <td className="table-cell text-sm text-gray-400 whitespace-nowrap">{f.collaborator_name}</td>
                </tr>
              ))}
              {facturas.length === 0 && (
                <tr><td colSpan={10} className="text-center py-12 text-gray-500">No hay facturas.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        {facturas.length >= 500 && (
          <div className="px-4 py-3 text-sm text-gray-500 border-t border-gray-700/40">
            Mostrando {facturas.length} facturas. Usar filtros para refinar resultados.
          </div>
        )}
      </div>

      {/* Create modal */}
      {showModal && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="modal-panel max-w-xl p-6" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="text-xl font-bold text-white">Emitir comprobante</h2>
              <button type="button" onClick={() => setShowModal(false)} className="btn-icon"><X size={18} /></button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="label">Cliente *</label>
                  <select value={form.client_id} onChange={e => setForm(f=>({...f, client_id: e.target.value}))} className="input-field" required>
                    <option value="">Seleccionar...</option>
                    {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="label">Tipo</label>
                  <select value={form.invoice_type} onChange={e => setForm(f=>({...f, invoice_type: e.target.value}))} className="input-field">
                    {INVOICE_TYPES.map(t => <option key={t} value={t}>Factura {t}</option>)}
                  </select>
                </div>
                <div><label className="label">Fecha *</label><input type="date" value={form.date} onChange={e => setForm(f=>({...f, date: e.target.value}))} className="input-field" required /></div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div><label className="label">CUIT Receptor</label><input value={form.receptor_cuit} onChange={e => setForm(f=>({...f, receptor_cuit: e.target.value}))} placeholder="XX-XXXXXXXX-X" className="input-field font-mono" /></div>
                <div><label className="label">Nombre Receptor</label><input value={form.receptor_name} onChange={e => setForm(f=>({...f, receptor_name: e.target.value}))} className="input-field" /></div>
              </div>
              <div>
                <label className="label">Concepto</label>
                <select value={form.concept} onChange={e => setForm(f=>({...f, concept: e.target.value}))} className="input-field">
                  <option>Productos</option><option>Servicios</option><option>Productos y Servicios</option>
                </select>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="label">Neto gravado *</label>
                  <input type="number" step="0.01" value={form.neto_gravado} onChange={e => handleNetoChange(e.target.value)} className="input-field font-mono" required />
                </div>
                <div>
                  <label className="label">IVA 21%</label>
                  <input type="number" step="0.01" value={form.iva_21} onChange={e => setForm(f=>({...f, iva_21: e.target.value, total: (parseFloat(f.neto_gravado)||0) + (parseFloat(e.target.value)||0) }))} className="input-field font-mono" />
                </div>
                <div>
                  <label className="label">Total</label>
                  <input type="number" step="0.01" value={form.total} onChange={e => setForm(f=>({...f, total: e.target.value}))} className="input-field font-mono font-bold" />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1 justify-center">Cancelar</button>
                <button type="submit" disabled={saving} className="btn-primary flex-1 justify-center">{saving ? 'Emitiendo...' : 'Emitir factura'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <BulkUploadModal
        open={showBulkModal}
        onClose={() => { setShowBulkModal(false); load() }}
        entity="invoices"
      />
    </div>
  )
}
