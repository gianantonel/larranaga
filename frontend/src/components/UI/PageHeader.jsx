export default function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 sm:gap-4">
      <div className="min-w-0">
        <h1
          className="text-2xl sm:text-3xl font-bold truncate"
          style={{ color: 'var(--text)', letterSpacing: '-0.03em' }}
        >
          {title}
        </h1>
        {subtitle && (
          <p className="mt-1 text-sm sm:text-base" style={{ color: 'var(--text-muted)' }}>
            {subtitle}
          </p>
        )}
      </div>
      {children && (
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">{children}</div>
      )}
    </div>
  )
}
