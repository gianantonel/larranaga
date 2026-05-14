import clsx from 'clsx'

/**
 * StatCard — Apple-minimalist
 *
 * Diferencia respecto al diseño anterior: paleta neutral en light/dark,
 * acento solo en el icono. La tipografía hace el trabajo, no el color.
 */
export default function StatCard({
  title, value, valueShort, subtitle, icon: Icon, color = 'brand', trend,
}) {
  // Colors usan CSS variables — funcionan en light y dark
  const iconBg = {
    brand:   { bg: 'var(--brand-soft)',                color: 'var(--brand)' },
    success: { bg: 'rgba(16,185,129,0.10)',            color: '#059669' },
    warning: { bg: 'rgba(245,158,11,0.10)',            color: '#D97706' },
    danger:  { bg: 'rgba(239,68,68,0.10)',             color: '#DC2626' },
    info:    { bg: 'rgba(14,165,233,0.10)',            color: '#0284C7' },
    neutral: { bg: 'var(--surface-2)',                 color: 'var(--text-muted)' },
  }[color] || { bg: 'var(--brand-soft)', color: 'var(--brand)' }

  return (
    <div className="stat-card">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p
            className="text-xs sm:text-sm font-medium truncate"
            style={{ color: 'var(--text-muted)' }}
          >
            {title}
          </p>
          <p
            className="text-2xl sm:text-3xl font-bold mt-1.5 break-words tabular-nums leading-tight"
            style={{ color: 'var(--text)', letterSpacing: '-0.02em' }}
          >
            {valueShort != null ? (
              <>
                <span className="xl:hidden">{valueShort}</span>
                <span className="hidden xl:inline">{value}</span>
              </>
            ) : value}
          </p>
          {subtitle && (
            <p className="text-xs sm:text-sm mt-1 truncate" style={{ color: 'var(--text-subtle)' }}>
              {subtitle}
            </p>
          )}
        </div>
        {Icon && (
          <div
            className="p-2.5 rounded-2xl shrink-0"
            style={{ background: iconBg.bg, color: iconBg.color }}
          >
            <Icon size={18} />
          </div>
        )}
      </div>
      {trend != null && (
        <p
          className="text-xs font-medium mt-2"
          style={{ color: trend >= 0 ? '#10B981' : '#EF4444' }}
        >
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% vs mes anterior
        </p>
      )}
    </div>
  )
}
