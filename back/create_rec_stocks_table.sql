-- rec_stocks 테이블 생성 스크립트
-- 목적: 추천 알고리즘에 의해 추천되는 종목들을 관리하는 테이블

CREATE TABLE IF NOT EXISTS rec_stocks (
    id SERIAL PRIMARY KEY,

    -- 종목 정보
    stock_name VARCHAR NOT NULL,          -- 종목명
    stock_code VARCHAR NOT NULL,          -- 종목코드

    -- 추천 정보
    recommendation_date DATE NOT NULL,    -- 추천날짜
    algorithm_id INTEGER NOT NULL,        -- 추천 알고리즘 ID (FK)

    -- 종가 및 전일비
    closing_price FLOAT NOT NULL,         -- 당일 종가
    change_rate FLOAT,                    -- 전일비 (%)

    -- 시스템 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 외래키
    FOREIGN KEY (algorithm_id) REFERENCES algorithm(id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_rec_stocks_stock_code ON rec_stocks(stock_code);
CREATE INDEX IF NOT EXISTS idx_rec_stocks_recommendation_date ON rec_stocks(recommendation_date);
CREATE INDEX IF NOT EXISTS idx_rec_stocks_algorithm_id ON rec_stocks(algorithm_id);

-- 복합 인덱스 (추천날짜와 종목코드로 빠른 조회)
CREATE INDEX IF NOT EXISTS idx_rec_stocks_date_code ON rec_stocks(recommendation_date, stock_code);

-- 복합 인덱스 (알고리즘과 추천날짜로 빠른 조회)
CREATE INDEX IF NOT EXISTS idx_rec_stocks_algo_date ON rec_stocks(algorithm_id, recommendation_date);
