'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'
import { tradingStocksAPI } from '@/lib/api'

interface UserProfile {
  id: number
  email: string
  username: string
  app_key?: string
  app_secret?: string
}

// 문자열을 * 로 마스킹하는 함수 (문자 개수만큼 * 표시)
function maskString(str: string): string {
  if (!str) return ''
  return '*'.repeat(str.length)
}

export default function ProfilePage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [showAppKey, setShowAppKey] = useState(false)
  const [showAppSecret, setShowAppSecret] = useState(false)
  const [appKey, setAppKey] = useState('')
  const [appSecret, setAppSecret] = useState('')

  // 프로필 정보 조회
  const { data: profile, isLoading } = useQuery<UserProfile>({
    queryKey: ['profile'],
    queryFn: async () => {
      const token = Cookies.get('access_token') || localStorage.getItem('access_token')
      const response = await fetch('/api/auth/me', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!response.ok) throw new Error('프로필 조회 실패')
      const data = await response.json()
      setAppKey(data.app_key || '')
      setAppSecret(data.app_secret || '')
      return data
    },
  })

  // 키움 API 설정 저장
  const updateMutation = useMutation({
    mutationFn: async (data: { app_key: string; app_secret: string }) => {
      const token = Cookies.get('access_token') || localStorage.getItem('access_token')
      const response = await fetch('/api/auth/update-kiwoom', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(data),
      })
      if (!response.ok) throw new Error('저장 실패')
      return response.json()
    },
    onSuccess: async () => {
      toast.success('키움증권 API 정보가 저장되었습니다')
      queryClient.invalidateQueries({ queryKey: ['profile'] })

      // 저장 후 자동으로 거래 기록 동기화 시작
      toast.loading('거래 기록을 동기화하는 중입니다...')
      try {
        await tradingStocksAPI.syncFromKiwoom(30) // 최근 30일 거래 기록 조회
        toast.dismiss()
        toast.success('거래 기록 동기화가 완료되었습니다')
      } catch (error) {
        console.warn('거래 기록 동기화 실패:', error)
        toast.dismiss()
        toast.error('거래 기록 동기화에 실패했습니다. 대시보드에서 수동으로 동기화할 수 있습니다.')
      }
    },
    onError: () => {
      toast.error('저장에 실패했습니다')
    },
  })

  const handleSave = () => {
    if (!appKey || !appSecret) {
      toast.error('APP KEY와 APP SECRET을 모두 입력해주세요')
      return
    }
    updateMutation.mutate({ app_key: appKey, app_secret: appSecret })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => router.push('/dashboard')}
            className="flex items-center text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            대시보드로 돌아가기
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">프로필 설정</h1>

          {/* 사용자 정보 */}
          <div className="mb-8 pb-8 border-b">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">사용자 정보</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  이메일
                </label>
                <input
                  type="email"
                  value={profile?.email || ''}
                  disabled
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  사용자명
                </label>
                <input
                  type="text"
                  value={profile?.username || ''}
                  disabled
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
                />
              </div>
            </div>
          </div>

          {/* 키움증권 API 설정 */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-2">키움증권 API 설정</h2>
             <p className="text-sm text-gray-600 mb-4">
              복기 모드에서 매매 내역을 자동으로 조회하려면 키움증권 API 신청 및 설정이 필요합니다.<br></br>
              아래의 사이트에서 키움증권 API 신청을 하신 후,<br></br>
              <a href='https://openapi.kiwoom.com/mgmt/VOpenApiRegView'><span style={{ color: 'blue', fontStyle:'italic'}}>https://openapi.kiwoom.com/mgmt/VOpenApiRegView</span></a><br></br>
              [계좌 APP Key 관리] Tab에서, IP 주소등록에 3.34.102.218 를 입력하고 (*주의: 본인 컴퓨터 IP가 아닙니다.)<br></br> 
              얻은 APP KEY와 APP SECRET 정보를 아래에 입력하시고 저장 버튼을 눌러주세요.
            </p>  
	  <div className="space-y-4">
              {/* APP KEY */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  APP KEY
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={showAppKey ? appKey : maskString(appKey)}
                    onChange={(e) => setAppKey(e.target.value)}
                    placeholder={appKey ? '' : '키움증권 APP KEY를 입력하세요'}
                    className="w-full px-4 py-2 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  {appKey && (
                    <button
                      type="button"
                      onClick={() => setShowAppKey(!showAppKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      title={showAppKey ? '숨기기' : '표시'}
                    >
                      {showAppKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  )}
                </div>
              </div>

              {/* APP SECRET */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  APP SECRET
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={showAppSecret ? appSecret : maskString(appSecret)}
                    onChange={(e) => setAppSecret(e.target.value)}
                    placeholder={appSecret ? '' : '키움증권 APP SECRET을 입력하세요'}
                    className="w-full px-4 py-2 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  {appSecret && (
                    <button
                      type="button"
                      onClick={() => setShowAppSecret(!showAppSecret)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      title={showAppSecret ? '숨기기' : '표시'}
                    >
                      {showAppSecret ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  )}
                </div>
              </div>

              {/* 저장 버튼 */}
              <div className="flex justify-end pt-4">
                <button
                  onClick={handleSave}
                  disabled={updateMutation.isPending}
                  className="flex items-center px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {updateMutation.isPending ? '저장 중...' : '저장'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
