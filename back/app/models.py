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


class Recap(Base):
    __tablename__ = "recap"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    trading_plan_id = sa.Column(sa.Integer, sa.ForeignKey("trading_plans.id"), nullable=True)  # nullable로 변경
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