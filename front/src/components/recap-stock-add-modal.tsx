'use client'

import { useState, useCallback } from 'react'
import { Search, X, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { stocksInfoAPI, tradingAPI } from '@/lib/api'
import { useToast } from '@/lib/use-toast'

interface StockInfo {
  id: number
  code: string
  name: string
  market_code: string
  market_name: string
  last_price: string
}

interface TradeFormData {
  tradeType: 'buy' | 'sell'
  executedPrice: number
  executedDate: string
  executedTime: string
  executedQuantity: number
}

const debounce = (func: Function, delay: number) => {
  let timeoutId: NodeJS.Timeout
  return (...args: any[]) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay)
  }
}

export default function RecapStockAddModal({ isOpen, onClose, onStockAdded }: {
  isOpen: boolean
  onClose: () => void
  onStockAdded: () => void
}) {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<StockInfo[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [selectedStock, setSelectedStock] = useState<StockInfo | null>(null)
  const [expandedStockCode, setExpandedStockCode] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  const [tradeForm, setTradeForm] = useState<TradeFormData>({
    tradeType: 'buy',
    executedPrice: 0,
    executedDate: new Date().toISOString().split('T')[0],
    executedTime: '09:30',
    executedQuantity: 0,
  })

  // Debounced search function
  const performSearch = useCallback(
    debounce(async (query: string) => {
      if (!query.trim()) {
        setSearchResults([])
        setIsSearching(false)
        return
      }

      setIsSearching(true)
      try {
        const response = await stocksInfoAPI.searchStocksInfo(query, undefined, 0, 50)
        const stocks = response.data?.data || []
        setSearchResults(stocks)
      } catch (error) {
        console.error('종목 검색 실패:', error)
        toast({
          title: '검색 실패',
          description: '종목 검색 중 오류가 발생했습니다.',
          variant: 'destructive',
        })
        setSearchResults([])
      } finally {
        setIsSearching(false)
      }
    }, 500),
    [toast]
  )

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value
    setSearchQuery(query)
    performSearch(query)
  }

  const handleStockSelect = (stock: StockInfo) => {
    setSelectedStock(stock)
    setExpandedStockCode(stock.code)
  }

  const handleTradeFormChange = (field: keyof TradeFormData, value: any) => {
    setTradeForm(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const validateForm = (): boolean => {
    if (!selectedStock) {
      toast({
        title: '종목 선택',
        description: '종목을 선택해주세요.',
        variant: 'default',
      })
      return false
    }

    if (tradeForm.executedPrice <= 0) {
      toast({
        title: '검증 오류',
        description: '체결 가격을 입력해주세요.',
        variant: 'default',
      })
      return false
    }

    if (tradeForm.executedQuantity <= 0) {
      toast({
        title: '검증 오류',
        description: '체결 수량을 입력해주세요.',
        variant: 'default',
      })
      return false
    }

    if (!tradeForm.executedDate) {
      toast({
        title: '검증 오류',
        description: '날짜를 선택해주세요.',
        variant: 'default',
      })
      return false
    }

    return true
  }

  const handleAddTrade = async () => {
    if (!validateForm()) return

    setIsSubmitting(true)
    try {
      // Combine date and time
      const [hours, minutes] = tradeForm.executedTime.split(':')
      const executedAt = new Date(
        `${tradeForm.executedDate}T${tradeForm.executedTime}:00`
      )

      const tradeData = {
        stock_code: selectedStock!.code,
        stock_name: selectedStock!.name,
        trade_type: tradeForm.tradeType === 'buy' ? '매수' : '매도',
        executed_price: tradeForm.executedPrice,
        executed_quantity: tradeForm.executedQuantity,
        executed_amount: tradeForm.executedPrice * tradeForm.executedQuantity,
        executed_at: executedAt.toISOString(),
        broker: 'manual', // 수동 입력
      }

      // Add trading history
      await tradingAPI.addTrading(tradeData)

      toast({
        title: '성공',
        description: `${selectedStock!.name}의 매매 기록이 추가되었습니다.`,
        variant: 'default',
      })

      // Reset and close
      setSearchQuery('')
      setSearchResults([])
      setSelectedStock(null)
      setExpandedStockCode(null)
      setTradeForm({
        tradeType: 'buy',
        executedPrice: 0,
        executedDate: new Date().toISOString().split('T')[0],
        executedTime: '09:30',
        executedQuantity: 0,
      })
      onStockAdded()
      onClose()
    } catch (error) {
      console.error('매매 기록 추가 실패:', error)
      toast({
        title: '추가 실패',
        description: '매매 기록 추가 중 오류가 발생했습니다.',
        variant: 'destructive',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-bold text-gray-900">복기 - 매매 기록 추가</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Search Section */}
          {!selectedStock && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-3">
                종목 검색
              </label>
              <div className="relative mb-4">
                <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="종목명 또는 종목코드로 검색 (예: 삼성전자, 005930)"
                  value={searchQuery}
                  onChange={handleSearchChange}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
                {isSearching && (
                  <Loader2 className="absolute right-3 top-3 h-5 w-5 text-blue-500 animate-spin" />
                )}
              </div>

              {/* Search Results */}
              {searchResults.length === 0 && searchQuery && !isSearching && (
                <div className="text-center text-gray-500 py-8">
                  검색 결과가 없습니다.
                </div>
              )}

              {searchResults.length === 0 && !searchQuery && !isSearching && (
                <div className="text-center text-gray-400 py-8">
                  종목명 또는 종목코드를 입력하여 검색해주세요.
                </div>
              )}

              {searchResults.length > 0 && (
                <div className="space-y-2">
                  {searchResults.map((stock) => (
                    <div
                      key={stock.code}
                      onClick={() => handleStockSelect(stock)}
                      className="p-3 rounded-lg border border-gray-200 hover:border-blue-400 hover:bg-blue-50 cursor-pointer transition-all"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-semibold text-gray-900">
                            {stock.name}
                            <span className="text-sm text-gray-500 ml-2">({stock.code})</span>
                          </div>
                          <div className="text-sm text-gray-600 mt-1">
                            <span className="inline-block bg-gray-100 px-2 py-1 rounded mr-2">
                              {stock.market_name}
                            </span>
                          </div>
                        </div>
                        <ChevronDown className="h-5 w-5 text-gray-400" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Trade Form Section */}
          {selectedStock && (
            <div className="space-y-6">
              {/* Selected Stock Display */}
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-between justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{selectedStock.name}</h3>
                    <p className="text-sm text-gray-600">({selectedStock.code})</p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedStock(null)
                      setSearchQuery('')
                      setSearchResults([])
                    }}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    변경
                  </button>
                </div>
              </div>

              {/* Trade Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  매매 타입
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="tradeType"
                      value="buy"
                      checked={tradeForm.tradeType === 'buy'}
                      onChange={(e) => handleTradeFormChange('tradeType', e.target.value as 'buy' | 'sell')}
                      className="w-4 h-4 text-blue-600"
                    />
                    <span className="ml-2 text-gray-700">매수</span>
                  </label>
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="tradeType"
                      value="sell"
                      checked={tradeForm.tradeType === 'sell'}
                      onChange={(e) => handleTradeFormChange('tradeType', e.target.value as 'buy' | 'sell')}
                      className="w-4 h-4 text-red-600"
                    />
                    <span className="ml-2 text-gray-700">매도</span>
                  </label>
                </div>
              </div>

              {/* Date & Time */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    날짜
                  </label>
                  <input
                    type="date"
                    value={tradeForm.executedDate}
                    onChange={(e) => handleTradeFormChange('executedDate', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    시각
                  </label>
                  <input
                    type="time"
                    value={tradeForm.executedTime}
                    onChange={(e) => handleTradeFormChange('executedTime', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Price & Quantity */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    체결 가격 (원)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="100"
                    value={tradeForm.executedPrice || ''}
                    onChange={(e) => handleTradeFormChange('executedPrice', Number(e.target.value))}
                    placeholder="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    체결 수량 (주)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="1"
                    value={tradeForm.executedQuantity || ''}
                    onChange={(e) => handleTradeFormChange('executedQuantity', Number(e.target.value))}
                    placeholder="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Total Amount Display */}
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="text-sm text-gray-600">
                  거래대금: <span className="font-semibold text-gray-900">
                    {(tradeForm.executedPrice * tradeForm.executedQuantity).toLocaleString()}원
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 transition-colors"
          >
            취소
          </button>
          <button
            onClick={handleAddTrade}
            disabled={isSubmitting || !selectedStock}
            className={`px-4 py-2 rounded-lg text-white flex items-center gap-2 transition-colors ${
              isSubmitting || !selectedStock
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            <span>추가</span>
          </button>
        </div>
      </div>
    </div>
  )
}
