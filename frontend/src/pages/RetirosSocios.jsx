import { useEffect, useState } from 'react'
import {
  ArrowDownToLine, Plus, X, CreditCard, Banknote, CheckCircle,
  AlertTriangle, CalendarDays, User as UserIcon,
} from 'lucide-react'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { formatCurrency } from '../utils/helpers'
import {
  getRetiros, crearRetiro, getProfesionales, getBilletesStock,
} from '../utils/api'

const DENOMINACIONES = [1000, 2000, 5000, 10000, 20000]
const today = () => new Date().toISOString().split('T')[0]
const emptyBilletes = () => Object.fromEntries(DENOMINACIONES.map((d) => [String(d), 0]))


export default function RetirosSocios() {
  const [retiros, setRetiros] = useState([])
  const [socios, setSocios] = useState([])
  const [stockBilletes, setStockBilletes] = useState([])
  const [loading, setLoading] = useState(true)
  const [filtros, setFiltros] = useState({ profesional_id: '', period: '' })
  const [modalOpen, setModalOpen] = useState(false)
  const [success, setSuccess] = useState(null)

  const cargarRetiros = () => {
    const params = {}
    if (filtros.profesional_id) params.profesional_id = filtros.profesional_id
    if (filtros.period) params.period = filtros.period
    return getRetiros(params).then((r) => setRetiros(r.data))
  }

  useEffect(() => {
    Promise.all([
      getProfesionales({ activo: true }),
      getBilletesStock(),
    ]).then(([p, b]) => {
      setSocios(p.data.filter((x) => x.tipo === 'socio'))
      setStockBilletes(b.data.billetes || [])
    }).then(cargarRetiros).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!loading) cargarRetiros()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros.profesional_id, filtros.period])

  const refrescarTrasCreacion = async () => {
    const [bRes] = await Promise.all([getBilletesStock(), cargarRetiros()])
    setStockBilletes(bRes.data.billetes || [])
  }

  if (loading) return <LoadingSpinner />

  const totalFiltrado = retiros.reduce((acc, r) => acc + r.importe, 0)

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <PageHeader
        title="Retiros de Socios"
        subtitle="Registro de retiros de honorarios de socios. Impacto automático en tesorería y caja."
      >
        <button
          onClick={() => { setModalOpen(true); setSuccess(null) }}
          className="btn-primary"
        >
          <Plus size={16} />
          Nuevo retiro
        </button>
      </PageHeader>

      {success && (
        <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-start gap-3">
          <CheckCircle className="text-emerald-400 mt-0.5 shrink-0" size={20} />
          <div>
            <p className="font-medium text-emerald-300">{success.mensaje}</p>
            <p className="text-sm text-emerald-400/80 mt-1">
              Total retirado por <strong className="text-emerald-300">{success.socio}</strong> en {new Date().getFullYear()}:
              <strong className="text-emerald-300 ml-1">{formatCurrency(success.totalAnio)}</strong>
            </p>
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="card mb-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="label">Socio</label>
            <select
              value={filtros.profesional_id}
              onChange={(e) => setFiltros((p) => ({ ...p, profesional_id: e.target.value }))}
              className="input-field"
            >
              <option value="">Todos los socios</option>
              {socios.map((s) => (
                <option key={s.id} value={s.id}>{s.nombre}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Período (mes)</label>
            <input
              type="month"
              value={filtros.period}
              onChange={(e) => setFiltros((p) => ({ ...p, period: e.target.value }))}
              className="input-field"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setFiltros({ profesional_id: '', period: '' })}
              className="btn-secondary w-full justify-center"
              disabled={!filtros.profesional_id && !filtros.period}
            >
              Limpiar filtros
            </button>
          </div>
        </div>
        {(filtros.profesional_id || filtros.period) && (
          <div className="mt-4 pt-4 border-t border-gray-700/40 flex items-center justify-between text-sm">
            <span className="text-gray-400">
              {retiros.length} retiro{retiros.length !== 1 && 's'} en el filtro actual
            </span>
            <span className="text-gray-300">
              Total: <strong className="text-white">{formatCurrency(totalFiltrado)}</strong>
            </span>
          </div>
        )}
      </div>

      {/* Tabla */}
      <div className="card overflow-hidden p-0">
        {retiros.length === 0 ? (
          <div className="p-12 text-center">
            <ArrowDownToLine size={48} className="mx-auto text-gray-600 mb-3" />
            <p className="text-gray-400 mb-1">Sin retiros registrados</p>
            <p className="text-sm text-gray-500">Hacé click en "Nuevo retiro" para empezar.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="table-header border-b border-gray-700/40">
                  <th className="text-left px-4 py-3">Fecha</th>
                  <th className="text-left px-4 py-3">Socio</th>
                  <th className="text-right px-4 py-3">Importe</th>
                  <th className="text-left px-4 py-3">Forma de pago</th>
                  <th className="text-left px-4 py-3">Banco / Conciliación</th>
                  <th className="text-left px-4 py-3">Notas</th>
                </tr>
              </thead>
              <tbody>
                {retiros.map((r) => (
                  <tr key={r.id} className="table-row border-b border-gray-700/20 last:border-0">
                    <td className="px-4 py-3 text-gray-300 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <CalendarDays size={14} className="text-gray-500" />
                        {r.fecha}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-200">
                      <div className="flex items-center gap-1.5">
                        <UserIcon size={14} className="text-violet-400" />
                        {r.profesional_nombre || `#${r.profesional_id}`}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-rose-300 whitespace-nowrap">
                      − {formatCurrency(r.importe)}
                    </td>
                    <td className="px-4 py-3">
                      {r.forma_pago === 'efectivo' ? (
                        <span className="inline-flex items-center gap-1 text-amber-300 text-xs px-2 py-0.5 bg-amber-500/10 border border-amber-500/30 rounded">
                          <Banknote size={12} /> Efectivo
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-sky-300 text-xs px-2 py-0.5 bg-sky-500/10 border border-sky-500/30 rounded">
                          <CreditCard size={12} /> Transferencia
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-300 text-xs">
                      {r.banco_origen && <div>{r.banco_origen}</div>}
                      {r.conciliado ? (
                        <span className="text-emerald-400">✓ conciliado</span>
                      ) : (
                        <span className="text-gray-500">pendiente</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs max-w-xs truncate" title={r.notas || ''}>
                      {r.notas || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {modalOpen && (
        <NuevoRetiroModal
          socios={socios}
          stockBilletes={stockBilletes}
          onClose={() => setModalOpen(false)}
          onSuccess={(payload) => {
            setSuccess(payload)
            setModalOpen(false)
            refrescarTrasCreacion()
          }}
        />
      )}
    </div>
  )
}


function NuevoRetiroModal({ socios, stockBilletes, onClose, onSuccess }) {
  const [form, setForm] = useState({
    profesional_id: '',
    importe: '',
    forma_pago: 'transferencia',
    banco_origen: '',
    fecha: today(),
    notas: '',
    billetes: emptyBilletes(),
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const set = (field, value) => setForm((p) => ({ ...p, [field]: value }))
  const setBillete = (denom, value) =>
    setForm((p) => ({
      ...p,
      billetes: { ...p.billetes, [String(denom)]: Math.max(0, parseInt(value) || 0) },
    }))

  const totalBilletes = DENOMINACIONES.reduce(
    (acc, d) => acc + d * (form.billetes[String(d)] || 0),
    0
  )
  const importeNum = parseFloat(form.importe) || 0
  const billetesOk = Math.abs(totalBilletes - importeNum) <= 1

  const submit = async (e) => {
    e.preventDefault()
    setError(null)

    if (!form.profesional_id || !form.importe) {
      setError('Completá socio e importe.')
      return
    }
    if (form.forma_pago === 'efectivo' && importeNum > 0 && !billetesOk) {
      setError(`La suma de billetes (${formatCurrency(totalBilletes)}) no coincide con el importe (${formatCurrency(importeNum)}).`)
      return
    }

    const payload = {
      profesional_id: parseInt(form.profesional_id),
      importe: importeNum,
      forma_pago: form.forma_pago,
      fecha: form.fecha || today(),
      banco_origen: form.forma_pago === 'transferencia' ? (form.banco_origen || null) : null,
      notas: form.notas || null,
      billetes: form.forma_pago === 'efectivo'
        ? Object.fromEntries(Object.entries(form.billetes).filter(([, v]) => v > 0))
        : null,
    }

    setSubmitting(true)
    try {
      const res = await crearRetiro(payload)
      const { retiro, total_retirado_socio_anio } = res.data
      onSuccess({
        mensaje: `Retiro de ${formatCurrency(retiro.importe)} registrado correctamente.`,
        socio: retiro.profesional_nombre || `Socio #${retiro.profesional_id}`,
        totalAnio: total_retirado_socio_anio,
      })
    } catch (err) {
      const detail = err.response?.data?.detail
      if (typeof detail === 'object' && detail?.error) {
        const extra = detail.diferencia
          ? ` (diferencia: ${formatCurrency(Math.abs(detail.diferencia))})`
          : detail.faltante
            ? ` (faltan ${detail.faltante} billetes de $${detail.stock_actual !== undefined ? '' : ''})`
            : ''
        setError(detail.error + extra)
      } else {
        setError(typeof detail === 'string' ? detail : 'Error al registrar el retiro.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="modal-panel max-w-xl p-6">
        <div className="flex items-center justify-between mb-5 pb-4 border-b border-gray-700/40">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <ArrowDownToLine size={20} className="text-violet-400" />
            Nuevo retiro
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white p-1" aria-label="Cerrar">
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-start gap-2 text-sm">
            <AlertTriangle className="text-rose-400 mt-0.5 shrink-0" size={16} />
            <p className="text-rose-300">{error}</p>
          </div>
        )}

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="label">Socio *</label>
            <select
              value={form.profesional_id}
              onChange={(e) => set('profesional_id', e.target.value)}
              className="input-field"
              required
            >
              <option value="">Seleccionar socio...</option>
              {socios.map((s) => (
                <option key={s.id} value={s.id}>{s.nombre}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Importe *</label>
              <input
                type="number" min="0" step="0.01"
                value={form.importe}
                onChange={(e) => set('importe', e.target.value)}
                placeholder="0"
                className="input-field"
                required
              />
            </div>
            <div>
              <label className="label">Fecha *</label>
              <input
                type="date"
                value={form.fecha}
                onChange={(e) => set('fecha', e.target.value)}
                className="input-field"
                required
              />
            </div>
          </div>

          <div>
            <label className="label">Forma de pago *</label>
            <div className="flex gap-3">
              {[
                { value: 'transferencia', label: 'Transferencia', icon: CreditCard },
                { value: 'efectivo', label: 'Efectivo', icon: Banknote },
              ].map(({ value, label, icon: Icon }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => set('forma_pago', value)}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg border text-sm font-medium transition-all ${
                    form.forma_pago === value
                      ? 'border-violet-500/60 bg-violet-600/20 text-violet-300'
                      : 'border-gray-700/50 bg-[#0f172a] text-gray-400 hover:border-gray-600'
                  }`}
                >
                  <Icon size={16} />
                  {label}
                </button>
              ))}
            </div>
          </div>

          {form.forma_pago === 'transferencia' && (
            <div>
              <label className="label">Banco origen</label>
              <input
                type="text"
                value={form.banco_origen}
                onChange={(e) => set('banco_origen', e.target.value)}
                placeholder="Ej: Banco Pampa"
                className="input-field"
              />
            </div>
          )}

          {form.forma_pago === 'efectivo' && (
            <div className="border border-amber-500/30 bg-amber-500/5 rounded-lg p-4">
              <p className="text-sm font-medium text-amber-300 mb-3">Detalle de billetes a retirar</p>
              <div className="space-y-2">
                {DENOMINACIONES.map((denom) => {
                  const stockActual = stockBilletes.find((b) => b.denominacion === denom)?.cantidad ?? 0
                  const qty = form.billetes[String(denom)] || 0
                  const insuficiente = qty > stockActual
                  return (
                    <div key={denom} className="flex items-center gap-3">
                      <span className="text-sm text-gray-300 w-24 text-right font-medium">
                        {formatCurrency(denom)}
                      </span>
                      <input
                        type="number"
                        min="0"
                        max={stockActual}
                        value={qty}
                        onChange={(e) => setBillete(denom, e.target.value)}
                        className={`w-20 bg-[#0f172a] border text-gray-100 rounded-md px-2 py-1 text-sm text-center focus:outline-none focus:ring-2 ${
                          insuficiente
                            ? 'border-rose-500/60 focus:ring-rose-400/40'
                            : 'border-gray-600/60 focus:ring-amber-400/40'
                        }`}
                      />
                      <span className="text-sm text-gray-400 w-28">
                        = {formatCurrency(denom * qty)}
                      </span>
                      <span className={`text-xs ${insuficiente ? 'text-rose-400' : 'text-gray-500'}`}>
                        (stock: {stockActual}{insuficiente && ` — falta ${qty - stockActual}`})
                      </span>
                    </div>
                  )
                })}
              </div>
              <div className={`mt-3 pt-3 border-t flex items-center justify-between text-sm ${
                importeNum > 0 ? (billetesOk ? 'border-emerald-500/40' : 'border-rose-500/40') : 'border-amber-500/30'
              }`}>
                <span className="font-medium text-gray-300">Total en billetes:</span>
                <span className={`font-bold ${
                  importeNum > 0
                    ? billetesOk ? 'text-emerald-400' : 'text-rose-400'
                    : 'text-gray-300'
                }`}>
                  {formatCurrency(totalBilletes)}
                  {importeNum > 0 && (billetesOk ? ' ✓' : ` (difiere ${formatCurrency(Math.abs(totalBilletes - importeNum))})`)}
                </span>
              </div>
            </div>
          )}

          <div>
            <label className="label">Notas</label>
            <textarea
              value={form.notas}
              onChange={(e) => set('notas', e.target.value)}
              rows={2}
              placeholder="Observaciones opcionales..."
              className="input-field resize-none"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || (form.forma_pago === 'efectivo' && importeNum > 0 && !billetesOk)}
              className="btn-primary flex-1 justify-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Registrando...' : 'Registrar retiro'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
