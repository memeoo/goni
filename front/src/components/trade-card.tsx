import { Clock, TrendingUp, TrendingDown, FileText, CheckCircle } from 'lucide-react'

interface TradeData {
  id?: number  // Trading 테이블의 ID
  stock_code: string
  stock_name: string
  trade_type: string  // '매수' 또는 '매도'
  price: number
  quantity: number
  datetime: string  // YYYYMMDDHHmmss
  order_no?: string
  has_recap?: boolean
}

interface TradeCardProps {
  trade?: TradeData
  onClick?: (tradeId: number) => void
}

export default function TradeCard({ trade, onClick }: TradeCardProps) {
  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ko-KR').format(num)
  }

  const formatDateTime = (dateTimeStr: string) => {
    // YYYYMMDDHHmmss -> YYYY-MM-DD HH:mm 또는 ISO 형식 지원
    if (!dateTimeStr) return ''

    let dateStr = String(dateTimeStr)

    // 만약 ISO 형식(YYYY-MM-DDTHH:mm:ss 형태)이면 파싱
    if (dateStr.includes('T') || dateStr.includes('-')) {
      try {
        const date = new Date(dateStr)
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        const hour = String(date.getHours()).padStart(2, '0')
        const minute = String(date.getMinutes()).padStart(2, '0')
        return `${year}-${month}-${day} ${hour}:${minute}`
      } catch {
        return dateStr
      }
    }

    // YYYYMMDDHHmmss 형식 처리
    if (dateStr.length === 14) {
      const year = dateStr.substring(0, 4)
      const month = dateStr.substring(4, 6)
      const day = dateStr.substring(6, 8)
      const hour = dateStr.substring(8, 10)
      const minute = dateStr.substring(10, 12)
      return `${year}-${month}-${day} ${hour}:${minute}`
    }

    return dateStr
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
      className={`bg-white border-2 rounded-lg p-4 min-h-[280px] hover:shadow-md transition-shadow cursor-pointer flex flex-col justify-between ${
        trade.has_recap
          ? 'border-green-400 bg-green-50'
          : 'border-gray-200'
      }`}
      onClick={() => trade.id && onClick?.(trade.id)}
    >
      <div>
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-gray-900">{trade.stock_name}</h3>
              {trade.has_recap && (
                <CheckCircle className="h-5 w-5 text-green-600" />
              )}
            </div>
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

      {/* Order Number & Recap Status */}
      <div className="mt-3 pt-3 border-t border-gray-100">
        {trade.order_no && (
          <p className="text-xs text-gray-400 mb-1">
            주문번호: {trade.order_no}
          </p>
        )}
        {trade.has_recap ? (
          <div className="flex items-center gap-1 text-xs text-green-600 font-medium">
            <CheckCircle className="h-3 w-3" />
            <span>복기 완료</span>
          </div>
        ) : (
          <p className="text-xs text-orange-500 font-medium">
            복기 미작성
          </p>
        )}
      </div>
    </div>
  )
}
