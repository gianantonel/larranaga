export const formatCurrency = (value) => {
  if (value == null) return '—'
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(value)
}

// Formato compacto para mobile/tablet: "$ 1,6M", "$ 28,5M", "$ 163,9M", "$ 1,2B"
export const formatCurrencyShort = (value) => {
  if (value == null) return '—'
  const v = Number(value) || 0
  const abs = Math.abs(v)
  const sign = v < 0 ? '-' : ''
  let n, suffix
  if (abs >= 1_000_000_000) { n = v / 1_000_000_000; suffix = 'B' }
  else if (abs >= 1_000_000) { n = v / 1_000_000; suffix = 'M' }
  else if (abs >= 1_000)     { n = v / 1_000;     suffix = 'K' }
  else                        { return formatCurrency(v) }
  // 1 decimal si <100, 0 decimales si >=100
  const dec = Math.abs(n) >= 100 ? 0 : 1
  const formatted = new Intl.NumberFormat('es-AR', {
    minimumFractionDigits: dec, maximumFractionDigits: dec,
  }).format(n)
  return `${sign}$ ${formatted.replace('-', '')}${suffix}`
}

export const formatNumber = (value) => {
  if (value == null) return '—'
  return new Intl.NumberFormat('es-AR').format(value)
}

export const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  const d = new Date(dateStr + (dateStr.includes('T') ? '' : 'T00:00:00'))
  return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export const formatPeriod = (period) => {
  if (!period) return '—'
  const [year, month] = period.split('-')
  const months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
  return `${months[parseInt(month) - 1]} ${year}`
}

export const formatDateTime = (dateStr) => {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleString('es-AR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

export const taskStatusConfig = {
  pendiente:   { label: 'Pendiente',   className: 'badge-yellow', dot: 'bg-amber-400' },
  en_curso:    { label: 'En curso',    className: 'badge-blue',   dot: 'bg-sky-400' },
  terminada:   { label: 'Terminada',   className: 'badge-green',  dot: 'bg-emerald-400' },
  bloqueada:   { label: 'Bloqueada',   className: 'badge-red',    dot: 'bg-rose-400' },
  postergada:  { label: 'Postergada',  className: 'badge-orange', dot: 'bg-orange-400' },
}

export const taskTypeConfig = {
  facturacion:          { label: 'Facturación',        color: '#6366f1', icon: '🧾' },
  comprobantes:         { label: 'Comprobantes',       color: '#0ea5e9', icon: '📋' },
  ddjj_iva:             { label: 'DDJJ IVA',           color: '#10b981', icon: '📊' },
  ddjj_ganancias:       { label: 'DDJJ Ganancias',     color: '#f59e0b', icon: '💰' },
  ddjj_bienes_personales:{ label: 'Bienes Personales', color: '#f97316', icon: '🏠' },
  ingresos_brutos:      { label: 'Ingresos Brutos',    color: '#a78bfa', icon: '📈' },
  legal:                { label: 'Legal',              color: '#f43f5e', icon: '⚖️' },
  otros:                { label: 'Otros',              color: '#9ca3af', icon: '📁' },
}

export const roleConfig = {
  admin1:       { label: 'Administrador 1', className: 'badge-purple' },
  admin2:       { label: 'Administrador 2', className: 'badge-purple' },
  admin3:       { label: 'Administrador 3', className: 'badge-purple' },
  collaborator: { label: 'Colaborador',     className: 'badge-blue' },
}

export const CHART_COLORS = [
  '#7c3aed', '#0ea5e9', '#10b981', '#f59e0b',
  '#f43f5e', '#6366f1', '#a78bfa', '#34d399',
]
