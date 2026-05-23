import { AlertTriangle, RefreshCw } from 'lucide-react'
import Button from './Button'

interface ErrorDisplayProps {
  message: string
  onRetry?: () => void
}

export default function ErrorDisplay({ message, onRetry }: ErrorDisplayProps) {
  return (
    <div className="flex flex-col items-center justify-center py-8 gap-4">
      <div className="flex items-center gap-2 text-neon-red">
        <AlertTriangle className="w-6 h-6" />
        <span className="font-mono text-sm">Error</span>
      </div>
      <p className="text-sm text-slate-400 text-center max-w-md">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" icon={<RefreshCw className="w-4 h-4" />} onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  )
}
