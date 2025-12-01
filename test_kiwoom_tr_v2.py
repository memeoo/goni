"""
키움 API TR ID: ka10172, ka10173 호출 테스트 (개선 버전 v2)
- WebSocket 메시지 핸들러 상태 추적
- 응답 수신 타임아웃 발생 원인 분석
- Raw 레벨에서의 동작 확인
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
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API 설정
APP_KEY = 'KY7QbSwIVVmjqBM5jIZHbcGOle2O8nQL7dFUNtVmTKU'
SECRET_KEY = 'KUwnffZOR2dP4nwEZCIgTAhu-FquHEa2Xx9mCKE9ak0'
ACCOUNT_NO = '52958566'


def print_section(title: str):
    """섹션 구분선 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def test_condition_list():
    """조건식 목록 조회 테스트"""
    print_section("Step 1: 조건식 목록 조회 (CNSRLST)")

    api = KiwoomAPI(
        app_key=APP_KEY,
        secret_key=SECRET_KEY,
        account_no=ACCOUNT_NO,
        use_mock=False
    )

    try:
        # 토큰 발급
        print("\n[1-1] 토큰 발급...")
        token = api.get_access_token()
        if not token:
            print("✗ 토큰 발급 실패")
            return None

        print(f"✓ 토큰 발급 성공")

        # WebSocket으로 조건식 목록 조회
        print("\n[1-2] WebSocket으로 조건식 목록 조회...")
        ws_client = KiwoomWebSocketClient(access_token=token, use_mock=False)
        condition_list = await ws_client.request_condition_list()

        if condition_list:
            print(f"✓ 조건식 목록 조회 성공: {len(condition_list)}개")
            for i, cond in enumerate(condition_list[:10], 1):
                print(f"   {i}. ID={cond[0]}, 이름={cond[1]}")
            return condition_list
        else:
            print("✗ 조건식 목록 조회 실패")
            return None

    except Exception as e:
        logger.error(f"조건식 목록 조회 실패: {e}", exc_info=True)
        print(f"✗ 조건식 목록 조회 실패: {e}")
        return None


async def test_ka10172_detailed(condition_id: str, token: str):
    """
    ka10172 상세 테스트
    - 요청 파라미터 확인
    - 응답 수신 상태 모니터링
    - 타임아웃 원인 분석
    """
    print_section(f"Step 2-1: ka10172 일반 조회 (search_type='0')")
    print(f"  조건식 ID: {condition_id}")
    print(f"  거래소: 코스피 (K)")
    print(f"  요청 타입: 일반 조회 (cont_yn='N')")

    try:
        ws_client = KiwoomWebSocketClient(access_token=token, use_mock=False)

        print("\n[2-1-1] WebSocket 연결 및 로그인...")
        await ws_client.connect()
        print("✓ 연결 성공")

        # 로그인 응답 대기
        await asyncio.sleep(1)

        print("\n[2-1-2] 요청 파라미터 구성...")
        request_param = {
            'trnm': 'CNSRREQ',
            'seq': condition_id,
            'search_type': '0',  # ka10172 일반 조회
            'stex_tp': 'K',      # 코스피
            'cont_yn': 'N',      # 연속조회 아님
            'next_key': ''       # 연속조회 키 없음
        }
        print(f"✓ 요청 파라미터: {json.dumps(request_param, indent=2, ensure_ascii=False)}")

        print("\n[2-1-3] 메시지 수신 태스크 시작...")
        receive_task = asyncio.create_task(ws_client.receive_messages())

        print("\n[2-1-4] 요청 전송...")
        await ws_client.send_message(request_param)
        print("✓ 요청 전송 완료")

        print("\n[2-1-5] 응답 대기 (최대 30초)...")
        max_wait = 300  # 30초 = 300 * 0.1초
        received = False

        for i in range(max_wait):
            # 응답 큐에서 조건식별 응답 확인
            if condition_id in ws_client.response_queue:
                response = ws_client.response_queue[condition_id]
                del ws_client.response_queue[condition_id]

                print(f"\n✓ 응답 수신 (대기 시간: {i * 0.1:.1f}초)")
                print(f"  응답 코드: {response.get('return_code')}")
                print(f"  응답 메시지: {response.get('return_msg')}")

                data = response.get('data', [])
                print(f"  종목 수: {len(data)}")

                if len(data) > 0:
                    print(f"\n  샘플 데이터 (첫 번째 종목):")
                    first_stock = data[0]
                    print(f"    {json.dumps(first_stock, indent=6, ensure_ascii=False)}")

                received = True
                await ws_client.disconnect()
                return response

            await asyncio.sleep(0.1)

        if not received:
            print(f"\n✗ 응답 수신 타임아웃 (30초 이상 대기)")
            print(f"\n[디버깅 정보]")
            print(f"  response_queue 상태: {list(ws_client.response_queue.keys())}")
            print(f"  response_data 상태: {ws_client.response_data}")

        await ws_client.disconnect()
        return None

    except Exception as e:
        logger.error(f"ka10172 테스트 실패: {e}", exc_info=True)
        print(f"\n✗ 테스트 실패: {e}")
        return None


