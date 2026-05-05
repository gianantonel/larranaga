import { useEffect, useState } from 'react'
import {
  TrendingUp, Calendar, CalendarRange, Filter, Download,
  AlertTriangle, ChevronRight, ChevronLeft,
} from 'lucide-react'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { formatCurrency } from '../utils/helpers'
import {
  getFlujoFondosMensual, getFlujoFondosAnual, getProfesionales,
  verificarConsistenciaFlujo,
} from '../utils/api'

const MESES_CORTO = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
const todayPeriodo = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

// Coloreo de saldo: rojo si cliente debe (>0), verde si saldo a favor (<0), gris si 0
const claseDeuda = (deuda) => {
  if (Math.abs(deuda) < 0.01) return 'text-gray-400'
  return deuda > 0 ? 'text-rose-400' : 'text-emerald-400'
}

const fmtDeuda = (deuda) => {
  if (Math.abs(deuda) < 0.01) return formatCurrency(0)
  return deuda > 0 ? formatCurrency(deuda) : `+${formatCurrency(-deuda)}`
}


export default function FlujoDeFondos() {
  const [modo, setModo] = useState('mensual')
  const [periodo, setPeriodo] = useState(todayPeriodo())
  const [year, setYear] = useState(new Date().getFullYear())
  const [profesionalId, setProfesionalId] = useState('')

  const [profesionales, setProfesionales] = useState([])
  const [data, setData] = useState(null)
  const [consistencia, setConsistencia] = useState(null)
  const [showInconsistencias, setShowInconsistencias] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    getProfesionales({ activo: true }).then((r) => setProfesionales(r.data))
  }, [])

  useEffect(() => {
    setLoading(true)
    setError(null)
    setShowInconsistencias(false)
    const p = profesionalId ? parseInt(profesionalId) : null
    const promise = modo === 'mensual'
      ? getFlujoFondosMensual(periodo, p)
      : getFlujoFondosAnual(year, p)
    promise
      .then((r) => setData(r.data))
      .catch((e) => {
        const detail = e.response?.data?.detail
        setError(typeof detail === 'string' ? detail : 'Error al cargar el flujo de fondos')
        setData(null)
      })
      .finally(() => setLoading(false))

    // Hook de consistencia (sólo en vista mensual)
    if (modo === 'mensual') {
      verificarConsistenciaFlujo(periodo)
        .then((r) => setConsistencia(r.data))
        .catch(() => setConsistencia(null))
    } else {
      setConsistencia(null)
    }
  }, [modo, periodo, year, profesionalId])

  const exportarCSV = () => {
    if (!data) return
    let csv, filename
    if (modo === 'mensual') {
      csv = 'Cliente,Deuda inicio,Devengado,Cobrado,Deuda fin\n'
      data.rows.forEach((r) => {
        csv += `"${r.cliente_nombre}",${r.deuda_inicio},${r.honorario_devengado},${r.cobrado},${r.deuda_fin}\n`
      })
      csv += `"TOTAL",${data.total.deuda_inicio},${data.total.honorario_devengado},${data.total.cobrado},${data.total.deuda_fin}\n`
      filename = `flujo_fondos_${periodo}.csv`
    } else {
      const headerMeses = MESES_CORTO.flatMap((m) => [`${m} dev`, `${m} cob`, `${m} fin`]).join(',')
      csv = `Cliente,${headerMeses},Total devengado,Total cobrado,Deuda fin (dic)\n`
      data.rows.forEach((r) => {
        const celdas = r.meses.flatMap((c) => [c.devengado, c.cobrado, c.deuda_fin]).join(',')
        csv += `"${r.cliente_nombre}",${celdas},${r.total_devengado},${r.total_cobrado},${r.deuda_fin}\n`
      })
      const totCeldas = data.total.meses.flatMap((c) => [c.devengado, c.cobrado, c.deuda_fin]).join(',')
      csv += `"TOTAL",${totCeldas},${data.total.total_devengado},${data.total.total_cobrado},\n`
      filename = `flujo_fondos_anual_${year}.csv`
    }
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      <PageHeader
        title="Flujo de Fondos"
        subtitle="Devengado vs cobrado por cliente y mes. Reemplaza el Excel del estudio."
      >
        <button onClick={exportarCSV} disabled={!data || loading} className="btn-secondary disabled:opacity-50">
          <Download size={16} />
          Exportar CSV
        </button>
      </PageHeader>

      {/* Controles */}
      <div className="card mb-4">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          <div className="md:col-span-3">
            <label className="label">Vista</label>
            <div className="flex gap-2">
              {[
                { value: 'mensual', label: 'Mensual', icon: Calendar },
                { value: 'anual', label: 'Anual', icon: CalendarRange },
              ].map(({ value, label, icon: Icon }) => (
                <button
                  key={value}
                  onClick={() => setModo(value)}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-lg border text-sm font-medium transition-all ${
                    modo === value
                      ? 'border-violet-500/60 bg-violet-600/20 text-violet-300'
                      : 'border-gray-700/50 bg-[#0f172a] text-gray-400 hover:border-gray-600'
                  }`}
                >
                  <Icon size={14} />
                  {label}
                </button>
              ))}
            </div>
          </div>

          {modo === 'mensual' ? (
            <div className="md:col-span-4">
              <label className="label">Período (mes)</label>
              <div className="flex gap-1.5">
                <button onClick={() => setPeriodo(prevMes(periodo))} className="shrink-0 px-2.5 rounded-lg border border-gray-700/50 bg-[#0f172a] text-gray-400 hover:text-violet-300 hover:border-violet-500/40 transition-colors flex items-center justify-center" aria-label="Mes anterior"><ChevronLeft size={16} /></button>
                <input
                  type="month"
                  value={periodo}
                  onChange={(e) => setPeriodo(e.target.value)}
                  className="input-field min-w-0 flex-1"
                />
                <button onClick={() => setPeriodo(nextMes(periodo))} className="shrink-0 px-2.5 rounded-lg border border-gray-700/50 bg-[#0f172a] text-gray-400 hover:text-violet-300 hover:border-violet-500/40 transition-colors flex items-center justify-center" aria-label="Mes siguiente"><ChevronRight size={16} /></button>
              </div>
            </div>
          ) : (
            <div className="md:col-span-4">
              <label className="label">Año</label>
              <div className="flex gap-1.5">
                <button onClick={() => setYear(year - 1)} className="shrink-0 px-2.5 rounded-lg border border-gray-700/50 bg-[#0f172a] text-gray-400 hover:text-violet-300 hover:border-violet-500/40 transition-colors flex items-center justify-center" aria-label="Año anterior"><ChevronLeft size={16} /></button>
                <input
                  type="number"
                  min="1900"
                  max="2100"
                  value={year}
                  onChange={(e) => setYear(parseInt(e.target.value) || year)}
                  className="input-field min-w-0 flex-1 text-center"
                />
                <button onClick={() => setYear(year + 1)} className="shrink-0 px-2.5 rounded-lg border border-gray-700/50 bg-[#0f172a] text-gray-400 hover:text-violet-300 hover:border-violet-500/40 transition-colors flex items-center justify-center" aria-label="Año siguiente"><ChevronRight size={16} /></button>
              </div>
            </div>
          )}

          <div className="md:col-span-3">
            <label className="label">Profesional</label>
            <select
              value={profesionalId}
              onChange={(e) => setProfesionalId(e.target.value)}
              className="input-field"
            >
              <option value="">Todos</option>
              {profesionales.map((p) => (
                <option key={p.id} value={p.id}>{p.nombre}</option>
              ))}
            </select>
          </div>

          <div className="md:col-span-2">
            <button
              onClick={() => { setProfesionalId(''); setPeriodo(todayPeriodo()); setYear(new Date().getFullYear()) }}
              className="btn-secondary w-full justify-center"
            >
              <Filter size={14} />
              Reset
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-start gap-3">
          <AlertTriangle className="text-rose-400 mt-0.5 shrink-0" size={20} />
          <p className="text-rose-300">{error}</p>
        </div>
      )}

      {consistencia && !consistencia.ok && (
        <div className="mb-4 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertTriangle className="text-amber-400 mt-0.5 shrink-0" size={20} />
            <div className="flex-1">
              <p className="font-medium text-amber-300">
                {consistencia.n_inconsistencias} cliente{consistencia.n_inconsistencias !== 1 && 's'} con inconsistencia entre Cuenta Corriente y Flujo de Fondos
              </p>
              <p className="text-sm text-amber-300/70 mt-1">
                La deuda calculada (deuda inicial + devengado − cobrado) no coincide con el saldo de CC al cierre del período. Revisá honorarios sin imputar a CC o pagos no registrados.
              </p>
              <button
                onClick={() => setShowInconsistencias((s) => !s)}
                className="mt-2 text-xs font-medium text-amber-200 hover:text-amber-100 underline underline-offset-2"
              >
                {showInconsistencias ? 'Ocultar detalle' : `Ver detalle (${consistencia.n_inconsistencias})`}
              </button>
            </div>
          </div>
          {showInconsistencias && (
            <div className="mt-4 max-h-72 overflow-y-auto border border-amber-500/20 rounded">
              <table className="w-full text-xs">
                <thead className="bg-amber-500/10">
                  <tr>
                    <th className="text-left px-3 py-2 text-amber-200">Cliente</th>
                    <th className="text-right px-3 py-2 text-amber-200">Devengado</th>
                    <th className="text-right px-3 py-2 text-amber-200">Cobrado</th>
                    <th className="text-right px-3 py-2 text-amber-200">Calculado</th>
                    <th className="text-right px-3 py-2 text-amber-200">Real CC</th>
                    <th className="text-right px-3 py-2 text-amber-200">Diferencia</th>
                  </tr>
                </thead>
                <tbody>
                  {consistencia.inconsistencias.map((i) => (
                    <tr key={i.cliente_id} className="border-t border-amber-500/10">
                      <td className="px-3 py-1.5 text-gray-300">{i.cliente_nombre}</td>
                      <td className="px-3 py-1.5 text-right text-gray-400">{formatCurrency(i.devengado)}</td>
                      <td className="px-3 py-1.5 text-right text-gray-400">{formatCurrency(i.cobrado)}</td>
                      <td className="px-3 py-1.5 text-right text-gray-300">{formatCurrency(i.deuda_fin_calculada)}</td>
                      <td className="px-3 py-1.5 text-right text-gray-300">{formatCurrency(i.deuda_fin_real)}</td>
                      <td className="px-3 py-1.5 text-right font-semibold text-amber-300">{formatCurrency(i.diferencia)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {loading && <div className="card"><LoadingSpinner /></div>}

      {!loading && !error && data && (
        data.year !== undefined
          ? <TablaAnual data={data} />
          : <TablaMensual data={data} />
      )}
    </div>
  )
}


function TablaMensual({ data }) {
  return (
    <div className="card overflow-hidden p-0">
      <div className="px-5 py-3 border-b border-gray-700/40 flex items-center gap-2">
        <TrendingUp size={16} className="text-violet-400" />
        <h2 className="font-semibold text-white">Período {data.periodo}</h2>
        <span className="ml-auto text-sm text-gray-400">{data.rows.length} cliente{data.rows.length !== 1 && 's'}</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="table-header border-b border-gray-700/40">
              <th className="text-left px-4 py-3">Cliente</th>
              <th className="text-right px-4 py-3">Deuda inicio</th>
              <th className="text-right px-4 py-3">Devengado</th>
              <th className="text-right px-4 py-3">Cobrado</th>
              <th className="text-right px-4 py-3">Deuda fin</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r) => (
              <tr key={r.cliente_id} className="table-row border-b border-gray-700/20 last:border-0">
                <td className="px-4 py-2.5 text-gray-200">{r.cliente_nombre}</td>
                <td className={`px-4 py-2.5 text-right whitespace-nowrap ${claseDeuda(r.deuda_inicio)}`}>{fmtDeuda(r.deuda_inicio)}</td>
                <td className="px-4 py-2.5 text-right text-gray-300 whitespace-nowrap">{formatCurrency(r.honorario_devengado)}</td>
                <td className="px-4 py-2.5 text-right text-emerald-300/90 whitespace-nowrap">{formatCurrency(r.cobrado)}</td>
                <td className={`px-4 py-2.5 text-right font-semibold whitespace-nowrap ${claseDeuda(r.deuda_fin)}`}>{fmtDeuda(r.deuda_fin)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="bg-violet-500/10 border-t border-violet-500/30 font-semibold">
              <td className="px-4 py-3 text-violet-300">TOTAL</td>
              <td className={`px-4 py-3 text-right ${claseDeuda(data.total.deuda_inicio)}`}>{fmtDeuda(data.total.deuda_inicio)}</td>
              <td className="px-4 py-3 text-right text-violet-200">{formatCurrency(data.total.honorario_devengado)}</td>
              <td className="px-4 py-3 text-right text-emerald-300">{formatCurrency(data.total.cobrado)}</td>
              <td className={`px-4 py-3 text-right ${claseDeuda(data.total.deuda_fin)}`}>{fmtDeuda(data.total.deuda_fin)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}


function TablaAnual({ data }) {
  return (
    <div className="card overflow-hidden p-0">
      <div className="px-5 py-3 border-b border-gray-700/40 flex items-center gap-2">
        <CalendarRange size={16} className="text-violet-400" />
        <h2 className="font-semibold text-white">Año {data.year}</h2>
        <span className="ml-auto text-sm text-gray-400">{data.rows.length} cliente{data.rows.length !== 1 && 's'}</span>
      </div>
      <div className="overflow-x-auto">
        <table className="text-xs">
          <thead>
            <tr className="table-header border-b border-gray-700/40">
              <th className="text-left px-3 py-2.5 sticky left-0 bg-[#1e293b] z-10 min-w-[180px]">Cliente</th>
              {MESES_CORTO.map((m) => (
                <th key={m} className="text-center px-2 py-2.5 min-w-[110px]">{m}</th>
              ))}
              <th className="text-right px-3 py-2.5 min-w-[110px]">Total dev</th>
              <th className="text-right px-3 py-2.5 min-w-[110px]">Total cob</th>
              <th className="text-right px-3 py-2.5 min-w-[110px]">Deuda fin</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r) => (
              <tr key={r.cliente_id} className="table-row border-b border-gray-700/20 last:border-0">
                <td className="px-3 py-2 text-gray-200 sticky left-0 bg-[#1a2332] z-10 font-medium">{r.cliente_nombre}</td>
                {r.meses.map((c, i) => <CeldaAnual key={i} c={c} />)}
                <td className="px-3 py-2 text-right text-gray-300 whitespace-nowrap">{formatCurrency(r.total_devengado)}</td>
                <td className="px-3 py-2 text-right text-emerald-300/90 whitespace-nowrap">{formatCurrency(r.total_cobrado)}</td>
                <td className={`px-3 py-2 text-right font-semibold whitespace-nowrap ${claseDeuda(r.deuda_fin)}`}>{fmtDeuda(r.deuda_fin)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="bg-violet-500/10 border-t border-violet-500/30 font-semibold">
              <td className="px-3 py-3 text-violet-300 sticky left-0 bg-[#211a36] z-10">TOTAL</td>
              {data.total.meses.map((c, i) => <CeldaAnual key={i} c={c} resaltado />)}
              <td className="px-3 py-3 text-right text-violet-200 whitespace-nowrap">{formatCurrency(data.total.total_devengado)}</td>
              <td className="px-3 py-3 text-right text-emerald-300 whitespace-nowrap">{formatCurrency(data.total.total_cobrado)}</td>
              <td className="px-3 py-3 text-right text-gray-400">—</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}


function CeldaAnual({ c, resaltado = false }) {
  const isEmpty = c.devengado === 0 && c.cobrado === 0 && Math.abs(c.deuda_fin) < 0.01
  if (isEmpty) {
    return <td className="px-2 py-2 text-center text-gray-600">—</td>
  }
  return (
    <td className={`px-2 py-2 text-right text-[11px] leading-tight whitespace-nowrap ${resaltado ? 'text-violet-200' : ''}`}>
      <div className="text-gray-300">D: {formatCurrency(c.devengado)}</div>
      <div className="text-emerald-300/90">C: {formatCurrency(c.cobrado)}</div>
      <div className={claseDeuda(c.deuda_fin)}>{fmtDeuda(c.deuda_fin)}</div>
    </td>
  )
}


// Utils para nav de meses
function prevMes(periodo) {
  const [y, m] = periodo.split('-').map(Number)
  if (m === 1) return `${y - 1}-12`
  return `${y}-${String(m - 1).padStart(2, '0')}`
}
function nextMes(periodo) {
  const [y, m] = periodo.split('-').map(Number)
  if (m === 12) return `${y + 1}-01`
  return `${y}-${String(m + 1).padStart(2, '0')}`
}
