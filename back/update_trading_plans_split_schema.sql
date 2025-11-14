-- 매매 계획 테이블 분리
-- 2025-11-13: trading_plans와 trading_plans_history로 분리

-- 1단계: 기존 테이블 백업 (필요한 경우)
-- CREATE TABLE trading_plans_backup AS SELECT * FROM trading_plans;

-- 2단계: 기존 trading_plans 테이블 삭제
DROP TABLE IF EXISTS trading_plans CASCADE;

-- 3단계: 새로운 trading_plans 테이블 (계획 모드 종목 목록용)
CREATE TABLE trading_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stock_code VARCHAR(10) NOT NULL,  -- 종목코드
    stock_name VARCHAR(100),           -- 종목명
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- trading_plans 인덱스
CREATE INDEX IF NOT EXISTS idx_trading_plans_user_id ON trading_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_plans_stock_code ON trading_plans(stock_code);
CREATE INDEX IF NOT EXISTS idx_trading_plans_created_at ON trading_plans(created_at DESC);

-- 4단계: trading_plans_history 테이블 (매매 계획 히스토리용)
CREATE TABLE trading_plans_history (
    id SERIAL PRIMARY KEY,
    trading_plan_id INTEGER NOT NULL REFERENCES trading_plans(id) ON DELETE CASCADE,

    -- 매매 종류 및 조건
    trading_type VARCHAR(10) NOT NULL CHECK (trading_type IN ('buy', 'sell')),  -- 'buy' or 'sell'
    condition TEXT,                    -- 매매 조건 (사용자 입력)

    -- 매매 계획 가격 및 금액
    target_price DECIMAL(12,2),        -- 매매 계획 가격
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

-- trading_plans_history 인덱스
CREATE INDEX IF NOT EXISTS idx_trading_plans_history_trading_plan_id ON trading_plans_history(trading_plan_id);
CREATE INDEX IF NOT EXISTS idx_trading_plans_history_trading_type ON trading_plans_history(trading_type);
CREATE INDEX IF NOT EXISTS idx_trading_plans_history_created_at ON trading_plans_history(created_at DESC);

-- 5단계: 트리거 함수 생성
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 6단계: 트리거 생성
CREATE TRIGGER update_trading_plans_updated_at BEFORE UPDATE ON trading_plans
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_trading_plans_history_updated_at BEFORE UPDATE ON trading_plans_history
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- 7단계: 권한 설정
GRANT ALL PRIVILEGES ON trading_plans TO goniadmin;
GRANT ALL PRIVILEGES ON trading_plans_history TO goniadmin;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO goniadmin;
