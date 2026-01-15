import { ReactNode } from 'react'

interface PanelProps {
  title?: string
  subtitle?: string
  icon?: ReactNode
  headerAction?: ReactNode
  children: ReactNode
  className?: string
  neonBorder?: boolean
  variant?: 'default' | 'success' | 'danger'
}

export default function Panel({
  title,
  subtitle,
  icon,
  headerAction,
  children,
  className = '',
  neonBorder = false,
  variant = 'default'
}: PanelProps) {
  const borderClasses = {
    default: neonBorder ? 'neon-border' : 'border border-terminal-border',
    success: 'neon-border-green',
    danger: 'neon-border-red',
  }

  return (
    <div className={`bg-terminal-surface/80 backdrop-blur-sm rounded-lg ${borderClasses[variant]} corner-accents ${className}`}>
      {(title || headerAction) && (
        <div className="flex items-center justify-between px-5 py-4 border-b border-terminal-border">
          <div className="flex items-center gap-3">
            {icon && (
              <div className="p-2 bg-terminal-bg rounded-md border border-terminal-border">
                {icon}
              </div>
            )}
            <div>
              {title && (
                <h2 className="font-display font-semibold text-sm tracking-wide text-white uppercase">
                  {title}
                </h2>
              )}
              {subtitle && (
                <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
              )}
            </div>
          </div>
          {headerAction}
        </div>
      )}
      <div className="p-5">
        {children}
      </div>
    </div>
  )
}
