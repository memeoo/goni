import sqlalchemy as sa
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    email = sa.Column(sa.String, unique=True, index=True)
    username = sa.Column(sa.String, unique=True, index=True)
    hashed_password = sa.Column(sa.String)
    is_active = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    app_key= sa.Column(sa.String, unique=True)
    app_secret= sa.Column(sa.String, unique=True)
    trading_plans = relationship("TradingPlan", back_populates="user")


class Stock(Base):
    __tablename__ = "stocks"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    symbol = sa.Column(sa.String, unique=True, index=True)  # 종목 코드
    name = sa.Column(sa.String)  # 종목명
    market = sa.Column(sa.String)  # 시장 (KOSPI, KOSDAQ)
    current_price = sa.Column(sa.Float)
    change_rate = sa.Column(sa.Float)
    volume = sa.Column(sa.BigInteger)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    
    trading_plans = relationship("TradingPlan", back_populates="stock")


class TradingPlan(Base):
    __tablename__ = "trading_plans"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    stock_id = sa.Column(sa.Integer, sa.ForeignKey("stocks.id"))

    # 매매 계획
    plan_type = sa.Column(sa.String)  # 'buy' or 'sell'
    target_price = sa.Column(sa.Float)
    quantity = sa.Column(sa.Integer)
    reason = sa.Column(sa.Text)  # 매매 이유

    # 실제 매매 결과
    executed_price = sa.Column(sa.Float, nullable=True)
    executed_quantity = sa.Column(sa.Integer, nullable=True)
    executed_at = sa.Column(sa.DateTime, nullable=True)

    # 복기
    review = sa.Column(sa.Text, nullable=True)  # 복기 내용
    profit_loss = sa.Column(sa.Float, nullable=True)  # 수익/손실

    status = sa.Column(sa.String, default="planned")  # planned, executed, reviewed
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="trading_plans")
    stock = relationship("Stock", back_populates="trading_plans")
    recap = relationship("Recap", back_populates="trading_plan", uselist=False)


class TradingStock(Base):
    __tablename__ = "trading_stocks"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    stock_name = sa.Column(sa.String, nullable=False)  # 종목명
    stock_code = sa.Column(sa.String, unique=True, nullable=False, index=True)  # 종목코드
    is_downloaded = sa.Column(sa.Boolean, default=False)  # 다운로드 여부
    latest_orderno = sa.Column(sa.String, nullable=True)  # 최근 거래의 주문번호 (마지막으로 동기화된 거래)

    # 계좌평가현황에서 가져온 정보
    avg_prc = sa.Column(sa.Float, nullable=True)  # 평균단가
    rmnd_qty = sa.Column(sa.Integer, nullable=True)  # 보유수량
    pur_amt = sa.Column(sa.BigInteger, nullable=True)  # 매입금액

    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TradingHistory(Base):
    __tablename__ = "trading_history"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True)

    # 체결 정보
    executed_at = sa.Column(sa.DateTime, nullable=False, index=True)  # 체결 시각(날짜, 시간)
    trade_type = sa.Column(sa.String, nullable=False)  # 매매구분 ('buy' or 'sell')
    order_no = sa.Column(sa.String, nullable=True, index=True)  # 주문번호

    # 종목 정보
    stock_name = sa.Column(sa.String, nullable=False)  # 종목명
    stock_code = sa.Column(sa.String, nullable=False, index=True)  # 종목코드

    # 체결 가격 정보
    executed_price = sa.Column(sa.Float, nullable=False)  # 체결 가격
    executed_quantity = sa.Column(sa.Integer, nullable=False)  # 체결 수량
    executed_amount = sa.Column(sa.BigInteger, nullable=False)  # 체결 금액 (가격 * 수량)

    # 증권사 정보
    broker = sa.Column(sa.String, nullable=False)  # 증권사 (ex: kiwoom, kis)

    # 시스템 정보
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


class StocksInfo(Base):
    __tablename__ = "stocks_info"

    id = sa.Column(sa.Integer, primary_key=True, index=True)

    # ka10099 API 응답 데이터 매핑
    code = sa.Column(sa.String, unique=True, nullable=False, index=True)  # 종목코드
    name = sa.Column(sa.String, nullable=False)  # 종목명
    list_count = sa.Column(sa.String, nullable=True)  # 상장주식수
    audit_info = sa.Column(sa.String, nullable=True)  # 감시종목 (정상, 투자주의환기종목 등)
    reg_day = sa.Column(sa.String, nullable=True)  # 상장일 (YYYYMMDD)
    last_price = sa.Column(sa.String, nullable=True)  # 종목액면가
    state = sa.Column(sa.String, nullable=True)  # 증거금상태 (증거금100%, 관리종목 등)
    market_code = sa.Column(sa.String, nullable=True)  # 마켓코드 (0: 코스피, 10: 코스닥 등)
    market_name = sa.Column(sa.String, nullable=True)  # 마켓명 (코스피, 코스닥 등)
    up_name = sa.Column(sa.String, nullable=True)  # 상위종목명
    up_size_name = sa.Column(sa.String, nullable=True)  # 상위사이즈명
    company_class_name = sa.Column(sa.String, nullable=True)  # 회사분류명 (외국기업 등)
    order_warning = sa.Column(sa.String, nullable=True)  # 주문경고 (0: 정상, 1: 경고 등)
    nxt_enable = sa.Column(sa.String, nullable=True)  # 다음조회여부 (Y/N)

    # 시스템 정보
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Recap(Base):
    __tablename__ = "recap"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    trading_plan_id = sa.Column(sa.Integer, sa.ForeignKey("trading_plans.id"), nullable=True)  # 계획 기반 복기
    trading_id = sa.Column(sa.Integer, sa.ForeignKey("trading_history.id"), nullable=True)  # TradingHistory 테이블과의 연결
    order_no = sa.Column(sa.String, index=True)  # 주문번호 (한투 API)

    # 매매 이유 항목들
    catalyst = sa.Column(sa.Text, nullable=True)  # 재료
    market_condition = sa.Column(sa.Text, nullable=True)  # 시황
    price_chart = sa.Column(sa.Text, nullable=True)  # 가격(차트)
    volume = sa.Column(sa.Text, nullable=True)  # 거래량
    supply_demand = sa.Column(sa.Text, nullable=True)  # 수급(외국인/기관)
    emotion = sa.Column(sa.Text, nullable=True)  # 심리(매매 당시의 감정)
    evaluation = sa.Column(sa.String, nullable=True)  # 평가 (good, so-so, bad)
    evaluation_reason = sa.Column(sa.Text, nullable=True)  # 평가 이유
    etc = sa.Column(sa.Text, nullable=True)  # 기타(자유 기술)

    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    trading_plan = relationship("TradingPlan", back_populates="recap")
    trading = relationship("TradingHistory")