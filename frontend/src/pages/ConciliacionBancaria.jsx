import { useEffect, useState } from 'react'
import {
  Banknote, Upload, RefreshCw, CheckCircle, AlertTriangle,
  X, Search, Link2, Unlink, ChevronRight,
} from 'lucide-react'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { formatCurrency, formatDate } from '../utils/helpers'
import {
  importarExtracto, getExtractos, getMovimientosExtracto,
  runMatching, matchManual, desconciliarMovimiento, sugerenciasMovimiento,
} from '../utils/api'

const BANCOS = [
  { value: 'pampa', label: 'Banco Pampa' },
  { value: 'santander', label: 'Banco Santander' },
  { value: 'mercadopago', label: 'Mercado Pago' },
]

const todayPeriod = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

// ─── Tab Importar ────────────────────────────────────────────────────────────

function TabImportar({ onImported }) {
  const [banco, setBanco] = useState('pampa')
  const [periodo, setPeriodo] = useState(todayPeriod())
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null); setResult(null)
    if (!file) { setError('Seleccioná un archivo'); return }

    const fd = new FormData()
    fd.append('banco', banco)
    fd.append('periodo', periodo)
    fd.append('file', file)

    setLoading(true)
    try {
      const r = await importarExtracto(fd)
      setResult(r.data)
      onImported?.()
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al importar el extracto')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card max-w-2xl space-y-5">
      <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
        <Upload size={20} /> Importar extracto bancario
      </h2>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Banco *</label>
          <select value={banco} onChange={(e) => setBanco(e.target.value)} className="input-field" required>
            {BANCOS.map((b) => <option key={b.value} value={b.value}>{b.label}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Período (YYYY-MM) *</label>
          <input
            type="text" value={periodo} onChange={(e) => setPeriodo(e.target.value)}
            placeholder="2026-02" className="input-field" pattern="\d{4}-\d{2}" required
          />
        </div>
      </div>

      <div>
        <label className="label">Archivo (.xlsx o .csv) *</label>
        <input
          type="file" accept=".xlsx,.xls,.csv"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="input-field file:mr-3 file:rounded file:border-0 file:bg-violet-600/20 file:px-3 file:py-1 file:text-violet-300 hover:file:bg-violet-600/30"
          required
        />
        {file && <p className="text-xs text-gray-400 mt-1">{file.name} · {(file.size / 1024).toFixed(1)} KB</p>}
      </div>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-center gap-2 text-sm text-rose-300">
          <AlertTriangle size={16} /> {String(error)}
        </div>
      )}
      {result && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg space-y-1 text-sm">
          <div className="flex items-center gap-2 text-emerald-300 font-medium">
            <CheckCircle size={16} /> Extracto importado correctamente.
          </div>
          <div className="text-gray-300">
            <strong>{result.extracto.n_movimientos}</strong> movimientos
            ({result.n_creditos} créditos por <strong>{formatCurrency(result.importe_total_creditos)}</strong>,
            {' '}{result.n_debitos} débitos por <strong>{formatCurrency(result.importe_total_debitos)}</strong>).
          </div>
        </div>
      )}

      <button type="submit" disabled={loading} className="btn-primary w-full justify-center disabled:opacity-50">
        {loading ? 'Procesando…' : 'Importar y procesar'}
      </button>
    </form>
  )
}

// ─── Modal de match manual ───────────────────────────────────────────────────

