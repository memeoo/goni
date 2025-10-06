"""
주식 데이터 수집 모듈
yfinance, 네이버 증권 등을 통해 실시간 및 과거 데이터 수집
"""

import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any


class DataCollector:
    def __init__(self):
        self.kospi_symbols = [
            '005930.KS',  # 삼성전자
            '000660.KS',  # SK하이닉스
            '035420.KS',  # NAVER
            '051910.KS',  # LG화학
            '006400.KS',  # 삼성SDI
            '035720.KS',  # 카카오
            '028260.KS',  # 삼성물산
            '068270.KS',  # 셀트리온
            '207940.KS',  # 삼성바이오로직스
            '066570.KS',  # LG전자
        ]
        
        self.kosdaq_symbols = [
            '091990.KQ',  # 셀트리온헬스케어
            '196170.KQ',  # 알테오젠
            '058470.KQ',  # 리노공업
            '240810.KQ',  # 원익IPS
            '112040.KQ',  # 위메이드
            '263750.KQ',  # 펄어비스
            '039030.KQ',  # 이오테크닉스
            '084370.KQ',  # 유진테크
            '214150.KQ',  # 클래시스
            '950140.KQ',  # 잉글우드랩
        ]
    
    async def collect_stock_data(self) -> List[Dict[str, Any]]:
        """주요 종목의 주식 데이터 수집"""
        all_symbols = self.kospi_symbols + self.kosdaq_symbols
        stock_data = []
        
        for symbol in all_symbols:
            try:
                ticker = yf.Ticker(symbol)
                
                # 과거 1년 데이터
                hist = ticker.history(period="1y")
                
                if not hist.empty:
                    current_price = hist['Close'][-1]
                    prev_price = hist['Close'][-2] if len(hist) > 1 else current_price
                    change_rate = ((current_price - prev_price) / prev_price) * 100
                    
                    stock_info = {
                        'symbol': symbol.replace('.KS', '').replace('.KQ', ''),
                        'yahoo_symbol': symbol,
                        'name': self._get_stock_name(symbol),
                        'market': 'KOSPI' if '.KS' in symbol else 'KOSDAQ',
                        'current_price': float(current_price),
                        'change_rate': float(change_rate),
                        'volume': int(hist['Volume'][-1]),
                        'historical_data': hist,
                        'updated_at': datetime.now()
                    }
                    
                    stock_data.append(stock_info)
                    print(f"수집 완료: {stock_info['name']} ({stock_info['symbol']})")
                
            except Exception as e:
                print(f"데이터 수집 실패 {symbol}: {e}")
                continue
        
        return stock_data
    
    async def collect_realtime_data(self) -> List[Dict[str, Any]]:
        """실시간 주식 데이터 수집"""
        all_symbols = self.kospi_symbols + self.kosdaq_symbols
        realtime_data = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for symbol in all_symbols:
                task = self._fetch_realtime_price(session, symbol)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict):
                    realtime_data.append(result)
        
        return realtime_data
    
    async def _fetch_realtime_price(self, session: aiohttp.ClientSession, symbol: str) -> Dict[str, Any]:
        """개별 종목의 실시간 가격 조회"""
        try:
            ticker = yf.Ticker(symbol)
            
            # 최근 5일 데이터로 실시간 가격 조회
            hist = ticker.history(period="5d", interval="1m")
            
            if not hist.empty:
                latest_data = hist.iloc[-1]
                
                return {
                    'symbol': symbol.replace('.KS', '').replace('.KQ', ''),
                    'price': float(latest_data['Close']),
                    'volume': int(latest_data['Volume']),
                    'timestamp': datetime.now()
                }
        except Exception as e:
            print(f"실시간 데이터 수집 실패 {symbol}: {e}")
            return {}
    
    def _get_stock_name(self, symbol: str) -> str:
        """종목 코드로 종목명 조회"""
        stock_names = {
            '005930.KS': '삼성전자',
            '000660.KS': 'SK하이닉스',
            '035420.KS': 'NAVER',
            '051910.KS': 'LG화학',
            '006400.KS': '삼성SDI',
            '035720.KS': '카카오',
            '028260.KS': '삼성물산',
            '068270.KS': '셀트리온',
            '207940.KS': '삼성바이오로직스',
            '066570.KS': 'LG전자',
            '091990.KQ': '셀트리온헬스케어',
            '196170.KQ': '알테오젠',
            '058470.KQ': '리노공업',
            '240810.KQ': '원익IPS',
            '112040.KQ': '위메이드',
            '263750.KQ': '펄어비스',
            '039030.KQ': '이오테크닉스',
            '084370.KQ': '유진테크',
            '214150.KQ': '클래시스',
            '950140.KQ': '잉글우드랩',
        }
        
        return stock_names.get(symbol, symbol)
    
    async def collect_market_index(self) -> Dict[str, Any]:
        """시장 지수 정보 수집"""
        try:
            # KOSPI 지수
            kospi = yf.Ticker('^KS11')
            kospi_hist = kospi.history(period="5d")
            
            # KOSDAQ 지수
            kosdaq = yf.Ticker('^KQ11')
            kosdaq_hist = kosdaq.history(period="5d")
            
            return {
                'kospi': {
                    'value': float(kospi_hist['Close'][-1]),
                    'change': float(kospi_hist['Close'][-1] - kospi_hist['Close'][-2]),
                    'change_rate': float(((kospi_hist['Close'][-1] - kospi_hist['Close'][-2]) / kospi_hist['Close'][-2]) * 100)
                },
                'kosdaq': {
                    'value': float(kosdaq_hist['Close'][-1]),
                    'change': float(kosdaq_hist['Close'][-1] - kosdaq_hist['Close'][-2]),
                    'change_rate': float(((kosdaq_hist['Close'][-1] - kosdaq_hist['Close'][-2]) / kosdaq_hist['Close'][-2]) * 100)
                },
                'updated_at': datetime.now()
            }
        
        except Exception as e:
            print(f"시장 지수 수집 실패: {e}")
            return {}
    
    async def collect_economic_indicators(self) -> Dict[str, Any]:
        """경제 지표 수집 (환율, 금리 등)"""
        try:
            # USD/KRW 환율
            usdkrw = yf.Ticker('USDKRW=X')
            usdkrw_hist = usdkrw.history(period="5d")
            
            # 국고채 10년 수익률 (한국)
            # kr10y = yf.Ticker('^IRX')  # 임시로 미국 3개월 국채
            
            return {
                'usd_krw': {
                    'rate': float(usdkrw_hist['Close'][-1]),
                    'change': float(usdkrw_hist['Close'][-1] - usdkrw_hist['Close'][-2]),
                    'change_rate': float(((usdkrw_hist['Close'][-1] - usdkrw_hist['Close'][-2]) / usdkrw_hist['Close'][-2]) * 100)
                },
                'updated_at': datetime.now()
            }
        
        except Exception as e:
            print(f"경제 지표 수집 실패: {e}")
            return {}