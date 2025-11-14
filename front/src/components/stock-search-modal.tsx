'use client'

import { useState, useCallback, useEffect } from 'react'
import { Search, X, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { stocksInfoAPI, tradingStocksAPI, tradingPlansAPI } from '@/lib/api'
import { useToast } from '@/lib/use-toast'

interface StockSearchModalProps {
  isOpen: boolean
  onClose: () => void
  onStockAdded: () => void
}

interface StockInfo {
  id: number
  code: string
  name: string
  market_code: string
  market_name: string
  last_price: string
}

interface OwnedStock {
  id: number
  stock_code: string
  stock_name: string
}

const debounce = (func: Function, delay: number) => {
  let timeoutId: NodeJS.Timeout
  return (...args: any[]) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay)
  }
}

export default function StockSearchModal({ isOpen, onClose, onStockAdded }: StockSearchModalProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<StockInfo[]>([])
  const [isSearching, isSetSearching] = useState(false)
  const [isAdding, setIsAdding] = useState(false)
  const [selectedStocks, setSelectedStocks] = useState<Set<string>>(new Set())
  const [showOwnedStocks, setShowOwnedStocks] = useState(false)
  const [ownedStocks, setOwnedStocks] = useState<OwnedStock[]>([])
  const [isLoadingOwned, setIsLoadingOwned] = useState(false)
  const { toast } = useToast()

  // Debounced search function
  const performSearch = useCallback(
    debounce(async (query: string) => {
      if (!query.trim()) {
        setSearchResults([])
        isSetSearching(false)
        return
      }

      isSetSearching(true)
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
        isSetSearching(false)
      }
    }, 500),
    [toast]
  )

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value
    setSearchQuery(query)
    performSearch(query)
  }

  const toggleStockSelection = (stockCode: string) => {
    const newSelected = new Set(selectedStocks)
    if (newSelected.has(stockCode)) {
      newSelected.delete(stockCode)
    } else {
      newSelected.add(stockCode)
    }
    setSelectedStocks(newSelected)
  }

  const handleLoadOwnedStocks = async () => {
    if (showOwnedStocks) {
      setShowOwnedStocks(false)
      return
    }

    setIsLoadingOwned(true)
    try {
      const response = await tradingStocksAPI.getOwnedStocks(0, 100)
      const stocks = response.data?.data || []
      setOwnedStocks(stocks)
      setShowOwnedStocks(true)
    } catch (error) {
      console.error('보유 종목 조회 실패:', error)
      toast({
        title: '조회 실패',
        description: '보유 종목 조회 중 오류가 발생했습니다.',
        variant: 'destructive',
      })
    } finally {
      setIsLoadingOwned(false)
    }
  }

  const handleAddSelectedStocksFromOwned = async () => {
    if (selectedStocks.size === 0) {
      toast({
        title: '종목 선택',
        description: '추가할 종목을 선택해주세요.',
        variant: 'default',
      })
      return
    }

    setIsAdding(true)
    try {
      const stockCodesToAdd = Array.from(selectedStocks)

      // 보유 종목에서 선택된 종목들의 정보 추출
      const selectedOwnedStocks = ownedStocks.filter(stock =>
        stockCodesToAdd.includes(stock.stock_code)
      )

      // 각 종목별로 trading_plans에 추가 (StocksInfo 테이블 참고하지 않음)
      // 보유 종목의 코드와 이름만으로 충분함
      await Promise.all(
        selectedOwnedStocks.map(stock =>
          tradingPlansAPI.addFromOwned([stock.stock_code])
        )
      )

      toast({
        title: '성공',
        description: `${selectedStocks.size}개의 종목이 계획에 추가되었습니다.`,
        variant: 'default',
      })

      // Reset and close
      setSelectedStocks(new Set())
      setShowOwnedStocks(false)
      onStockAdded()
      onClose()
    } catch (error) {
      console.error('종목 추가 실패:', error)
      toast({
        title: '추가 실패',
        description: '종목 추가 중 오류가 발생했습니다.',
        variant: 'destructive',
      })
    } finally {
      setIsAdding(false)
    }
  }

  const handleAddSelectedStocks = async () => {
    if (selectedStocks.size === 0) {
      toast({
        title: '종목 선택',
        description: '추가할 종목을 선택해주세요.',
        variant: 'default',
      })
      return
    }

    setIsAdding(true)
    try {
      const selectedStocksList = searchResults.filter(stock => selectedStocks.has(stock.code))
      const stockCodesToAdd = selectedStocksList.map(stock => stock.code)

      // trading_plans 테이블에 직접 추가 (계획 모드)
      await tradingPlansAPI.addFromOwned(stockCodesToAdd)

      toast({
        title: '성공',
        description: `${selectedStocks.size}개의 종목이 추가되었습니다.`,
        variant: 'default',
      })

      // Reset and close
      setSearchQuery('')
      setSearchResults([])
      setSelectedStocks(new Set())
      onStockAdded()
      onClose()
    } catch (error) {
      console.error('종목 추가 실패:', error)
      toast({
        title: '추가 실패',
        description: '종목 추가 중 오류가 발생했습니다.',
        variant: 'destructive',
      })
    } finally {
      setIsAdding(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-bold text-gray-900">종목 검색 및 추가</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Search Input */}
        <div className="p-6 border-b space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="종목명 또는 종목코드로 검색 (예: 삼성전자, 005930)"
              value={searchQuery}
              onChange={handleSearchChange}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
              disabled={showOwnedStocks}
            />
            {isSearching && (
              <Loader2 className="absolute right-3 top-3 h-5 w-5 text-blue-500 animate-spin" />
            )}
          </div>

          {/* Owned Stocks Button */}
          <button
            onClick={handleLoadOwnedStocks}
            disabled={isLoadingOwned}
            className="w-full flex items-center justify-between px-4 py-2 bg-gray-100 hover:bg-gray-200 disabled:bg-gray-200 rounded-lg text-gray-700 transition-colors"
          >
            <span className="font-medium">보유 종목으로 추가하기</span>
            {isLoadingOwned ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              showOwnedStocks ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />
            )}
          </button>
        </div>

        {/* Results */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Search Results */}
          {!showOwnedStocks && (
            <>
              {searchResults.length === 0 && searchQuery && !isSearching && (
                <div className="text-center text-gray-500 py-8">
                  검색 결과가 없습니다.
                </div>
              )}

              {searchResults.length > 0 && (
                <div className="space-y-2">
                  {searchResults.map((stock) => (
                    <div
                      key={stock.code}
                      onClick={() => toggleStockSelection(stock.code)}
                      className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
                        selectedStocks.has(stock.code)
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 bg-white'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-1">
                          <div className="font-semibold text-gray-900">
                            {stock.name}
                            <span className="text-sm text-gray-500 ml-2">({stock.code})</span>
                          </div>
                          <div className="text-sm text-gray-600 mt-1">
                            <span className="inline-block bg-gray-100 px-2 py-1 rounded mr-2">
                              {stock.market_name}
                            </span>
                            <span className="text-gray-500">
                              현재가: {stock.last_price}
                            </span>
                          </div>
                        </div>
                        <div
                          className={`w-6 h-6 border-2 rounded mt-1 flex-shrink-0 ${
                            selectedStocks.has(stock.code)
                              ? 'border-blue-500 bg-blue-500'
                              : 'border-gray-300'
                          }`}
                        >
                          {selectedStocks.has(stock.code) && (
                            <svg
                              className="w-full h-full text-white"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={3}
                                d="M5 13l4 4L19 7"
                              />
                            </svg>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Owned Stocks Grid */}
          {showOwnedStocks && (
            <>
              {ownedStocks.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  보유 종목이 없습니다.
                </div>
              ) : (
                <div>
                  <div className="grid grid-cols-3 gap-3">
                    {ownedStocks.map((stock) => (
                      <button
                        key={stock.stock_code}
                        onClick={() => toggleStockSelection(stock.stock_code)}
                        className={`p-3 rounded-lg border-2 cursor-pointer transition-all text-center ${
                          selectedStocks.has(stock.stock_code)
                            ? 'border-blue-500 bg-blue-500 text-white'
                            : 'border-gray-300 bg-gray-50 hover:border-gray-400 text-gray-900'
                        }`}
                      >
                        <div className="font-semibold truncate">{stock.stock_name}</div>
                        <div className="text-xs text-opacity-75 truncate">
                          {selectedStocks.has(stock.stock_code) ? stock.stock_code : stock.stock_code}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
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
            onClick={showOwnedStocks ? handleAddSelectedStocksFromOwned : handleAddSelectedStocks}
            disabled={isAdding || selectedStocks.size === 0}
            className={`px-4 py-2 rounded-lg text-white flex items-center gap-2 transition-colors ${
              isAdding || selectedStocks.size === 0
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isAdding && <Loader2 className="h-4 w-4 animate-spin" />}
            <span>
              {selectedStocks.size > 0 ? `추가 (${selectedStocks.size})` : '추가'}
            </span>
          </button>
        </div>
      </div>
    </div>
  )
}
