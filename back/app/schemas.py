from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


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
    app_key: Optional[str] = None
    app_secret: Optional[str] = None

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
    stock_code: str  # 종목코드
    stock_name: Optional[str] = None  # 종목명


class TradingPlanCreate(TradingPlanBase):
    pass


class TradingPlanUpdate(TradingPlanBase):
    pass


class TradingPlan(TradingPlanBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TradingPlanHistoryBase(BaseModel):
    trading_type: str  # 'buy' or 'sell'
    condition: Optional[str] = None  # 매매 조건
    target_price: Optional[float] = None  # 매매 계획 가격
    amount: Optional[int] = None  # 매매 금액
    reason: Optional[str] = None  # 매매 이유
    proportion: Optional[float] = None  # 매도 비중 (%)
    sp_condition: Optional[str] = None  # 익절 조건
    sp_price: Optional[float] = None  # 익절 가격
    sp_ratio: Optional[float] = None  # 익절 수익률 (%)
    sl_condition: Optional[str] = None  # 손절 조건
    sl_price: Optional[float] = None  # 손절 가격
    sl_ratio: Optional[float] = None  # 손절 수익률 (%)


class TradingPlanHistoryCreate(TradingPlanHistoryBase):
    pass


class TradingPlanHistoryUpdate(TradingPlanHistoryBase):
    pass


class TradingPlanHistory(TradingPlanHistoryBase):
    id: int
    trading_plan_id: int
    created_at: datetime
    updated_at: datetime

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
    trading_id: Optional[int] = None
    order_no: Optional[str] = None


class RecapUpdate(RecapBase):
    pass


class Recap(RecapBase):
    id: int
    user_id: int
    trading_plan_id: Optional[int] = None
    trading_id: Optional[int] = None
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
    data: List[ChartDataPoint]
    total_records: int


class TradingBase(BaseModel):
    """매매 기록 기본 정보"""
    executed_at: datetime  # 체결 시각(날짜, 시간)
    trade_type: str  # 매매구분 ('buy' or 'sell')
    order_no: Optional[str] = None  # 주문번호
    stock_name: str  # 종목명
    stock_code: str  # 종목코드
    executed_price: float  # 체결 가격
    executed_quantity: int  # 체결 수량
    executed_amount: int  # 체결 금액
    broker: str  # 증권사 (ex: kiwoom, kis)


class TradingCreate(TradingBase):
    """매매 기록 생성"""
    pass


class Trading(TradingBase):
    """매매 기록 조회"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SyncDashboardTradesRequest(BaseModel):
    """대시보드 종목 거래 기록 동기화 요청"""
    stock_codes: List[str]  # 종목코드 리스트


class StocksInfoBase(BaseModel):
    """종목정보 기본 정보 (ka10099 API)"""
    code: str  # 종목코드
    name: str  # 종목명
    list_count: Optional[str] = None  # 상장주식수
    audit_info: Optional[str] = None  # 감시종목 (정상, 투자주의환기종목 등)
    reg_day: Optional[str] = None  # 상장일 (YYYYMMDD)
    last_price: Optional[str] = None  # 종목액면가
    state: Optional[str] = None  # 증거금상태 (증거금100%, 관리종목 등)
    market_code: Optional[str] = None  # 마켓코드 (0: 코스피, 10: 코스닥 등)
    market_name: Optional[str] = None  # 마켓명 (코스피, 코스닥 등)
    up_name: Optional[str] = None  # 상위종목명
    up_size_name: Optional[str] = None  # 상위사이즈명
    company_class_name: Optional[str] = None  # 회사분류명 (외국기업 등)
    order_warning: Optional[str] = None  # 주문경고 (0: 정상, 1: 경고 등)
    nxt_enable: Optional[str] = None  # 다음조회여부 (Y/N)


class StocksInfoCreate(StocksInfoBase):
    """종목정보 생성"""
    pass


class StocksInfo(StocksInfoBase):
    """종목정보 조회"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TradingStockBase(BaseModel):
    """매매 종목 기본 정보"""
    stock_name: str  # 종목명
    stock_code: str  # 종목코드


class TradingStockCreate(TradingStockBase):
    """매매 종목 생성"""
    pass


class TradingStock(TradingStockBase):
    """매매 종목 조회"""
    id: int
    is_downloaded: bool
    latest_orderno: Optional[str] = None
    reg_type: str = 'manual'  # 등록 방식 ('api': API 동기화, 'manual': 수동 등록)
    avg_prc: Optional[float] = None
    rmnd_qty: Optional[int] = None
    pur_amt: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True