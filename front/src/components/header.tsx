'use client'

import { useState } from 'react'
import { TrendingUp, Plus, RefreshCw, Settings, LogOut, User } from 'lucide-react'
import { clearAuthToken } from '@/lib/api'
import { useRouter } from 'next/navigation'

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
  const today = new Date().toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })

  const handleLogout = () => {
    clearAuthToken()
    router.push('/login')
  }

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          {/* Left: App Title */}
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-8 w-8 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">Goni</h1>
          </div>

          {/* Center: Mode Toggle */}
          <div className="flex items-center space-x-4">
            <div className="bg-gray-100 rounded-lg p-1 flex">
              <button
                onClick={() => onModeChange('plan')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  mode === 'plan'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                계획 모드
              </button>
              <button
                onClick={() => onModeChange('review')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  mode === 'review'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                복기 모드
              </button>
            </div>
          </div>

          {/* Right: Date and Action Buttons */}
          <div className="flex items-center space-x-4">
            {/* Today's Date */}
            <div className="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded-lg">
              {today}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-2">
              <button
                onClick={onAddStock}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <Plus className="h-4 w-4" />
                <span>종목 추가</span>
              </button>

              <button
                onClick={onRefresh}
                disabled={isRefreshing}
                className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                  isRefreshing
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                <span>{isRefreshing ? '새로고침 중...' : '새로고침'}</span>
              </button>

              <button
                onClick={onStrategyManage}
                className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors flex items-center space-x-2"
              >
                <Settings className="h-4 w-4" />
                <span>전략 관리</span>
              </button>

              <button
                onClick={() => router.push('/profile')}
                className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors flex items-center space-x-2"
              >
                <User className="h-4 w-4" />
                <span>프로필</span>
              </button>

              <button
                onClick={handleLogout}
                className="bg-red-100 text-red-700 px-4 py-2 rounded-lg hover:bg-red-200 transition-colors flex items-center space-x-2"
              >
                <LogOut className="h-4 w-4" />
                <span>로그아웃</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}