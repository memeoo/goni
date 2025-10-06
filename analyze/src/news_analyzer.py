"""
뉴스 분석 모듈
종목 관련 뉴스 수집 및 감정 분석
"""

import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re


class NewsAnalyzer:
    def __init__(self):
        self.positive_keywords = [
            '상승', '호재', '성장', '증가', '개선', '확대', '투자', '수주', '계약',
            '신규', '출시', '개발', '혁신', '성과', '실적', '매출', '이익', '배당',
            '인수', '합병', '제휴', '협력', '승인', '허가'
        ]
        
        self.negative_keywords = [
            '하락', '악재', '감소', '축소', '손실', '적자', '부진', '우려', '리스크',
            '하향', '조정', '취소', '연기', '중단', '분쟁', '소송', '제재', '규제',
            '경고', '위기', '파업', '사고', '결함', '리콜'
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def analyze_stock_news(self, symbol: str) -> float:
        """특정 종목의 뉴스 감정 분석"""
        try:
            # 네이버 증권 뉴스 수집
            news_articles = await self._collect_naver_news(symbol)
            
            # 다음 증권 뉴스 수집 (추가)
            daum_articles = await self._collect_daum_news(symbol)
            news_articles.extend(daum_articles)
            
            if not news_articles:
                return 0.0  # 중립
            
            # 감정 점수 계산
            sentiment_scores = []
            for article in news_articles:
                score = self._calculate_sentiment_score(article)
                sentiment_scores.append(score)
            
            # 전체 감정 점수 (가중 평균)
            if sentiment_scores:
                total_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                # -1.0 ~ 1.0 범위로 정규화
                return max(-1.0, min(1.0, total_sentiment))
            
            return 0.0
            
        except Exception as e:
            print(f"뉴스 분석 실패 {symbol}: {e}")
            return 0.0
    
    async def _collect_naver_news(self, symbol: str) -> List[Dict[str, Any]]:
        """네이버 증권 뉴스 수집"""
        articles = []
        
        try:
            # 네이버 증권 뉴스 URL (종목 코드 기반)
            url = f"https://finance.naver.com/item/news.nhn?code={symbol}"
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 뉴스 제목과 링크 추출
                        news_items = soup.select('.title')
                        
                        for item in news_items[:10]:  # 최대 10개
                            title_link = item.find('a')
                            if title_link:
                                title = title_link.text.strip()
                                link = 'https://finance.naver.com' + title_link.get('href', '')
                                
                                # 뉴스 내용 수집
                                content = await self._fetch_article_content(session, link)
                                
                                articles.append({
                                    'title': title,
                                    'content': content,
                                    'link': link,
                                    'source': 'naver',
                                    'timestamp': datetime.now()
                                })
                                
                                # 요청 간격 조절
                                await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"네이버 뉴스 수집 실패 {symbol}: {e}")
        
        return articles
    
    async def _collect_daum_news(self, symbol: str) -> List[Dict[str, Any]]:
        """다음 증권 뉴스 수집"""
        articles = []
        
        try:
            # 다음 증권 뉴스 URL
            url = f"https://finance.daum.net/quotes/A{symbol}#news"
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 뉴스 제목 추출 (다음의 경우 동적 로딩이므로 제한적)
                        news_items = soup.select('.newsList .item')
                        
                        for item in news_items[:5]:  # 최대 5개
                            title_elem = item.select_one('.subject')
                            if title_elem:
                                title = title_elem.text.strip()
                                
                                articles.append({
                                    'title': title,
                                    'content': title,  # 제목만 사용
                                    'link': '',
                                    'source': 'daum',
                                    'timestamp': datetime.now()
                                })
            
        except Exception as e:
            print(f"다음 뉴스 수집 실패 {symbol}: {e}")
        
        return articles
    
    async def _fetch_article_content(self, session: aiohttp.ClientSession, url: str) -> str:
        """뉴스 기사 내용 수집"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 네이버 뉴스 본문 추출
                    content_elem = soup.select_one('#content')
                    if content_elem:
                        # 불필요한 태그 제거
                        for script in content_elem(["script", "style"]):
                            script.decompose()
                        
                        content = content_elem.get_text(strip=True)
                        return content[:1000]  # 최대 1000자
            
        except Exception as e:
            print(f"기사 내용 수집 실패 {url}: {e}")
        
        return ""
    
    def _calculate_sentiment_score(self, article: Dict[str, Any]) -> float:
        """개별 기사의 감정 점수 계산"""
        text = f"{article['title']} {article['content']}"
        text = text.lower()
        
        positive_count = 0
        negative_count = 0
        
        # 긍정 키워드 카운트
        for keyword in self.positive_keywords:
            positive_count += text.count(keyword)
        
        # 부정 키워드 카운트
        for keyword in self.negative_keywords:
            negative_count += text.count(keyword)
        
        # 점수 계산
        total_keywords = positive_count + negative_count
        
        if total_keywords == 0:
            return 0.0  # 중립
        
        # -1.0 ~ 1.0 범위로 정규화
        sentiment_score = (positive_count - negative_count) / total_keywords
        
        # 키워드 밀도에 따른 가중치 적용
        keyword_density = total_keywords / len(text.split()) if len(text.split()) > 0 else 0
        weight = min(1.0, keyword_density * 10)  # 최대 가중치 1.0
        
        return sentiment_score * weight
    
    def get_trending_stocks_news(self) -> List[Dict[str, Any]]:
        """실시간 이슈 종목 뉴스"""
        try:
            # 네이버 증권 메인 페이지에서 이슈 종목 추출
            url = "https://finance.naver.com/"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                trending_news = []
                
                # 주요 뉴스 추출
                news_items = soup.select('.news_area .newsList li')
                
                for item in news_items[:10]:
                    title_elem = item.select_one('a')
                    if title_elem:
                        title = title_elem.text.strip()
                        link = title_elem.get('href', '')
                        
                        # 종목명 추출 (간단한 패턴 매칭)
                        stock_pattern = r'([가-힣]+(?:전자|화학|바이오|제약|금융|건설|통신|에너지|자동차|반도체))'
                        matches = re.findall(stock_pattern, title)
                        
                        trending_news.append({
                            'title': title,
                            'link': link,
                            'extracted_stocks': matches,
                            'timestamp': datetime.now()
                        })
                
                return trending_news
            
        except Exception as e:
            print(f"이슈 종목 뉴스 수집 실패: {e}")
        
        return []
    
    def analyze_market_sentiment(self) -> Dict[str, Any]:
        """전체 시장 감정 분석"""
        try:
            # 주요 경제 뉴스 수집 및 분석
            economic_news = self._collect_economic_news()
            
            # 감정 점수 계산
            sentiment_scores = []
            for news in economic_news:
                score = self._calculate_sentiment_score(news)
                sentiment_scores.append(score)
            
            if sentiment_scores:
                market_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            else:
                market_sentiment = 0.0
            
            # 시장 분위기 분류
            if market_sentiment > 0.3:
                mood = 'bullish'
            elif market_sentiment < -0.3:
                mood = 'bearish'
            else:
                mood = 'neutral'
            
            return {
                'sentiment_score': market_sentiment,
                'market_mood': mood,
                'news_count': len(economic_news),
                'analysis_time': datetime.now()
            }
            
        except Exception as e:
            print(f"시장 감정 분석 실패: {e}")
            return {
                'sentiment_score': 0.0,
                'market_mood': 'neutral',
                'news_count': 0,
                'analysis_time': datetime.now()
            }
    
    def _collect_economic_news(self) -> List[Dict[str, Any]]:
        """경제 뉴스 수집"""
        news = []
        
        try:
            # 네이버 경제 뉴스
            url = "https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=258"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                news_items = soup.select('.newsflash_body .type06_headline li')
                
                for item in news_items[:20]:  # 최대 20개
                    title_elem = item.select_one('a')
                    if title_elem:
                        title = title_elem.text.strip()
                        
                        news.append({
                            'title': title,
                            'content': title,
                            'source': 'naver_economy',
                            'timestamp': datetime.now()
                        })
            
        except Exception as e:
            print(f"경제 뉴스 수집 실패: {e}")
        
        return news