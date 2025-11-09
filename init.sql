-- 초기 데이터베이스 설정 스크립트

-- 기본 사용자 생성 (이미 환경변수로 설정됨)
-- CREATE USER goniadmin WITH PASSWORD 'shsbsy70';
-- CREATE DATABASE goni OWNER goniadmin;

-- UUID 확장 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 타임존 설정
SET timezone = 'Asia/Seoul';

-- 샘플 데이터 삽입을 위한 테이블 (FastAPI에서 생성되는 테이블과 동일)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(20) NOT NULL,
    current_price DECIMAL(12,2),
    change_rate DECIMAL(5,2),
    volume BIGINT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trading_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    plan_type VARCHAR(10) NOT NULL CHECK (plan_type IN ('buy', 'sell')),
    target_price DECIMAL(12,2) NOT NULL,
    quantity INTEGER NOT NULL,
    reason TEXT NOT NULL,
    executed_price DECIMAL(12,2),
    executed_quantity INTEGER,
    executed_at TIMESTAMP WITH TIME ZONE,
    review TEXT,
    profit_loss DECIMAL(12,2),
    status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'executed', 'reviewed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_stocks_symbol ON stocks(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_plans_user_id ON trading_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_plans_stock_id ON trading_plans(stock_id);
CREATE INDEX IF NOT EXISTS idx_trading_plans_status ON trading_plans(status);
CREATE INDEX IF NOT EXISTS idx_trading_plans_created_at ON trading_plans(created_at DESC);

-- 샘플 주식 데이터 삽입
INSERT INTO stocks (symbol, name, market, current_price, change_rate, volume) VALUES
('005930', '삼성전자', 'KOSPI', 70000, 1.5, 1000000),
('000660', 'SK하이닉스', 'KOSPI', 85000, 2.3, 800000),
('035420', 'NAVER', 'KOSPI', 180000, -0.8, 500000),
('051910', 'LG화학', 'KOSPI', 420000, 3.2, 300000),
('006400', '삼성SDI', 'KOSPI', 380000, 1.8, 250000),
('035720', '카카오', 'KOSPI', 45000, -1.2, 900000),
('068270', '셀트리온', 'KOSPI', 160000, 2.1, 400000),
('207940', '삼성바이오로직스', 'KOSPI', 750000, 0.5, 150000),
('066570', 'LG전자', 'KOSPI', 95000, 1.7, 600000),
('028260', '삼성물산', 'KOSPI', 110000, -0.3, 350000),
('091990', '셀트리온헬스케어', 'KOSDAQ', 82000, 3.5, 450000),
('196170', '알테오젠', 'KOSDAQ', 85000, 2.8, 200000),
('058470', '리노공업', 'KOSDAQ', 180000, 4.2, 180000),
('240810', '원익IPS', 'KOSDAQ', 35000, 1.9, 220000),
('112040', '위메이드', 'KOSDAQ', 40000, -2.1, 350000)
ON CONFLICT (symbol) DO NOTHING;

-- 트리거 함수: updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_trading_plans_updated_at BEFORE UPDATE ON trading_plans
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TABLE IF NOT EXISTS stocks_info (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    list_count VARCHAR(50),
    audit_info VARCHAR(50),
    reg_day VARCHAR(10),
    last_price VARCHAR(20),
    state VARCHAR(50),
    market_code VARCHAR(10),
    market_name VARCHAR(50),
    up_name VARCHAR(255),
    up_size_name VARCHAR(255),
    company_class_name VARCHAR(50),
    order_warning VARCHAR(10),
    nxt_enable VARCHAR(1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- stocks_info 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_stocks_info_code ON stocks_info(code);
CREATE INDEX IF NOT EXISTS idx_stocks_info_market_code ON stocks_info(market_code);
CREATE INDEX IF NOT EXISTS idx_stocks_info_name ON stocks_info(name);
CREATE INDEX IF NOT EXISTS idx_stocks_info_created_at ON stocks_info(created_at DESC);

-- 권한 설정
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO goniadmin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO goniadmin;

-- 샘플 사용자 생성 (개발용)
-- 비밀번호: testpassword123 (bcrypt 해시)
INSERT INTO users (email, username, hashed_password) VALUES
('test@goni.com', 'testuser', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewpaXAo4UETWvAse')
ON CONFLICT (email) DO NOTHING;