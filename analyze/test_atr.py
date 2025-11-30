#!/usr/bin/env python3
"""
ATR (Average True Range) 계산 및 손절매 설정 테스트

40일봉 기준으로 ATR을 계산하고, 손절매 가격을 설정하는 함수들을 테스트합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.technical_analyzer import TechnicalAnalyzer


def generate_sample_stock_data(days: int = 100) -> pd.DataFrame:
    """
    샘플 주식 데이터 생성 (테스트용)

    Args:
        days: 생성할 데이터 기간 (일)

    Returns:
        pd.DataFrame: OHLC 데이터
    """
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

    # 기본 가격을 10,000원으로 설정
    base_price = 10000

    # 랜덤 걷기로 가격 변동 생성
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, days)  # 일일 수익률
    closes = base_price * np.exp(np.cumsum(returns))

    data = []
    for i, (date, close) in enumerate(zip(dates, closes)):
        # Open: 전일 종가 + 작은 gap
        open_price = closes[i-1] if i > 0 else close
        open_price += np.random.normal(0, close * 0.005)

        # High, Low: close 기준으로 변동
        high = max(open_price, close) + abs(np.random.normal(0, close * 0.01))
        low = min(open_price, close) - abs(np.random.normal(0, close * 0.01))

        # Volume: 평균 100만주
        volume = int(np.random.normal(1000000, 200000))

        data.append({
            'Date': date,
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': volume
        })

    return pd.DataFrame(data)


def test_calculate_atr_40days():
    """40일봉 ATR 계산 테스트"""
    print("\n" + "="*70)
    print("[테스트 1] 40일봉 기준 ATR 계산")
    print("="*70)

    # 샘플 데이터 생성
    df = generate_sample_stock_data(days=100)

    stock_data = {
        'symbol': 'TEST',
        'historical_data': df
    }

    # ATR 계산
    analyzer = TechnicalAnalyzer()
    result = analyzer.calculate_atr_40days(stock_data, period=40, multiplier=2.0)

    if 'error' in result:
        print(f"❌ 오류: {result['error']}")
        return

    print(f"\n✅ ATR 계산 성공\n")
    print(f"현재가: {result['current_price']:,.0f}원")
    print(f"40일 ATR: {result['atr_40d']:,.2f}원")
    print(f"손절매 배수: {result['stop_loss_multiplier']}배")
    print(f"손절매 가격: {result['stop_loss_price']:,.0f}원")
    print(f"손절률: {result['stop_loss_ratio']:.2f}%")

    print(f"\n📊 ATR 통계:")
    stats = result['statistics']
    print(f"  최소값: {stats['atr_min']:,.2f}원")
    print(f"  최대값: {stats['atr_max']:,.2f}원")
    print(f"  평균값: {stats['atr_mean']:,.2f}원")
    print(f"  표준편차: {stats['atr_std']:,.2f}원")


def test_multiple_periods():
    """여러 기간별 ATR 비교 테스트"""
    print("\n" + "="*70)
    print("[테스트 2] 여러 기간별 ATR 비교")
    print("="*70)

    # 샘플 데이터 생성
    df = generate_sample_stock_data(days=100)

    stock_data = {
        'symbol': 'TEST',
        'historical_data': df
    }

    # 여러 기간별 ATR 계산
    analyzer = TechnicalAnalyzer()
    result = analyzer.calculate_atr_multiple_periods(stock_data, periods=[14, 20, 40, 60])

    if 'error' in result:
        print(f"❌ 오류: {result['error']}")
        return

    print(f"\n✅ ATR 계산 성공\n")
    print(f"현재가: {result['current_price']:,.0f}원\n")

    print("📊 기간별 ATR 및 변동성:")
    print("-"*70)
    print(f"{'기간':<10} | {'ATR':<15} | {'변동성':<10}")
    print("-"*70)

    for period in [14, 20, 40, 60]:
        atr = result['atr_by_period'][f'atr_{period}d']
        volatility = result['volatility_ratio'][f'volatility_{period}d']
        print(f"{period}일{'':<6} | {atr:>13,.2f}원 | {volatility:>8.2f}%")


def test_stop_loss_levels():
    """다양한 배수의 손절매 가격 계산 테스트"""
    print("\n" + "="*70)
    print("[테스트 3] 다양한 배수의 손절매 가격 계산")
    print("="*70)

    # 샘플 데이터 생성
    df = generate_sample_stock_data(days=100)

    stock_data = {
        'symbol': 'TEST',
        'historical_data': df
    }

    # 40일 ATR 계산
    analyzer = TechnicalAnalyzer()
    atr_result = analyzer.calculate_atr_40days(stock_data, period=40)

    current_price = atr_result['current_price']
    atr_value = atr_result['atr_40d']

    # 손절매 가격 계산
    multipliers = [1.0, 1.5, 2.0, 2.5, 3.0]
    stop_loss_result = analyzer.calculate_stop_loss_levels(current_price, atr_value, multipliers)

    print(f"\n✅ 손절매 가격 계산 성공\n")
    print(f"진입가: {stop_loss_result['entry_price']:,.0f}원")
    print(f"ATR: {stop_loss_result['atr']:,.2f}원\n")

    print("📊 배수별 손절매 가격:")
    print("-"*70)
    print(f"{'배수':<10} | {'손절가':<15} | {'손절률':<10} | {'리스크':<15}")
    print("-"*70)

    for multiplier in multipliers:
        level = stop_loss_result['stop_loss_levels'][f'multiplier_{multiplier}x']
        print(f"{multiplier:.1f}배{'':<6} | {level['stop_loss_price']:>13,.0f}원 | "
              f"{level['stop_loss_ratio']:>8.2f}% | {level['risk_amount']:>13,.0f}원")


def test_practical_example():
    """실전 예시: 신고가 돌파 후 손절매 설정"""
    print("\n" + "="*70)
    print("[테스트 4] 실전 예시: 신고가 돌파 매수 후 손절매 설정")
    print("="*70)

    # 샘플 데이터 생성 (100일)
    df = generate_sample_stock_data(days=100)

    stock_data = {
        'symbol': 'SAMPLESTOCK',
        'historical_data': df
    }

    analyzer = TechnicalAnalyzer()

    # 1단계: 40일 ATR 계산
    atr_result = analyzer.calculate_atr_40days(stock_data, period=40, multiplier=2.0)

    current_price = atr_result['current_price']
    atr_value = atr_result['atr_40d']

    print(f"\n📈 신고가 돌파 매수 시뮬레이션\n")
    print(f"종목: {stock_data['symbol']}")
    print(f"현재가(매수가): {current_price:,.0f}원")
    print(f"40일 ATR: {atr_value:,.2f}원")

    # 2단계: 다양한 손절매 시나리오
    print(f"\n💼 손절매 시나리오:")
    print("-"*70)

    scenarios = [
        {"name": "보수적 (3배 손절)", "multiplier": 3.0},
        {"name": "중간 (2배 손절)", "multiplier": 2.0},
        {"name": "공격적 (1.5배 손절)", "multiplier": 1.5},
    ]

    for scenario in scenarios:
        stop_loss_price = current_price - (atr_value * scenario['multiplier'])
        stop_loss_ratio = ((current_price - stop_loss_price) / current_price) * 100

        print(f"\n🎯 {scenario['name']}")
        print(f"  손절가: {stop_loss_price:,.0f}원")
        print(f"  손절률: {stop_loss_ratio:.2f}%")
        print(f"  리스크: {atr_value * scenario['multiplier']:,.0f}원")

    # 3단계: 목표가 설정 (수익 목표)
    print(f"\n🎁 수익 목표 설정 (위험대비 수익비 1:2):")
    print("-"*70)

    risk_amount_2x = atr_value * 2.0
    for reward_ratio in [1.5, 2.0, 2.5, 3.0]:
        target_price = current_price + (risk_amount_2x * reward_ratio)
        profit = target_price - current_price
        profit_ratio = (profit / current_price) * 100

        print(f"\n📊 위험대비 수익비 1:{reward_ratio}")
        print(f"  목표가: {target_price:,.0f}원")
        print(f"  예상 수익: {profit:,.0f}원 ({profit_ratio:.2f}%)")


def main():
    """모든 테스트 실행"""
    print("\n" + "="*70)
    print("ATR (Average True Range) 계산 및 손절매 설정 테스트")
    print("="*70)

    try:
        test_calculate_atr_40days()
        test_multiple_periods()
        test_stop_loss_levels()
        test_practical_example()

        print("\n" + "="*70)
        print("✅ 모든 테스트 완료")
        print("="*70)

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
