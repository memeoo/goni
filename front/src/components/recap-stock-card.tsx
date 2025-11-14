import { FileText } from 'lucide-react'

interface RecentTrade {
  trade_type: 'buy' | 'sell' | '매수' | '매도'
  executed_price: number
  executed_quantity: number
  executed_at: string
}

interface RecapStockData {
  id: number
  stock_code: string
  stock_name: string
  is_downloaded?: boolean
  recent_trades?: RecentTrade[]
}

interface RecapStockCardProps {
  stock?: RecapStockData
  onClick?: (stock: RecapStockData) => void
}

export default function RecapStockCard({ stock, onClick }: RecapStockCardProps) {
  // Empty card when no stock data
  if (!stock) {
    return (
      <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-2 sm:p-6 min-h-[90px] sm:min-h-[180px] flex flex-col items-center justify-center hover:border-gray-400 transition-colors">
        <FileText className="h-8 sm:h-12 w-8 sm:w-12 text-gray-400 mb-1 sm:mb-2" />
        <p className="text-gray-500 text-xs sm:text-sm">종목이 없습니다</p>
      </div>
    )
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${month}-${day}`
  }

  const getTradeLabel = (tradeType: string) => {
    if (tradeType === 'buy' || tradeType === '매수') {
      return '매수'
    }
    return '매도'
  }

  const getTradeColor = (tradeType: string) => {
    if (tradeType === 'buy' || tradeType === '매수') {
      return 'text-red-600' // Buy is red in Korean stock market
    }
    return 'text-blue-600' // Sell is blue
  }

  return (
    <div
      className="bg-white border-2 border-gray-200 rounded-lg p-2 sm:p-4 min-h-[90px] sm:min-h-[180px] hover:shadow-md transition-shadow cursor-pointer flex flex-col justify-between group"
      onClick={() => onClick?.(stock)}
    >
      {/* Stock Info */}
      <h3 className="text-sm sm:text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-1">
        {stock.stock_name}
      </h3>

      {/* Recent Trades */}
      {stock.recent_trades && stock.recent_trades.length > 0 && (
        <div className="space-y-0.5 sm:space-y-1 mt-1 sm:mt-3 pt-1 sm:pt-3 border-t border-gray-200">
          {stock.recent_trades.slice(0, 2).map((trade, index) => (
            <div key={index} className="text-2xs sm:text-xs flex justify-between items-center gap-1">
              <span className={`font-semibold whitespace-nowrap ${getTradeColor(trade.trade_type)}`}>
                {getTradeLabel(trade.trade_type)}
              </span>
              <span className="text-gray-700 text-right truncate">
                {trade.executed_price.toLocaleString()}원
              </span>
              <span className="text-gray-600 whitespace-nowrap">
                {trade.executed_quantity}주
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
