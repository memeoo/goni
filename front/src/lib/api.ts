import axios from 'axios'
import Cookies from 'js-cookie'

// API Base URL 결정 로직:
// - 클라이언트 사이드: NEXT_PUBLIC_API_URL 사용 (모바일 등 외부 접속을 위해)
// - 서버 사이드: BACKEND_URL 사용 (localhost에서 백엔드로 직접 호출)
const API_BASE_URL = typeof window !== 'undefined'
  ? (process.env.NEXT_PUBLIC_API_URL || '') // 클라이언트: 명시적 URL 또는 상대경로
  : (process.env.BACKEND_URL || 'http://localhost:8000') // 서버: localhost 사용

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds timeout
})

// Request interceptor for auth token
api.interceptors.request.use(
  (config) => {
    // Try to get token from cookies first, then localStorage
    const token = Cookies.get('access_token') || localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // 401 Unauthorized: 토큰 만료 또는 검증 실패
    if (error.response?.status === 401) {
      // Clear tokens from both storage methods
      Cookies.remove('access_token')
      localStorage.removeItem('access_token')

      // Only redirect if we're in a browser environment
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    }

    // CORS 에러가 아니거나 기타 네트워크 에러인 경우 로그 출력
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.warn('[API] 네트워크 연결 오류 - 서버 상태를 확인하세요')
    }

    return Promise.reject(error)
  }
)

// Helper function to set auth token
export const setAuthToken = (token: string) => {
  // Set token in both cookies and localStorage for redundancy
  Cookies.set('access_token', token, { expires: 1 }) // 1 day
  localStorage.setItem('access_token', token)
}

// Helper function to clear auth token
export const clearAuthToken = () => {
  Cookies.remove('access_token')
  localStorage.removeItem('access_token')
}

export default api

// API functions
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/api/auth/token', 
      new URLSearchParams({ username, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    ),
  register: (userData: { email: string; username: string; password: string }) =>
    api.post('/api/auth/register', userData),
  getMe: () => api.get('/api/auth/me'),
}

export const stocksAPI = {
  getStocks: (skip = 0, limit = 100) =>
    api.get(`/api/stocks?skip=${skip}&limit=${limit}`),
  getStock: (stockId: number) =>
    api.get(`/api/stocks/${stockId}`),
  createStock: (stockData: any) =>
    api.post('/api/stocks', stockData),
  updateStock: (stockId: number, stockData: any) =>
    api.put(`/api/stocks/${stockId}`, stockData),
  getChartData: (stockCode: string, days = 60) =>
    api.get(`/api/stocks/${stockCode}/chart-data?days=${days}`),
  getOHLCData: (stockCode: string, days = 60) =>
    api.get(`/api/stocks/${stockCode}/ohlc?days=${days}`),
  getVolumeData: (stockCode: string, days = 60) =>
    api.get(`/api/stocks/${stockCode}/volume?days=${days}`),
  getCurrentPrice: (stockCode: string) =>
    api.get(`/api/stocks/${stockCode}/current-price`),
  getForeignInstitutionalData: (stockCode: string) =>
    api.get(`/api/stocks/${stockCode}/foreign-institutional`),
}

export const tradingPlansAPI = {
  getPlanModeStocks: (skip = 0, limit = 100) =>
    api.get(`/api/trading-plans/plan-mode?skip=${skip}&limit=${limit}`),
  getTradingPlans: (skip = 0, limit = 100) =>
    api.get(`/api/trading-plans?skip=${skip}&limit=${limit}`),
  getTradingPlan: (planId: number) =>
    api.get(`/api/trading-plans/${planId}`),
  saveTradingPlan: (planData: any) =>
    api.post('/api/trading-plans', planData),
  createTradingPlan: (planData: any) =>
    api.post('/api/trading-plans', planData),
  addFromOwned: (stockCodes: string[]) =>
    api.post('/api/trading-plans/add-from-owned', { stock_codes: stockCodes }),
  updateTradingPlan: (planId: number, planData: any) =>
    api.put(`/api/trading-plans/${planId}`, planData),
  deleteTradingPlan: (planId: number) =>
    api.delete(`/api/trading-plans/${planId}`),
  getRecentTrades: (limit = 20) =>
    api.get(`/api/trading-plans/trades/recent?limit=${limit}`),
}

