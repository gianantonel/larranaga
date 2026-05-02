import { useEffect, useState } from 'react'
import { DollarSign, CreditCard, Banknote, CheckCircle, AlertTriangle } from 'lucide-react'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { formatCurrency } from '../utils/helpers'
import {
  getClients, getProfesionales, getHonorarios,
  registrarCobro, getBilletesStock,
} from '../utils/api'

const DENOMINACIONES = [1000, 2000, 5000, 10000, 20000]

const today = () => new Date().toISOString().split('T')[0]

const emptyBilletes = () =>
  Object.fromEntries(DENOMINACIONES.map((d) => [String(d), 0]))

export default function RegistrarCobro() {
  const [clientes, setClientes] = useState([])
  const [profesionales, setProfesionales] = useState([])
  const [honorarios, setHonorarios] = useState([])
  const [stockBilletes, setStockBilletes] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(null)
  const [error, setError] = useState(null)

  const [form, setForm] = useState({
    cliente_id: '',
    honorario_id: '',
    importe: '',
    forma_pago: 'transferencia',
    profesional_destino_id: '',
    fecha: today(),
    fuente_pago: '',
    notas: '',
    billetes: emptyBilletes(),
  })

  useEffect(() => {
    Promise.all([
      getClients(),
      getProfesionales({ activo: true }),
      getBilletesStock(),
    ]).then(([c, p, b]) => {
      setClientes(c.data.filter((cl) => cl.is_active))
      setProfesionales(p.data)
      setStockBilletes(b.data.billetes || [])
    }).finally(() => setLoading(false))
  }, [])

  // Cuando cambia el cliente, cargar sus honorarios del mes actual
  useEffect(() => {
    if (!form.cliente_id) { setHonorarios([]); return }
    const periodo = today().slice(0, 7)
    getHonorarios({ client_id: form.cliente_id, period: periodo })
      .then((r) => setHonorarios(r.data))
      .catch(() => setHonorarios([]))
  }, [form.cliente_id])

  const set = (field, value) =>
    setForm((prev) => ({ ...prev, [field]: value }))

  const setBillete = (denom, value) =>
    setForm((prev) => ({
      ...prev,
      billetes: { ...prev.billetes, [String(denom)]: Math.max(0, parseInt(value) || 0) },
    }))

  // ── Cálculo de totales de billetes ─────────────────────────────────────────
  const totalBilletes = DENOMINACIONES.reduce(
    (acc, d) => acc + d * (form.billetes[String(d)] || 0),
    0
  )
  const importeNum = parseFloat(form.importe) || 0
  const billetesOk = Math.abs(totalBilletes - importeNum) <= 1

  // ── Submit ─────────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    if (!form.cliente_id || !form.importe || !form.forma_pago) {
      setError('Completá cliente, importe y forma de pago.')
      return
    }
    if (form.forma_pago === 'efectivo' && !billetesOk) {
      setError(`La suma de billetes ($${totalBilletes.toLocaleString('es-AR')}) no coincide con el importe ($${importeNum.toLocaleString('es-AR')}).`)
      return
    }

    const payload = {
      cliente_id: parseInt(form.cliente_id),
      importe: importeNum,
      forma_pago: form.forma_pago,
      fecha: form.fecha || today(),
      honorario_id: form.honorario_id ? parseInt(form.honorario_id) : null,
      profesional_destino_id: form.profesional_destino_id ? parseInt(form.profesional_destino_id) : null,
      fuente_pago: form.fuente_pago || null,
      notas: form.notas || null,
      billetes: form.forma_pago === 'efectivo'
        ? Object.fromEntries(
            Object.entries(form.billetes).filter(([, v]) => v > 0)
          )
        : null,
    }

    setSubmitting(true)
    try {
      const res = await registrarCobro(payload)
      const { pago, saldo_cc_actual } = res.data
      setSuccess({
        mensaje: `Cobro de ${formatCurrency(pago.importe)} registrado correctamente.`,
        saldo: saldo_cc_actual,
        clienteNombre: clientes.find((c) => c.id === pago.client_id)?.name || '',
      })
      // Reset form
      setForm({
        cliente_id: '',
        honorario_id: '',
        importe: '',
        forma_pago: 'transferencia',
        profesional_destino_id: '',
        fecha: today(),
        fuente_pago: '',
        notas: '',
        billetes: emptyBilletes(),
      })
      setHonorarios([])
    } catch (err) {
      const detail = err.response?.data?.detail
      if (typeof detail === 'object' && detail?.error) {
        setError(detail.error + (detail.diferencia ? ` (diferencia: $${Math.abs(detail.diferencia).toLocaleString('es-AR')})` : ''))
      } else {
        setError(typeof detail === 'string' ? detail : 'Error al registrar el cobro.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <LoadingSpinner />

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <PageHeader
        title="Registrar Cobro"
        subtitle="Registrá un pago de cliente. El impacto en cuenta corriente es automático."
        icon={DollarSign}
      />

      {/* Banner de éxito */}
      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle className="text-green-500 mt-0.5 shrink-0" size={20} />
          <div>
            <p className="font-medium text-green-800">{success.mensaje}</p>
            <p className="text-sm text-green-700 mt-1">
              Saldo CC de {success.clienteNombre}: <strong>{formatCurrency(success.saldo)}</strong>
            </p>
          </div>
        </div>
      )}

      {/* Banner de error */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertTriangle className="text-red-500 mt-0.5 shrink-0" size={20} />
          <p className="text-red-800">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">

        {/* Cliente */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Cliente *</label>
          <select
            value={form.cliente_id}
            onChange={(e) => { set('cliente_id', e.target.value); set('honorario_id', '') }}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">Seleccionar cliente...</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        {/* Honorario */}
        {honorarios.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Honorario del mes (opcional)</label>
            <select
              value={form.honorario_id}
              onChange={(e) => {
                set('honorario_id', e.target.value)
                const h = honorarios.find((h) => String(h.id) === e.target.value)
                if (h) set('importe', String(h.importe))
              }}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Sin honorario asociado</option>
              {honorarios.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.period} — {formatCurrency(h.importe)} ({h.tipo})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Importe y Fecha */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Importe *</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={form.importe}
              onChange={(e) => set('importe', e.target.value)}
              placeholder="0"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fecha *</label>
            <input
              type="date"
              value={form.fecha}
              onChange={(e) => set('fecha', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
        </div>

        {/* Forma de pago */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Forma de pago *</label>
          <div className="flex gap-3">
            {[
              { value: 'transferencia', label: 'Transferencia', icon: CreditCard },
              { value: 'efectivo', label: 'Efectivo', icon: Banknote },
            ].map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                type="button"
                onClick={() => set('forma_pago', value)}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg border-2 text-sm font-medium transition-colors ${
                  form.forma_pago === value
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                <Icon size={16} />
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Panel de billetes (solo efectivo) */}
        {form.forma_pago === 'efectivo' && (
          <div className="border border-amber-200 bg-amber-50 rounded-lg p-4">
            <p className="text-sm font-medium text-amber-800 mb-3">Detalle de billetes recibidos</p>
            <div className="space-y-2">
              {DENOMINACIONES.map((denom) => {
                const stockActual = stockBilletes.find((b) => b.denominacion === denom)?.cantidad ?? 0
                const qty = form.billetes[String(denom)] || 0
                return (
                  <div key={denom} className="flex items-center gap-3">
                    <span className="text-sm text-gray-700 w-24 text-right font-medium">
                      {formatCurrency(denom)}
                    </span>
                    <input
                      type="number"
                      min="0"
                      value={qty}
                      onChange={(e) => setBillete(denom, e.target.value)}
                      className="w-20 border border-gray-300 rounded-md px-2 py-1 text-sm text-center focus:outline-none focus:ring-2 focus:ring-amber-400"
                    />
                    <span className="text-sm text-gray-500 w-28">
                      = {formatCurrency(denom * qty)}
                    </span>
                    <span className="text-xs text-gray-400">
                      (stock actual: {stockActual})
                    </span>
                  </div>
                )
              })}
            </div>

            {/* Resumen billetes vs importe */}
            <div className={`mt-3 pt-3 border-t flex items-center justify-between text-sm ${
              importeNum > 0 ? (billetesOk ? 'border-green-300' : 'border-red-300') : 'border-amber-200'
            }`}>
              <span className="font-medium text-gray-700">Total en billetes:</span>
              <span className={`font-bold ${
                importeNum > 0
                  ? billetesOk ? 'text-green-600' : 'text-red-600'
                  : 'text-gray-600'
              }`}>
                {formatCurrency(totalBilletes)}
                {importeNum > 0 && (
                  billetesOk
                    ? ' ✓'
                    : ` (difiere $${Math.abs(totalBilletes - importeNum).toLocaleString('es-AR')})`
                )}
              </span>
            </div>
          </div>
        )}

        {/* Profesional destinatario */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Profesional destinatario</label>
          <select
            value={form.profesional_destino_id}
            onChange={(e) => set('profesional_destino_id', e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Sin asignar</option>
            {profesionales.map((p) => (
              <option key={p.id} value={p.id}>{p.nombre}</option>
            ))}
          </select>
        </div>

        {/* Fuente de pago */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Fuente del pago (empresa / persona)</label>
          <input
            type="text"
            value={form.fuente_pago}
            onChange={(e) => set('fuente_pago', e.target.value)}
            placeholder="Ej: Restaurante El Gaucho"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Notas */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Notas</label>
          <textarea
            value={form.notas}
            onChange={(e) => set('notas', e.target.value)}
            rows={2}
            placeholder="Observaciones opcionales..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={submitting || (form.forma_pago === 'efectivo' && importeNum > 0 && !billetesOk)}
          className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {submitting ? 'Registrando...' : 'Registrar cobro'}
        </button>
      </form>
    </div>
  )
}
