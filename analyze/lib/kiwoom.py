"""
키움증권 Open REST API를 이용한 주식 데이터 fetch
"""

import requests
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class KiwoomAPI:
    """키움증권 Open REST API 클래스"""

    def __init__(self, app_key: str, secret_key: str, account_no: str, use_mock: bool = False):
        """
        Args:
            app_key: 앱 키
            secret_key: 시크릿 키
            account_no: 계좌번호
            use_mock: 모의투자 여부 (True: 모의투자, False: 실전투자)
        """
        self.app_key = app_key
        self.secret_key = secret_key
        self.account_no = account_no
        self.base_url = 'https://mockapi.kiwoom.com' if use_mock else 'https://api.kiwoom.com'
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    def get_access_token(self) -> Optional[str]:
        """
        접근 토큰을 발급받습니다.
        이미 유효한 토큰이 있으면 재사용하고, 없거나 만료되었으면 새로 발급받습니다.

        Returns:
            str: 접근 토큰, 실패시 None
        """
        # 기존 토큰이 유효하면 재사용
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                logger.info("기존 토큰 재사용")
                return self.access_token

        # 새로운 토큰 발급
        endpoint = '/oauth2/token'
        url = self.base_url + endpoint

        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
        }

        data = {
            'grant_type': 'client_credentials',
            'appkey': self.app_key,
            'secretkey': self.secret_key,
        }

        try:
            logger.info("접근 토큰 발급 요청 중...")
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()

            result = response.json()

            # 응답 검증
            if result.get('return_code') != 0:
                logger.error(f"토큰 발급 실패: {result.get('return_msg', 'Unknown error')}")
                return None

            # 토큰 추출 (키움 API는 'token' 필드 사용)
            token = result.get('token') or result.get('access_token')
            if not token:
                logger.error(f"토큰 발급 실패 (토큰 없음): {result}")
                return None

            self.access_token = token

            # 만료 시간 설정
            expires_dt = result.get('expires_dt')  # YYYYMMDDHHmmss 형식
            if expires_dt:
                try:
                    self.token_expires_at = datetime.strptime(expires_dt, '%Y%m%d%H%M%S') - timedelta(minutes=1)  # 여유시간 1분
                except Exception as e:
                    logger.warning(f"만료 시간 파싱 실패: {e}, 기본값(24시간) 사용")
                    self.token_expires_at = datetime.now() + timedelta(hours=24)
            else:
                # expires_in이 있으면 사용, 없으면 기본 24시간
                expires_in = result.get('expires_in', 86400)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

            logger.info(f"접근 토큰 발급 성공 (만료: {self.token_expires_at.strftime('%Y-%m-%d %H:%M:%S')})")
            logger.debug(f"Response: {json.dumps(result, indent=4, ensure_ascii=False)}")

            return self.access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"접근 토큰 발급 HTTP 오류: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"접근 토큰 발급 실패: {e}")
            return None

    def _make_request(
        self,
        endpoint: str,
        api_id: str,
        data: Dict[str, Any],
        cont_yn: str = 'N',
        next_key: str = ''
    ) -> Optional[Dict[str, Any]]:
        """
        API 요청을 수행합니다.

        Args:
            endpoint: API 엔드포인트 (예: '/api/dostk/acnt')
            api_id: API ID (TR명, 예: 'ka10170')
            data: 요청 데이터
            cont_yn: 연속조회여부 ('N' 또는 'Y')
            next_key: 연속조회키

        Returns:
            dict: 응답 데이터, 실패시 None
        """
        # 토큰 확인
        token = self.get_access_token()
        if not token:
            logger.error("유효한 토큰이 없습니다")
            return None

        url = self.base_url + endpoint

        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': api_id,
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()

            result = response.json()

            logger.info(f"API 요청 성공: {api_id}")
            logger.debug(f"Response Code: {response.status_code}")
            logger.debug(f"Response Headers: {json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False)}")
            logger.debug(f"Response Body: {json.dumps(result, indent=4, ensure_ascii=False)}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 HTTP 오류: {api_id}, {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"API 요청 실패: {api_id}, {e}")
            return None

    def get_daily_trading_diary(
        self,
        base_dt: str = '',
        ottks_tp: str = '1',
        ch_crd_tp: str = '0'
    ) -> Optional[Dict[str, Any]]:
        """
        당일매매일지를 조회합니다.

        Args:
            base_dt: 기준일자 YYYYMMDD (공백입력시 금일데이터, 최근 2개월까지 제공)
            ottks_tp: 단주구분 ('1': 당일매수에 대한 당일매도, '2': 당일매도 전체)
            ch_crd_tp: 현금신용구분 ('0': 전체, '1': 현금매매만, '2': 신용매매만)

        Returns:
            dict: 당일매매일지 데이터, 실패시 None
        """
        endpoint = '/api/dostk/acnt'
        api_id = 'ka10170'

        data = {
            'base_dt': base_dt,
            'ottks_tp': ottks_tp,
            'ch_crd_tp': ch_crd_tp,
        }

        return self._make_request(endpoint, api_id, data)

    def get_recent_trades(self, days: int = 5) -> List[Dict[str, Any]]:
        """
        최근 N일간의 매매(매수/매도) 데이터를 가져옵니다.

        Args:
            days: 조회할 일수 (기본값: 5일)

        Returns:
            list: 매매 데이터 리스트
            [
                {
                    'stock_code': '005930',      # 종목코드
                    'stock_name': '삼성전자',     # 종목명
                    'trade_type': '매수',        # 매매구분 (매수/매도)
                    'price': 50000,             # 체결가격
                    'quantity': 10,             # 체결수량
                    'datetime': '20241120143000' # 체결일시 (YYYYMMDDHHmmss)
                },
                ...
            ]
        """
        endpoint = '/api/dostk/acnt'
        api_id = 'kt00007'

        all_trades = []

        # 최근 N일 조회
        for i in range(days):
            target_date = datetime.now() - timedelta(days=i)
            ord_dt = target_date.strftime('%Y%m%d')

            logger.info(f"매매내역 조회 중: {ord_dt}")

            data = {
                'ord_dt': ord_dt,           # 주문일자
                'qry_tp': '4',              # 조회구분: 4(체결내역만)
                'stk_bond_tp': '1',         # 주식채권구분: 1(주식)
                'sell_tp': '0',             # 매도수구분: 0(전체)
                'stk_cd': '',               # 종목코드: 공백(전체종목)
                'fr_ord_no': '',            # 시작주문번호: 공백(전체주문)
                'dmst_stex_tp': '%',        # 국내거래소구분: %(전체)
            }

            # API 호출
            result = self._make_request(endpoint, api_id, data)

            if not result:
                logger.warning(f"{ord_dt} 매매내역 조회 실패")
                continue

            # 응답 데이터 파싱
            if 'return_code' in result and result['return_code'] != 0:
                logger.warning(f"{ord_dt} 조회 오류: {result.get('return_msg', 'Unknown error')}")
                continue

            # 응답 구조 디버깅
            logger.debug(f"{ord_dt} 응답 키: {list(result.keys())}")

            # 체결내역 데이터 추출 (키 이름: acnt_ord_cntr_prps_dtl)
            trade_list = result.get('acnt_ord_cntr_prps_dtl', [])

            for trade in trade_list:
                # 체결수량이 0보다 큰 경우만 추가 (실제 체결된 건만)
                cntr_qty_str = trade.get('cntr_qty', '0').strip()
                cntr_qty = int(cntr_qty_str) if cntr_qty_str else 0

                if cntr_qty <= 0:
                    continue

                # 체결단가 파싱
                cntr_uv_str = trade.get('cntr_uv', '0').strip()
                cntr_uv = float(cntr_uv_str) if cntr_uv_str else 0.0

                # 종목코드에서 'A' 접두사 제거
                stock_code = trade.get('stk_cd', '').replace('A', '')

                # 매매구분 파싱 (io_tp_nm: 현금매수, 현금매도 등)
                io_tp_nm = trade.get('io_tp_nm', '')
                trade_type = '매도' if '매도' in io_tp_nm else '매수'

                # 체결시간 (cnfm_tm이 있으면 사용, 없으면 ord_tm 사용)
                trade_time = trade.get('cnfm_tm', '') or trade.get('ord_tm', '')
                trade_datetime = ord_dt + trade_time.replace(':', '')

                trade_data = {
                    'stock_code': stock_code,
                    'stock_name': trade.get('stk_nm', ''),
                    'trade_type': trade_type,
                    'price': cntr_uv,
                    'quantity': cntr_qty,
                    'datetime': trade_datetime,
                    'order_no': trade.get('ord_no', ''),
                }

                all_trades.append(trade_data)

        logger.info(f"총 {len(all_trades)}건의 매매내역 조회 완료")

        # 최신순 정렬 (날짜시간 기준 내림차순)
        all_trades.sort(key=lambda x: x['datetime'], reverse=True)

        return all_trades


if __name__ == '__main__':
    # 테스트
    logging.basicConfig(level=logging.INFO)

    # 설정 (실제 사용시 환경변수나 설정 파일에서 로드하는 것을 권장)
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

    # 접근 토큰 발급 테스트
    print("=" * 50)
    print("접근 토큰 발급 테스트")
    print("=" * 50)
    token = api.get_access_token()
    if token:
        print(f"✓ 토큰 발급 성공")
        print(f"  토큰: {token[:20]}...{token[-20:]}")
    else:
        print("✗ 토큰 발급 실패")

    # 당일매매일지 조회 테스트
    print("\n" + "=" * 50)
    print("당일매매일지 조회 테스트")
    print("=" * 50)
    result = api.get_daily_trading_diary(base_dt='20241120')
    if result:
        print(f"✓ 조회 성공")
        print(json.dumps(result, indent=4, ensure_ascii=False))
    else:
        print("✗ 조회 실패")

    # 최근 5일 매매내역 조회 테스트
    print("\n" + "=" * 50)
    print("최근 5일 매매내역 조회 테스트")
    print("=" * 50)
    trades = api.get_recent_trades(days=5)
    if trades:
        print(f"✓ 조회 성공 (총 {len(trades)}건)")
        for i, trade in enumerate(trades[:10], 1):  # 최근 10건만 출력
            print(f"{i}. [{trade['datetime']}] {trade['stock_name']}({trade['stock_code']}) "
                  f"{trade['trade_type']} {trade['quantity']}주 @ {trade['price']:,.0f}원")
        if len(trades) > 10:
            print(f"... 외 {len(trades) - 10}건")
    else:
        print("조회된 매매내역이 없습니다")