function ModalMatchManual({ movimiento, onClose, onSaved }) {
  const [candidatos, setCandidatos] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!movimiento) return
    setLoading(true)
    sugerenciasMovimiento(movimiento.id, 5)
      .then((r) => setCandidatos(r.data))
      .catch(() => setCandidatos([]))
      .finally(() => setLoading(false))
  }, [movimiento])

  const handleAsociar = async (pagoId) => {
    setSaving(true); setError(null)
    try {
      await matchManual(movimiento.id, { pago_id: pagoId, nota: 'match manual desde UI' })
      onSaved?.()
      onClose()
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo asociar')
    } finally {
      setSaving(false)
    }
  }

  if (!movimiento) return null

  return (
    <div className="modal-backdrop">
      <div className="modal-panel max-w-2xl">
        <div className="flex items-center justify-between p-5 border-b border-gray-700/50">
          <h3 className="font-semibold text-gray-100">Asociar movimiento manualmente</h3>
          <button onClick={onClose} className="btn-icon"><X size={20} /></button>
        </div>

        <div className="p-5 space-y-4">
          <div className="bg-[#0f172a]/70 border border-gray-700/40 rounded-lg p-3 text-sm space-y-1">
            <div className="text-gray-400">Movimiento bancario:</div>
            <div className="text-gray-100 font-medium">{movimiento.descripcion}</div>
            <div className="text-gray-400">
              {formatDate(movimiento.fecha)} · <strong className="text-gray-200">{formatCurrency(movimiento.importe)}</strong>
              {movimiento.cuit_detectado && <> · CUIT: <code className="text-violet-300">{movimiento.cuit_detectado}</code></>}
            </div>
          </div>

          <h4 className="text-sm font-medium text-gray-300">Pagos candidatos</h4>

          {loading ? (
            <div className="text-center py-8 text-gray-500 text-sm">Buscando candidatos…</div>
          ) : candidatos.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-sm">No hay pagos pendientes que coincidan.</div>
          ) : (
            <div className="space-y-2">
              {candidatos.map((c) => (
                <div key={c.pago_id} className="flex items-center gap-3 p-3 bg-[#0f172a]/50 border border-gray-700/40 rounded-lg hover:border-violet-500/40 transition">
                  <div className="flex-1">
                    <div className="text-sm text-gray-100 font-medium">{c.client_name}</div>
                    <div className="text-xs text-gray-400">
                      {formatDate(c.fecha)} · {formatCurrency(c.importe)}
                    </div>
                  </div>
                  <span className="badge-purple">score {(c.score * 100).toFixed(0)}%</span>
                  <button
                    onClick={() => handleAsociar(c.pago_id)}
                    disabled={saving}
                    className="btn-primary text-sm py-1.5 px-3 disabled:opacity-50"
                  >
                    <Link2 size={14} /> Asociar
                  </button>
                </div>
              ))}
            </div>
          )}

          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-sm text-rose-300">
              {String(error)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Tab Detalle Extracto (Conciliados + Pendientes) ─────────────────────────

function TabExtracto({ extracto, refrescar }) {
  const [movimientos, setMovimientos] = useState([])
  const [loading, setLoading] = useState(true)
  const [matching, setMatching] = useState(false)
  const [showOnly, setShowOnly] = useState('all')  // all | pendientes | conciliados
  const [search, setSearch] = useState('')
  const [modalMov, setModalMov] = useState(null)
  const [stats, setStats] = useState(null)

  const cargar = () => {
    setLoading(true)
    getMovimientosExtracto(extracto.id)
      .then((r) => setMovimientos(r.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { cargar() }, [extracto.id])

  const handleRunMatching = async () => {
    setMatching(true)
    try {
      const r = await runMatching(extracto.id)
      setStats(r.data.stats)
      cargar()
      refrescar?.()
    } finally {
      setMatching(false)
    }
  }

  const handleDesconciliar = async (mov) => {
    if (!confirm(`Desconciliar este movimiento? (${formatCurrency(mov.importe)})`)) return
    await desconciliarMovimiento(mov.id)
    cargar()
    refrescar?.()
  }

  const filtered = movimientos.filter((m) => {
    if (showOnly === 'pendientes' && m.conciliado) return false
    if (showOnly === 'conciliados' && !m.conciliado) return false
    if (search && !m.descripcion.toLowerCase().includes(search.toLowerCase()) &&
        !(m.cuit_detectado || '').includes(search)) return false
    return true
  })

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={handleRunMatching}
          disabled={matching}
          className="btn-primary disabled:opacity-50"
        >
          <RefreshCw size={16} className={matching ? 'animate-spin' : ''} />
          {matching ? 'Procesando…' : 'Correr matching automático'}
        </button>

        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-400">Mostrar:</span>
          {[['all', 'Todos'], ['pendientes', 'Pendientes'], ['conciliados', 'Conciliados']].map(([v, l]) => (
            <button
              key={v}
              onClick={() => setShowOnly(v)}
              className={`px-3 py-1 rounded-full text-xs font-medium ${
                showOnly === v
                  ? 'bg-violet-600/30 text-violet-300 border border-violet-500/40'
                  : 'bg-[#1f2937] text-gray-400 border border-gray-700/50 hover:text-gray-200'
              }`}
            >{l}</button>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2 bg-[#0f172a] border border-gray-700/50 rounded-lg px-3 py-1.5">
          <Search size={14} className="text-gray-500" />
          <input
            value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Descripción o CUIT…"
            className="bg-transparent text-sm text-gray-100 placeholder-gray-500 outline-none w-48"
          />
        </div>
      </div>

      {stats && (
        <div className="card-sm bg-emerald-500/5 border-emerald-500/30 text-sm">
          <div className="flex items-center gap-2 text-emerald-300 font-medium mb-1">
            <CheckCircle size={14} /> Matching ejecutado:
            <strong>{stats.auto}</strong> conciliados,
            <strong>{stats.manual_required}</strong> requieren revisión manual.
          </div>
          <div className="text-xs text-gray-400">
            Por tipo: {Object.entries(stats.by_type).filter(([, v]) => v > 0).map(([k, v]) => `${k}: ${v}`).join(' · ') || 'ninguno'}
          </div>
        </div>
      )}

      {loading ? <LoadingSpinner /> : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead className="bg-[#0f172a]/60 border-b border-gray-700/50">
              <tr>
                <th className="table-header">Fecha</th>
                <th className="table-header">Tipo</th>
                <th className="table-header">Descripción</th>
                <th className="table-header text-right">Importe</th>
                <th className="table-header">CUIT</th>
                <th className="table-header text-center">Estado</th>
                <th className="table-header text-right">Acción</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={7} className="py-12 text-center text-gray-500 text-sm">
                  No hay movimientos con esos filtros.
                </td></tr>
              ) : filtered.map((m) => (
                <tr key={m.id} className="table-row">
                  <td className="table-cell whitespace-nowrap">{formatDate(m.fecha)}</td>
                  <td className="table-cell">
                    <span className={m.tipo === 'C' ? 'badge-green' : 'badge-red'}>
                      {m.tipo === 'C' ? 'Crédito' : 'Débito'}
                    </span>
                  </td>
                  <td className="table-cell text-xs">{m.descripcion}</td>
                  <td className="table-cell text-right font-mono">{formatCurrency(m.importe)}</td>
                  <td className="table-cell text-xs text-violet-300">{m.cuit_detectado || '—'}</td>
                  <td className="table-cell text-center">
                    {m.conciliado ? (
                      <span className="badge-green"><CheckCircle size={12} /> Conciliado</span>
                    ) : (
                      <span className="badge-yellow">Pendiente</span>
                    )}
                  </td>
                  <td className="table-cell text-right">
                    {m.conciliado ? (
                      <button onClick={() => handleDesconciliar(m)} className="btn-icon hover:text-rose-400" title="Desconciliar">
                        <Unlink size={14} />
                      </button>
                    ) : m.tipo === 'C' ? (
                      <button onClick={() => setModalMov(m)} className="btn-icon hover:text-violet-300" title="Asociar manualmente">
                        <Link2 size={14} />
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modalMov && (
        <ModalMatchManual movimiento={modalMov} onClose={() => setModalMov(null)} onSaved={() => { cargar(); refrescar?.() }} />
      )}
    </div>
  )
}

// ─── Página principal ────────────────────────────────────────────────────────

export default function ConciliacionBancaria() {
  const [tab, setTab] = useState('importar')   // importar | extracto
  const [extractos, setExtractos] = useState([])
  const [extractoActivo, setExtractoActivo] = useState(null)
  const [loading, setLoading] = useState(true)

  const cargarExtractos = () => {
    setLoading(true)
    getExtractos()
      .then((r) => setExtractos(r.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { cargarExtractos() }, [])

  return (
    <div className="p-6">
      <PageHeader
        title="Conciliación bancaria"
        subtitle="Importar extractos · matchear con pagos · resolver pendientes."
        icon={Banknote}
      />

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-700/50 mb-6">
        {[['importar', 'Importar extracto'], ['extracto', 'Extractos importados']].map(([v, l]) => (
          <button
            key={v}
            onClick={() => { setTab(v); if (v === 'extracto') cargarExtractos() }}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition ${
              tab === v
                ? 'border-violet-500 text-violet-300'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >{l}</button>
        ))}
      </div>

      {tab === 'importar' && <TabImportar onImported={cargarExtractos} />}

      {tab === 'extracto' && (
        loading ? <LoadingSpinner /> :
        extractoActivo ? (
          <div className="space-y-4">
            <button
              onClick={() => setExtractoActivo(null)}
              className="text-sm text-gray-400 hover:text-gray-200 flex items-center gap-1"
            >← volver al listado</button>
            <div className="card-sm">
              <div className="text-sm text-gray-400">Extracto:</div>
              <div className="text-gray-100 font-medium">
                {extractoActivo.banco.toUpperCase()} · {extractoActivo.periodo} ·
                {' '}{extractoActivo.archivo_nombre || 'sin nombre'}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {extractoActivo.n_movimientos} movimientos · {extractoActivo.n_conciliados} conciliados · {extractoActivo.n_pendientes} pendientes
              </div>
            </div>
            <TabExtracto extracto={extractoActivo} refrescar={cargarExtractos} />
          </div>
        ) : extractos.length === 0 ? (
          <div className="card text-center text-gray-500 py-12">
            No hay extractos importados. Subí uno en la pestaña "Importar extracto".
          </div>
        ) : (
          <div className="card p-0 overflow-hidden">
            <table className="w-full">
              <thead className="bg-[#0f172a]/60 border-b border-gray-700/50">
                <tr>
                  <th className="table-header">Banco</th>
                  <th className="table-header">Período</th>
                  <th className="table-header">Archivo</th>
                  <th className="table-header text-right">Movs.</th>
                  <th className="table-header text-right">Conciliados</th>
                  <th className="table-header text-right">Pendientes</th>
                  <th className="table-header text-right">Acción</th>
                </tr>
              </thead>
              <tbody>
                {extractos.map((e) => (
                  <tr key={e.id} className="table-row">
                    <td className="table-cell">{e.banco.toUpperCase()}</td>
                    <td className="table-cell">{e.periodo}</td>
                    <td className="table-cell text-xs">{e.archivo_nombre || '—'}</td>
                    <td className="table-cell text-right">{e.n_movimientos}</td>
                    <td className="table-cell text-right text-emerald-400">{e.n_conciliados}</td>
                    <td className="table-cell text-right text-amber-400">{e.n_pendientes}</td>
                    <td className="table-cell text-right">
                      <button onClick={() => setExtractoActivo(e)} className="btn-secondary text-sm py-1.5 px-3">
                        Ver detalle <ChevronRight size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  )
}
