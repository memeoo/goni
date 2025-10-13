import { Clock, TrendingUp, TrendingDown, FileText } from 'lucide-react'

interface TradeData {
  stock_code: string
  stock_name: string
  trade_type: string  // '매수' 또는 '매도'
  price: number
  quantity: number
  datetime: string  // YYYYMMDDHHmmss
  order_no?: string
}

interface TradeCardProps {
  trade?: TradeData
  onClick?: () => void
}

export default function TradeCard({ trade, onClick }: TradeCardProps) {
  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ko-KR').format(num)
  }

  const formatDateTime = (dateTimeStr: string) => {
    // YYYYMMDDHHmmss -> YYYY-MM-DD HH:mm
    if (!dateTimeStr || dateTimeStr.length !== 14) return dateTimeStr

    const year = dateTimeStr.substring(0, 4)
    const month = dateTimeStr.substring(4, 6)
    const day = dateTimeStr.substring(6, 8)
    const hour = dateTimeStr.substring(8, 10)
    const minute = dateTimeStr.substring(10, 12)

    return `${year}-${month}-${day} ${hour}:${minute}`
  }

  // Empty card when no trade data
  if (!trade) {
    return (
      <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-4 min-h-[280px] flex flex-col items-center justify-center hover:border-gray-400 transition-colors">
        <FileText className="h-12 w-12 text-gray-400 mb-2" />
        <p className="text-gray-500 text-sm">매매 내역이 없습니다</p>
      </div>
    )
  }

  const isBuy = trade.trade_type === '매수'
  const totalAmount = trade.price * trade.quantity

  return (
    <div
      className="bg-white border border-gray-200 rounded-lg p-4 min-h-[280px] hover:shadow-md transition-shadow cursor-pointer flex flex-col justify-between"
      onClick={onClick}
    >
      <div>
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{trade.stock_name}</h3>
            <p className="text-sm text-gray-500">{trade.stock_code}</p>
          </div>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            isBuy
              ? 'bg-red-100 text-red-800'
              : 'bg-blue-100 text-blue-800'
          }`}>
            {trade.trade_type}
          </div>
        </div>

        {/* Trading Details */}
        <div className="space-y-3 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">체결가:</span>
            <div className="flex items-center">
              {isBuy ? (
                <TrendingUp className="h-4 w-4 text-red-600 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 text-blue-600 mr-1" />
              )}
              <span className={`font-semibold ${isBuy ? 'text-red-600' : 'text-blue-600'}`}>
                {formatNumber(trade.price)}원
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">체결수량:</span>
            <span className="font-medium text-gray-900">
              {formatNumber(trade.quantity)}주
            </span>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-gray-100">
            <span className="text-sm text-gray-600">총 금액:</span>
            <span className="font-semibold text-gray-900">
              {formatNumber(totalAmount)}원
            </span>
          </div>
        </div>

        {/* Date & Time */}
        <div className="flex items-center text-sm text-gray-500 mt-4">
          <Clock className="h-4 w-4 mr-1" />
          {formatDateTime(trade.datetime)}
        </div>
      </div>

      {/* Order Number (Optional) */}
      {trade.order_no && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-400">
            주문번호: {trade.order_no}
          </p>
        </div>
      )}
    </div>
  )
}
