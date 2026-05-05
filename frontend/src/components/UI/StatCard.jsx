import clsx from 'clsx'

export default function StatCard({ title, value, valueShort, subtitle, icon: Icon, color = 'violet', trend }) {
  const colorMap = {
    violet:  { bg: 'bg-violet-500/15', text: 'text-violet-400', border: 'border-violet-500/20' },
    cyan:    { bg: 'bg-sky-500/15',    text: 'text-sky-400',    border: 'border-sky-500/20' },
    emerald: { bg: 'bg-emerald-500/15',text: 'text-emerald-400',border: 'border-emerald-500/20' },
    amber:   { bg: 'bg-amber-500/15',  text: 'text-amber-400',  border: 'border-amber-500/20' },
    rose:    { bg: 'bg-rose-500/15',   text: 'text-rose-400',   border: 'border-rose-500/20' },
    indigo:  { bg: 'bg-indigo-500/15', text: 'text-indigo-400', border: 'border-indigo-500/20' },
  }
  const c = colorMap[color] || colorMap.violet

  return (
    <div className={clsx('stat-card', 'border', c.border)}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-xs sm:text-sm font-medium text-gray-400 truncate">{title}</p>
          <p className={clsx('text-xl sm:text-2xl lg:text-3xl font-bold mt-1 break-words tabular-nums leading-tight', c.text)}>
            {valueShort != null ? (
              <>
                <span className="xl:hidden">{valueShort}</span>
                <span className="hidden xl:inline">{value}</span>
              </>
            ) : value}
          </p>
          {subtitle && <p className="text-xs sm:text-sm text-gray-500 mt-1 truncate">{subtitle}</p>}
        </div>
        {Icon && (
          <div className={clsx('p-2 sm:p-3 rounded-xl shrink-0', c.bg)}>
            <Icon size={20} className={c.text} />
          </div>
        )}
      </div>
      {trend != null && (
        <p className={clsx('text-sm font-medium', trend >= 0 ? 'text-emerald-400' : 'text-rose-400')}>
          {trend >= 0 ? '▲' : '▼'} {Math.abs(trend)}% vs mes anterior
        </p>
      )}
    </div>
  )
}
