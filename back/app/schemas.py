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


class ChartDataPoint(BaseModel):
    """일봉 차트 데이터 포인트"""
    date: str  # YYYY-MM-DD
    open: float  # 시가
    high: float  # 고가
    low: float   # 저가
    close: float  # 종가
    volume: int  # 거래량
    trade_amount: int  # 거래대금
    change_rate: Optional[float] = None  # 변화율 (전일대비 %)
    ma5: Optional[float] = None  # 5일 이동평균선
    ma10: Optional[float] = None  # 10일 이동평균선
    ma20: Optional[float] = None  # 20일 이동평균선
    ma60: Optional[float] = None  # 60일 이동평균선


class DailyChartResponse(BaseModel):
    """일봉 차트 조회 응답"""
    stock_code: str
    data: list[ChartDataPoint]
    total_records: int