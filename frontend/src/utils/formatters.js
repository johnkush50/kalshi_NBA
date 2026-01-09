export function formatCurrency(cents, showSign = false) {
  const dollars = cents / 100
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(Math.abs(dollars))
  
  if (showSign && cents !== 0) {
    return cents > 0 ? `+${formatted}` : `-${formatted}`
  }
  return cents < 0 ? `-${formatted}` : formatted
}

export function formatCents(cents, showSign = false) {
  const abs = Math.abs(cents).toFixed(1)
  if (showSign && cents !== 0) {
    return cents > 0 ? `+${abs}¢` : `-${abs}¢`
  }
  return cents < 0 ? `-${abs}¢` : `${abs}¢`
}

export function formatPercent(value, decimals = 1) {
  return `${value.toFixed(decimals)}%`
}

export function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatTime(dateString) {
  return new Date(dateString).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function getPnLColor(value) {
  if (value > 0) return 'text-profit'
  if (value < 0) return 'text-loss'
  return 'text-neutral'
}

export function getPnLBgColor(value) {
  if (value > 0) return 'bg-profit/20'
  if (value < 0) return 'bg-loss/20'
  return 'bg-neutral/20'
}
