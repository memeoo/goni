"""
키움 API TR ID: ka10172, ka10173 호출 테스트
- ka10172: 조건검색 일반 조회 (search_type='0')
- ka10173: 조건검색 실시간 조회 (search_type='1')
"""

import sys
import json
import logging
import asyncio
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent / 'analyze' / 'lib'))

from kiwoom import KiwoomAPI, KiwoomWebSocketClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API 설정
APP_KEY = 'KY7QbSwIVVmjqBM5jIZHbcGOle2O8nQL7dFUNtVmTKU'
SECRET_KEY = 'KUwnffZOR2dP4nwEZCIgTAhu-FquHEa2Xx9mCKE9ak0'
ACCOUNT_NO = '52958566'


def print_section(title: str):
    """섹션 구분선 출력"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


async def test_ka10172_general_search():
    """
    ka10172: 조건검색 일반 조회 테스트
    - search_type='0'
    - stex_tp (거래소구분) 지원: 'K'(코스피), 'Q'(코스닥), '%'(전체)
    - 연속조회 지원: cont_yn, next_key
    """
    print_section("ka10172: 조건검색 일반 조회 테스트")

    api = KiwoomAPI(
        app_key=APP_KEY,
        secret_key=SECRET_KEY,
        account_no=ACCOUNT_NO,
        use_mock=False
    )

    try:
        # 1단계: 토큰 발급
        print("\n[Step 1] 접근 토큰 발급...")
        token = api.get_access_token()
        if not token:
            print("✗ 토큰 발급 실패")
            return False
        print(f"✓ 토큰 발급 성공: {token[:20]}...{token[-20:]}")

        # 2단계: 조건 검색 목록 조회
        print("\n[Step 2] 조건 검색 목록 조회...")
        conditions = api.get_condition_list(use_mock=False)
        if not conditions:
            print("✗ 조건 검색 목록 조회 실패")
            return False

        print(f"✓ 조건 검색 목록 조회 성공: 총 {len(conditions)}개")
        for i, cond in enumerate(conditions[:5], 1):  # 최대 5개 표시
            print(f"   {i}. ID: {cond['id']}, 조건명: {cond['name']}")
        if len(conditions) > 5:
            print(f"   ... 외 {len(conditions) - 5}개")

        # 3단계: 첫 번째 조건으로 일반 조회 테스트
        if conditions:
            condition_id = conditions[0]['id']
            condition_name = conditions[0]['name']

            print(f"\n[Step 3] ka10172 일반 조회 테스트")
            print(f"   조건식: {condition_name} (ID: {condition_id})")
            print(f"   거래소: 코스피 (K)")
            print(f"   search_type: '0' (일반 조회)")

            results = api.search_condition(
                condition_id=condition_id,
                search_type='0',      # ka10172 일반 조회
                stock_exchange_type='K'  # 코스피
            )

            if results is not None:
                print(f"✓ 일반 조회 성공: {len(results)}개 종목")
                for i, stock in enumerate(results[:10], 1):  # 최대 10개 표시
                    print(f"   {i}. {stock['stock_name']}({stock['stock_code']}) - "
                          f"현재가: {stock['current_price']:,.0f}원, "
                          f"상태: {stock['status']}")
                if len(results) > 10:
                    print(f"   ... 외 {len(results) - 10}개")
                return True
            else:
                print("✗ 일반 조회 실패")
                return False
        else:
            print("✗ 사용 가능한 조건식이 없습니다")
            return False

    except Exception as e:
        logger.error(f"ka10172 테스트 실패: {e}", exc_info=True)
        print(f"✗ 테스트 실패: {e}")
        return False


async def test_ka10173_realtime_search():
    """
    ka10173: 조건검색 실시간 조회 테스트
    - search_type='1'
    - stex_tp 미지원 (거래소구분 없음)
    - 실시간 데이터 수신
    """
    print_section("ka10173: 조건검색 실시간 조회 테스트")

    api = KiwoomAPI(
        app_key=APP_KEY,
        secret_key=SECRET_KEY,
        account_no=ACCOUNT_NO,
        use_mock=False
    )

    try:
        # 1단계: 토큰 발급
        print("\n[Step 1] 접근 토큰 발급...")
        token = api.get_access_token()
        if not token:
            print("✗ 토큰 발급 실패")
            return False
        print(f"✓ 토큰 발급 성공: {token[:20]}...{token[-20:]}")

        # 2단계: 조건 검색 목록 조회
        print("\n[Step 2] 조건 검색 목록 조회...")
        conditions = api.get_condition_list(use_mock=False)
        if not conditions:
            print("✗ 조건 검색 목록 조회 실패")
            return False

        print(f"✓ 조건 검색 목록 조회 성공: 총 {len(conditions)}개")
        for i, cond in enumerate(conditions[:5], 1):
            print(f"   {i}. ID: {cond['id']}, 조건명: {cond['name']}")
        if len(conditions) > 5:
            print(f"   ... 외 {len(conditions) - 5}개")

        # 3단계: 첫 번째 조건으로 실시간 조회 테스트
        if conditions:
            condition_id = conditions[0]['id']
            condition_name = conditions[0]['name']

            print(f"\n[Step 3] ka10173 실시간 조회 테스트")
            print(f"   조건식: {condition_name} (ID: {condition_id})")
            print(f"   search_type: '1' (실시간 조회)")
            print(f"   주의: 거래소구분(stex_tp)은 사용되지 않음")

            results = api.search_condition(
                condition_id=condition_id,
                search_type='1',      # ka10173 실시간 조회
                stock_exchange_type='%'  # 실시간에서는 무시됨
            )

            if results is not None:
                print(f"✓ 실시간 조회 성공: {len(results)}개 종목")
                for i, stock in enumerate(results[:10], 1):  # 최대 10개 표시
                    print(f"   {i}. {stock['stock_name']}({stock['stock_code']}) - "
                          f"현재가: {stock['current_price']:,.0f}원, "
                          f"상태: {stock['status']}")
                if len(results) > 10:
                    print(f"   ... 외 {len(results) - 10}개")
                return True
            else:
                print("✗ 실시간 조회 실패")
                return False
        else:
            print("✗ 사용 가능한 조건식이 없습니다")
            return False

    except Exception as e:
        logger.error(f"ka10173 테스트 실패: {e}", exc_info=True)
        print(f"✗ 테스트 실패: {e}")
        return False


async def test_websocket_raw():
    """
    WebSocket 직접 호출 테스트 (raw 레벨)
    """
    print_section("WebSocket 직접 호출 테스트 (Raw Level)")

    api = KiwoomAPI(
        app_key=APP_KEY,
        secret_key=SECRET_KEY,
        account_no=ACCOUNT_NO,
        use_mock=False
    )

    try:
        # 1단계: 토큰 발급
        print("\n[Step 1] 접근 토큰 발급...")
        token = api.get_access_token()
        if not token:
            print("✗ 토큰 발급 실패")
            return False
        print(f"✓ 토큰 발급 성공")

        # 2단계: WebSocket 클라이언트로 조건식 목록 조회
        print("\n[Step 2] WebSocket으로 조건식 목록 조회...")
        ws_client = KiwoomWebSocketClient(access_token=token, use_mock=False)
        condition_list = await ws_client.request_condition_list()

        if condition_list:
            print(f"✓ 조건식 목록 조회 성공: {len(condition_list)}개")
            for i, cond in enumerate(condition_list[:5], 1):
                print(f"   {i}. {cond}")

            # 3단계: 첫 번째 조건식으로 검색 테스트
            if condition_list:
                condition_id = condition_list[0][0]
                condition_name = condition_list[0][1]

                # ka10172 일반 조회
                print(f"\n[Step 3-1] ka10172 일반 조회 (search_type='0')")
                print(f"   조건식: {condition_name} (ID: {condition_id})")

                ws_client = KiwoomWebSocketClient(access_token=token, use_mock=False)
                response = await ws_client.request_condition_search(
                    condition_id=condition_id,
                    search_type='0',  # ka10172
                    stock_exchange_type='K'
                )

                if response:
                    data = response.get('data', [])
                    print(f"✓ ka10172 응답 수신: {len(data)}개 종목")
                    if data:
                        first_stock = data[0]
                        print(f"   첫 종목 데이터: {json.dumps(first_stock, indent=4, ensure_ascii=False)}")
                else:
                    print("✗ ka10172 응답 실패")

                # ka10173 실시간 조회
                print(f"\n[Step 3-2] ka10173 실시간 조회 (search_type='1')")
                print(f"   조건식: {condition_name} (ID: {condition_id})")

                ws_client = KiwoomWebSocketClient(access_token=token, use_mock=False)
                response = await ws_client.request_condition_search(
                    condition_id=condition_id,
                    search_type='1',  # ka10173
                    stock_exchange_type='%'
                )

                if response:
                    data = response.get('data', [])
                    print(f"✓ ka10173 응답 수신: {len(data)}개 종목")
                    if data:
                        first_stock = data[0]
                        print(f"   첫 종목 데이터: {json.dumps(first_stock, indent=4, ensure_ascii=False)}")
                else:
                    print("✗ ka10173 응답 실패")

                return True
        else:
            print("✗ 조건식 목록 조회 실패")
            return False

    except Exception as e:
        logger.error(f"WebSocket 테스트 실패: {e}", exc_info=True)
        print(f"✗ 테스트 실패: {e}")
        return False


async def main():
    """메인 테스트 함수"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  키움 API TR ID 호출 테스트: ka10172, ka10173".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")

    results = {}

    # ka10172 테스트
    print("\n\n[테스트 1/3] ka10172 일반 조회 테스트 시작...")
    results['ka10172'] = await test_ka10172_general_search()

    # ka10173 테스트
    print("\n\n[테스트 2/3] ka10173 실시간 조회 테스트 시작...")
    results['ka10173'] = await test_ka10173_realtime_search()

    # WebSocket 직접 호출 테스트
    print("\n\n[테스트 3/3] WebSocket 직접 호출 테스트 시작...")
    results['websocket'] = await test_websocket_raw()

    # 최종 결과
    print_section("최종 테스트 결과")
    print("\n테스트 결과 요약:")
    print(f"  ka10172 (일반 조회):  {'✓ 성공' if results['ka10172'] else '✗ 실패'}")
    print(f"  ka10173 (실시간 조회): {'✓ 성공' if results['ka10173'] else '✗ 실패'}")
    print(f"  WebSocket 직접 호출:  {'✓ 성공' if results['websocket'] else '✗ 실패'}")

    total_passed = sum(1 for v in results.values() if v)
    print(f"\n전체 결과: {total_passed}/3 통과")

    if total_passed == 3:
        print("\n🎉 모든 테스트가 성공했습니다!")
    else:
        print("\n⚠️  일부 테스트가 실패했습니다. 로그를 확인하세요.")

    print("\n")


if __name__ == '__main__':
    asyncio.run(main())
