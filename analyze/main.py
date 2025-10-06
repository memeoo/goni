"""
종목 분석 및 추천 서비스 메인 모듈
실시간 데이터 수집, 기술적 분석, 뉴스 분석 등을 수행
"""

import asyncio
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv

from src.data_collector import DataCollector
from src.technical_analyzer import TechnicalAnalyzer
from src.news_analyzer import NewsAnalyzer
from src.database import Database

load_dotenv()


class AnalysisService:
    def __init__(self):
        self.data_collector = DataCollector()
        self.technical_analyzer = TechnicalAnalyzer()
        self.news_analyzer = NewsAnalyzer()
        self.db = Database()
    
    async def run_daily_analysis(self):
        """일일 종목 분석 실행"""
        print(f"[{datetime.now()}] 일일 분석 시작")
        
        try:
            # 1. 주식 데이터 수집
            stocks_data = await self.data_collector.collect_stock_data()
            print(f"수집된 종목 수: {len(stocks_data)}")
            
            # 2. 기술적 분석
            for stock_data in stocks_data:
                technical_signals = self.technical_analyzer.analyze(stock_data)
                
                # 3. 뉴스 분석
                news_sentiment = await self.news_analyzer.analyze_stock_news(
                    stock_data['symbol']
                )
                
                # 4. 종합 분석 결과 저장
                analysis_result = {
                    'symbol': stock_data['symbol'],
                    'technical_signals': technical_signals,
                    'news_sentiment': news_sentiment,
                    'analysis_date': datetime.now(),
                    'recommendation': self._generate_recommendation(
                        technical_signals, news_sentiment
                    )
                }
                
                await self.db.save_analysis_result(analysis_result)
            
            print(f"[{datetime.now()}] 일일 분석 완료")
            
        except Exception as e:
            print(f"분석 중 오류 발생: {e}")
    
    def _generate_recommendation(self, technical_signals, news_sentiment):
        """기술적 분석과 뉴스 분석을 종합하여 추천 생성"""
        score = 0
        
        # 기술적 지표 점수
        if technical_signals.get('rsi_signal') == 'buy':
            score += 1
        elif technical_signals.get('rsi_signal') == 'sell':
            score -= 1
            
        if technical_signals.get('macd_signal') == 'buy':
            score += 1
        elif technical_signals.get('macd_signal') == 'sell':
            score -= 1
            
        if technical_signals.get('bollinger_signal') == 'buy':
            score += 1
        elif technical_signals.get('bollinger_signal') == 'sell':
            score -= 1
        
        # 뉴스 감정 점수
        if news_sentiment > 0.3:
            score += 1
        elif news_sentiment < -0.3:
            score -= 1
        
        # 추천 결정
        if score >= 2:
            return 'strong_buy'
        elif score == 1:
            return 'buy'
        elif score == -1:
            return 'sell'
        elif score <= -2:
            return 'strong_sell'
        else:
            return 'hold'
    
    async def run_realtime_monitoring(self):
        """실시간 모니터링 (장중)"""
        print(f"[{datetime.now()}] 실시간 모니터링 시작")
        
        while True:
            try:
                # 실시간 데이터 수집 및 분석
                realtime_data = await self.data_collector.collect_realtime_data()
                
                # 급등/급락 감지
                alerts = self.technical_analyzer.detect_price_alerts(realtime_data)
                
                for alert in alerts:
                    await self.db.save_alert(alert)
                    print(f"알림: {alert}")
                
                # 30초 대기
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"실시간 모니터링 오류: {e}")
                await asyncio.sleep(60)


def run_scheduler():
    """스케줄러 실행"""
    service = AnalysisService()
    
    # 평일 오전 9시에 일일 분석 실행
    schedule.every().monday.at("09:00").do(
        lambda: asyncio.run(service.run_daily_analysis())
    )
    schedule.every().tuesday.at("09:00").do(
        lambda: asyncio.run(service.run_daily_analysis())
    )
    schedule.every().wednesday.at("09:00").do(
        lambda: asyncio.run(service.run_daily_analysis())
    )
    schedule.every().thursday.at("09:00").do(
        lambda: asyncio.run(service.run_daily_analysis())
    )
    schedule.every().friday.at("09:00").do(
        lambda: asyncio.run(service.run_daily_analysis())
    )
    
    print("분석 서비스 스케줄러 시작")
    
    while True:
        schedule.run_pending()
        time.sleep(1)


async def main():
    """메인 함수"""
    service = AnalysisService()
    
    # 초기 분석 실행
    await service.run_daily_analysis()
    
    # 실시간 모니터링과 스케줄러를 동시에 실행
    await asyncio.gather(
        service.run_realtime_monitoring(),
        asyncio.to_thread(run_scheduler)
    )


if __name__ == "__main__":
    asyncio.run(main())