export const tradingAPI = {
  getRecentTrades: (limit = 100) =>
    api.get(`/api/trading?limit=${limit}`),
  syncTradedStocks: () =>
    api.post('/api/trading/sync-stocks'),
  addTrading: (tradeData: any) =>
    api.post('/api/trading', tradeData),
}

export const tradingStocksAPI = {
  getOwnedStocks: (skip = 0, limit = 100) =>
    api.get(`/api/trading-stocks/owned?skip=${skip}&limit=${limit}`),
  getPlanModeStocks: (skip = 0, limit = 100) =>
    api.get(`/api/trading-stocks/plan-mode?skip=${skip}&limit=${limit}`),
  getTradingStocks: (skip = 0, limit = 100) =>
    api.get(`/api/trading-stocks?skip=${skip}&limit=${limit}`),
  syncFromKiwoom: (days = 5) =>
    api.post(`/api/trading-stocks/sync-from-kiwoom?days=${days}`),
  syncStockHistory: (stockCode: string) =>
    api.post(`/api/trading-stocks/${stockCode}/sync-history`),
  syncAccountEvaluation: () =>
    api.post('/api/trading-stocks/sync-account-evaluation'),
  addStock: (stockCode: string, stockName: string) => {
    const params = new URLSearchParams()
    params.append('stock_code', stockCode)
    params.append('stock_name', stockName)
    return api.post(`/api/trading-stocks?${params.toString()}`)
  },
}

export const stocksInfoAPI = {
  getStocksInfo: (skip = 0, limit = 100, marketCode?: string) => {
    const params = new URLSearchParams()
    params.append('skip', skip.toString())
    params.append('limit', limit.toString())
    if (marketCode) params.append('market_code', marketCode)
    return api.get(`/api/stocks-info/?${params.toString()}`)
  },
  searchStocksInfo: (query: string, marketCode?: string, skip = 0, limit = 50) => {
    const params = new URLSearchParams()
    params.append('q', query)
    params.append('skip', skip.toString())
    params.append('limit', limit.toString())
    if (marketCode) params.append('market_code', marketCode)
    return api.get(`/api/stocks-info/search?${params.toString()}`)
  },
  getStockInfoByCode: (code: string) =>
    api.get(`/api/stocks-info/${code}`),
}

export const recStocksAPI = {
  getRecStocks: (skip = 0, limit = 100) =>
    api.get(`/api/rec-stocks?skip=${skip}&limit=${limit}`),
  getRecStockById: (recStockId: number) =>
    api.get(`/api/rec-stocks/${recStockId}`),
  getRecStocksByAlgorithm: (algorithmId: number, skip = 0, limit = 100) =>
    api.get(`/api/rec-stocks/algorithm/${algorithmId}?skip=${skip}&limit=${limit}`),
  getRecStocksByDate: (date: string, skip = 0, limit = 100) =>
    api.get(`/api/rec-stocks/date/${date}?skip=${skip}&limit=${limit}`),
  getLatestRecStocks: (days = 7, skip = 0, limit = 100) =>
    api.get(`/api/rec-stocks/latest/${days}?skip=${skip}&limit=${limit}`),
  createRecStock: (recStockData: any) =>
    api.post('/api/rec-stocks', recStockData),
  updateRecStock: (recStockId: number, recStockData: any) =>
    api.put(`/api/rec-stocks/${recStockId}`, recStockData),
  deleteRecStock: (recStockId: number) =>
    api.delete(`/api/rec-stocks/${recStockId}`),
}

export const principlesAPI = {
  getPrinciples: () =>
    api.get('/api/principles/'),
  createPrinciple: (principleText: string) =>
    api.post('/api/principles/', { principle_text: principleText }),
  deletePrinciple: (principleId: number) =>
    api.delete(`/api/principles/${principleId}`),
}