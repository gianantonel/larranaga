import clsx from 'clsx'
import { taskStatusConfig, taskTypeConfig, roleConfig } from '../../utils/helpers'

export function StatusBadge({ status }) {
  const config = taskStatusConfig[status] || { label: status, className: 'badge-gray' }
  return (
    <span className={config.className}>
      <span className={clsx('w-1.5 h-1.5 rounded-full', config.dot)} />
      {config.label}
    </span>
  )
}

export function TypeBadge({ type }) {
  const config = taskTypeConfig[type] || { label: type, color: '#9ca3af', icon: '📁' }
  return (
    <span className="badge border" style={{ backgroundColor: config.color + '20', color: config.color, borderColor: config.color + '40' }}>
      {config.icon} {config.label}
    </span>
  )
}

export function RoleBadge({ role }) {
  const config = roleConfig[role] || { label: role, className: 'badge-gray' }
  return <span className={config.className}>{config.label}</span>
}

export function FiledBadge({ filed }) {
  return filed
    ? <span className="badge-green">✓ Presentado</span>
    : <span className="badge-yellow">⏳ Pendiente</span>
}
