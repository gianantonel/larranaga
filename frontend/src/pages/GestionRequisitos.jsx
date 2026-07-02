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
  const { isAdmin, isSuperAdmin } = useAuth()
  const { flags, loading, setFlag, verificationMode, toggleVerificationMode } = useFeatureFlags()
  const [activeFase, setActiveFase] = useState(1)
  const [confirmFlag, setConfirmFlag] = useState(null)   // { flag, field }
  const [savingCodigo, setSavingCodigo] = useState(null)

  // admin y super_admin gestionan qué acciones ve el nivel de abajo
  if (!isAdmin) return <Navigate to="/dashboard" replace />

  // field: 'enabled_admin' (super_admin → admin) | 'enabled' (admin → colaborador)
  const handleToggle = async (flag, field) => {
    const newValue = !flag[field]
    if (newValue && !flag.implementado) {
      setConfirmFlag({ flag, field })
      return
    }
    setSavingCodigo(flag.codigo)
    try { await setFlag(flag.codigo, { [field]: newValue }) }
    finally { setSavingCodigo(null) }
  }

  const confirmActivate = async () => {
    const { flag, field } = confirmFlag
    setConfirmFlag(null)
    setSavingCodigo(flag.codigo)
    try { await setFlag(flag.codigo, { [field]: true }) }
    finally { setSavingCodigo(null) }
  }

  if (loading) return <div className="flex items-center justify-center min-h-[40vh]"><LoadingSpinner /></div>

  const flagsFase = flags.filter(f => f.fase === activeFase)
  // El admin solo ve/gestiona lo que el super_admin le habilitó.
  const flagsVisibles = isSuperAdmin ? flagsFase : flagsFase.filter(f => f.enabled_admin)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Gestión de Requisitos"
        subtitle={isSuperAdmin
          ? 'Elegí qué ve el admin y qué ve el colaborador. El colaborador nunca ve algo que el admin no ve.'
          : 'Elegí qué acciones ve el colaborador. Solo aparecen las que el super_admin te habilitó.'}
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
        {flagsVisibles.map(flag => (
          <RequirementCard
            key={flag.codigo}
            flag={flag}
            isSuperAdmin={isSuperAdmin}
            saving={savingCodigo === flag.codigo}
            onToggleAdmin={() => handleToggle(flag, 'enabled_admin')}
            onToggleColab={() => handleToggle(flag, 'enabled')}
          />
        ))}
        {flagsVisibles.length === 0 && (
          <p className="col-span-full text-sm" style={{ color: 'var(--text-muted)' }}>
            {isSuperAdmin ? 'No hay requisitos en esta fase.' : 'El super_admin no te habilitó requisitos en esta fase.'}
          </p>
        )}
      </div>

      {confirmFlag && (
        <ConfirmModal
          flag={confirmFlag.flag}
          onConfirm={confirmActivate}
          onCancel={() => setConfirmFlag(null)}
        />
      )}
    </div>
  )
}

function RequirementCard({ flag, isSuperAdmin, saving, onToggleAdmin, onToggleColab }) {
  const { statusIcon, statusLabel, statusColor } = (() => {
    if (!flag.implementado) return {
      statusIcon: <AlertTriangle size={13} />, statusLabel: 'Sin implementar', statusColor: '#9ca3af',
    }
    if (flag.enabled) return {
      statusIcon: <CheckCircle2 size={13} />, statusLabel: 'Activo', statusColor: '#10b981',
    }
    return {
      statusIcon: <Clock size={13} />, statusLabel: 'Listo, inactivo', statusColor: '#f59e0b',
    }
  })()

  return (
    <div className="card p-4 flex flex-col gap-3" style={{ minHeight: 200 }}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <RequirementBadge flag={flag} size="md" />
          <span className="text-xs truncate" style={{ color: 'var(--text-muted)' }}>
            {flag.area} · {flag.dificultad}
          </span>
        </div>
        <span
          className="flex items-center gap-1 text-[11px] font-medium shrink-0"
          style={{ color: statusColor }}
        >
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
            {flag.ruta_frontend}
          </p>
        )}
      </div>

      <div className="pt-2 border-t space-y-2" style={{ borderColor: 'var(--border)' }}>
        {isSuperAdmin && (
          <div className="flex items-center justify-between">
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Ve el admin</span>
            <Toggle checked={flag.enabled_admin} disabled={saving} onChange={onToggleAdmin} />
          </div>
        )}
        <div className="flex items-center justify-between">
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Ve el colaborador</span>
          <Toggle
            checked={flag.enabled}
            disabled={saving || (isSuperAdmin && !flag.enabled_admin)}
            onChange={onToggleColab}
          />
        </div>
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
        background: checked ? '#10b981' : 'var(--surface-2)',
        border: `1px solid ${checked ? '#10b981' : 'var(--border)'}`,
        opacity: disabled ? 0.4 : 1,
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
              se verá el ítem en el sidebar pero la página estará vacía.
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
