export default function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
      <div>
        <h1 className="text-2xl font-bold text-white">{title}</h1>
        {subtitle && <p className="text-gray-400 mt-0.5 text-base">{subtitle}</p>}
      </div>
      {children && <div className="flex items-center gap-3 w-full sm:w-auto">{children}</div>}
    </div>
  )
}
