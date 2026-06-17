import clsx from 'clsx'

export default function RequirementBadge({ flag, codigo, size = 'sm' }) {
  const code = codigo || flag?.codigo
  if (!code) return null

  let cls = 'badge-gray'
  let title = code
  if (flag) {
    title = `${flag.codigo} — ${flag.titulo}`
    if (!flag.implementado) cls = 'badge-gray'
    else if (flag.enabled) cls = 'badge-green'
    else cls = 'badge-yellow'
  }

  return (
    <span
      className={clsx(cls, size === 'sm' ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-1')}
      title={title}
      style={{ fontFamily: 'ui-monospace, monospace' }}
    >
      {code}
    </span>
  )
}
