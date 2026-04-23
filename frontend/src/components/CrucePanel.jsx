import { useState } from 'react'
import { GitMerge, Download, Loader2, CheckCircle, XCircle, MinusCircle } from 'lucide-react'
import { syncComprobantes, getCruce, exportHolistor } from '../utils/api'
import { formatCurrency, formatDate } from '../utils/helpers'

const SCORE_CONFIG = {
  exact:  { label: 'Exacto',    icon: CheckCircle,  cls: 'text-emerald-400' },
  approx: { label: 'Aproximado', icon: CheckCircle, cls: 'text-amber-400' },
  none:   { label: 'Sin match', icon: XCircle,       cls: 'text-rose-400' },
}

export default function CrucePanel({ clientId, period }) {
  const [syncing, setSyncing] = useState(false)
  const [crucing, setCrucing] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [cruce, setCruce] = useState(null)
  const [error, setError] = useState('')
  const [step, setStep] = useState('')

  const handleCruce = async () => {
    if (!clientId || !period) return
    setError('')
    setCruce(null)

    // Step 1: sync comprobantes
    setSyncing(true)
    setStep('Descargando comprobantes de ARCA…')
    try {
      await syncComprobantes({ client_id: Number(clientId), period })
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al descargar comprobantes')
      setSyncing(false); setStep(''); return
    }
    setSyncing(false)

    // Step 2: run cruce
    setCrucing(true)
    setStep('Cruzando retenciones ↔ comprobantes…')
    try {
      const res = await getCruce(Number(clientId), period)
      setCruce(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al cruzar datos')
    } finally {
      setCrucing(false); setStep('')
    }
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      const res = await exportHolistor(Number(clientId), period)
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `holistor_${clientId}_${period}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError('Error al exportar CSV')
    } finally {
      setExporting(false)
    }
  }

  const isLoading = syncing || crucing

  return (
    <div className="space-y-4">
      {/* Header + action */}
      <div className="card p-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <GitMerge size={16} className="text-violet-400" />
              Cruce Retenciones ↔ Comprobantes
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">
              Descarga Mis Comprobantes Recibidos y cruza con las retenciones por CUIT emisor y fecha.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleCruce}
              disabled={isLoading || !clientId || !period}
              className="btn-primary flex items-center gap-2 text-sm"
            >
              {isLoading
                ? <Loader2 size={15} className="animate-spin" />
                : <GitMerge size={15} />}
              {isLoading ? step : 'Cruzar ARCA'}
            </button>
            {cruce && (
              <button
                onClick={handleExport}
                disabled={exporting}
                className="btn-secondary flex items-center gap-2 text-sm"
              >
                {exporting
                  ? <Loader2 size={15} className="animate-spin" />
                  : <Download size={15} />}
                CSV Holistor
              </button>
            )}
          </div>
        </div>
        {error && (
          <div className="mt-3 p-2 rounded-lg bg-rose-500/10 border border-rose-500/40 text-rose-300 text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {cruce && (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-3 gap-3">
            <div className="card p-3 text-center">
              <p className="text-2xl font-bold text-white">{cruce.total_retenciones}</p>
              <p className="text-xs text-gray-400 mt-0.5">Retenciones</p>
            </div>
            <div className="card p-3 text-center border-emerald-500/30">
              <p className="text-2xl font-bold text-emerald-400">{cruce.matched}</p>
              <p className="text-xs text-gray-400 mt-0.5">Cruzadas</p>
            </div>
            <div className="card p-3 text-center border-rose-500/30">
              <p className="text-2xl font-bold text-rose-400">{cruce.unmatched}</p>
              <p className="text-xs text-gray-400 mt-0.5">Sin cruce</p>
            </div>
          </div>

          {/* Table */}
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-700/40">
              <h4 className="text-sm font-semibold text-white">Detalle por retención</h4>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-white/3 text-xs text-gray-400 uppercase">
                  <tr>
                    <th className="px-3 py-2 text-left">Match</th>
                    <th className="px-3 py-2 text-left">Fecha Ret.</th>
                    <th className="px-3 py-2 text-left">CUIT Agente</th>
                    <th className="px-3 py-2 text-right">Importe Ret.</th>
                    <th className="px-3 py-2 text-center">Cód. Holistor</th>
                    <th className="px-3 py-2 text-left">Cbte. cruzado</th>
                    <th className="px-3 py-2 text-left">Emisor</th>
                    <th className="px-3 py-2 text-right">Otros Tributos Cbte.</th>
                  </tr>
                </thead>
                <tbody>
                  {cruce.items.map((item, i) => {
                    const sc = SCORE_CONFIG[item.match_score] || SCORE_CONFIG.none
                    const Icon = sc.icon
                    return (
                      <tr key={i} className="border-t border-gray-700/30 hover:bg-white/3">
                        <td className="px-3 py-2">
                          <span className={`flex items-center gap-1 text-xs ${sc.cls}`}>
                            <Icon size={13} />
                            {sc.label}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-gray-200">{formatDate(item.fecha_retencion)}</td>
                        <td className="px-3 py-2 text-gray-300 font-mono text-xs">{item.cuit_agente || '—'}</td>
                        <td className="px-3 py-2 text-right font-medium text-gray-100">
                          {formatCurrency(item.importe_retencion)}
                        </td>
                        <td className="px-3 py-2 text-center">
                          {item.codigo_holistor && (
                            <span className="inline-block px-2 py-0.5 rounded border border-violet-500/40 bg-violet-500/20 text-violet-300 text-xs">
                              {item.codigo_holistor}
                            </span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-gray-400 text-xs">
                          {item.comprobante_id
                            ? `${item.tipo_comprobante || ''} ${item.numero_desde || ''} (${formatDate(item.fecha_emision)})`
                            : <span className="text-rose-400/70">—</span>}
                        </td>
                        <td className="px-3 py-2 text-gray-400 text-xs truncate max-w-[180px]">
                          {item.denominacion_receptor || '—'}
                        </td>
                        <td className="px-3 py-2 text-right text-gray-300">
                          {item.otros_tributos_comprobante != null
                            ? formatCurrency(item.otros_tributos_comprobante)
                            : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {cruce.unmatched > 0 && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
              <MinusCircle size={14} className="shrink-0 mt-0.5" />
              <span>
                {cruce.unmatched} retenci{cruce.unmatched === 1 ? 'ón' : 'ones'} sin comprobante cruzado.
                Esto ocurre cuando el agente de percepción no emitió facturas electrónicas en ARCA para ese período,
                o cuando la percepción proviene de una liquidación separada (p. ej. ARBA, bancos).
                Revisión manual requerida para completar el campo AB de Holistor.
              </span>
            </div>
          )}
        </>
      )}
    </div>
  )
}
