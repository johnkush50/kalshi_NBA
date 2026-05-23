import { Loader2 } from 'lucide-react'

interface LoadingProps {
  message?: string
  size?: 'sm' | 'md' | 'lg'
}

export default function Loading({ message = 'Loading...', size = 'md' }: LoadingProps) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  }

  return (
    <div className="flex flex-col items-center justify-center py-8 gap-3">
      <Loader2 className={`${sizes[size]} text-neon-cyan animate-spin`} />
      <span className="text-sm font-mono text-slate-400">{message}</span>
    </div>
  )
}
