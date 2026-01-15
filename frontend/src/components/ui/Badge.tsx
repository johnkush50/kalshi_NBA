import { ReactNode } from 'react'

interface BadgeProps {
  variant?: 'default' | 'success' | 'danger' | 'warning' | 'info'
  size?: 'sm' | 'md'
  icon?: ReactNode
  children: ReactNode
  pulse?: boolean
}

export default function Badge({
  variant = 'default',
  size = 'sm',
  icon,
  children,
  pulse = false
}: BadgeProps) {
  const variantClasses = {
    default: 'bg-slate-700/50 text-slate-300 border-slate-600',
    success: 'bg-neon-green/10 text-neon-green border-neon-green/30',
    danger: 'bg-neon-red/10 text-neon-red border-neon-red/30',
    warning: 'bg-neon-yellow/10 text-neon-yellow border-neon-yellow/30',
    info: 'bg-neon-cyan/10 text-neon-cyan border-neon-cyan/30',
  }

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-xs',
  }

  return (
    <span className={`inline-flex items-center gap-1.5 font-mono font-medium uppercase tracking-wider rounded-full border ${variantClasses[variant]} ${sizeClasses[size]}`}>
      {pulse && (
        <span className="relative flex h-2 w-2">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
            variant === 'success' ? 'bg-neon-green' :
            variant === 'danger' ? 'bg-neon-red' :
            variant === 'warning' ? 'bg-neon-yellow' :
            'bg-neon-cyan'
          }`} />
          <span className={`relative inline-flex rounded-full h-2 w-2 ${
            variant === 'success' ? 'bg-neon-green' :
            variant === 'danger' ? 'bg-neon-red' :
            variant === 'warning' ? 'bg-neon-yellow' :
            'bg-neon-cyan'
          }`} />
        </span>
      )}
      {icon}
      {children}
    </span>
  )
}
