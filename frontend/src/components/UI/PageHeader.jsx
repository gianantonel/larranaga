export default function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4 mb-4 sm:mb-6">
      <div className="min-w-0">
        <h1 className="text-xl sm:text-2xl font-bold text-white truncate">{title}</h1>
        {subtitle && <p className="text-gray-400 mt-0.5 text-sm sm:text-base">{subtitle}</p>}
      </div>
      {children && (
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">{children}</div>
      )}
    </div>
  )
}
