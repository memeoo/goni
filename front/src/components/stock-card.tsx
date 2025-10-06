'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatCurrency, formatPercent, formatNumber, cn } from '@/lib/utils'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { Stock } from '@/types'

interface StockCardProps {
  stock: Stock
  onClick?: () => void
}

export function StockCard({ stock, onClick }: StockCardProps) {
  const isPositive = stock.change_rate >= 0
  const changeColor = isPositive ? 'text-red-500' : 'text-blue-500'
  const TrendIcon = isPositive ? TrendingUp : TrendingDown

  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:shadow-md',
        onClick && 'hover:scale-[1.02]'
      )}
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">{stock.name}</CardTitle>
          <Badge variant="outline" className="text-xs">
            {stock.market}
          </Badge>
        </div>
        <p className="text-sm text-gray-500">{stock.symbol}</p>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold">
              {formatCurrency(stock.current_price)}
            </span>
            <div className={cn('flex items-center space-x-1', changeColor)}>
              <TrendIcon className="h-4 w-4" />
              <span className="font-semibold">
                {formatPercent(stock.change_rate)}
              </span>
            </div>
          </div>
          
          <div className="flex justify-between text-sm text-gray-600">
            <span>거래량</span>
            <span>{formatNumber(stock.volume)}</span>
          </div>
          
          <div className="flex justify-between text-sm text-gray-500">
            <span>업데이트</span>
            <span>
              {new Date(stock.updated_at).toLocaleTimeString('ko-KR', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}