/**
 * Logo Larrañaga & Asociados
 * Triángulo "A" rojo (#9D1626 en light, #DC2626 en dark) + texto.
 * Replica el isologo del estudio: estudiolarranaga.com
 */
export default function Logo({ size = 'md', showSubtitle = true, variant = 'horizontal' }) {
  const sizes = {
    sm: { mark: 24, title: 'text-base',  sub: 'text-[8px]'  },
    md: { mark: 36, title: 'text-xl',    sub: 'text-[10px]' },
    lg: { mark: 52, title: 'text-3xl',   sub: 'text-xs'     },
    xl: { mark: 72, title: 'text-5xl',   sub: 'text-sm'     },
  }
  const s = sizes[size] || sizes.md

  const Mark = (
    <svg
      width={s.mark}
      height={s.mark}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="shrink-0"
      aria-hidden="true"
    >
      {/* Triángulo principal (rojo brand) */}
      <path
        d="M50 8 L92 86 L8 86 Z"
        style={{ fill: 'var(--brand)' }}
      />
      {/* Triángulo interior negativo (hace la "A") */}
      <path
        d="M50 36 L72 76 L28 76 Z"
        style={{ fill: 'var(--bg)' }}
      />
      {/* Travesaño de la A */}
      <rect x="36" y="62" width="28" height="6" style={{ fill: 'var(--brand)' }} />
    </svg>
  )

  if (variant === 'mark') return Mark

  return (
    <div className="flex items-center gap-3 select-none">
      {Mark}
      <div className="flex flex-col leading-tight">
        <span
          className={`${s.title} font-bold tracking-tight`}
          style={{ color: 'var(--text)', letterSpacing: '-0.02em' }}
        >
          LARRAÑAGA
        </span>
        {showSubtitle && (
          <span
            className={`${s.sub} font-medium uppercase tracking-[0.2em]`}
            style={{ color: 'var(--text-muted)' }}
          >
            & Asociados
          </span>
        )}
      </div>
    </div>
  )
}
