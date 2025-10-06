export interface User {
  id: number
  email: string
  username: string
  is_active: boolean
  created_at: string
}

export interface Stock {
  id: number
  symbol: string
  name: string
  market: string
  current_price: number
  change_rate: number
  volume: number
  updated_at: string
}

export interface TradingPlan {
  id: number
  user_id: number
  stock_id: number
  plan_type: 'buy' | 'sell'
  target_price: number
  quantity: number
  reason: string
  executed_price?: number
  executed_quantity?: number
  executed_at?: string
  review?: string
  profit_loss?: number
  status: 'planned' | 'executed' | 'reviewed'
  created_at: string
  updated_at: string
  stock: Stock
}

export interface TradingPlanCreate {
  stock_id: number
  plan_type: 'buy' | 'sell'
  target_price: number
  quantity: number
  reason: string
}

export interface TradingPlanUpdate {
  executed_price?: number
  executed_quantity?: number
  review?: string
  profit_loss?: number
  status?: 'planned' | 'executed' | 'reviewed'
}

export interface LoginFormData {
  username: string
  password: string
}

export interface RegisterFormData {
  email: string
  username: string
  password: string
  confirmPassword: string
}