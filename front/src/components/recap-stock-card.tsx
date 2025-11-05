import { FileText } from 'lucide-react'

interface RecapStockData {
  id: number
  stock_code: string
  stock_name: string
  is_downloaded?: boolean
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

  return (
    <div
      className="bg-white border-2 border-gray-200 rounded-lg p-6 min-h-[180px] hover:shadow-md transition-shadow cursor-pointer flex flex-col justify-center items-center text-center group"
      onClick={() => onClick?.(stock)}
    >
      {/* Stock Info */}
      <div className="space-y-2">
        <h3 className="text-xl font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
          {stock.stock_name}
        </h3>
        <p className="text-sm text-gray-500 font-mono">
          {stock.stock_code}
        </p>
      </div>

      {/* Downloaded Status Badge */}
      {stock.is_downloaded !== undefined && (
        <div className="mt-4 pt-4 border-t border-gray-100 w-full">
          {stock.is_downloaded ? (
            <span className="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
              ✓ 데이터 완료
            </span>
          ) : (
            <span className="inline-block px-2 py-1 bg-gray-100 text-gray-800 text-xs font-medium rounded">
              데이터 미완료
            </span>
          )}
        </div>
      )}
    </div>
  )
}
