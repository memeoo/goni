'use client'

import { BarChart3 } from 'lucide-react'
import { useChartData } from '@/lib/hooks/use-chart-data'
import { useCurrentPrice } from '@/lib/hooks/use-current-price'
import TradeInfo from './trade-info';

interface Stock {
  id: number
  symbol: string
  name: string
  current_price: number
  change_rate: number
  volume: number
}

interface PlanStockCardProps {
  stock?: Stock
  onClick?: () => void
}

// 차트 섹션 컴포넌트
function ChartSection({ stockCode }: { stockCode: string }) {
  const { data: chartData, isLoading, error } = useChartData(stockCode, 25)

  if (isLoading) {
    return (
      <div className="bg-gray-50 rounded-lg h-60 flex items-center justify-center">
        <div className="text-center">
          <BarChart3 className="h-8 w-8 text-gray-400 mx-auto mb-2 animate-pulse" />
          <span className="text-sm text-gray-500">차트 로딩 중...</span>
        </div>
      </div>
    )
  }

  if (error || !chartData?.data?.length) {
    return (
      <div className="bg-gray-50 rounded-lg h-60 flex items-center justify-center">
        <div className="text-center">
          <BarChart3 className="h-8 w-8 text-gray-400 mx-auto mb-2" />
          <span className="text-sm text-gray-500">
            {error ? '차트 데이터 로드 실패' : '차트 데이터 없음'}
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg">
      {/* <StockCandlestickChart 
        data={chartData.data} 
        height={240}
        className="w-full"
        stockCode={stockCode}
      /> */}
    </div>
  )
}

export default function PlanStockCard({ stock, onClick }: PlanStockCardProps) {
  // 실제 현재가 데이터 조회
  const { data: currentPriceData, isLoading: priceLoading } = useCurrentPrice(stock?.symbol || '')

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ko-KR').format(num)
  }

  const formatVolume = (volume: number) => {
    if (volume >= 10000000) {
      return `${(volume / 10000000).toFixed(1)}천만`
    } else if (volume >= 10000) {
      return `${(volume / 10000).toFixed(1)}만`
    }
    return formatNumber(volume)
  }

  // 실제 데이터가 있으면 사용, 없으면 기본 데이터 사용
  const displayPrice = currentPriceData?.current_price || stock?.current_price || 0
  const displayChangeRate = currentPriceData?.change_rate || stock?.change_rate || 0
  const displayChangePrice = currentPriceData?.change_price || 0
  const displayVolume = currentPriceData?.volume || stock?.volume || 0

  // Empty card when no stock data
  if (!stock) {
    return (
      <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-4 min-h-[380px] flex flex-col items-center justify-center hover:border-gray-400 transition-colors cursor-pointer">
        <BarChart3 className="h-12 w-12 text-gray-400 mb-2" />
        <p className="text-gray-500 text-sm">종목을 추가해주세요</p>
      </div>
    )
  }

  return (
    <div 
      className="bg-white border border-gray-200 rounded-lg p-4 min-h-[380px] hover:shadow-md transition-shadow cursor-pointer flex flex-col justify-between"
      onClick={onClick}
    >
      {/* Stock Header with Price Info */}
      <div>
        <div className="mb-2">
          <div className="flex justify-between items-start mb-2">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{stock.name}</h3>
              <p className="text-sm text-gray-500">{stock.symbol}</p>
            </div>
            <div className="text-right">
              {priceLoading ? (
                <div className="text-xl font-bold text-gray-400 animate-pulse">
                  로딩중...
                </div>
              ) : (
                <>
                  <div className="text-xl font-bold text-gray-900">
                    {formatNumber(displayPrice)}원
                  </div>
                  <div className="flex items-center justify-end">
                    <span className={`text-sm font-medium ${
                      displayChangeRate >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {displayChangeRate >= 0 ? '+' : ''}{displayChangeRate}%
                    </span>
                    <span className={`text-sm font-medium ml-2 ${
                      displayChangeRate >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      ({displayChangeRate >= 0 ? '+' : ''}{formatNumber(displayChangePrice)}원)
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="mb-0">
          <ChartSection stockCode={stock.symbol} />
        </div>
      </div>

      {/* Trade Info */}
      <TradeInfo stockCode={stock.symbol} latestVolume={displayVolume} />
    </div>
  )
}