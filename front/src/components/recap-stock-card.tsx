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
      <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-6 min-h-[180px] flex flex-col items-center justify-center hover:border-gray-400 transition-colors">
        <FileText className="h-12 w-12 text-gray-400 mb-2" />
        <p className="text-gray-500 text-sm">종목이 없습니다</p>
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
      className="bg-white border-2 border-gray-200 rounded-lg p-4 min-h-[180px] hover:shadow-md transition-shadow cursor-pointer flex flex-col justify-between group"
      onClick={() => onClick?.(stock)}
    >
      {/* Stock Info */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
          {stock.stock_name}
        </h3>
        <p className="text-xs text-gray-500 font-mono">
          {stock.stock_code}
        </p>
      </div>

      {/* Recent Trades */}
      {stock.recent_trades && stock.recent_trades.length > 0 && (
        <div className="space-y-1 mt-3 pt-3 border-t border-gray-200">
          {stock.recent_trades.slice(0, 3).map((trade, index) => (
            <div key={index} className="text-xs flex justify-between items-center">
              <span className={`font-semibold ${getTradeColor(trade.trade_type)}`}>
                {getTradeLabel(trade.trade_type)}
              </span>
              <span className="text-gray-700">
                {trade.executed_price.toLocaleString()}원
              </span>
              <span className="text-gray-600">
                {trade.executed_quantity}주
              </span>
              <span className="text-gray-500">
                {formatDate(trade.executed_at)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
