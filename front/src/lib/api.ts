import axios from 'axios'
import Cookies from 'js-cookie'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
    if (error.response?.status === 401) {
      // Clear tokens from both storage methods
      Cookies.remove('access_token')
      localStorage.removeItem('access_token')
      
      // Only redirect if we're in a browser environment
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
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
  getTradingPlans: (skip = 0, limit = 100) =>
    api.get(`/api/trading-plans?skip=${skip}&limit=${limit}`),
  getTradingPlan: (planId: number) =>
    api.get(`/api/trading-plans/${planId}`),
  createTradingPlan: (planData: any) =>
    api.post('/api/trading-plans', planData),
  updateTradingPlan: (planId: number, planData: any) =>
    api.put(`/api/trading-plans/${planId}`, planData),
  deleteTradingPlan: (planId: number) =>
    api.delete(`/api/trading-plans/${planId}`),
  getRecentTrades: (limit = 20) =>
    api.get(`/api/trading-plans/trades/recent?limit=${limit}`),
  syncRecentTrades: (limit = 20) =>
    api.post(`/api/trading-plans/trades/sync?limit=${limit}`),
}

export const tradingAPI = {
  syncDashboardTrades: (stockCodes: string[]) =>
    api.post('/api/trading/sync-dashboard-trades', { stock_codes: stockCodes }),
}