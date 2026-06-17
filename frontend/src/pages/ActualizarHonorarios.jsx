import { useState } from 'react'
import {
  Percent, Calculator, ArrowLeft, ArrowRight, CheckCircle,
  AlertTriangle, Info, Plus, Minus,
} from 'lucide-react'
import PageHeader from '../components/UI/PageHeader'
import { formatCurrency } from '../utils/helpers'
import {
  previewActualizacionHonorarios,
  aplicarActualizacionHonorarios,
} from '../utils/api'

const FUENTES = [
  { value: 'ipc', label: 'IPC', desc: 'Índice de precios al consumidor' },
  { value: 'manual', label: 'Manual', desc: 'Valor fijado por el estudio' },
  { value: 'negociado', label: 'Negociado', desc: 'Acordado con el cliente' },
]

const periodoActual = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}


export default function ActualizarHonorarios() {
  const [step, setStep] = useState(1)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  // Step 1 — input del índice
  const [form, setForm] = useState({
    indice_pct: '',
    fuente: 'ipc',
    periodo_aplicacion: periodoActual(),
    notas: '',
  })

  // Step 2 — preview con selección
  const [preview, setPreview] = useState(null)        // { indice_id, rows: [...] }
  const [selectedIds, setSelectedIds] = useState(new Set())

  // Step 3 — resultado
  const [result, setResult] = useState(null)

  const setField = (k, v) => setForm((p) => ({ ...p, [k]: v }))

  // Step 1 — calcular preview
  const handlePreview = async (e) => {
    e?.preventDefault()
    setError(null)

    const pct = parseFloat(form.indice_pct)
    if (isNaN(pct) || pct === 0) {
      setError('Ingresá un índice distinto de 0 (positivo o negativo).')
      return
    }
    if (!form.periodo_aplicacion || form.periodo_aplicacion.length !== 7) {
      setError('Ingresá un período válido (formato YYYY-MM).')
      return
    }

    setSubmitting(true)
    try {
      const res = await previewActualizacionHonorarios({
        indice_pct: pct,
        periodo_aplicacion: form.periodo_aplicacion,
        fuente: form.fuente,
        notas: form.notas || null,
      })
      setPreview(res.data)
      // Pre-seleccionar todos los que aplican (tipo fijo)
      const aplicables = res.data.rows.filter((r) => r.aplica_indice).map((r) => r.cliente_id)
      setSelectedIds(new Set(aplicables))
      setStep(2)
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Error al calcular el preview.')
    } finally {
      setSubmitting(false)
    }
  }

  // Step 2 — toggle de cliente
  const toggleClient = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const aplicablesIds = preview ? preview.rows.filter((r) => r.aplica_indice).map((r) => r.cliente_id) : []
  const allSelected = aplicablesIds.length > 0 && aplicablesIds.every((id) => selectedIds.has(id))
  const toggleAll = () => {
    if (allSelected) setSelectedIds(new Set())
    else setSelectedIds(new Set(aplicablesIds))
  }

  // Step 2 → 3 — aplicar
  const handleAplicar = async () => {
    setError(null)
    if (selectedIds.size === 0) {
      setError('Seleccioná al menos un cliente.')
      return
    }
    setSubmitting(true)
    try {
      const res = await aplicarActualizacionHonorarios({
        indice_id: preview.indice_id,
        client_ids: Array.from(selectedIds),
      })
      setResult(res.data)
      setStep(3)
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Error al aplicar la actualización.')
    } finally {
      setSubmitting(false)
    }
  }

  const reset = () => {
    setStep(1)
    setForm({ indice_pct: '', fuente: 'ipc', periodo_aplicacion: periodoActual(), notas: '' })
    setPreview(null)
    setSelectedIds(new Set())
    setResult(null)
    setError(null)
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <PageHeader
        title="Actualizar Honorarios"
        subtitle="Aplicación cuatrimestral de un índice (IPC, manual o negociado) con validación cliente por cliente."
      />

      <Stepper step={step} />

      {error && (
        <div className="mb-4 p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-start gap-3">
          <AlertTriangle className="text-rose-400 mt-0.5 shrink-0" size={20} />
          <p className="text-rose-300">{error}</p>
        </div>
      )}

      {step === 1 && (
        <Step1
          form={form}
          setField={setField}
          submitting={submitting}
          onPreview={handlePreview}
        />
      )}

      {step === 2 && preview && (
        <Step2
          preview={preview}
          selectedIds={selectedIds}
          toggleClient={toggleClient}
          allSelected={allSelected}
          toggleAll={toggleAll}
          submitting={submitting}
          onBack={() => setStep(1)}
          onAplicar={handleAplicar}
        />
      )}

      {step === 3 && result && preview && (
        <Step3 result={result} preview={preview} onReset={reset} />
      )}
    </div>
  )
}


