'use client'

import { BarChart3, X } from 'lucide-react'
import { useState } from 'react'

interface Stock {
  id: number
  stock_code: string
  stock_name: string
  is_downloaded?: boolean
}

interface PlanStockCardProps {
  stock?: Stock
  onClick?: (stock: Stock) => void
  onDelete?: (stockId: number) => void
}

export default function PlanStockCard({ stock, onClick, onDelete }: PlanStockCardProps) {
  const [isHovering, setIsHovering] = useState(false)

  // Empty card when no stock data
  if (!stock) {
    return (
      <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-2 sm:p-4 min-h-[100px] sm:min-h-[200px] flex flex-col items-center justify-center hover:border-gray-400 transition-colors cursor-pointer">
        <BarChart3 className="h-8 sm:h-12 w-8 sm:w-12 text-gray-400 mb-1 sm:mb-2" />
        <p className="text-gray-500 text-xs sm:text-sm">종목을 추가해주세요</p>
      </div>
    )
  }

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation() // 카드 클릭 이벤트 전파 방지
    if (onDelete) {
      onDelete(stock.id)
    }
  }

  return (
    <div
      className="relative bg-white border border-gray-200 rounded-lg p-2 sm:p-4 min-h-[80px] sm:min-h-[200px] hover:shadow-md transition-shadow cursor-pointer flex flex-col justify-center"
      onClick={() => onClick?.(stock)}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      {/* Delete Button */}
      {isHovering && (
        <button
          onClick={handleDeleteClick}
          className="absolute top-1 sm:top-2 right-1 sm:right-2 p-1 sm:p-1.5 bg-red-500 hover:bg-red-600 text-white rounded-full transition-colors z-10"
          title="삭제"
          aria-label="종목 삭제"
        >
          <X className="h-3 sm:h-4 w-3 sm:w-4" />
        </button>
      )}

      {/* Stock Name */}
      <div>
        <h3 className="text-sm sm:text-lg font-semibold text-gray-900">{stock.stock_name}</h3>
        <p className="text-xs sm:text-sm text-gray-500">{stock.stock_code}</p>
      </div>
    </div>
  )
}