from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class StockBase(BaseModel):
    symbol: str
    name: str
    market: str


class StockCreate(StockBase):
    current_price: float
    change_rate: float
    change_price: float
    volume: int


class Stock(StockBase):
    id: int
    current_price: float
    change_rate: float
    change_price: float
    volume: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TradingPlanBase(BaseModel):
    stock_id: int
    plan_type: str
    target_price: float
    quantity: int
    reason: str


class TradingPlanCreate(TradingPlanBase):
    pass


class TradingPlanUpdate(BaseModel):
    executed_price: Optional[float] = None
    executed_quantity: Optional[int] = None
    review: Optional[str] = None
    profit_loss: Optional[float] = None
    status: Optional[str] = None


class TradingPlan(TradingPlanBase):
    id: int
    user_id: int
    executed_price: Optional[float] = None
    executed_quantity: Optional[int] = None
    executed_at: Optional[datetime] = None
    review: Optional[str] = None
    profit_loss: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime
    stock: Stock
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class RecapBase(BaseModel):
    catalyst: Optional[str] = None
    market_condition: Optional[str] = None
    price_chart: Optional[str] = None
    volume: Optional[str] = None
    supply_demand: Optional[str] = None
    emotion: Optional[str] = None
    evaluation: Optional[str] = None
    evaluation_reason: Optional[str] = None
    etc: Optional[str] = None


class RecapCreate(RecapBase):
    trading_plan_id: Optional[int] = None
    order_no: Optional[str] = None


class RecapUpdate(RecapBase):
    pass


class Recap(RecapBase):
    id: int
    user_id: int
    trading_plan_id: Optional[int] = None
    order_no: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True