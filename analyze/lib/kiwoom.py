"""
키움증권 Open REST API를 이용한 주식 데이터 fetch
"""

import requests
import json
import logging
import asyncio
import websockets
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class KiwoomWebSocketClient:
    """키움증권 WebSocket 실시간 데이터 클라이언트"""

    def __init__(self, access_token: str, use_mock: bool = False):
        """
        Args:
            access_token: 키움증권 API 접근 토큰
            use_mock: 모의투자 여부 (True: 모의투자, False: 실전투자)
        """
        self.access_token = access_token
        self.websocket_url = 'wss://mockapi.kiwoom.com:10000/api/dostk/websocket' if use_mock else 'wss://api.kiwoom.com:10000/api/dostk/websocket'
        self.websocket = None
        self.connected = False
        self.keep_running = True
        self.response_data = None
        self.response_queue = {}  # 응답을 조건식 ID별로 저장

    async def connect(self):
        """WebSocket 서버에 연결합니다."""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            self.connected = True
            logger.info("WebSocket 서버에 연결했습니다")

            # 로그인 패킷 전송
            login_param = {
                'trnm': 'LOGIN',
                'token': self.access_token
            }

            logger.info('WebSocket 로그인 패킷을 전송합니다')
            await self.send_message(login_param)

        except Exception as e:
            logger.error(f'WebSocket 연결 오류: {e}')
            self.connected = False
            raise

    async def send_message(self, message: Dict[str, Any]):
        """서버에 메시지를 보냅니다."""
        if not self.connected:
            await self.connect()

        if self.connected:
            message_str = json.dumps(message)
            await self.websocket.send(message_str)
            logger.debug(f'메시지 전송: {message_str}')

    async def receive_messages(self):
        """서버에서 오는 메시지를 수신합니다."""
        while self.keep_running:
            try:
                if not self.websocket:
                    await asyncio.sleep(0.1)
                    continue

                response = json.loads(await self.websocket.recv())
                logger.debug(f'WebSocket 응답 수신: {response}')

                trnm = response.get('trnm')

                # 로그인 응답 처리
                if trnm == 'LOGIN':
                    if response.get('return_code') != 0:
                        logger.error(f'로그인 실패: {response.get("return_msg")}')
                        await self.disconnect()
                        return False
                    else:
                        logger.info('로그인 성공')
                    # response_data에 저장
                    self.response_data = response

                # PING 응답 처리 (PING을 받으면 그대로 다시 보내기)
                elif trnm == 'PING':
                    logger.debug('PING 응답 수신 및 재전송')
                    await self.send_message(response)
                    # PING은 response_data에 저장하지 않음

                # 조건식 목록 조회 응답
                elif trnm == 'CNSRLST':
                    logger.info(f'조건식 목록 응답 수신: {len(response.get("data", []))}개')
                    self.response_data = response

                # 조건식 검색 응답 (일반 조회 또는 실시간 조회)
                elif trnm == 'CNSRREQ':
                    seq = response.get('seq')  # 조건식 ID
                    logger.info(f'조건식 {seq} 검색 응답 수신: {len(response.get("data", []))}개 종목')
                    # 응답을 조건식 ID별로 저장
                    if seq:
                        self.response_queue[seq] = response
                    # 동시에 response_data에도 저장 (하위 호환성)
                    self.response_data = response

                # 조건식 실시간 해제 응답
                elif trnm == 'CNSRCLR':
                    logger.info(f'조건식 실시간 해제 응답: {response}')
                    self.response_data = response

                # 기타 응답
                else:
                    logger.info(f'WebSocket 응답 [{trnm}]: {response}')
                    self.response_data = response

            except websockets.ConnectionClosed:
                logger.error('WebSocket 연결이 서버에 의해 종료됨')
                self.connected = False
                return False
            except asyncio.CancelledError:
                logger.debug('메시지 수신 태스크가 취소됨')
                return False
            except Exception as e:
                logger.error(f'WebSocket 메시지 수신 오류: {e}')
                return False

    async def disconnect(self):
        """WebSocket 연결을 종료합니다."""
        self.keep_running = False
        if self.connected and self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info('WebSocket 연결을 종료했습니다')

    async def request_condition_list(self) -> Optional[List[List[str]]]:
        """
        조건 검색 목록을 조회합니다 (CNSRLST).

        Returns:
            list: 조건 검색 목록
                [
                    ['0', '조건1'],
                    ['1', '조건2'],
                    ...
                ]
                실패시 None
        """
        try:
            await self.connect()

            # 메시지 수신 태스크를 백그라운드에서 실행
            receive_task = asyncio.create_task(self.receive_messages())

            # 로그인 응답 대기 (최대 5초)
            await asyncio.sleep(1)

            # 조건 검색 목록 요청
            request_param = {'trnm': 'CNSRLST'}
            await self.send_message(request_param)

            # 응답 대기 (최대 5초)
            for _ in range(50):  # 5초간 대기
                if self.response_data and self.response_data.get('trnm') == 'CNSRLST':
                    response = self.response_data
                    self.response_data = None  # 응답 초기화

                    # 응답 검증
                    if response.get('return_code') != 0:
                        logger.error(f"조건 검색 목록 조회 오류: {response.get('return_msg', 'Unknown error')}")
                        return None

                    condition_list = response.get('data', [])
                    logger.info(f"조건 검색 목록 조회 성공: 총 {len(condition_list)}개")

                    return condition_list

                await asyncio.sleep(0.1)

            logger.error("조건 검색 목록 조회 타임아웃")
            return None

        except Exception as e:
            logger.error(f"조건 검색 목록 조회 실패: {e}")
            return None
        finally:
            await self.disconnect()

    async def request_condition_search(
        self,
        condition_id: str,
        search_type: str = '0',
        stock_exchange_type: str = 'K',
        cont_yn: str = 'N',
        next_key: str = ''
    ) -> Optional[Dict[str, Any]]:
        """
        조건식으로 종목을 검색합니다 (CNSRREQ).

        Args:
            condition_id: 조건식 ID (조건 검색 목록에서 조회한 ID)
            search_type: 조회 타입
                - '0': 일반 조회 (ka10172)
                - '1': 실시간 조회 (ka10173)
            stock_exchange_type: 거래소 구분 ('K': 코스피, 'Q': 코스닥, '%': 전체)
                - 실시간 조회('1')에서는 사용되지 않음
            cont_yn: 연속조회여부 ('N': 아니오, 'Y': 예) - 일반 조회에서만 사용
            next_key: 연속조회키 (연속조회시 사용) - 일반 조회에서만 사용

        Returns:
            dict: 조건 검색 결과
                {
                    'return_code': 0,
                    'return_msg': '',
                    'seq': '조건식번호',
                    'cont_yn': 'N',
                    'next_key': '',
                    'data': [
                        {
                            '9001': 'A005930',           # 종목코드
                            '302': '삼성전자',           # 종목명
                            '10': '000075000',          # 현재가
                            '25': '5',                  # 상태값
                            '11': '-00000100',          # 기타필드들...
                            ...
                        },
                        ...
                    ]
                }
                실패시 None
        """
        try:
            await self.connect()

            # 메시지 수신 태스크를 백그라운드에서 실행
            receive_task = asyncio.create_task(self.receive_messages())

            # 로그인 응답 대기
            await asyncio.sleep(1)

            # 응답 큐 초기화 (해당 조건식 ID의 응답 제거)
            if condition_id in self.response_queue:
                del self.response_queue[condition_id]

            # 조건 검색 요청 구성 (search_type에 따라 다름)
            if search_type == '1':
                # 실시간 조회 (ka10173): stex_tp 없음
                request_param = {
                    'trnm': 'CNSRREQ',
                    'seq': condition_id,
                    'search_type': '1',  # 실시간 조회
                }
                logger.info(f"조건 검색 요청 시작 (실시간): condition_id={condition_id}")
            else:
                # 일반 조회 (ka10172): stex_tp, cont_yn, next_key 포함
                request_param = {
                    'trnm': 'CNSRREQ',
                    'seq': condition_id,
                    'search_type': '0',  # 일반 조회
                    'stex_tp': stock_exchange_type,
                    'cont_yn': cont_yn,
                    'next_key': next_key
                }
                logger.info(f"조건 검색 요청 시작 (일반): condition_id={condition_id}, stex_tp={stock_exchange_type}")

            await self.send_message(request_param)

            # 응답 대기 (최대 30초로 증가)
            max_wait = 300 if search_type == '1' else 200  # 실시간은 30초, 일반은 20초
            for _ in range(max_wait):
                # 응답 큐에서 조건식별 응답 확인
                if condition_id in self.response_queue:
                    response = self.response_queue[condition_id]
                    del self.response_queue[condition_id]

                    # 응답 검증
                    if response.get('return_code') != 0:
                        logger.error(f"조건 검색 요청 오류: {response.get('return_msg', 'Unknown error')}")
                        return None

                    data = response.get('data', [])
                    logger.info(f"조건 검색 결과: 조건식 {condition_id}, 총 {len(data)}개 종목")

                    return response

                await asyncio.sleep(0.1)

            logger.error(f"조건 검색 요청 타임아웃: condition_id={condition_id}")
            return None

        except Exception as e:
            logger.error(f"조건 검색 요청 실패: {e}", exc_info=True)
            return None
        finally:
            await self.disconnect()


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

    def get_daily_chart(
        self,
        stock_code: str,
        base_dt: str = '',
        upd_stkpc_tp: str = '1'
    ) -> Optional[Dict[str, Any]]:
        """
        주식 일봉 차트 데이터를 조회합니다 (ka10081 API).

        Args:
            stock_code: 종목코드 (6자리, 예: '005930')
            base_dt: 기준일자 YYYYMMDD (공백입력시 금일데이터)
            upd_stkpc_tp: 수정주가구분 ('0': 미수정, '1': 수정, 기본값: '1')

        Returns:
            dict: 일봉 차트 데이터
            {
                'stk_cd': '005930',
                'stk_dt_pole_chart_qry': [
                    {
                        'dt': '20250908',       # 날짜
                        'open_pric': '69800',   # 시가
                        'high_pric': '70500',   # 고가
                        'low_pric': '69600',    # 저가
                        'cur_prc': '70100',     # 종가
                        'trde_qty': '9263135',  # 거래량
                        'trde_prica': '648525'  # 거래대금
                    },
                    ...
                ],
                'return_code': 0,
                'return_msg': '정상적으로 처리되었습니다'
            }
        """
        endpoint = '/api/dostk/chart'
        api_id = 'ka10081'

        data = {
            'stk_cd': stock_code,
            'base_dt': base_dt,
            'upd_stkpc_tp': upd_stkpc_tp,
        }

        result = self._make_request(endpoint, api_id, data)

        if not result:
            logger.error(f"일봉 차트 조회 실패: {stock_code}")
            return None

        # 응답 검증
        if result.get('return_code') != 0:
            logger.error(f"일봉 차트 조회 오류: {result.get('return_msg', 'Unknown error')}")
            return None

        logger.info(f"일봉 차트 조회 성공: {stock_code} ({len(result.get('stk_dt_pole_chart_qry', []))}개 데이터)")
        return result

    def get_account_evaluation(
        self,
        qry_tp: str = '0',
        dmst_stex_tp: str = 'KRX'
    ) -> Optional[Dict[str, Any]]:
        """
        계좌평가현황을 조회합니다 (kt00004 API).

        Args:
            qry_tp: 상장폐지조회구분
                   '0': 전체 (기본값)
                   '1': 상장폐지종목제외
            dmst_stex_tp: 국내거래소구분
                         'KRX': 한국거래소 (기본값)
                         'NXT': 넥스트트레이드

        Returns:
            dict: 계좌평가현황 데이터
            {
                'acnt_nm': '김키움',              # 계좌명
                'brch_nm': '키움은행',            # 지점명
                'tot_est_amt': '342000000',      # 총평가금액
                'aset_evlt_amt': '761950000',    # 자산평가금액
                'tot_pur_amt': '2786000',        # 총매입금액
                'tdy_lspft_amt': '1000000',      # 당일손익금액
                'lspft_amt': '500000',           # 손익금액
                'tdy_lspft_rt': '1.5',           # 당일손익율
                'lspft_rt': '2.5',               # 손익율
                'stk_acnt_evlt_prst': [          # 종목별 계좌평가현황
                    {
                        'stk_cd': 'A005930',        # 종목코드
                        'stk_nm': '삼성전자',       # 종목명
                        'rmnd_qty': '3',            # 잔량
                        'avg_prc': '124500',        # 평균단가
                        'cur_prc': '70000',         # 현재가
                        'evlt_amt': '209542000',    # 평가금액
                        'pl_amt': '-163958000',     # 손익금액
                        'pl_rt': '-43.8977',        # 손익율
                        'pur_amt': '373500000'      # 매입금액
                    },
                    ...
                ],
                'return_code': 0,
                'return_msg': '조회가 완료되었습니다.'
            }
        """
        endpoint = '/api/dostk/acnt'
        api_id = 'kt00004'

        data = {
            'qry_tp': qry_tp,
            'dmst_stex_tp': dmst_stex_tp,
        }

        result = self._make_request(endpoint, api_id, data)

        if not result:
            logger.error("계좌평가현황 조회 실패")
            return None

        # 응답 검증
        if result.get('return_code') != 0:
            logger.error(f"계좌평가현황 조회 오류: {result.get('return_msg', 'Unknown error')}")
            return None

        # 종목 정보 파싱
        stocks = result.get('stk_acnt_evlt_prst', [])
        logger.info(f"계좌평가현황 조회 성공: 총 {len(stocks)}개 보유종목")

        for stock in stocks:
            # 종목코드에서 'A' 접두사 제거
            stock_cd = stock.get('stk_cd', '')
            if stock_cd.startswith('A'):
                stock['stk_cd'] = stock_cd[1:]

            # 숫자 문자열을 숫자로 변환 (가독성 개선)
            for field in ['rmnd_qty', 'avg_prc', 'cur_prc', 'evlt_amt', 'pl_amt', 'pur_amt']:
                if field in stock:
                    try:
                        stock[field] = float(stock[field].strip() or '0')
                    except (ValueError, AttributeError):
                        stock[field] = 0

            # 비율은 float로 변환
            for field in ['pl_rt']:
                if field in stock:
                    try:
                        stock[field] = float(stock[field].strip() or '0')
                    except (ValueError, AttributeError):
                        stock[field] = 0

        # 계좌 정보의 숫자도 변환
        account_fields = ['tot_est_amt', 'aset_evlt_amt', 'tot_pur_amt', 'prsm_dpst_aset_amt',
                         'tdy_lspft_amt', 'lspft_amt', 'tdy_lspft_rt', 'lspft_rt']
        for field in account_fields:
            if field in result:
                try:
                    result[field] = float(result[field].strip() or '0')
                except (ValueError, AttributeError):
                    result[field] = 0

        logger.debug(f"계좌평가현황: {json.dumps(result, indent=4, ensure_ascii=False)}")
        return result

    def get_stocks_info(
        self,
        mrkt_tp: str = '0',
        cont_yn: str = 'N',
        next_key: str = ''
    ) -> Optional[Dict[str, Any]]:
        """
        종목정보리스트를 조회합니다 (ka10099 API).

        Args:
            mrkt_tp: 시장구분
                    '0': 코스피 (기본값)
                    '10': 코스닥
                    '3': ELW
                    '8': ETF
                    '30': K-OTC
                    '50': 코넥스
                    '5': 신주인수권
                    '4': 뮤추얼펀드
                    '6': 리츠
                    '9': 하이일드
            cont_yn: 연속조회여부 ('N' 또는 'Y')
            next_key: 연속조회키

        Returns:
            dict: 종목정보 데이터
            {
                'return_msg': '정상적으로 처리되었습니다',
                'return_code': 0,
                'list': [
                    {
                        'code': '005930',              # 종목코드
                        'name': '삼성전자',            # 종목명
                        'listCount': '0000000123759593', # 상장주식수
                        'auditInfo': '투자주의환기종목', # 감시종목
                        'regDay': '20091204',          # 상장일
                        'lastPrice': '00000197',       # 종목액면가
                        'state': '관리종목',            # 증거금상태
                        'marketCode': '10',            # 마켓코드
                        'marketName': '코스닥',        # 마켓명
                        'upName': '',                  # 상위종목명
                        'upSizeName': '',              # 상위사이즈명
                        'companyClassName': '외국기업', # 회사분류명
                        'orderWarning': '0',           # 주문경고
                        'nxtEnable': 'Y'               # 다음조회여부
                    },
                    ...
                ],
                'cont-yn': 'N',                        # 연속조회여부 (응답 헤더)
                'next-key': ''                         # 연속조회키 (응답 헤더)
            }
        """
        endpoint = '/api/dostk/stkinfo'
        api_id = 'ka10099'

        data = {
            'mrkt_tp': mrkt_tp,
        }

        result = self._make_request(endpoint, api_id, data, cont_yn=cont_yn, next_key=next_key)

        if not result:
            logger.error(f"종목정보리스트 조회 실패: mrkt_tp={mrkt_tp}")
            return None

        # 응답 검증
        if result.get('return_code') != 0:
            logger.error(f"종목정보리스트 조회 오류: {result.get('return_msg', 'Unknown error')}")
            return None

        # 종목 정보 파싱
        stocks = result.get('list', [])
        logger.info(f"종목정보리스트 조회 성공: 시장={mrkt_tp}, 조회된 종목 수={len(stocks)}")

        return result

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

    def get_condition_list(self, use_mock: bool = False) -> Optional[List[Dict[str, Any]]]:
        """
        사용자가 키움에 설정한 조건 검색 목록을 조회합니다.

        이 메서드는 WebSocket을 사용하여 실시간으로 조건 검색 목록을 가져옵니다.
        비동기 작업이므로 asyncio 이벤트 루프가 필요합니다.

        Args:
            use_mock: 모의투자 여부 (True: 모의투자, False: 실전투자)

        Returns:
            list: 조건 검색 목록
                [
                    {
                        'id': '0',
                        'name': '조건1'
                    },
                    {
                        'id': '1',
                        'name': '조건2'
                    },
                    ...
                ]
                실패시 None

        Example:
            >>> api = KiwoomAPI(app_key, secret_key, account_no)
            >>> conditions = api.get_condition_list()
            >>> if conditions:
            ...     for condition in conditions:
            ...         print(f"조건 ID: {condition['id']}, 조건명: {condition['name']}")
        """
        try:
            # 접근 토큰 발급
            token = self.get_access_token()
            if not token:
                logger.error("유효한 토큰이 없습니다")
                return None

            # WebSocket 클라이언트 생성
            ws_client = KiwoomWebSocketClient(access_token=token, use_mock=use_mock)

            # 비동기 함수 실행
            condition_list = asyncio.run(ws_client.request_condition_list())

            if not condition_list:
                logger.warning("조건 검색 목록이 없거나 조회 실패")
                return None

            # 응답 데이터를 딕셔너리 리스트로 변환
            formatted_conditions = []
            for condition in condition_list:
                if isinstance(condition, list) and len(condition) >= 2:
                    formatted_conditions.append({
                        'id': condition[0],
                        'name': condition[1]
                    })

            logger.info(f"조건 검색 목록 포맷팅 완료: {len(formatted_conditions)}개")
            return formatted_conditions

        except Exception as e:
            logger.error(f"조건 검색 목록 조회 실패: {e}")
            return None

    def search_condition(
        self,
        condition_id: str,
        search_type: str = '0',
        stock_exchange_type: str = 'K',
        use_mock: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """
        조건식으로 종목을 검색합니다 (CNSRREQ).

        조건 검색 목록에서 조회한 조건식으로 해당 조건을 만족하는 종목을 검색합니다.

        Args:
            condition_id: 조건식 ID (get_condition_list()에서 조회한 'id' 값)
            search_type: 조회 타입 (기본값: '0')
                - '0': 일반 조회
                - '1': 실시간 조회 등
            stock_exchange_type: 거래소 구분 (기본값: 'K')
                - 'K': 코스피
                - 'Q': 코스닥
                - '%': 전체
            use_mock: 모의투자 여부 (True: 모의투자, False: 실전투자)

        Returns:
            list: 검색 결과 종목 리스트
                [
                    {
                        'stock_code': 'A005930',      # 종목코드
                        'stock_name': '삼성전자',      # 종목명
                        'current_price': 75000,       # 현재가
                        'status': 5,                   # 상태값
                        'raw_data': {...}             # 원본 응답 데이터
                    },
                    ...
                ]
                실패시 None

        Example:
            >>> api = KiwoomAPI(app_key, secret_key, account_no)
            >>> conditions = api.get_condition_list()
            >>> if conditions:
            ...     results = api.search_condition(conditions[0]['id'])
            ...     if results:
            ...         for stock in results:
            ...             print(f"{stock['stock_name']}({stock['stock_code']}): {stock['current_price']}")
        """
        try:
            # 접근 토큰 발급
            token = self.get_access_token()
            if not token:
                logger.error("유효한 토큰이 없습니다")
                return None

            # WebSocket 클라이언트 생성
            ws_client = KiwoomWebSocketClient(access_token=token, use_mock=use_mock)

            # 비동기 함수 실행
            response = asyncio.run(ws_client.request_condition_search(
                condition_id=condition_id,
                search_type=search_type,
                stock_exchange_type=stock_exchange_type
            ))

            if not response:
                logger.warning("조건 검색 결과가 없거나 조회 실패")
                return None

            # 응답 데이터 파싱
            data = response.get('data', [])
            if not data:
                logger.info(f"조건식 {condition_id}으로 검색한 결과가 없습니다")
                return []

            # 응답 데이터를 사용하기 쉬운 형식으로 변환
            formatted_stocks = []
            for stock_data in data:
                try:
                    # 종목코드에서 'A' 접두사 제거
                    stock_code = stock_data.get('9001', '').replace('A', '')
                    stock_name = stock_data.get('302', '')
                    current_price_str = stock_data.get('10', '0').strip()
                    status = stock_data.get('25', '')

                    # 현재가를 숫자로 변환
                    try:
                        current_price = float(current_price_str) if current_price_str else 0.0
                    except (ValueError, TypeError):
                        current_price = 0.0

                    formatted_stocks.append({
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'current_price': current_price,
                        'status': status,
                        'raw_data': stock_data  # 원본 데이터 포함
                    })

                except Exception as e:
                    logger.warning(f"종목 데이터 파싱 오류: {stock_data}, {e}")
                    continue

            logger.info(f"조건식 {condition_id}으로 {len(formatted_stocks)}개 종목 검색 완료")
            return formatted_stocks

        except Exception as e:
            logger.error(f"조건 검색 실패: {e}")
            return None


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

    # 계좌평가현황 조회 테스트 (kt00004)
    print("\n" + "=" * 50)
    print("계좌평가현황 조회 테스트 (kt00004)")
    print("=" * 50)
    account = api.get_account_evaluation()
    if account:
        print(f"✓ 조회 성공")
        print(f"  계좌명: {account.get('acnt_nm')}")
        print(f"  지점명: {account.get('brch_nm')}")
        print(f"  총평가금액: {account.get('tot_est_amt'):,.0f}원")
        print(f"  자산평가금액: {account.get('aset_evlt_amt'):,.0f}원")
        print(f"  보유종목 수: {len(account.get('stk_acnt_evlt_prst', []))}")
        print(f"\n  보유종목:")
        for i, stock in enumerate(account.get('stk_acnt_evlt_prst', [])[:5], 1):  # 최근 5개만 출력
            print(f"  {i}. {stock.get('stk_nm')}({stock.get('stk_cd')}) "
                  f"수량: {stock.get('rmnd_qty'):.0f}주, "
                  f"평가금액: {stock.get('evlt_amt'):,.0f}원, "
                  f"손익율: {stock.get('pl_rt'):.2f}%")
        if len(account.get('stk_acnt_evlt_prst', [])) > 5:
            print(f"  ... 외 {len(account.get('stk_acnt_evlt_prst', [])) - 5}개")
    else:
        print("조회 실패")

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

    # 일봉 차트 조회 테스트 (ka10081)
    print("\n" + "=" * 50)
    print("일봉 차트 조회 테스트 (ka10081)")
    print("=" * 50)
    chart = api.get_daily_chart(stock_code='005930')
    if chart:
        print(f"✓ 조회 성공")
        chart_data = chart.get('stk_dt_pole_chart_qry', [])
        print(f"  종목코드: {chart.get('stk_cd')}")
        print(f"  데이터 건수: {len(chart_data)}")
        for i, data in enumerate(chart_data[:5], 1):  # 최근 5개만 출력
            print(f"{i}. [{data['dt']}] 시가:{data['open_pric']} 고가:{data['high_pric']} "
                  f"저가:{data['low_pric']} 종가:{data['cur_prc']} 거래량:{data['trde_qty']}")
        if len(chart_data) > 5:
            print(f"... 외 {len(chart_data) - 5}건")
    else:
        print("✗ 일봉 차트 조회 실패")