async def test_ka10173_detailed(condition_id: str, token: str):
    """
    ka10173 상세 테스트
    - 요청 파라미터 확인 (stex_tp 미지원)
    - 응답 수신 상태 모니터링
    """
    print_section(f"Step 2-2: ka10173 실시간 조회 (search_type='1')")
    print(f"  조건식 ID: {condition_id}")
    print(f"  주의: 거래소 구분(stex_tp) 미지원")

    try:
        ws_client = KiwoomWebSocketClient(access_token=token, use_mock=False)

        print("\n[2-2-1] WebSocket 연결 및 로그인...")
        await ws_client.connect()
        print("✓ 연결 성공")

        # 로그인 응답 대기
        await asyncio.sleep(1)

        print("\n[2-2-2] 요청 파라미터 구성...")
        request_param = {
            'trnm': 'CNSRREQ',
            'seq': condition_id,
            'search_type': '1',  # ka10173 실시간 조회 (stex_tp 없음)
        }
        print(f"✓ 요청 파라미터: {json.dumps(request_param, indent=2, ensure_ascii=False)}")

        print("\n[2-2-3] 메시지 수신 태스크 시작...")
        receive_task = asyncio.create_task(ws_client.receive_messages())

        print("\n[2-2-4] 요청 전송...")
        await ws_client.send_message(request_param)
        print("✓ 요청 전송 완료")

        print("\n[2-2-5] 응답 대기 (최대 30초)...")
        max_wait = 300  # 30초 = 300 * 0.1초
        received = False

        for i in range(max_wait):
            # 응답 큐에서 조건식별 응답 확인
            if condition_id in ws_client.response_queue:
                response = ws_client.response_queue[condition_id]
                del ws_client.response_queue[condition_id]

                print(f"\n✓ 응답 수신 (대기 시간: {i * 0.1:.1f}초)")
                print(f"  응답 코드: {response.get('return_code')}")
                print(f"  응답 메시지: {response.get('return_msg')}")

                data = response.get('data', [])
                print(f"  종목 수: {len(data)}")

                if len(data) > 0:
                    print(f"\n  샘플 데이터 (첫 번째 종목):")
                    first_stock = data[0]
                    print(f"    {json.dumps(first_stock, indent=6, ensure_ascii=False)}")

                received = True
                await ws_client.disconnect()
                return response

            await asyncio.sleep(0.1)

        if not received:
            print(f"\n✗ 응답 수신 타임아웃 (30초 이상 대기)")
            print(f"\n[디버깅 정보]")
            print(f"  response_queue 상태: {list(ws_client.response_queue.keys())}")
            print(f"  response_data 상태: {ws_client.response_data}")

        await ws_client.disconnect()
        return None

    except Exception as e:
        logger.error(f"ka10173 테스트 실패: {e}", exc_info=True)
        print(f"\n✗ 테스트 실패: {e}")
        return None


async def main():
    """메인 테스트 함수"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  키움 API 조건검색 TR ID 테스트: ka10172, ka10173 (v2)".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")

    # 접근 토큰 발급
    api = KiwoomAPI(
        app_key=APP_KEY,
        secret_key=SECRET_KEY,
        account_no=ACCOUNT_NO,
        use_mock=False
    )

    print("\n[초기화] 접근 토큰 발급...")
    token = api.get_access_token()
    if not token:
        print("✗ 토큰 발급 실패")
        return
    print(f"✓ 토큰 발급 성공")

    # Step 1: 조건식 목록 조회
    condition_list = await test_condition_list()
    if not condition_list or len(condition_list) == 0:
        print("\n조건식이 없어서 테스트를 계속할 수 없습니다.")
        return

    # 첫 번째 조건식으로 테스트
    condition_id = condition_list[0][0]
    condition_name = condition_list[0][1]

    print(f"\n선택된 조건식: {condition_name} (ID: {condition_id})")

    # Step 2: ka10172, ka10173 테스트
    print("\n")
    response_ka10172 = await test_ka10172_detailed(condition_id, token)

    print("\n")
    response_ka10173 = await test_ka10173_detailed(condition_id, token)

    # 최종 결과
    print_section("최종 테스트 결과")

    print("\n테스트 결과:")
    print(f"  조건식 목록 조회: ✓ 성공 ({len(condition_list)}개)")
    print(f"  ka10172 (일반 조회):   {'✓ 성공' if response_ka10172 else '✗ 실패'}")
    print(f"  ka10173 (실시간 조회): {'✓ 성공' if response_ka10173 else '✗ 실패'}")

    if response_ka10172 and response_ka10173:
        print("\n🎉 모든 TR ID 호출이 성공했습니다!")
    else:
        print("\n⚠️  일부 TR ID 호출이 실패했습니다.")
        if not response_ka10172:
            print("  - ka10172 응답 수신 실패 (타임아웃 또는 에러 응답)")
        if not response_ka10173:
            print("  - ka10173 응답 수신 실패 (타임아웃 또는 에러 응답)")

    print("\n")


if __name__ == '__main__':
    asyncio.run(main())
