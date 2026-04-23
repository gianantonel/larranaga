import { useEffect, useState } from 'react'
import { Download, Loader2, RefreshCw, Trash2 } from 'lucide-react'
import { syncRetenciones, getRetenciones, deleteRetencion } from '../utils/api'
import { formatCurrency, formatDate } from '../utils/helpers'

const IMPUESTOS = [
  { value: 217, label: 'IVA (217)', descripcion: 'IVA' },
  { value: 11,  label: 'Ganancias Retención (11)', descripcion: 'Ganancias' },
  { value: 10,  label: 'Ganancias Percepción (10)', descripcion: 'Ganancias' },
  { value: 767, label: 'Bienes Personales (767)', descripcion: 'Bienes Personales' },
]

const HOLISTOR_COLORS = {
  PIVC: 'bg-violet-500/20 text-violet-300 border-violet-500/40',
  PGAN: 'bg-sky-500/20 text-sky-300 border-sky-500/40',
  PIBA: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  OTRO: 'bg-gray-500/20 text-gray-300 border-gray-500/40',
}

export default function RetencionesPanel({ clientId, defaultPeriod = '' }) {
  const [period, setPeriod] = useState(defaultPeriod)
  const [impuesto, setImpuesto] = useState(217)
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [records, setRecords] = useState([])
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState('')
  const [lastSync, setLastSync] = useState(null)

  const loadExisting = () => {
    if (!clientId) return
    setLoading(true)
    const params = { client_id: clientId }
    if (period) params.period = period
    getRetenciones(params)
      .then((r) => setRecords(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadExisting() }, [clientId, period])

  const handleSync = async () => {
    setError('')
    if (!clientId) { setError('Cliente requerido'); return }
    if (!/^\d{4}-\d{2}$/.test(period)) { setError('Período inválido (YYYY-MM)'); return }
    const imp = IMPUESTOS.find(i => i.value === Number(impuesto))
    setSyncing(true)
    try {
      const res = await syncRetenciones({
        client_id: Number(clientId),
        period,
        impuesto_retenido: Number(impuesto),
        descripcion_impuesto: imp?.descripcion || 'IVA',
        incluir_percepciones: true,
        incluir_retenciones: true,
      })
      setLastSync(res.data)
      setSummary(res.data.summary_by_holistor || {})
      setRecords(res.data.records || [])
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Error al consultar ARCA')
    } finally {
      setSyncing(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar este registro?')) return
    try {
      await deleteRetencion(id)
      setRecords(rs => rs.filter(r => r.id !== id))
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al eliminar')
    }
  }

  const totalImporte = records.reduce((acc, r) => acc + (r.importe || 0), 0)

  return (
    <div className="space-y-4">
      {/* Form */}
      <div className="card p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Período (YYYY-MM)</label>
            <input
              type="month"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="input-field w-full"
            />
          </div>
          <div className="md:col-span-2">
            <label className="text-xs text-gray-400 mb-1 block">Impuesto</label>
            <select
              value={impuesto}
              onChange={(e) => setImpuesto(Number(e.target.value))}
              className="input-field w-full"
            >
              {IMPUESTOS.map(i => <option key={i.value} value={i.value}>{i.label}</option>)}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={handleSync}
              disabled={syncing || !clientId || !period}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {syncing ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
              {syncing ? 'Consultando…' : 'Consultar ARCA'}
            </button>
          </div>
        </div>
        {error && (
          <div className="mt-3 p-2 rounded-lg bg-rose-500/10 border border-rose-500/40 text-rose-300 text-sm">
            {error}
          </div>
        )}
        {lastSync && (
          <div className="mt-3 text-xs text-gray-400">
            Última sync: {lastSync.total_records} registros ({lastSync.inserted} nuevos, {lastSync.skipped_duplicates} duplicados)
          </div>
        )}
      </div>

      {/* Summary chips */}
      {records.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(
            records.reduce((acc, r) => {
              const k = r.codigo_holistor || 'OTRO'
              acc[k] = acc[k] || { count: 0, total: 0 }
              acc[k].count++
              acc[k].total += r.importe || 0
              return acc
            }, {})
          ).map(([code, s]) => (
            <div key={code} className={`px-3 py-2 rounded-lg border text-sm ${HOLISTOR_COLORS[code] || HOLISTOR_COLORS.OTRO}`}>
              <span className="font-bold">{code}</span> · {s.count} · {formatCurrency(s.total)}
            </div>
          ))}
          <div className="px-3 py-2 rounded-lg border border-gray-600 bg-white/5 text-sm text-gray-200">
            <span className="font-bold">Total</span> · {records.length} · {formatCurrency(totalImporte)}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700/40">
          <h3 className="text-sm font-semibold text-white">Registros {period && `· ${period}`}</h3>
          <button
            onClick={loadExisting}
            className="text-xs text-gray-400 hover:text-white flex items-center gap-1"
          >
            <RefreshCw size={12} /> Recargar
          </button>
        </div>
        {loading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Cargando…</div>
        ) : records.length === 0 ? (
          <div className="p-8 text-center text-gray-500 text-sm">
            No hay registros. Consultá ARCA para traer retenciones/percepciones.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-white/3 text-xs text-gray-400 uppercase">
                <tr>
                  <th className="px-3 py-2 text-left">Fecha</th>
                  <th className="px-3 py-2 text-left">Agente</th>
                  <th className="px-3 py-2 text-left">Régimen</th>
                  <th className="px-3 py-2 text-left">Tipo</th>
                  <th className="px-3 py-2 text-left">Comprobante</th>
                  <th className="px-3 py-2 text-right">Importe</th>
                  <th className="px-3 py-2 text-center">Cód.</th>
                  <th className="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {records.map(r => (
                  <tr key={r.id} className="border-t border-gray-700/30 hover:bg-white/3">
                    <td className="px-3 py-2 text-gray-200">{formatDate(r.fecha_retencion)}</td>
                    <td className="px-3 py-2 text-gray-300 font-mono text-xs">{r.cuit_agente || '—'}</td>
                    <td className="px-3 py-2 text-gray-300">{r.codigo_regimen || '—'}</td>
                    <td className="px-3 py-2 text-gray-300">{r.tipo_operacion || '—'}</td>
                    <td className="px-3 py-2 text-gray-400 text-xs">{r.numero_comprobante || r.numero_certificado || '—'}</td>
                    <td className="px-3 py-2 text-right text-gray-100 font-medium">{formatCurrency(r.importe)}</td>
                    <td className="px-3 py-2 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded border text-xs ${HOLISTOR_COLORS[r.codigo_holistor] || HOLISTOR_COLORS.OTRO}`}>
                        {r.codigo_holistor || 'OTRO'}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <button
                        onClick={() => handleDelete(r.id)}
                        className="text-gray-500 hover:text-rose-400 p-1"
                        title="Eliminar"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
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
