import { useEffect, useState } from 'react'
import { ChevronDown, ChevronRight, Lock, CheckCircle, AlertTriangle, X, CalendarCheck } from 'lucide-react'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { formatCurrency, formatDate } from '../utils/helpers'
import { getLiquidacionesPreviewAll, cerrarLiquidacion } from '../utils/api'

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

function ModalCierre({ preview, onClose, onConfirm, loading }) {
  const [cobEfectivo, setCobEfectivo] = useState('')
  const [cobTransferencia, setCobTransferencia] = useState('')

  const cobTotal = (parseFloat(cobEfectivo) || 0) + (parseFloat(cobTransferencia) || 0)
  const saldoSiguiente = preview.total_a_cobrar - cobTotal

  return (
    <div className="modal-backdrop">
      <div className="modal-panel max-w-md">
        <div className="flex items-center justify-between p-5 border-b border-gray-700/50">
          <h3 className="font-semibold text-gray-100">
            Cerrar período — {preview.profesional_nombre}
          </h3>
          <button onClick={onClose} className="btn-icon">
            <X size={20} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div className="bg-[#0f172a]/70 border border-gray-700/40 rounded-lg p-3 text-sm space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-400">Total a cobrar:</span>
              <span className="font-semibold text-gray-100">{formatCurrency(preview.total_a_cobrar)}</span>
            </div>
          </div>

          <div>
            <label className="label">Cobro en efectivo</label>
            <input
              type="number" min="0" step="0.01"
              value={cobEfectivo}
              onChange={(e) => setCobEfectivo(e.target.value)}
              placeholder="0"
              className="input-field"
            />
          </div>

          <div>
            <label className="label">Cobro por transferencia</label>
            <input
              type="number" min="0" step="0.01"
              value={cobTransferencia}
              onChange={(e) => setCobTransferencia(e.target.value)}
              placeholder="0"
              className="input-field"
            />
          </div>

          <div className="bg-violet-500/10 rounded-lg p-3 text-sm space-y-1 border border-violet-500/30">
            <div className="flex justify-between">
              <span className="text-gray-400">Total cobrado:</span>
              <span className="font-medium text-gray-200">{formatCurrency(cobTotal)}</span>
            </div>
            <div className="flex justify-between font-semibold">
              <span className="text-gray-300">Saldo que arrastra al mes siguiente:</span>
              <span className={saldoSiguiente >= 0 ? 'text-violet-300' : 'text-rose-400'}>
                {formatCurrency(saldoSiguiente)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex gap-3 p-5 border-t border-gray-700/50">
          <button onClick={onClose} className="btn-secondary flex-1 justify-center">
            Cancelar
          </button>
          <button
            onClick={() => onConfirm(parseFloat(cobEfectivo) || 0, parseFloat(cobTransferencia) || 0)}
            disabled={loading}
            className="btn-primary flex-1 justify-center disabled:opacity-50"
          >
            {loading ? 'Cerrando...' : 'Confirmar cierre'}
          </button>
        </div>
      </div>
    </div>
  )
}

function FilaProfesional({ preview, onCerrar }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <>
      <tr className="table-row">
        <td className="table-cell">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 text-sm font-medium text-gray-100"
          >
            {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            {preview.profesional_nombre}
          </button>
        </td>
        <td className="table-cell text-right">
          {formatCurrency(preview.honorarios_brutos)}
        </td>
        <td className="table-cell text-right text-amber-400">
          {formatCurrency(preview.adelantos_cobrados)}
        </td>
        <td className="table-cell text-right text-gray-500">
          {formatCurrency(preview.saldo_anterior)}
        </td>
        <td className="table-cell text-right text-emerald-400">
          {formatCurrency(preview.reintegros_total)}
        </td>
        <td className="table-cell text-right font-bold text-gray-100">
          {formatCurrency(preview.total_a_cobrar)}
        </td>
        <td className="table-cell text-center">
          {preview.cerrada ? (
            <span className="badge-green">
              <CheckCircle size={12} /> CERRADO
            </span>
          ) : (
            <button onClick={() => onCerrar(preview)} className="badge-purple hover:bg-violet-500/25 transition">
              <Lock size={12} /> Cerrar
            </button>
          )}
        </td>
      </tr>

      {expanded && (
        <tr>
          <td colSpan={7} className="bg-[#0f172a]/50 px-6 py-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">

              <div>
                <p className="font-medium text-gray-300 mb-2">Honorarios</p>
                {preview.detalle_honorarios.length === 0 ? (
                  <p className="text-gray-500 italic">Sin honorarios calculados</p>
                ) : (
                  <ul className="space-y-1">
                    {preview.detalle_honorarios.map((h) => (
                      <li key={h.honorario_id} className="flex justify-between text-gray-400">
                        <span>{h.cliente_nombre}</span>
                        <span className="font-medium text-gray-200">{formatCurrency(h.importe)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div>
                <p className="font-medium text-gray-300 mb-2">Adelantos cobrados</p>
                {preview.detalle_adelantos.length === 0 ? (
                  <p className="text-gray-500 italic">Sin adelantos</p>
                ) : (
                  <ul className="space-y-1">
                    {preview.detalle_adelantos.map((a) => (
                      <li key={a.pago_id} className="flex justify-between text-gray-400">
                        <span>{formatDate(a.fecha)} · {a.cliente_nombre}</span>
                        <span className="font-medium text-amber-400">{formatCurrency(a.importe)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div>
                <p className="font-medium text-gray-300 mb-2">Reintegros</p>
                {preview.detalle_reintegros.length === 0 ? (
                  <p className="text-gray-500 italic">Sin reintegros</p>
                ) : (
                  <ul className="space-y-1">
                    {preview.detalle_reintegros.map((r) => (
                      <li key={r.reintegro_id} className="flex justify-between text-gray-400">
                        <span>{r.concepto}</span>
                        <span className="font-medium text-emerald-400">{formatCurrency(r.importe)}</span>
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

      <div className="flex items-center gap-3 mb-6">
        <label className="text-sm font-medium text-gray-300">Período:</label>
        <select
          value={periodo}
          onChange={(e) => setPeriodo(e.target.value)}
          className="input-field max-w-xs"
        >
          {periodoOptions.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <span className="text-sm text-gray-500 font-medium">{periodoLabel(periodo)}</span>
      </div>

      {successMsg && (
        <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center gap-2 text-sm text-emerald-300">
          <CheckCircle size={16} /> {successMsg}
          <button onClick={() => setSuccessMsg(null)} className="ml-auto"><X size={14} /></button>
        </div>
      )}
      {error && (
        <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-center gap-2 text-sm text-rose-300">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead className="bg-[#0f172a]/60 border-b border-gray-700/50">
              <tr>
                <th className="table-header">Profesional</th>
                <th className="table-header text-right">Hon. Brutos</th>
                <th className="table-header text-right text-amber-400">Adelantos</th>
                <th className="table-header text-right">Saldo Ant.</th>
                <th className="table-header text-right text-emerald-400">Reintegros</th>
                <th className="table-header text-right text-violet-300">Total a Cobrar</th>
                <th className="table-header text-center">Estado</th>
              </tr>
            </thead>
            <tbody>
              {previews.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-gray-500 text-sm">
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
              <tfoot className="bg-[#0f172a]/60 border-t-2 border-gray-700/60">
                <tr>
                  <td className="table-cell font-bold text-gray-300">TOTALES</td>
                  <td className="table-cell font-bold text-right text-gray-100">{formatCurrency(totales.honorarios_brutos)}</td>
                  <td className="table-cell font-bold text-right text-amber-400">{formatCurrency(totales.adelantos_cobrados)}</td>
                  <td className="table-cell font-bold text-right text-gray-400">{formatCurrency(totales.saldo_anterior)}</td>
                  <td className="table-cell font-bold text-right text-emerald-400">{formatCurrency(totales.reintegros_total)}</td>
                  <td className="table-cell font-bold text-right text-violet-300">{formatCurrency(totales.total_a_cobrar)}</td>
                  <td />
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      )}

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
