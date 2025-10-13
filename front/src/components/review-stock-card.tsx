import { Calendar, TrendingUp, TrendingDown, FileText, BarChart3 } from 'lucide-react'
import TradeInfo from './trade-info'
import StockCandlestickChart from './stock-candlestick-chart'
import { useCurrentPrice } from '@/lib/hooks/use-current-price'
import { useChartData } from '@/lib/hooks/use-chart-data'

interface TradingRecord {
  id: number
  stock_name: string
  stock_symbol: string
  entry_date: string
  exit_date?: string
  entry_price: number
  exit_price?: number
  quantity: number
  plan_summary: string
  result_summary?: string
  profit_loss?: number
  review_notes?: string
}

interface ReviewStockCardProps {
  record?: TradingRecord
  onClick?: () => void
}

// 차트 섹션 컴포넌트
function ChartSection({ stockCode }: { stockCode: string }) {
  const { data: chartData, isLoading, error } = useChartData(stockCode, 25)

  if (isLoading) {
    return (
      <div className="bg-gray-50 rounded-lg h-32 flex items-center justify-center">
        <div className="text-center">
          <BarChart3 className="h-6 w-6 text-gray-400 mx-auto mb-1 animate-pulse" />
          <span className="text-xs text-gray-500">차트 로딩 중...</span>
        </div>
      </div>
    )
  }

  if (error || !chartData?.data?.length) {
    return (
      <div className="bg-gray-50 rounded-lg h-32 flex items-center justify-center">
        <div className="text-center">
          <BarChart3 className="h-6 w-6 text-gray-400 mx-auto mb-1" />
          <span className="text-xs text-gray-500">
            {error ? '차트 로드 실패' : '차트 데이터 없음'}
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg">
      <StockCandlestickChart 
        data={chartData.data} 
        height={120}
        className="w-full"
      />
    </div>
  )
}

export default function ReviewStockCard({ record, onClick }: ReviewStockCardProps) {
  // 실제 현재가 데이터 조회
  const { data: currentPriceData } = useCurrentPrice(record?.stock_symbol || '')

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ko-KR').format(num)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric'
    })
  }

  // Empty card when no record data
  if (!record) {
    return (
      <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-4 min-h-[350px] flex flex-col items-center justify-center hover:border-gray-400 transition-colors cursor-pointer">
        <FileText className="h-12 w-12 text-gray-400 mb-2" />
        <p className="text-gray-500 text-sm">복기 내용이 없습니다</p>
      </div>
    )
  }

  const isCompleted = record.exit_date && record.exit_price && record.profit_loss !== undefined
  const profitLoss = record.profit_loss || 0
  const isProfit = profitLoss > 0

  return (
    <div 
      className="bg-white border border-gray-200 rounded-lg p-4 min-h-[350px] hover:shadow-md transition-shadow cursor-pointer flex flex-col justify-between"
      onClick={onClick}
    >
      <div>
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{record.stock_name}</h3>
            <p className="text-sm text-gray-500">{record.stock_symbol}</p>
          </div>
          <div className="flex items-center text-sm text-gray-500">
            <Calendar className="h-4 w-4 mr-1" />
            {formatDate(record.entry_date)}
          </div>
        </div>

        {/* Chart */}
        <div className="mb-3">
          <ChartSection stockCode={record.stock_symbol} />
        </div>

        {/* Trading Summary */}
        <div className="mb-4">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-gray-500">진입가:</span>
              <span className="ml-2 font-medium">{formatNumber(record.entry_price)}원</span>
            </div>
            {isCompleted && (
              <div>
                <span className="text-gray-500">청산가:</span>
                <span className="ml-2 font-medium">{formatNumber(record.exit_price!)}원</span>
              </div>
            )}
            <div>
              <span className="text-gray-500">수량:</span>
              <span className="ml-2 font-medium">{formatNumber(record.quantity)}주</span>
            </div>
            {isCompleted && (
              <div className="flex items-center">
                <span className="text-gray-500">손익:</span>
                <div className="ml-2 flex items-center">
                  {isProfit ? (
                    <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-600 mr-1" />
                  )}
                  <span className={`font-medium ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
                    {isProfit ? '+' : ''}{formatNumber(profitLoss)}원
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Trade Info */}
        <TradeInfo stockCode={record.stock_symbol} latestVolume={currentPriceData?.volume} />

        {/* Plan Summary */}
        <div className="mb-4 mt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-1">매매 계획</h4>
          <p className="text-sm text-gray-600 line-clamp-2">
            {record.plan_summary}
          </p>
        </div>

        {/* Result & Review */}
        {isCompleted && (
          <div className="space-y-3">
            {record.result_summary && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-1">거래 결과</h4>
                <p className="text-sm text-gray-600 line-clamp-2">
                  {record.result_summary}
                </p>
              </div>
            )}
            
            {record.review_notes && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-1">복기 노트</h4>
                <p className="text-sm text-gray-600 line-clamp-2">
                  {record.review_notes}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Status Badge */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          isCompleted 
            ? 'bg-green-100 text-green-800' 
            : 'bg-yellow-100 text-yellow-800'
        }`}>
          {isCompleted ? '완료' : '진행중'}
        </span>
      </div>
    </div>
  )
}