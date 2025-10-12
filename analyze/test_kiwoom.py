"""
키움증권 API 테스트 코드
"""

import logging
import json
from lib.kiwoom import KiwoomAPI

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_kiwoom_api():
    """키움증권 API 테스트"""

    # API 설정 (kiwoom_dev_info.txt 파일 기준)
    APP_KEY = 'KY7QbSwIVVmjqBM5jIZHbcGOle2O8nQL7dFUNtVmTKU'
    SECRET_KEY = 'KUwnffZOR2dP4nwEZCIgTAhu-FquHEa2Xx9mCKE9ak0'
    ACCOUNT_NO = '52958566'

    # API 인스턴스 생성 (실전투자)
    api = KiwoomAPI(
        app_key=APP_KEY,
        secret_key=SECRET_KEY,
        account_no=ACCOUNT_NO,
        use_mock=False
    )

    print("=" * 60)
    print("키움증권 API 테스트")
    print("=" * 60)

    # 1. 접근 토큰 발급 테스트
    print("\n[1] 접근 토큰 발급 테스트")
    print("-" * 60)
    token = api.get_access_token()
    if token:
        print(f"✓ 토큰 발급 성공")
        print(f"  토큰 (앞 20자): {token[:20]}...")
        print(f"  토큰 (뒤 20자): ...{token[-20:]}")
        print(f"  만료 시간: {api.token_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("✗ 토큰 발급 실패")
        return

    # 2. 최근 30일 매매내역 조회 테스트
    print("\n[2] 최근 30일 매매내역 조회 테스트")
    print("-" * 60)
    trades = api.get_recent_trades(days=30)

    if trades:
        print(f"✓ 조회 성공 (총 {len(trades)}건)\n")

        # 매매내역 출력
        if len(trades) > 0:
            print("매매내역 상세:")
            print("-" * 60)
            for i, trade in enumerate(trades[:20], 1):  # 최근 20건만 출력
                # 날짜시간 포맷팅
                dt_str = trade['datetime']
                if len(dt_str) >= 14:
                    formatted_dt = f"{dt_str[:4]}-{dt_str[4:6]}-{dt_str[6:8]} {dt_str[8:10]}:{dt_str[10:12]}:{dt_str[12:14]}"
                else:
                    formatted_dt = dt_str

                print(f"{i:2d}. [{formatted_dt}] {trade['stock_name']:10s} ({trade['stock_code']}) "
                      f"{trade['trade_type']:3s} {trade['quantity']:5d}주 @ {trade['price']:>10,.0f}원")

            if len(trades) > 20:
                print(f"\n... 외 {len(trades) - 20}건")

            # 통계 정보
            print("\n" + "-" * 60)
            print("매매 통계:")
            buy_count = sum(1 for t in trades if t['trade_type'] == '매수')
            sell_count = sum(1 for t in trades if t['trade_type'] == '매도')
            buy_amount = sum(t['price'] * t['quantity'] for t in trades if t['trade_type'] == '매수')
            sell_amount = sum(t['price'] * t['quantity'] for t in trades if t['trade_type'] == '매도')

            print(f"  매수 건수: {buy_count}건")
            print(f"  매도 건수: {sell_count}건")
            print(f"  매수 금액: {buy_amount:,.0f}원")
            print(f"  매도 금액: {sell_amount:,.0f}원")
            print(f"  순매매 금액: {sell_amount - buy_amount:,.0f}원")

            # 종목별 통계
            stock_trades = {}
            for trade in trades:
                stock_key = f"{trade['stock_name']}({trade['stock_code']})"
                if stock_key not in stock_trades:
                    stock_trades[stock_key] = {'count': 0, 'buy': 0, 'sell': 0}
                stock_trades[stock_key]['count'] += 1
                if trade['trade_type'] == '매수':
                    stock_trades[stock_key]['buy'] += 1
                else:
                    stock_trades[stock_key]['sell'] += 1

            print("\n종목별 매매 현황:")
            for stock, stats in sorted(stock_trades.items(), key=lambda x: x[1]['count'], reverse=True):
                print(f"  {stock}: 총 {stats['count']}건 (매수 {stats['buy']}, 매도 {stats['sell']})")
        else:
            print("조회된 매매내역이 없습니다.")
    else:
        print("매매내역 조회 결과가 없습니다.")

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)


if __name__ == '__main__':
    test_kiwoom_api()
