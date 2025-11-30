"""
기술적 분석 모듈
RSI, MACD, 볼린저 밴드 등 기술적 지표를 활용한 매매 신호 생성
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any

# ta 모듈이 없을 경우 대비
try:
    import ta
except ImportError:
    ta = None


class TechnicalAnalyzer:
    def __init__(self):
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.bollinger_period = 20
        self.bollinger_std = 2
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
    
    def analyze(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """종목의 기술적 분석 수행"""
        df = stock_data['historical_data'].copy()
        
        if len(df) < 50:  # 최소 데이터 요구사항
            return {'error': '분석을 위한 충분한 데이터가 없습니다'}
        
        # 기술적 지표 계산
        indicators = self._calculate_indicators(df)
        
        # 매매 신호 생성
        signals = self._generate_signals(indicators)
        
        # 지지/저항선 계산
        support_resistance = self._calculate_support_resistance(df)
        
        # 추세 분석
        trend_analysis = self._analyze_trend(df, indicators)
        
        return {
            'symbol': stock_data['symbol'],
            'indicators': indicators,
            'signals': signals,
            'support_resistance': support_resistance,
            'trend_analysis': trend_analysis,
            'analysis_timestamp': pd.Timestamp.now()
        }
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """기술적 지표 계산"""
        indicators = {}
        
        # RSI (Relative Strength Index)
        indicators['rsi'] = ta.momentum.RSIIndicator(
            close=df['Close'], window=14
        ).rsi().iloc[-1]
        
        # MACD (Moving Average Convergence Divergence)
        macd_indicator = ta.trend.MACD(
            close=df['Close'],
            window_fast=self.macd_fast,
            window_slow=self.macd_slow,
            window_sign=self.macd_signal
        )
        indicators['macd'] = macd_indicator.macd().iloc[-1]
        indicators['macd_signal'] = macd_indicator.macd_signal().iloc[-1]
        indicators['macd_histogram'] = macd_indicator.macd_diff().iloc[-1]
        
        # 볼린저 밴드
        bollinger = ta.volatility.BollingerBands(
            close=df['Close'],
            window=self.bollinger_period,
            window_dev=self.bollinger_std
        )
        indicators['bollinger_upper'] = bollinger.bollinger_hband().iloc[-1]
        indicators['bollinger_lower'] = bollinger.bollinger_lband().iloc[-1]
        indicators['bollinger_middle'] = bollinger.bollinger_mavg().iloc[-1]
        
        # 이동평균선
        indicators['sma_5'] = ta.trend.SMAIndicator(close=df['Close'], window=5).sma_indicator().iloc[-1]
        indicators['sma_20'] = ta.trend.SMAIndicator(close=df['Close'], window=20).sma_indicator().iloc[-1]
        indicators['sma_60'] = ta.trend.SMAIndicator(close=df['Close'], window=60).sma_indicator().iloc[-1]
        indicators['ema_12'] = ta.trend.EMAIndicator(close=df['Close'], window=12).ema_indicator().iloc[-1]
        indicators['ema_26'] = ta.trend.EMAIndicator(close=df['Close'], window=26).ema_indicator().iloc[-1]
        
        # 스토캐스틱
        stoch = ta.momentum.StochasticOscillator(
            high=df['High'], low=df['Low'], close=df['Close']
        )
        indicators['stoch_k'] = stoch.stoch().iloc[-1]
        indicators['stoch_d'] = stoch.stoch_signal().iloc[-1]
        
        # 거래량 지표
        indicators['volume_sma'] = ta.volume.VolumeSMAIndicator(
            close=df['Close'], volume=df['Volume'], window=20
        ).volume_sma().iloc[-1]
        
        # ATR (Average True Range) - 변동성 지표
        indicators['atr'] = ta.volatility.AverageTrueRange(
            high=df['High'], low=df['Low'], close=df['Close'], window=14
        ).average_true_range().iloc[-1]
        
        # 현재가
        indicators['current_price'] = df['Close'].iloc[-1]
        
        return indicators
    
    def _generate_signals(self, indicators: Dict[str, Any]) -> Dict[str, str]:
        """매매 신호 생성"""
        signals = {}
        
        # RSI 신호
        if indicators['rsi'] < self.rsi_oversold:
            signals['rsi_signal'] = 'buy'
        elif indicators['rsi'] > self.rsi_overbought:
            signals['rsi_signal'] = 'sell'
        else:
            signals['rsi_signal'] = 'hold'
        
        # MACD 신호
        if indicators['macd'] > indicators['macd_signal'] and indicators['macd_histogram'] > 0:
            signals['macd_signal'] = 'buy'
        elif indicators['macd'] < indicators['macd_signal'] and indicators['macd_histogram'] < 0:
            signals['macd_signal'] = 'sell'
        else:
            signals['macd_signal'] = 'hold'
        
        # 볼린저 밴드 신호
        current_price = indicators['current_price']
        if current_price <= indicators['bollinger_lower']:
            signals['bollinger_signal'] = 'buy'
        elif current_price >= indicators['bollinger_upper']:
            signals['bollinger_signal'] = 'sell'
        else:
            signals['bollinger_signal'] = 'hold'
        
        # 이동평균선 신호
        if (indicators['sma_5'] > indicators['sma_20'] > indicators['sma_60'] and
            indicators['ema_12'] > indicators['ema_26']):
            signals['moving_average_signal'] = 'buy'
        elif (indicators['sma_5'] < indicators['sma_20'] < indicators['sma_60'] and
              indicators['ema_12'] < indicators['ema_26']):
            signals['moving_average_signal'] = 'sell'
        else:
            signals['moving_average_signal'] = 'hold'
        
        # 스토캐스틱 신호
        if indicators['stoch_k'] < 20 and indicators['stoch_d'] < 20:
            signals['stochastic_signal'] = 'buy'
        elif indicators['stoch_k'] > 80 and indicators['stoch_d'] > 80:
            signals['stochastic_signal'] = 'sell'
        else:
            signals['stochastic_signal'] = 'hold'
        
        return signals
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict[str, List[float]]:
        """지지선과 저항선 계산"""
        # 최근 60일 데이터 사용
        recent_data = df.tail(60)
        
        # 고점과 저점 찾기
        highs = recent_data['High'].values
        lows = recent_data['Low'].values
        
        # 지지선 (최근 저점들의 평균)
        support_levels = []
        for i in range(2, len(lows)-2):
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and
                lows[i] < lows[i+1] and lows[i] < lows[i+2]):
                support_levels.append(lows[i])
        
        # 저항선 (최근 고점들의 평균)
        resistance_levels = []
        for i in range(2, len(highs)-2):
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and
                highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                resistance_levels.append(highs[i])
        
        return {
            'support_levels': sorted(support_levels)[-3:] if support_levels else [],
            'resistance_levels': sorted(resistance_levels, reverse=True)[:3] if resistance_levels else []
        }
    
    def _analyze_trend(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """추세 분석"""
        # 최근 20일 가격 변화
        recent_data = df.tail(20)
        price_change = (recent_data['Close'].iloc[-1] - recent_data['Close'].iloc[0]) / recent_data['Close'].iloc[0] * 100
        
        # 추세 방향
        if price_change > 5:
            trend_direction = 'strong_uptrend'
        elif price_change > 1:
            trend_direction = 'uptrend'
        elif price_change < -5:
            trend_direction = 'strong_downtrend'
        elif price_change < -1:
            trend_direction = 'downtrend'
        else:
            trend_direction = 'sideways'
        
        # 추세 강도 (이동평균선 정렬 정도)
        ma_alignment = 0
        if indicators['sma_5'] > indicators['sma_20']:
            ma_alignment += 1
        if indicators['sma_20'] > indicators['sma_60']:
            ma_alignment += 1
        if indicators['ema_12'] > indicators['ema_26']:
            ma_alignment += 1
        
        trend_strength = ma_alignment / 3  # 0~1 사이 값
        
        # 변동성 분석
        volatility = indicators['atr'] / indicators['current_price'] * 100
        
        return {
            'direction': trend_direction,
            'strength': trend_strength,
            'price_change_20d': price_change,
            'volatility': volatility
        }
    
    def detect_price_alerts(self, realtime_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """실시간 가격 알림 감지"""
        alerts = []
        
        for data in realtime_data:
            if not data:
                continue
                
            # 급등/급락 감지 (임시 로직 - 실제로는 더 정교한 로직 필요)
            # 여기서는 단순히 예시로 구현
            symbol = data['symbol']
            price = data['price']
            
            # 실제 구현시에는 이전 가격과 비교하여 급등/급락 판단
            # 예: 5분 내 5% 이상 변동시 알림
            
            alert = {
                'symbol': symbol,
                'alert_type': 'price_change',
                'message': f'{symbol} 가격 변동 감지: {price:,.0f}원',
                'timestamp': data['timestamp'],
                'price': price
            }
            
            alerts.append(alert)
        
        return alerts
    
    def calculate_target_price(self, stock_data: Dict[str, Any]) -> Dict[str, float]:
        """목표가 계산"""
        df = stock_data['historical_data'].copy()
        current_price = df['Close'].iloc[-1]

        # 볼린저 밴드 기반 목표가
        bollinger = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
        upper_band = bollinger.bollinger_hband().iloc[-1]
        lower_band = bollinger.bollinger_lband().iloc[-1]

        # ATR 기반 목표가
        atr = ta.volatility.AverageTrueRange(
            high=df['High'], low=df['Low'], close=df['Close'], window=14
        ).average_true_range().iloc[-1]

        return {
            'buy_target': lower_band,
            'sell_target': upper_band,
            'stop_loss_long': current_price - (atr * 2),
            'stop_loss_short': current_price + (atr * 2),
            'risk_reward_ratio': (upper_band - current_price) / (current_price - lower_band) if current_price > lower_band else 0
        }

    def calculate_atr_40days(self, stock_data: Dict[str, Any], period: int = 40, multiplier: float = 2.0) -> Dict[str, Any]:
        """
        40일봉 기준 ATR 계산 및 손절매 가격 설정

        Args:
            stock_data: 종목 데이터 (historical_data 포함)
            period: ATR 계산 기간 (기본값: 40일)
            multiplier: 손절매 배수 (기본값: 2.0)

        Returns:
            dict: ATR 관련 지표
                {
                    'atr_40d': ATR 값,
                    'current_price': 현재가,
                    'entry_price': 매입가,
                    'stop_loss_price': 손절매 가격 (매입가 - ATR * 배수),
                    'stop_loss_ratio': 손절률 (%),
                    'true_ranges': TR 값들,
                    'atr_history': ATR 추이
                }
        """
        df = stock_data['historical_data'].copy()

        if len(df) < period:
            return {
                'error': f'{period}일 이상의 데이터가 필요합니다. 현재: {len(df)}일'
            }

        # True Range 계산
        df['TR'] = self._calculate_true_range(df)

        # ATR 계산 (period일 기준 이동평균)
        df['ATR'] = df['TR'].rolling(window=period).mean()

        # 현재가 (마지막 종가)
        current_price = df['Close'].iloc[-1]
        current_atr = df['ATR'].iloc[-1]

        # 손절매 계산
        entry_price = current_price  # 현재가를 진입가로 가정
        stop_loss_price = entry_price - (current_atr * multiplier)
        stop_loss_ratio = ((entry_price - stop_loss_price) / entry_price) * 100

        # ATR 추이 (최근 10일)
        atr_history = df['ATR'].tail(10).to_dict()
        tr_history = df['TR'].tail(10).to_dict()

        return {
            'atr_40d': current_atr,
            'current_price': current_price,
            'entry_price': entry_price,
            'stop_loss_price': stop_loss_price,
            'stop_loss_ratio': stop_loss_ratio,
            'stop_loss_multiplier': multiplier,
            'true_ranges_last_10': tr_history,
            'atr_history_last_10': atr_history,
            'statistics': {
                'atr_min': df['ATR'].min(),
                'atr_max': df['ATR'].max(),
                'atr_mean': df['ATR'].mean(),
                'atr_std': df['ATR'].std()
            }
        }

    def _calculate_true_range(self, df: pd.DataFrame) -> pd.Series:
        """
        True Range (실제 변동폭) 계산

        TR = max(
            |High - Low|,
            |High - Close_prev|,
            |Low - Close_prev|
        )
        """
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr

    def calculate_atr_multiple_periods(self, stock_data: Dict[str, Any], periods: List[int] = None) -> Dict[str, Any]:
        """
        여러 기간별 ATR 비교 계산

        Args:
            stock_data: 종목 데이터
            periods: ATR 계산 기간 리스트 (기본값: [14, 20, 40, 60])

        Returns:
            dict: 기간별 ATR 값
        """
        if periods is None:
            periods = [14, 20, 40, 60]

        df = stock_data['historical_data'].copy()

        if len(df) < max(periods):
            return {
                'error': f'{max(periods)}일 이상의 데이터가 필요합니다. 현재: {len(df)}일'
            }

        # True Range 계산 (한 번만)
        df['TR'] = self._calculate_true_range(df)

        current_price = df['Close'].iloc[-1]
        result = {
            'current_price': current_price,
            'atr_by_period': {},
            'volatility_ratio': {}
        }

        # 각 기간별 ATR 계산
        for period in periods:
            atr_value = df['TR'].rolling(window=period).mean().iloc[-1]
            volatility = (atr_value / current_price) * 100  # 변동성 비율 (%)

            result['atr_by_period'][f'atr_{period}d'] = atr_value
            result['volatility_ratio'][f'volatility_{period}d'] = volatility

        return result

    def calculate_stop_loss_levels(self,
                                  entry_price: float,
                                  atr_value: float,
                                  multipliers: List[float] = None) -> Dict[str, float]:
        """
        다양한 배수의 손절매 가격 계산

        Args:
            entry_price: 진입가
            atr_value: ATR 값
            multipliers: 손절매 배수 리스트 (기본값: [1.0, 1.5, 2.0, 2.5, 3.0])

        Returns:
            dict: 배수별 손절매 가격 및 손절률
        """
        if multipliers is None:
            multipliers = [1.0, 1.5, 2.0, 2.5, 3.0]

        result = {
            'entry_price': entry_price,
            'atr': atr_value,
            'stop_loss_levels': {}
        }

        for multiplier in multipliers:
            stop_loss_price = entry_price - (atr_value * multiplier)
            stop_loss_ratio = ((entry_price - stop_loss_price) / entry_price) * 100

            result['stop_loss_levels'][f'multiplier_{multiplier}x'] = {
                'stop_loss_price': stop_loss_price,
                'stop_loss_ratio': stop_loss_ratio,
                'risk_amount': atr_value * multiplier
            }

        return result