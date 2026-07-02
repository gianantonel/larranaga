import { useEffect, useState } from 'react'
import {
  Search, Plus, X, DollarSign, Wallet, Trash2, CheckCircle2, Loader2, Briefcase,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { formatCurrency } from '../utils/helpers'
import {
  getLiquidacionesPreviewAll, createProfesional,
  liquidarProfesional, registrarPagoProfesional, eliminarPagoProfesional,
} from '../utils/api'

const todayPeriod = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}
const todayDate = () => new Date().toISOString().split('T')[0]

const MEDIOS = [
  { v: 'transferencia', l: 'Transferencia' },
  { v: 'efectivo', l: 'Efectivo' },
  { v: 'deposito', l: 'Depósito' },
  { v: 'cheque', l: 'Cheque' },
]
const ESTADO_BADGE = { pagado: 'badge-green', parcial: 'badge-yellow', sin_liquidar: 'badge-gray', pendiente: 'badge-blue' }
const ESTADO_LABEL = { pagado: 'Pagado', parcial: 'Parcial', sin_liquidar: 'Sin liquidar', pendiente: 'Pendiente' }

export default function Liquidaciones() {
  const { isAdmin } = useAuth()
  const [periodo, setPeriodo] = useState(todayPeriod())
  const [previews, setPreviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState(null)
  const [medio, setMedio] = useState('transferencia')
  const [liquidando, setLiquidando] = useState(false)
  const [okMsg, setOkMsg] = useState('')

  // Nuevo profesional
  const [showProfModal, setShowProfModal] = useState(false)
  const [profForm, setProfForm] = useState({ nombre: '', tipo: 'profesional' })

  // Modal de pagos parciales
  const [pagoProf, setPagoProf] = useState(null)
  const [pagoForm, setPagoForm] = useState({ monto: '', medio_pago: 'transferencia', fecha: todayDate() })

  const load = () => {
    setLoading(true)
    getLiquidacionesPreviewAll(periodo)
      .then(r => setPreviews(r.data))
      .catch(() => setPreviews([]))
      .finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [periodo])

  const selected = previews.find(p => p.profesional_id === selectedId) || null
  useEffect(() => { if (selected) setMedio(selected.medio_pago || 'transferencia'); setOkMsg('') }, [selectedId, periodo])

  const replacePreview = (pv) => setPreviews(ps => ps.map(p => p.profesional_id === pv.profesional_id ? pv : p))

  // ─── Liquidar total ──────────────────────────────────────────────────────
  const handleLiquidarTotal = async () => {
    if (!selected) return
    if (!confirm(`¿Liquidar a ${selected.profesional_nombre} por ${formatCurrency(selected.total_a_cobrar)} (pago total)?`)) return
    setLiquidando(true); setOkMsg('')
    try {
      const { data } = await liquidarProfesional(selected.profesional_id, periodo, { medio_pago: medio, modo: 'total' })
      replacePreview(data)
      setOkMsg(`Liquidado: ${data.profesional_nombre} · ${formatCurrency(data.pagado)}`)
    } catch (e) { alert(e.response?.data?.detail || 'Error al liquidar') }
    finally { setLiquidando(false) }
  }

  // ─── Pagos parciales ──────────────────────────────────────────────────────
  const openPago = (pv) => {
    setPagoProf(pv)
    setPagoForm({ monto: String(pv.restante || ''), medio_pago: pv.medio_pago || medio || 'transferencia', fecha: todayDate() })
  }
  const refreshPago = (pv) => { replacePreview(pv); setPagoProf(pv) }
  const addPago = async (e) => {
    e.preventDefault()
    const monto = parseFloat(pagoForm.monto)
    if (!monto || monto <= 0) { alert('Ingresá un importe válido'); return }
    try {
      const { data } = await registrarPagoProfesional({
        profesional_id: pagoProf.profesional_id, period: periodo,
        monto, medio_pago: pagoForm.medio_pago, fecha: pagoForm.fecha || undefined,
      })
      refreshPago(data)
      setPagoForm(f => ({ ...f, monto: String(data.restante || '') }))
    } catch (e) { alert(e.response?.data?.detail?.error || e.response?.data?.detail || 'Error al registrar pago') }
  }
  const delPago = async (id) => {
    try { const { data } = await eliminarPagoProfesional(id); refreshPago(data) }
    catch (e) { alert('Error al eliminar pago') }
  }

  // ─── Nuevo profesional ────────────────────────────────────────────────────
  const handleSaveProf = async (e) => {
    e.preventDefault()
    try {
      await createProfesional({ nombre: profForm.nombre, tipo: profForm.tipo })
      setShowProfModal(false); setProfForm({ nombre: '', tipo: 'profesional' })
      load()
    } catch (e) { alert(e.response?.data?.detail || 'Error al crear profesional') }
  }

  const handleSaveMedio = async (v) => {
    setMedio(v)
    if (selected && selected.estado !== 'sin_liquidar') {
      // si ya hay liquidación, persistir el medio re-liquidando en su mismo modo no aplica;
      // el medio se usa en el próximo pago. Solo actualizamos local.
    }
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center"><LoadingSpinner /></div>

  const filtered = previews.filter(p => p.profesional_nombre.toLowerCase().includes(search.toLowerCase()))
  const totalGeneral = previews.reduce((a, p) => a + p.total_a_cobrar, 0)

  return (
    <div className="page">
      <PageHeader title="Liquidaciones" subtitle="Liquidación mensual de profesionales del estudio">
        <input type="month" value={periodo} onChange={e => setPeriodo(e.target.value)} className="input-field w-auto" />
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Profesionales */}
        <div className="card p-0 overflow-hidden flex flex-col h-[calc(100vh-14rem)]">
          <div className="p-3 border-b border-[var(--border)] space-y-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input placeholder="Buscar profesional..." value={search} onChange={e => setSearch(e.target.value)} className="input-field w-full pl-9" />
            </div>
            {isAdmin && (
              <button onClick={() => setShowProfModal(true)} className="btn-secondary text-sm w-full justify-center"><Plus size={15} /> Nuevo profesional</button>
            )}
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {filtered.map(p => (
              <button key={p.profesional_id} onClick={() => setSelectedId(p.profesional_id)}
                className={`w-full text-left p-3 rounded-lg transition-colors border ${selectedId === p.profesional_id ? 'bg-violet-600/15 border-violet-500/50' : 'border-transparent hover:bg-white/5'}`}>
                <p className="text-sm font-medium text-white truncate">{p.profesional_nombre}</p>
                <div className="flex items-center justify-between mt-0.5">
                  <span className="text-xs text-gray-400">{formatCurrency(p.total_a_cobrar)}</span>
                  <span className={ESTADO_BADGE[p.estado]}>{ESTADO_LABEL[p.estado]}</span>
                </div>
              </button>
            ))}
            {filtered.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                <Briefcase size={32} className="mx-auto mb-2 opacity-20" />
                <p className="text-sm">{search ? 'Sin resultados para la búsqueda' : 'No hay profesionales'}</p>
              </div>
            )}
          </div>
          <div className="p-3 border-t border-[var(--border)] text-sm text-gray-400">
            Total a cobrar del mes:{' '}
            <span className={`font-semibold ${totalGeneral > 0 ? 'text-emerald-400' : 'text-white'}`}>{formatCurrency(totalGeneral)}</span>
          </div>
        </div>

        {/* Detalle */}
        <div className="card p-0 overflow-hidden lg:col-span-2 flex flex-col h-[calc(100vh-14rem)]">
          {!selected ? (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
              <Briefcase size={56} className="mb-3 opacity-20" /><p>Seleccioná un profesional para ver su liquidación</p>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-5">
              <div className="flex items-start justify-between gap-3 mb-4">
                <div>
                  <h2 className="text-lg font-bold text-white">{selected.profesional_nombre}</h2>
                  <span className="text-xs text-gray-400">{periodo}</span>
                </div>
                <span className={ESTADO_BADGE[selected.estado]}>{ESTADO_LABEL[selected.estado]}</span>
              </div>

              {okMsg && (
                <div className="mb-4 flex items-center gap-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 px-3 py-2 text-sm text-emerald-300">
                  <CheckCircle2 size={16} /> {okMsg}
                </div>
              )}

              {/* Desglose */}
              <div className="rounded-xl border border-[var(--border)] divide-y divide-[var(--border)] mb-4">
                {[
                  ['Honorarios brutos', selected.honorarios_brutos, 'text-white'],
                  ['Adelantos cobrados', -selected.adelantos_cobrados, 'text-amber-300'],
                  ['Saldo anterior', selected.saldo_anterior, 'text-gray-300'],
                  ['Reintegros', selected.reintegros_total, 'text-emerald-300'],
                ].map(([l, v, c]) => (
                  <div key={l} className="flex items-center justify-between px-4 py-2.5 text-sm">
                    <span className="text-gray-400">{l}</span>
                    <span className={`font-mono ${c}`}>{formatCurrency(v)}</span>
                  </div>
                ))}
                <div className="flex items-center justify-between px-4 py-3 bg-[var(--surface-2)]">
                  <span className="font-semibold text-white">Total a cobrar</span>
                  <span className="font-mono font-bold text-lg text-violet-300">{formatCurrency(selected.total_a_cobrar)}</span>
                </div>
              </div>

              {/* Estado de pago */}
              {selected.estado !== 'sin_liquidar' && (
                <div className="grid grid-cols-2 gap-2 mb-4 text-center">
                  <div className="rounded-lg bg-emerald-500/10 p-2"><p className="text-[11px] text-gray-500">Pagado</p><p className="font-mono font-bold text-emerald-300">{formatCurrency(selected.pagado)}</p></div>
                  <div className="rounded-lg bg-amber-500/10 p-2"><p className="text-[11px] text-gray-500">Restante</p><p className="font-mono font-bold text-amber-300">{formatCurrency(selected.restante)}</p></div>
                </div>
              )}

              {/* Acciones de pago */}
              {selected.estado !== 'pagado' ? (
                <div className="rounded-xl border border-[var(--border)] p-4 space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] text-gray-500 block mb-1">Medio de pago</label>
                      <select value={medio} onChange={e => handleSaveMedio(e.target.value)} className="input-field py-1.5 text-sm w-full">
                        {MEDIOS.map(m => <option key={m.v} value={m.v}>{m.l}</option>)}
                      </select>
                    </div>
                    <div className="flex items-end gap-2">
                      <button onClick={handleLiquidarTotal} disabled={liquidando || selected.total_a_cobrar <= 0} className="btn-primary flex-1 justify-center">
                        {liquidando ? <Loader2 size={16} className="animate-spin" /> : <DollarSign size={16} />} Liquidar (total)
                      </button>
                      <button onClick={() => openPago(selected)} className="btn-secondary justify-center"><Wallet size={16} /> Parcial</button>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500">«Liquidar (total)» registra el pago completo. «Parcial» abre el detalle para cargar pagos sucesivos.</p>
                </div>
              ) : (
                <div className="flex items-center justify-between rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3">
                  <span className="flex items-center gap-2 text-sm text-emerald-300"><CheckCircle2 size={16} /> Liquidación pagada</span>
                  <button onClick={() => openPago(selected)} className="btn-secondary text-sm py-1"><Wallet size={14} /> Ver pagos</button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── MODAL: Pagos parciales ───────────────────────────────────────────── */}
      {pagoProf && (
        <div className="modal-backdrop" onClick={() => setPagoProf(null)}>
          <div className="modal-panel max-w-lg p-6" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2 className="text-lg font-bold text-white">Pagos</h2>
                <p className="text-sm text-gray-400">{pagoProf.profesional_nombre} · {periodo}</p>
              </div>
              <button onClick={() => setPagoProf(null)} className="btn-icon"><X size={18} /></button>
            </div>

            <div className="grid grid-cols-3 gap-2 mb-4 text-center">
              <div className="rounded-lg bg-white/5 p-2"><p className="text-[11px] text-gray-500">Total</p><p className="font-mono font-bold text-white">{formatCurrency(pagoProf.total_a_cobrar)}</p></div>
              <div className="rounded-lg bg-emerald-500/10 p-2"><p className="text-[11px] text-gray-500">Pagado</p><p className="font-mono font-bold text-emerald-300">{formatCurrency(pagoProf.pagado)}</p></div>
              <div className="rounded-lg bg-amber-500/10 p-2"><p className="text-[11px] text-gray-500">Restante</p><p className="font-mono font-bold text-amber-300">{formatCurrency(pagoProf.restante)}</p></div>
            </div>

            <p className="text-[11px] uppercase tracking-wide text-gray-500 mb-1">Historial de pagos</p>
            <div className="space-y-1 mb-4 max-h-44 overflow-y-auto">
              {(pagoProf.pagos || []).length === 0 && <p className="text-sm text-gray-500 text-center py-3">Todavía no hay pagos.</p>}
              {(pagoProf.pagos || []).map(p => (
                <div key={p.id} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2 text-sm">
                  <span className="font-mono font-medium text-white">{formatCurrency(p.monto)}</span>
                  <span className="text-gray-400 capitalize">{p.medio_pago}</span>
                  <span className="text-gray-500 text-xs">{p.fecha}</span>
                  <button onClick={() => delPago(p.id)} className="text-gray-500 hover:text-rose-400"><Trash2 size={14} /></button>
                </div>
              ))}
            </div>

            {pagoProf.restante > 0.005 ? (
              <form onSubmit={addPago} className="grid grid-cols-1 sm:grid-cols-4 gap-2 items-end border-t border-[var(--border)] pt-4">
                <div>
                  <label className="text-[11px] text-gray-500 block mb-0.5">Importe</label>
                  <input type="number" step="0.01" value={pagoForm.monto} onChange={e => setPagoForm(f => ({ ...f, monto: e.target.value }))} placeholder={String(pagoProf.restante)} className="input-field py-1.5 text-sm font-mono w-full" required />
                </div>
                <div>
                  <label className="text-[11px] text-gray-500 block mb-0.5">Medio</label>
                  <select value={pagoForm.medio_pago} onChange={e => setPagoForm(f => ({ ...f, medio_pago: e.target.value }))} className="input-field py-1.5 text-sm w-full">
                    {MEDIOS.map(m => <option key={m.v} value={m.v}>{m.l}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[11px] text-gray-500 block mb-0.5">Fecha</label>
                  <input type="date" value={pagoForm.fecha} onChange={e => setPagoForm(f => ({ ...f, fecha: e.target.value }))} className="input-field py-1.5 text-sm w-full" />
                </div>
                <button type="submit" className="btn-primary justify-center"><Plus size={15} /> Pago</button>
              </form>
            ) : (
              <div className="flex items-center justify-center gap-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 px-3 py-2 text-sm text-emerald-300">
                <CheckCircle2 size={16} /> Pago completo
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── MODAL: Nuevo profesional ─────────────────────────────────────────── */}
      {showProfModal && (
        <div className="modal-backdrop" onClick={() => setShowProfModal(false)}>
          <div className="modal-panel max-w-md p-6" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="text-lg font-bold text-white">Nuevo profesional</h2>
              <button onClick={() => setShowProfModal(false)} className="btn-icon"><X size={18} /></button>
            </div>
            <form onSubmit={handleSaveProf} className="space-y-4">
              <div><label className="label">Nombre *</label><input value={profForm.nombre} onChange={e => setProfForm(f => ({ ...f, nombre: e.target.value }))} className="input-field" required /></div>
              <div>
                <label className="label">Tipo</label>
                <select value={profForm.tipo} onChange={e => setProfForm(f => ({ ...f, tipo: e.target.value }))} className="input-field">
                  <option value="profesional">Profesional</option>
                  <option value="socio">Socio</option>
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowProfModal(false)} className="btn-secondary flex-1 justify-center">Cancelar</button>
                <button type="submit" className="btn-primary flex-1 justify-center">Agregar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
