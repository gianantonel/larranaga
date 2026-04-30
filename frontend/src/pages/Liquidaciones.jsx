import { useEffect, useState } from 'react'
import { ChevronDown, ChevronRight, Lock, CheckCircle, AlertTriangle, X } from 'lucide-react'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { formatCurrency, formatDate } from '../utils/helpers'
import { getLiquidacionesPreviewAll, cerrarLiquidacion } from '../utils/api'
import { CalendarCheck } from 'lucide-react'

const todayPeriod = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

const MESES = [
  'Enero','Febrero','Marzo','Abril','Mayo','Junio',
  'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre',
]

function periodoLabel(periodo) {
  const [y, m] = periodo.split('-')
  return `${MESES[parseInt(m) - 1]} ${y}`
}

// ── Modal de cierre ────────────────────────────────────────────────────────────
function ModalCierre({ preview, onClose, onConfirm, loading }) {
  const [cobEfectivo, setCobEfectivo] = useState('')
  const [cobTransferencia, setCobTransferencia] = useState('')

  const cobTotal = (parseFloat(cobEfectivo) || 0) + (parseFloat(cobTransferencia) || 0)
  const saldoSiguiente = preview.total_a_cobrar - cobTotal

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-5 border-b">
          <h3 className="font-semibold text-gray-900">
            Cerrar período — {preview.profesional_nombre}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div className="bg-gray-50 rounded-lg p-3 text-sm space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-600">Total a cobrar:</span>
              <span className="font-semibold">{formatCurrency(preview.total_a_cobrar)}</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cobro en efectivo</label>
            <input
              type="number" min="0" step="0.01"
              value={cobEfectivo}
              onChange={(e) => setCobEfectivo(e.target.value)}
              placeholder="0"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cobro por transferencia</label>
            <input
              type="number" min="0" step="0.01"
              value={cobTransferencia}
              onChange={(e) => setCobTransferencia(e.target.value)}
              placeholder="0"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="bg-blue-50 rounded-lg p-3 text-sm space-y-1 border border-blue-100">
            <div className="flex justify-between">
              <span className="text-gray-600">Total cobrado:</span>
              <span className="font-medium">{formatCurrency(cobTotal)}</span>
            </div>
            <div className="flex justify-between font-semibold">
              <span className="text-gray-700">Saldo que arrastra al mes siguiente:</span>
              <span className={saldoSiguiente >= 0 ? 'text-blue-700' : 'text-red-600'}>
                {formatCurrency(saldoSiguiente)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex gap-3 p-5 border-t">
          <button
            onClick={onClose}
            className="flex-1 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={() => onConfirm(parseFloat(cobEfectivo) || 0, parseFloat(cobTransferencia) || 0)}
            disabled={loading}
            className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Cerrando...' : 'Confirmar cierre'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Fila de profesional ────────────────────────────────────────────────────────
function FilaProfesional({ preview, onCerrar }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <>
      <tr className="hover:bg-gray-50 border-b border-gray-100">
        <td className="py-3 px-4">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 text-sm font-medium text-gray-900"
          >
            {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            {preview.profesional_nombre}
          </button>
        </td>
        <td className="py-3 px-4 text-sm text-right text-gray-700">
          {formatCurrency(preview.honorarios_brutos)}
        </td>
        <td className="py-3 px-4 text-sm text-right text-amber-700">
          {formatCurrency(preview.adelantos_cobrados)}
        </td>
        <td className="py-3 px-4 text-sm text-right text-gray-500">
          {formatCurrency(preview.saldo_anterior)}
        </td>
        <td className="py-3 px-4 text-sm text-right text-green-700">
          {formatCurrency(preview.reintegros_total)}
        </td>
        <td className="py-3 px-4 text-sm text-right font-bold text-gray-900">
          {formatCurrency(preview.total_a_cobrar)}
        </td>
        <td className="py-3 px-4 text-center">
          {preview.cerrada ? (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-100 px-2 py-1 rounded-full">
              <CheckCircle size={12} /> CERRADO
            </span>
          ) : (
            <button
              onClick={() => onCerrar(preview)}
              className="inline-flex items-center gap-1 text-xs font-medium text-blue-700 bg-blue-100 px-2 py-1 rounded-full hover:bg-blue-200 transition-colors"
            >
              <Lock size={12} /> Cerrar
            </button>
          )}
        </td>
      </tr>

      {/* Detalle expandible */}
      {expanded && (
        <tr>
          <td colSpan={7} className="bg-gray-50 px-6 py-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">

              {/* Honorarios */}
              <div>
                <p className="font-medium text-gray-700 mb-2">Honorarios</p>
                {preview.detalle_honorarios.length === 0 ? (
                  <p className="text-gray-400 italic">Sin honorarios calculados</p>
                ) : (
                  <ul className="space-y-1">
                    {preview.detalle_honorarios.map((h) => (
                      <li key={h.honorario_id} className="flex justify-between text-gray-600">
                        <span>{h.cliente_nombre}</span>
                        <span className="font-medium">{formatCurrency(h.importe)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Adelantos */}
              <div>
                <p className="font-medium text-gray-700 mb-2">Adelantos cobrados</p>
                {preview.detalle_adelantos.length === 0 ? (
                  <p className="text-gray-400 italic">Sin adelantos</p>
                ) : (
                  <ul className="space-y-1">
                    {preview.detalle_adelantos.map((a) => (
                      <li key={a.pago_id} className="flex justify-between text-gray-600">
                        <span>{formatDate(a.fecha)} · {a.cliente_nombre}</span>
                        <span className="font-medium text-amber-700">{formatCurrency(a.importe)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Reintegros */}
              <div>
                <p className="font-medium text-gray-700 mb-2">Reintegros</p>
                {preview.detalle_reintegros.length === 0 ? (
                  <p className="text-gray-400 italic">Sin reintegros</p>
                ) : (
                  <ul className="space-y-1">
                    {preview.detalle_reintegros.map((r) => (
                      <li key={r.reintegro_id} className="flex justify-between text-gray-600">
                        <span>{r.concepto}</span>
                        <span className="font-medium text-green-700">{formatCurrency(r.importe)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

// ── Página principal ───────────────────────────────────────────────────────────
export default function Liquidaciones() {
  const [periodo, setPeriodo] = useState(todayPeriod())
  const [previews, setPreviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [modalData, setModalData] = useState(null)
  const [cerrando, setCerrando] = useState(false)
  const [successMsg, setSuccessMsg] = useState(null)

  const cargar = (p) => {
    setLoading(true)
    setError(null)
    getLiquidacionesPreviewAll(p)
      .then((r) => setPreviews(r.data))
      .catch(() => setError('No se pudo cargar las liquidaciones.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { cargar(periodo) }, [periodo])

  const handleCerrar = async (cobEfectivo, cobTransferencia) => {
    setCerrando(true)
    try {
      await cerrarLiquidacion(modalData.profesional_id, periodo, {
        cobro_efectivo: cobEfectivo,
        cobro_transferencia: cobTransferencia,
      })
      setSuccessMsg(`Liquidación de ${modalData.profesional_nombre} cerrada correctamente.`)
      setModalData(null)
      cargar(periodo)
    } catch {
      setError('No se pudo cerrar la liquidación.')
    } finally {
      setCerrando(false)
    }
  }

  // Totales pie de tabla
  const totales = previews.reduce(
    (acc, p) => ({
      honorarios_brutos: acc.honorarios_brutos + p.honorarios_brutos,
      adelantos_cobrados: acc.adelantos_cobrados + p.adelantos_cobrados,
      saldo_anterior: acc.saldo_anterior + p.saldo_anterior,
      reintegros_total: acc.reintegros_total + p.reintegros_total,
      total_a_cobrar: acc.total_a_cobrar + p.total_a_cobrar,
    }),
    { honorarios_brutos: 0, adelantos_cobrados: 0, saldo_anterior: 0, reintegros_total: 0, total_a_cobrar: 0 }
  )

  // Selector de período
  const years = [2025, 2026, 2027]
  const periodoOptions = years.flatMap((y) =>
    Array.from({ length: 12 }, (_, i) => {
      const m = String(i + 1).padStart(2, '0')
      return { value: `${y}-${m}`, label: `${MESES[i]} ${y}` }
    })
  )

  return (
    <div className="p-6">
      <PageHeader
        title="Liquidaciones del mes"
        subtitle="Resumen de honorarios, adelantos y total a cobrar por profesional."
        icon={CalendarCheck}
      />

      {/* Selector de período */}
      <div className="flex items-center gap-3 mb-6">
        <label className="text-sm font-medium text-gray-700">Período:</label>
        <select
          value={periodo}
          onChange={(e) => setPeriodo(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {periodoOptions.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <span className="text-sm text-gray-500 font-medium">{periodoLabel(periodo)}</span>
      </div>

      {/* Mensajes */}
      {successMsg && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-sm text-green-800">
          <CheckCircle size={16} /> {successMsg}
          <button onClick={() => setSuccessMsg(null)} className="ml-auto"><X size={14} /></button>
        </div>
      )}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-800">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase tracking-wide">Profesional</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 uppercase tracking-wide">Hon. Brutos</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-amber-600 uppercase tracking-wide">Adelantos</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide">Saldo Ant.</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-green-600 uppercase tracking-wide">Reintegros</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-900 uppercase tracking-wide">Total a Cobrar</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-gray-600 uppercase tracking-wide">Estado</th>
              </tr>
            </thead>
            <tbody>
              {previews.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-gray-400 text-sm">
                    No hay profesionales activos.
                  </td>
                </tr>
              ) : (
                previews.map((p) => (
                  <FilaProfesional
                    key={p.profesional_id}
                    preview={p}
                    onCerrar={setModalData}
                  />
                ))
              )}
            </tbody>
            {previews.length > 0 && (
              <tfoot className="bg-gray-50 border-t-2 border-gray-300">
                <tr>
                  <td className="py-3 px-4 text-sm font-bold text-gray-700">TOTALES</td>
                  <td className="py-3 px-4 text-sm font-bold text-right">{formatCurrency(totales.honorarios_brutos)}</td>
                  <td className="py-3 px-4 text-sm font-bold text-right text-amber-700">{formatCurrency(totales.adelantos_cobrados)}</td>
                  <td className="py-3 px-4 text-sm font-bold text-right text-gray-500">{formatCurrency(totales.saldo_anterior)}</td>
                  <td className="py-3 px-4 text-sm font-bold text-right text-green-700">{formatCurrency(totales.reintegros_total)}</td>
                  <td className="py-3 px-4 text-sm font-bold text-right text-gray-900">{formatCurrency(totales.total_a_cobrar)}</td>
                  <td />
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      )}

      {/* Modal de cierre */}
      {modalData && (
        <ModalCierre
          preview={modalData}
          onClose={() => setModalData(null)}
          onConfirm={handleCerrar}
          loading={cerrando}
        />
      )}
    </div>
  )
}
