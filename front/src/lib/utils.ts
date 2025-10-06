import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
  }).format(amount)
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat('ko-KR').format(num)
}

export function formatPercent(value: number, decimals = 2): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date(date))
}

export function formatDateTime(date: string | Date): string {
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date))
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null

  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

export function calculateProfit(
  buyPrice: number,
  sellPrice: number,
  quantity: number
): {
  profit: number
  profitRate: number
} {
  const profit = (sellPrice - buyPrice) * quantity
  const profitRate = ((sellPrice - buyPrice) / buyPrice) * 100

  return { profit, profitRate }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'planned':
      return 'text-blue-600 bg-blue-100'
    case 'executed':
      return 'text-orange-600 bg-orange-100'
    case 'reviewed':
      return 'text-green-600 bg-green-100'
    default:
      return 'text-gray-600 bg-gray-100'
  }
}

export function getRecommendationColor(recommendation: string): string {
  switch (recommendation) {
    case 'strong_buy':
      return 'text-green-700 bg-green-100'
    case 'buy':
      return 'text-green-600 bg-green-50'
    case 'hold':
      return 'text-yellow-600 bg-yellow-100'
    case 'sell':
      return 'text-red-600 bg-red-50'
    case 'strong_sell':
      return 'text-red-700 bg-red-100'
    default:
      return 'text-gray-600 bg-gray-100'
  }
}

export function getRecommendationText(recommendation: string): string {
  switch (recommendation) {
    case 'strong_buy':
      return '적극 매수'
    case 'buy':
      return '매수'
    case 'hold':
      return '보유'
    case 'sell':
      return '매도'
    case 'strong_sell':
      return '적극 매도'
    default:
      return '알 수 없음'
  }
}