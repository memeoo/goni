-- 매매 계획 테이블 스키마 업데이트
-- 2025-11-13: trading_plans 테이블 재설계

-- 1단계: 기존 데이터 백업 (필요한 경우)
-- CREATE TABLE trading_plans_backup AS SELECT * FROM trading_plans;

-- 2단계: 기존 테이블 제약 조건 및 트리거 제거
DROP TRIGGER IF EXISTS update_trading_plans_updated_at ON trading_plans CASCADE;

-- 3단계: 새로운 스키마로 trading_plans 테이블 재생성
-- 기존 테이블 삭제 및 재생성 (데이터 손실 주의)
DROP TABLE IF EXISTS trading_plans CASCADE;

CREATE TABLE trading_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 종목 정보
    stock_code VARCHAR(10) NOT NULL,  -- 종목코드
    stock_name VARCHAR(100),           -- 종목명

    -- 매매 종류 및 조건
    trading_type VARCHAR(10) NOT NULL CHECK (trading_type IN ('buy', 'sell')),  -- 'buy' or 'sell'
    condition TEXT,                    -- 매매 조건 (사용자 입력)

    -- 매매 계획 가격 및 금액
    target_price DECIMAL(12,2),        -- 매매 계획 가격 (매수가/매도가)
    amount BIGINT,                     -- 매매 금액

    -- 매매 이유
    reason TEXT,                       -- 매매 이유

    -- 매도 계획 비중 (매도일 때만)
    proportion DECIMAL(5,2),           -- 매도 비중 (%)

    -- 익절(Stop Profit) 설정
    sp_condition TEXT,                 -- 익절 조건
    sp_price DECIMAL(12,2),            -- 익절 가격
    sp_ratio DECIMAL(5,2),             -- 익절 수익률 (%)

    -- 손절(Stop Loss) 설정
    sl_condition TEXT,                 -- 손절 조건
    sl_price DECIMAL(12,2),            -- 손절 가격
    sl_ratio DECIMAL(5,2),             -- 손절 수익률 (%)

    -- 시스템 정보
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_trading_plans_user_id ON trading_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_plans_stock_code ON trading_plans(stock_code);
CREATE INDEX IF NOT EXISTS idx_trading_plans_trading_type ON trading_plans(trading_type);
CREATE INDEX IF NOT EXISTS idx_trading_plans_created_at ON trading_plans(created_at DESC);

-- 트리거 함수 생성 (이미 존재하지 않는 경우)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거: updated_at 자동 업데이트
CREATE TRIGGER update_trading_plans_updated_at BEFORE UPDATE ON trading_plans
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- 권한 설정
GRANT ALL PRIVILEGES ON trading_plans TO goniadmin;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO goniadmin;