function Stepper({ step }) {
  const items = [
    { n: 1, label: 'Definir índice' },
    { n: 2, label: 'Validar y seleccionar' },
    { n: 3, label: 'Confirmación' },
  ]
  return (
    <div className="mb-6 flex items-center justify-center gap-2">
      {items.map(({ n, label }, i) => (
        <div key={n} className="flex items-center">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-medium ${
            n < step ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300' :
            n === step ? 'bg-violet-600/20 border-violet-500/40 text-violet-200' :
            'bg-gray-800/40 border-gray-700/40 text-gray-500'
          }`}>
            {n < step ? <CheckCircle size={14} /> : <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
              n === step ? 'bg-violet-500/30' : 'bg-gray-700/60'
            }`}>{n}</span>}
            <span>{label}</span>
          </div>
          {i < items.length - 1 && (
            <div className={`w-8 h-px mx-1 ${n < step ? 'bg-emerald-500/40' : 'bg-gray-700/40'}`} />
          )}
        </div>
      ))}
    </div>
  )
}


function Step1({ form, setField, submitting, onPreview }) {
  const setIndice = (delta) => {
    const cur = parseFloat(form.indice_pct) || 0
    setField('indice_pct', String(Math.round((cur + delta) * 10) / 10))
  }

  return (
    <form onSubmit={onPreview} className="card space-y-5">
      <h2 className="text-lg font-semibold text-white flex items-center gap-2">
        <Percent size={18} className="text-violet-400" />
        Definí el índice y la fuente
      </h2>

      <div>
        <label className="label">Índice (%) *</label>
        <div className="flex gap-2 items-stretch">
          <button
            type="button"
            onClick={() => setIndice(-0.5)}
            className="shrink-0 px-3 rounded-lg border border-gray-700/50 bg-[#0f172a] text-gray-400 hover:text-violet-300 hover:border-violet-500/40 transition-colors flex items-center justify-center"
            aria-label="Restar 0.5"
          >
            <Minus size={16} />
          </button>
          <input
            type="number"
            step="0.1"
            value={form.indice_pct}
            onChange={(e) => setField('indice_pct', e.target.value)}
            placeholder="ej: 12.5 (positivo o negativo)"
            className="input-field flex-1 text-center text-lg font-semibold"
            required
          />
          <button
            type="button"
            onClick={() => setIndice(0.5)}
            className="shrink-0 px-3 rounded-lg border border-gray-700/50 bg-[#0f172a] text-gray-400 hover:text-violet-300 hover:border-violet-500/40 transition-colors flex items-center justify-center"
            aria-label="Sumar 0.5"
          >
            <Plus size={16} />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-1.5 flex items-center gap-1">
          <Info size={12} />
          Acepta valores negativos (descuento). Solo afecta clientes con honorario fijo.
        </p>
      </div>

      <div>
        <label className="label">Fuente del índice *</label>
        <div className="grid grid-cols-3 gap-2">
          {FUENTES.map(({ value, label, desc }) => (
            <button
              key={value}
              type="button"
              onClick={() => setField('fuente', value)}
              className={`text-left p-3 rounded-lg border transition-all ${
                form.fuente === value
                  ? 'border-violet-500/60 bg-violet-600/15'
                  : 'border-gray-700/50 bg-[#0f172a] hover:border-gray-600'
              }`}
            >
              <div className={`text-sm font-semibold ${form.fuente === value ? 'text-violet-200' : 'text-gray-300'}`}>{label}</div>
              <div className="text-xs text-gray-500 mt-0.5">{desc}</div>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="label">Período de aplicación *</label>
        <input
          type="month"
          value={form.periodo_aplicacion}
          onChange={(e) => setField('periodo_aplicacion', e.target.value)}
          className="input-field"
          required
        />
        <p className="text-xs text-gray-500 mt-1.5">
          A partir de este mes los nuevos honorarios se calculan con el índice aplicado.
        </p>
      </div>

      <div>
        <label className="label">Notas</label>
        <textarea
          value={form.notas}
          onChange={(e) => setField('notas', e.target.value)}
          rows={2}
          placeholder="Contexto opcional (ej: aumento abril 2026 según informe IPC INDEC)"
          className="input-field resize-none"
        />
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="btn-primary w-full justify-center"
      >
        {submitting ? 'Calculando...' : (
          <>
            <Calculator size={16} />
            Calcular preview
            <ArrowRight size={16} />
          </>
        )}
      </button>
    </form>
  )
}


function Step2({ preview, selectedIds, toggleClient, allSelected, toggleAll, submitting, onBack, onAplicar }) {
  const aplicables = preview.rows.filter((r) => r.aplica_indice)
  const noAplicables = preview.rows.filter((r) => !r.aplica_indice)

  const totalActual = aplicables.reduce((acc, r) => acc + (r.importe_actual || 0), 0)
  const totalPropuestoSel = aplicables
    .filter((r) => selectedIds.has(r.cliente_id))
    .reduce((acc, r) => acc + (r.importe_propuesto || 0), 0)
  const totalActualSel = aplicables
    .filter((r) => selectedIds.has(r.cliente_id))
    .reduce((acc, r) => acc + (r.importe_actual || 0), 0)

  return (
    <div className="space-y-4">
      <div className="card flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400">Índice persistido</p>
          <p className="text-lg font-bold text-white">
            {preview.indice_pct >= 0 ? '+' : ''}{preview.indice_pct}% — {preview.fuente.toUpperCase()}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">
            Período de aplicación: {preview.periodo_aplicacion} · ID #{preview.indice_id}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-400">Seleccionados</p>
          <p className="text-2xl font-bold text-violet-300">
            {selectedIds.size} <span className="text-sm font-normal text-gray-500">/ {aplicables.length}</span>
          </p>
        </div>
      </div>

      <div className="card overflow-hidden p-0">
        <div className="px-5 py-3 border-b border-gray-700/40 flex items-center gap-3">
          <button
            onClick={toggleAll}
            className="text-sm text-violet-300 hover:text-violet-200 font-medium underline underline-offset-2"
          >
            {allSelected ? 'Deseleccionar todos' : 'Seleccionar todos'}
          </button>
          <span className="text-sm text-gray-500 ml-auto">{aplicables.length} clientes con honorario fijo</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="table-header border-b border-gray-700/40">
                <th className="text-center px-3 py-2.5 w-10">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleAll}
                    className="accent-violet-500"
                  />
                </th>
                <th className="text-left px-4 py-2.5">Cliente</th>
                <th className="text-right px-4 py-2.5">Importe actual</th>
                <th className="text-right px-4 py-2.5">Importe propuesto</th>
                <th className="text-right px-4 py-2.5">Δ</th>
                <th className="text-right px-4 py-2.5">Δ%</th>
              </tr>
            </thead>
            <tbody>
              {aplicables.map((r) => {
                const checked = selectedIds.has(r.cliente_id)
                const delta = (r.importe_propuesto || 0) - (r.importe_actual || 0)
                return (
                  <tr
                    key={r.cliente_id}
                    onClick={() => toggleClient(r.cliente_id)}
                    className={`cursor-pointer table-row border-b border-gray-700/20 last:border-0 ${
                      checked ? 'bg-violet-500/5' : ''
                    }`}
                  >
                    <td className="px-3 py-2 text-center">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleClient(r.cliente_id)}
                        onClick={(e) => e.stopPropagation()}
                        className="accent-violet-500"
                      />
                    </td>
                    <td className="px-4 py-2 text-gray-200">{r.cliente_nombre}</td>
                    <td className="px-4 py-2 text-right text-gray-400 whitespace-nowrap">{formatCurrency(r.importe_actual)}</td>
                    <td className="px-4 py-2 text-right text-violet-200 font-semibold whitespace-nowrap">{formatCurrency(r.importe_propuesto)}</td>
                    <td className={`px-4 py-2 text-right whitespace-nowrap ${delta >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
                      {delta >= 0 ? '+' : ''}{formatCurrency(delta)}
                    </td>
                    <td className={`px-4 py-2 text-right font-semibold whitespace-nowrap ${(r.delta_pct || 0) >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
                      {(r.delta_pct || 0) >= 0 ? '+' : ''}{r.delta_pct}%
                    </td>
                  </tr>
                )
              })}
            </tbody>
            <tfoot>
              <tr className="bg-violet-500/10 border-t border-violet-500/30 font-semibold">
                <td className="px-3 py-3" colSpan={2}>
                  <span className="text-violet-300">TOTAL ({selectedIds.size} seleccionados)</span>
                </td>
                <td className="px-4 py-3 text-right text-gray-400 whitespace-nowrap">{formatCurrency(totalActualSel)}</td>
                <td className="px-4 py-3 text-right text-violet-200 whitespace-nowrap">{formatCurrency(totalPropuestoSel)}</td>
                <td className={`px-4 py-3 text-right whitespace-nowrap ${totalPropuestoSel >= totalActualSel ? 'text-emerald-300' : 'text-rose-300'}`}>
                  {totalPropuestoSel - totalActualSel >= 0 ? '+' : ''}{formatCurrency(totalPropuestoSel - totalActualSel)}
                </td>
                <td className="px-4 py-3 text-right text-gray-500">—</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {noAplicables.length > 0 && (
        <details className="card p-4">
          <summary className="cursor-pointer text-sm text-gray-400 hover:text-gray-300 flex items-center gap-2">
            <Info size={14} />
            {noAplicables.length} cliente{noAplicables.length !== 1 && 's'} no aplicable{noAplicables.length !== 1 && 's'} (honorario por producto)
          </summary>
          <ul className="mt-3 text-xs text-gray-500 space-y-0.5 ml-5 list-disc">
            {noAplicables.map((r) => <li key={r.cliente_id}>{r.cliente_nombre}</li>)}
          </ul>
        </details>
      )}

      <div className="flex gap-3">
        <button onClick={onBack} className="btn-secondary">
          <ArrowLeft size={16} />
          Volver
        </button>
        <button
          onClick={onAplicar}
          disabled={submitting || selectedIds.size === 0}
          className="btn-primary flex-1 justify-center disabled:opacity-50"
        >
          {submitting ? 'Aplicando...' : (
            <>
              Aplicar a {selectedIds.size} cliente{selectedIds.size !== 1 && 's'}
              <ArrowRight size={16} />
            </>
          )}
        </button>
      </div>
    </div>
  )
}


function Step3({ result, preview, onReset }) {
  const aplicados = result.detalle.filter((d) => d.importe_nuevo !== undefined)
  const saltados = result.detalle.filter((d) => d.motivo)
  const totalProyectado = aplicados.reduce((acc, d) => acc + (d.importe_nuevo || 0), 0)

  return (
    <div className="space-y-4">
      <div className="card text-center py-8">
        <CheckCircle size={56} className="mx-auto text-emerald-400 mb-3" />
        <h2 className="text-2xl font-bold text-white mb-1">¡Actualización aplicada!</h2>
        <p className="text-gray-400">
          {result.aplicados} cliente{result.aplicados !== 1 && 's'} actualizado{result.aplicados !== 1 && 's'}
          {result.saltados > 0 && ` · ${result.saltados} saltado${result.saltados !== 1 && 's'}`}
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="card">
          <p className="text-sm text-gray-400 mb-1">Índice aplicado</p>
          <p className="text-2xl font-bold text-violet-300">
            {preview.indice_pct >= 0 ? '+' : ''}{preview.indice_pct}%
          </p>
          <p className="text-xs text-gray-500 mt-1">{preview.fuente.toUpperCase()} · {preview.periodo_aplicacion}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-400 mb-1">Devengado proyectado próximo mes</p>
          <p className="text-2xl font-bold text-emerald-300">{formatCurrency(totalProyectado)}</p>
          <p className="text-xs text-gray-500 mt-1">Suma de los nuevos importes confirmados</p>
        </div>
      </div>

      {aplicados.length > 0 && (
        <div className="card overflow-hidden p-0">
          <div className="px-5 py-3 border-b border-gray-700/40 flex items-center gap-2">
            <CheckCircle size={16} className="text-emerald-400" />
            <h3 className="font-semibold text-white">Aplicados</h3>
          </div>
          <table className="w-full text-sm">
            <thead className="table-header border-b border-gray-700/40">
              <tr>
                <th className="text-left px-4 py-2">Cliente</th>
                <th className="text-right px-4 py-2">Anterior</th>
                <th className="text-right px-4 py-2">Nuevo</th>
              </tr>
            </thead>
            <tbody>
              {aplicados.map((d) => (
                <tr key={d.client_id} className="table-row border-b border-gray-700/20 last:border-0">
                  <td className="px-4 py-2 text-gray-200">{d.client_name}</td>
                  <td className="px-4 py-2 text-right text-gray-400 whitespace-nowrap">{formatCurrency(d.importe_anterior)}</td>
                  <td className="px-4 py-2 text-right text-emerald-300 font-semibold whitespace-nowrap">{formatCurrency(d.importe_nuevo)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {saltados.length > 0 && (
        <details className="card p-4">
          <summary className="cursor-pointer text-sm text-amber-300 hover:text-amber-200 flex items-center gap-2 font-medium">
            <AlertTriangle size={14} />
            {saltados.length} saltado{saltados.length !== 1 && 's'}
          </summary>
          <ul className="mt-3 text-xs text-gray-400 space-y-1 ml-5 list-disc">
            {saltados.map((d) => (
              <li key={d.client_id}>
                {d.client_name || `Cliente #${d.client_id}`} — {d.motivo}
              </li>
            ))}
          </ul>
        </details>
      )}

      <div className="flex gap-3">
        <button onClick={onReset} className="btn-primary flex-1 justify-center">
          Nueva actualización
        </button>
      </div>
    </div>
  )
}
