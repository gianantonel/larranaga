/**
 * StatCard — Apple-minimalist (Ciudad style)
 *
 * Default monochrome: icono en gris neutro, valor en text-color.
 * Solo usa color cuando aporta info real (status badges via 'color' prop).
 */
export default function StatCard({
  title, value, valueShort, subtitle, icon: Icon, color = 'neutral', trend,
}) {
  // Map colors → CSS vars (todos funcionan en light/dark)
  const palette = {
    neutral: { bg: 'var(--surface-2)',           color: 'var(--text-muted)' },
    brand:   { bg: 'var(--brand-soft)',          color: 'var(--brand)' },
    success: { bg: 'rgba(16,185,129,0.10)',      color: '#059669' },
    warning: { bg: 'rgba(245,158,11,0.10)',      color: '#B45309' },
    danger:  { bg: 'rgba(239,68,68,0.10)',       color: '#DC2626' },
    info:    { bg: 'rgba(14,165,233,0.10)',      color: '#0284C7' },
  }
  const c = palette[color] || palette.neutral

  return (
    <div className="stat-card">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="stat-label truncate">{title}</p>
          <p
            className="stat-value text-2xl sm:text-3xl mt-2 break-words leading-tight"
          >
            {valueShort != null ? (
              <>
                <span className="xl:hidden">{valueShort}</span>
                <span className="hidden xl:inline">{value}</span>
              </>
            ) : value}
          </p>
          {subtitle && (
            <p
              className="text-xs mt-1.5 truncate"
              style={{ color: 'var(--text-faint)' }}
            >
              {subtitle}
            </p>
          )}
        </div>
        {Icon && (
          <div
            className="p-2.5 rounded-2xl shrink-0"
            style={{ background: c.bg, color: c.color }}
          >
            <Icon size={16} strokeWidth={1.75} />
          </div>
        )}
      </div>
      {trend != null && (
        <p
          className="text-[11px] font-medium mt-3 tracking-tight"
          style={{ color: trend >= 0 ? '#059669' : '#DC2626' }}
        >
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% vs mes anterior
        </p>
      )}
    </div>
  )
}
