import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Eye, AlertTriangle, CheckCircle2, Clock } from 'lucide-react'
import PageHeader from '../components/UI/PageHeader'
import RequirementBadge from '../components/UI/RequirementBadge'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { useAuth } from '../context/AuthContext'
import { useFeatureFlags } from '../context/FeatureFlagsContext'

const FASES = [
  { num: 1, label: 'Fase 1 — Quick wins' },
  { num: 2, label: 'Fase 2 — Pipeline IVA + Tesorería' },
  { num: 3, label: 'Fase 3 — Conciliación + Flujo' },
  { num: 4, label: 'Fase 4 — Reportes avanzados' },
]

export default function GestionRequisitos() {
  const { isSuperAdmin } = useAuth()
  const { flags, loading, setFlag, verificationMode, toggleVerificationMode } = useFeatureFlags()
  const [activeFase, setActiveFase] = useState(1)
  const [confirmFlag, setConfirmFlag] = useState(null)
  const [savingCodigo, setSavingCodigo] = useState(null)

  if (!isSuperAdmin) return <Navigate to="/dashboard" replace />

  const handleToggle = async (flag) => {
    if (!flag.implementado && !flag.enabled) {
      setConfirmFlag(flag)
      return
    }
    setSavingCodigo(flag.codigo)
    try { await setFlag(flag.codigo, !flag.enabled) }
    finally { setSavingCodigo(null) }
  }

  const confirmActivate = async () => {
    const flag = confirmFlag
    setConfirmFlag(null)
    setSavingCodigo(flag.codigo)
    try { await setFlag(flag.codigo, true) }
    finally { setSavingCodigo(null) }
  }

  if (loading) return <div className="flex items-center justify-center min-h-[40vh]"><LoadingSpinner /></div>

  const flagsActivos = flags.filter(f => f.fase === activeFase)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Gestión de Requisitos"
        subtitle="Activá o desactivá cada R-XX. Solo super_admin. Los colaboradores solo ven los que están activos."
      >
        <button
          onClick={toggleVerificationMode}
          className={verificationMode ? 'btn btn-primary' : 'btn btn-secondary'}
        >
          <Eye size={16} />
          Modo verificación {verificationMode ? 'ON' : 'OFF'}
        </button>
      </PageHeader>

      <div className="flex flex-wrap gap-2">
        {FASES.map(f => (
          <button
            key={f.num}
            onClick={() => setActiveFase(f.num)}
            className={activeFase === f.num ? 'btn btn-primary btn-sm' : 'btn btn-ghost btn-sm'}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {flagsActivos.map(flag => (
          <RequirementCard
            key={flag.codigo}
            flag={flag}
            saving={savingCodigo === flag.codigo}
            onToggle={() => handleToggle(flag)}
          />
        ))}
        {flagsActivos.length === 0 && (
          <p className="col-span-full text-sm" style={{ color: 'var(--text-muted)' }}>
            No hay requisitos en esta fase.
          </p>
        )}
      </div>

      {confirmFlag && (
        <ConfirmModal
          flag={confirmFlag}
          onConfirm={confirmActivate}
          onCancel={() => setConfirmFlag(null)}
        />
      )}
    </div>
  )
}

function RequirementCard({ flag, saving, onToggle }) {
  const statusIcon = flag.implementado
    ? (flag.enabled
        ? <CheckCircle2 size={14} className="text-emerald-500" />
        : <Clock size={14} className="text-amber-500" />)
    : <AlertTriangle size={14} className="text-zinc-400" />
  const statusLabel = !flag.implementado ? 'Pendiente' : flag.enabled ? 'Activo' : 'Inactivo'

  return (
    <div className="card p-4 flex flex-col gap-3" style={{ minHeight: 200 }}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <RequirementBadge flag={flag} size="md" />
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {flag.area} · {flag.dificultad}
          </span>
        </div>
        <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-muted)' }}>
          {statusIcon} {statusLabel}
        </span>
      </div>

      <div className="flex-1">
        <h3 className="text-sm font-semibold leading-snug" style={{ color: 'var(--text)' }}>
          {flag.titulo}
        </h3>
        <p className="mt-1 text-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>
          {flag.descripcion}
        </p>
        {flag.ruta_frontend && (
          <p className="mt-2 text-[10px] font-mono" style={{ color: 'var(--text-faint)' }}>
            UI: {flag.ruta_frontend}
          </p>
        )}
      </div>

      <div className="flex items-center justify-between pt-2 border-t" style={{ borderColor: 'var(--border)' }}>
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
          {flag.enabled ? 'Visible para colaboradores' : 'Oculto para colaboradores'}
        </span>
        <Toggle checked={flag.enabled} disabled={saving} onChange={onToggle} />
      </div>
    </div>
  )
}

function Toggle({ checked, disabled, onChange }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={onChange}
      className="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
      style={{
        background: checked ? 'var(--brand)' : 'var(--surface-2)',
        border: '1px solid var(--border)',
        opacity: disabled ? 0.5 : 1,
        cursor: disabled ? 'not-allowed' : 'pointer',
      }}
    >
      <span
        className="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
        style={{ transform: checked ? 'translateX(22px)' : 'translateX(4px)' }}
      />
    </button>
  )
}

function ConfirmModal({ flag, onConfirm, onCancel }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.5)' }}>
      <div className="card p-6 max-w-md mx-4 space-y-4">
        <div className="flex items-center gap-3">
          <AlertTriangle size={24} className="text-amber-500 shrink-0" />
          <div>
            <h3 className="font-semibold" style={{ color: 'var(--text)' }}>Activar requisito pendiente</h3>
            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
              <b>{flag.codigo}</b> ({flag.titulo}) todavía no está implementado. Si lo activás,
              los colaboradores verán el ítem en el sidebar pero la página estará vacía.
            </p>
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button onClick={onCancel} className="btn btn-ghost">Cancelar</button>
          <button onClick={onConfirm} className="btn btn-primary">Activar igual</button>
        </div>
      </div>
    </div>
  )
}
