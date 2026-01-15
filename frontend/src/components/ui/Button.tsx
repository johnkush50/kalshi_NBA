import { ReactNode, ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  icon?: ReactNode
  children: ReactNode
}

export default function Button({
  variant = 'primary',
  size = 'md',
  icon,
  children,
  className = '',
  ...props
}: ButtonProps) {
  const baseClasses = 'inline-flex items-center justify-center gap-2 font-medium font-mono uppercase tracking-wider transition-all duration-200 rounded-md disabled:opacity-50 disabled:cursor-not-allowed'

  const variantClasses = {
    primary: 'bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40 hover:bg-neon-cyan/30 hover:shadow-neon-cyan',
    secondary: 'bg-terminal-bg text-slate-300 border border-terminal-border hover:bg-terminal-hover hover:text-white',
    success: 'bg-neon-green/20 text-neon-green border border-neon-green/40 hover:bg-neon-green/30 hover:shadow-neon-green',
    danger: 'bg-neon-red/20 text-neon-red border border-neon-red/40 hover:bg-neon-red/30 hover:shadow-neon-red',
    ghost: 'text-slate-400 hover:text-white hover:bg-terminal-hover',
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-[10px]',
    md: 'px-4 py-2 text-xs',
    lg: 'px-6 py-3 text-sm',
  }

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {icon}
      {children}
    </button>
  )
}
