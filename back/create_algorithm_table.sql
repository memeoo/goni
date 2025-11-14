-- Algorithm 테이블 생성 스크립트
CREATE TABLE IF NOT EXISTS algorithm (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_algorithm_name ON algorithm(name);

-- 테스트 데이터 (선택사항)
-- INSERT INTO algorithm (name, description) VALUES
-- ('고니 퀀트 알고리즘 v1', '머신러닝 기반의 종목 추천 알고리즘');
