"""
분석 결과 데이터베이스 연동 모듈
PostgreSQL에 분석 결과 저장 및 조회
"""

import asyncio
import asyncpg
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self):
        self.connection_string = os.getenv(
            "DATABASE_URL",
            "postgresql://goniadmin:shsbsy70@localhost:5432/goni"
        )
        self.pool = None
    
    async def connect(self):
        """데이터베이스 연결 풀 생성"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            print("데이터베이스 연결 풀 생성 완료")
            
            # 테이블 생성
            await self._create_tables()
            
        except Exception as e:
            print(f"데이터베이스 연결 실패: {e}")
            raise
    
    async def disconnect(self):
        """데이터베이스 연결 풀 종료"""
        if self.pool:
            await self.pool.close()
            print("데이터베이스 연결 풀 종료")
    
    async def _create_tables(self):
        """분석 관련 테이블 생성"""
        async with self.pool.acquire() as connection:
            # 종목 분석 결과 테이블
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS stock_analysis (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    analysis_data JSONB NOT NULL,
                    technical_signals JSONB,
                    news_sentiment FLOAT,
                    recommendation VARCHAR(20),
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 실시간 알림 테이블
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS price_alerts (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    price FLOAT,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE
                )
            """)
            
            # 시장 지수 데이터 테이블
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS market_indices (
                    id SERIAL PRIMARY KEY,
                    index_name VARCHAR(20) NOT NULL,
                    value FLOAT NOT NULL,
                    change_amount FLOAT,
                    change_rate FLOAT,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 뉴스 감정 분석 테이블
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS news_sentiment (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10),
                    title TEXT NOT NULL,
                    content TEXT,
                    sentiment_score FLOAT NOT NULL,
                    source VARCHAR(50),
                    published_at TIMESTAMP,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 인덱스 생성
            await connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_stock_analysis_symbol_date 
                ON stock_analysis(symbol, analysis_date DESC)
            """)
            
            await connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_alerts_symbol_time 
                ON price_alerts(symbol, triggered_at DESC)
            """)
            
            print("분석 테이블 생성/확인 완료")
    
    async def save_analysis_result(self, analysis_data: Dict[str, Any]):
        """종목 분석 결과 저장"""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute("""
                    INSERT INTO stock_analysis 
                    (symbol, analysis_data, technical_signals, news_sentiment, recommendation, analysis_date)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                    analysis_data['symbol'],
                    json.dumps(analysis_data, default=str, ensure_ascii=False),
                    json.dumps(analysis_data.get('technical_signals', {}), default=str),
                    analysis_data.get('news_sentiment', 0.0),
                    analysis_data.get('recommendation', 'hold'),
                    analysis_data.get('analysis_date', datetime.now())
                )
                
                print(f"분석 결과 저장 완료: {analysis_data['symbol']}")
                
        except Exception as e:
            print(f"분석 결과 저장 실패 {analysis_data.get('symbol', 'unknown')}: {e}")
    
    async def save_alert(self, alert_data: Dict[str, Any]):
        """가격 알림 저장"""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute("""
                    INSERT INTO price_alerts 
                    (symbol, alert_type, message, price, triggered_at)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    alert_data['symbol'],
                    alert_data['alert_type'],
                    alert_data['message'],
                    alert_data.get('price'),
                    alert_data.get('timestamp', datetime.now())
                )
                
                print(f"알림 저장 완료: {alert_data['symbol']}")
                
        except Exception as e:
            print(f"알림 저장 실패 {alert_data.get('symbol', 'unknown')}: {e}")
    
    async def save_market_index(self, index_data: Dict[str, Any]):
        """시장 지수 데이터 저장"""
        try:
            async with self.pool.acquire() as connection:
                # KOSPI
                if 'kospi' in index_data:
                    kospi = index_data['kospi']
                    await connection.execute("""
                        INSERT INTO market_indices 
                        (index_name, value, change_amount, change_rate, recorded_at)
                        VALUES ($1, $2, $3, $4, $5)
                    """,
                        'KOSPI',
                        kospi['value'],
                        kospi['change'],
                        kospi['change_rate'],
                        index_data.get('updated_at', datetime.now())
                    )
                
                # KOSDAQ
                if 'kosdaq' in index_data:
                    kosdaq = index_data['kosdaq']
                    await connection.execute("""
                        INSERT INTO market_indices 
                        (index_name, value, change_amount, change_rate, recorded_at)
                        VALUES ($1, $2, $3, $4, $5)
                    """,
                        'KOSDAQ',
                        kosdaq['value'],
                        kosdaq['change'],
                        kosdaq['change_rate'],
                        index_data.get('updated_at', datetime.now())
                    )
                
                print("시장 지수 저장 완료")
                
        except Exception as e:
            print(f"시장 지수 저장 실패: {e}")
    
    async def save_news_sentiment(self, news_data: List[Dict[str, Any]], symbol: str = None):
        """뉴스 감정 분석 결과 저장"""
        try:
            async with self.pool.acquire() as connection:
                for news in news_data:
                    await connection.execute("""
                        INSERT INTO news_sentiment 
                        (symbol, title, content, sentiment_score, source, published_at, analyzed_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                        symbol,
                        news.get('title', ''),
                        news.get('content', ''),
                        news.get('sentiment_score', 0.0),
                        news.get('source', ''),
                        news.get('timestamp'),
                        datetime.now()
                    )
                
                print(f"뉴스 감정 분석 저장 완료: {len(news_data)}건")
                
        except Exception as e:
            print(f"뉴스 감정 분석 저장 실패: {e}")
    
    async def get_latest_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """특정 종목의 최신 분석 결과 조회"""
        try:
            async with self.pool.acquire() as connection:
                row = await connection.fetchrow("""
                    SELECT * FROM stock_analysis 
                    WHERE symbol = $1 
                    ORDER BY analysis_date DESC 
                    LIMIT 1
                """, symbol)
                
                if row:
                    return {
                        'id': row['id'],
                        'symbol': row['symbol'],
                        'analysis_data': row['analysis_data'],
                        'technical_signals': row['technical_signals'],
                        'news_sentiment': row['news_sentiment'],
                        'recommendation': row['recommendation'],
                        'analysis_date': row['analysis_date'],
                        'created_at': row['created_at']
                    }
                
                return None
                
        except Exception as e:
            print(f"분석 결과 조회 실패 {symbol}: {e}")
            return None
    
    async def get_recommendations(self, recommendation_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """추천 종목 목록 조회"""
        try:
            async with self.pool.acquire() as connection:
                if recommendation_type:
                    query = """
                        SELECT DISTINCT ON (symbol) * FROM stock_analysis 
                        WHERE recommendation = $1 
                        ORDER BY symbol, analysis_date DESC 
                        LIMIT $2
                    """
                    rows = await connection.fetch(query, recommendation_type, limit)
                else:
                    query = """
                        SELECT DISTINCT ON (symbol) * FROM stock_analysis 
                        ORDER BY symbol, analysis_date DESC 
                        LIMIT $1
                    """
                    rows = await connection.fetch(query, limit)
                
                recommendations = []
                for row in rows:
                    recommendations.append({
                        'id': row['id'],
                        'symbol': row['symbol'],
                        'analysis_data': row['analysis_data'],
                        'technical_signals': row['technical_signals'],
                        'news_sentiment': row['news_sentiment'],
                        'recommendation': row['recommendation'],
                        'analysis_date': row['analysis_date']
                    })
                
                return recommendations
                
        except Exception as e:
            print(f"추천 목록 조회 실패: {e}")
            return []
    
    async def get_recent_alerts(self, symbol: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """최근 알림 목록 조회"""
        try:
            async with self.pool.acquire() as connection:
                if symbol:
                    query = """
                        SELECT * FROM price_alerts 
                        WHERE symbol = $1 
                        ORDER BY triggered_at DESC 
                        LIMIT $2
                    """
                    rows = await connection.fetch(query, symbol, limit)
                else:
                    query = """
                        SELECT * FROM price_alerts 
                        ORDER BY triggered_at DESC 
                        LIMIT $1
                    """
                    rows = await connection.fetch(query, limit)
                
                alerts = []
                for row in rows:
                    alerts.append({
                        'id': row['id'],
                        'symbol': row['symbol'],
                        'alert_type': row['alert_type'],
                        'message': row['message'],
                        'price': row['price'],
                        'triggered_at': row['triggered_at'],
                        'is_read': row['is_read']
                    })
                
                return alerts
                
        except Exception as e:
            print(f"알림 목록 조회 실패: {e}")
            return []
    
    async def mark_alert_as_read(self, alert_id: int):
        """알림을 읽음으로 표시"""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute("""
                    UPDATE price_alerts 
                    SET is_read = TRUE 
                    WHERE id = $1
                """, alert_id)
                
                print(f"알림 읽음 처리 완료: {alert_id}")
                
        except Exception as e:
            print(f"알림 읽음 처리 실패 {alert_id}: {e}")
    
    async def get_market_indices_history(self, days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """시장 지수 히스토리 조회"""
        try:
            async with self.pool.acquire() as connection:
                query = """
                    SELECT * FROM market_indices 
                    WHERE recorded_at >= NOW() - INTERVAL '%s days'
                    ORDER BY index_name, recorded_at DESC
                """ % days
                
                rows = await connection.fetch(query)
                
                indices = {'KOSPI': [], 'KOSDAQ': []}
                for row in rows:
                    index_data = {
                        'value': row['value'],
                        'change_amount': row['change_amount'],
                        'change_rate': row['change_rate'],
                        'recorded_at': row['recorded_at']
                    }
                    
                    if row['index_name'] in indices:
                        indices[row['index_name']].append(index_data)
                
                return indices
                
        except Exception as e:
            print(f"시장 지수 히스토리 조회 실패: {e}")
            return {'KOSPI': [], 'KOSDAQ': []}