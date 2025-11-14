'use client'

import { useState } from 'react'
import { TrendingUp, Plus, RefreshCw, Settings, LogOut, User, Menu, X, ArrowRight } from 'lucide-react'
import { clearAuthToken } from '@/lib/api'
import { useRouter, usePathname } from 'next/navigation'

interface HeaderProps {
  mode: 'plan' | 'review'
  onModeChange: (mode: 'plan' | 'review') => void
  onRefresh: () => void
  onAddStock: () => void
  onStrategyManage: () => void
  isRefreshing?: boolean
}

export default function Header({
  mode,
  onModeChange,
  onRefresh,
  onAddStock,
  onStrategyManage,
  isRefreshing = false
}: HeaderProps) {
  const router = useRouter()
  const pathname = usePathname()
  const [menuOpen, setMenuOpen] = useState(false)
  const today = new Date().toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })

  // 현재 페이지에 따른 버튼 텍스트 결정
  const isRecommendationPage = pathname === '/recommendation'
  const strategyButtonLabel = isRecommendationPage ? '계획/복기' : '추천'
  const strategyButtonIcon = isRecommendationPage ? Settings : ArrowRight

  const handleLogout = () => {
    clearAuthToken()
    router.push('/login')
  }

  return (
    <header className="bg-white shadow-sm border-b sticky top-0 z-40">
      <div className="mx-auto px-3 sm:px-4 md:px-6 lg:px-8">
        {/* Desktop View */}
        <div className="hidden md:flex justify-between items-center py-4">
          {/* Left: App Title */}
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-8 w-8 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">Goni</h1>
          </div>

          {/* Center: Mode Toggle - 추천 페이지에서는 숨김 */}
          {!isRecommendationPage && (
            <div className="flex items-center">
              <div className="bg-gray-100 rounded-lg p-1 flex">
                <button
                  onClick={() => onModeChange('plan')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    mode === 'plan'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  계획
                </button>
                <button
                  onClick={() => onModeChange('review')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    mode === 'review'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  복기
                </button>
              </div>
            </div>
          )}

          {/* Right: Date and Action Buttons */}
          <div className="flex items-center gap-2">
            {/* Today's Date */}
            <div className="text-xs sm:text-sm text-gray-600 bg-gray-50 px-2 sm:px-3 py-2 rounded-lg hidden sm:block whitespace-nowrap">
              {today}
            </div>

            {/* Action Buttons */}
            <button
              onClick={onAddStock}
              className="bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-1 text-sm"
              title="종목 추가"
            >
              <Plus className="h-4 w-4" />
              <span className="hidden lg:inline">추가</span>
            </button>

            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className={`px-3 py-2 rounded-lg flex items-center gap-1 transition-colors text-sm ${
                isRefreshing
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              title="새로고침"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span className="hidden lg:inline">{isRefreshing ? '중' : '새로'}</span>
            </button>

            <button
              onClick={onStrategyManage}
              className="bg-gray-100 text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-1 hidden sm:flex text-sm"
              title={strategyButtonLabel}
            >
              {isRecommendationPage ? <Settings className="h-4 w-4" /> : <ArrowRight className="h-4 w-4" />}
              <span className="hidden lg:inline">{strategyButtonLabel}</span>
            </button>

            <button
              onClick={() => router.push('/profile')}
              className="bg-gray-100 text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-1 hidden sm:flex text-sm"
              title="프로필"
            >
              <User className="h-4 w-4" />
              <span className="hidden lg:inline">프로필</span>
            </button>

            <button
              onClick={handleLogout}
              className="bg-red-100 text-red-700 px-3 py-2 rounded-lg hover:bg-red-200 transition-colors flex items-center gap-1 hidden sm:flex text-sm"
              title="로그아웃"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden lg:inline">로그아웃</span>
            </button>
          </div>
        </div>

        {/* Mobile View */}
        <div className="md:hidden py-3 flex justify-between items-center">
          {/* Left: App Title */}
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-6 w-6 text-blue-600" />
            <h1 className="text-xl font-bold text-gray-900">Goni</h1>
          </div>

          {/* Center: Mode Toggle - 추천 페이지에서는 숨김 */}
          {!isRecommendationPage && (
            <div className="flex-1 mx-3">
              <div className="bg-gray-100 rounded-lg p-0.5 flex justify-center">
                <button
                  onClick={() => onModeChange('plan')}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex-1 ${
                    mode === 'plan'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  계획
                </button>
                <button
                  onClick={() => onModeChange('review')}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex-1 ${
                    mode === 'review'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  복기
                </button>
              </div>
            </div>
          )}

          {/* Right: Menu Button */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="text-gray-600 hover:text-gray-900 transition-colors"
          >
            {menuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {menuOpen && (
          <div className="md:hidden border-t pb-3 space-y-2">
            <div className="text-xs text-gray-500 px-2 py-1">
              {today}
            </div>

            <button
              onClick={() => {
                onAddStock()
                setMenuOpen(false)
              }}
              className="w-full text-left bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 text-sm"
            >
              <Plus className="h-4 w-4" />
              <span>종목 추가</span>
            </button>

            <button
              onClick={() => {
                onRefresh()
                setMenuOpen(false)
              }}
              disabled={isRefreshing}
              className={`w-full text-left px-3 py-2 rounded-lg flex items-center gap-2 transition-colors text-sm ${
                isRefreshing
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>{isRefreshing ? '새로고침 중...' : '새로고침'}</span>
            </button>

            <button
              onClick={() => {
                onStrategyManage()
                setMenuOpen(false)
              }}
              className="w-full text-left bg-gray-100 text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2 text-sm"
            >
              {isRecommendationPage ? <Settings className="h-4 w-4" /> : <ArrowRight className="h-4 w-4" />}
              <span>{strategyButtonLabel}</span>
            </button>

            <button
              onClick={() => {
                router.push('/profile')
                setMenuOpen(false)
              }}
              className="w-full text-left bg-gray-100 text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2 text-sm"
            >
              <User className="h-4 w-4" />
              <span>프로필</span>
            </button>

            <button
              onClick={() => {
                handleLogout()
                setMenuOpen(false)
              }}
              className="w-full text-left bg-red-100 text-red-700 px-3 py-2 rounded-lg hover:bg-red-200 transition-colors flex items-center gap-2 text-sm"
            >
              <LogOut className="h-4 w-4" />
              <span>로그아웃</span>
            </button>
          </div>
        )}
      </div>
    </header>
  )
}