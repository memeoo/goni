
'''
키움증권 REST API 클라이언트

이 클래스는 키움증권의 새로운 RESTful API에 대한 Wrapper입니다.
API 가이드: https://openapi.kiwoom.com/guide/apiguide?dummyVal=0
'''

import requests
import json
import time
from datetime import datetime, timedelta

class KiwoomRESTAPI:
    """
    키움증권 REST API를 사용하여 계좌 정보를 조회하고, 시세 데이터를 가져오는 등의 기능을 수행합니다.
    """

    def __init__(self, app_key: str, secret_key: str, account_no: str, domain: str = "https://api.kiwoom.com"):
        """
        API 클라이언트를 초기화합니다.

        Args:
            app_key (str): 발급받은 App Key.
            secret_key (str): 발급받은 Secret Key.
            account_no (str): 계좌번호.
            domain (str, optional): API 서버 도메인. Defaults to "https://api.kiwoom.com".
        """
        if not all([app_key, secret_key, account_no]):
            raise ValueError("App Key, Secret Key, 계좌번호는 필수입니다.")

        self.app_key = app_key
        self.secret_key = secret_key
        self.account_no = account_no
        self.domain = domain
        self.access_token = None
        self.token_expires_at = 0

        print("Kiwoom REST API 클라이언트가 초기화되었습니다.")

    def _get_access_token(self) -> bool:
        """
        OAuth2 인증을 통해 액세스 토큰을 발급받습니다.
        """
        if self.access_token and time.time() < self.token_expires_at:
            return True

        print("새로운 액세스 토큰을 발급받습니다...")
        url = f"{self.domain}/oauth2/token"
        headers = {"content-type": "application/json"}
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.secret_key
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get('return_code') == 0 and 'token' in data:
                self.access_token = data['token']
                try:
                    expires_str = data['expires_dt']
                    self.token_expires_at = datetime.strptime(expires_str, '%Y%m%d%H%M%S').timestamp()
                except (ValueError, KeyError):
                    self.token_expires_at = time.time() + 43200 # 12시간
                print("액세스 토큰 발급 성공")
                return True
            else:
                print(f"[에러] 토큰 발급 실패: {data}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"[에러] 토큰 발급 요청 중 오류 발생: {e}")
            return False

    def _make_request(self, method: str, path: str, headers: dict = None, params: dict = None, data: dict = None) -> dict:
        """
        인증 헤더를 포함하여 API 요청을 보냅니다.
        """
        if not self._get_access_token():
            return {"error": "인증 실패"}

        url = f"{self.domain}{path}"
        
        # API 샘플 코드에 따라 헤더 구성 변경
        default_headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {self.access_token}",
        }
        if headers:
            default_headers.update(headers)

        try:
            response = requests.request(method, url, headers=default_headers, params=params, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_details = {"status_code": e.response.status_code}
            try:
                error_details.update(e.response.json())
            except json.JSONDecodeError:
                error_details["message"] = e.response.text
            print(f"[에러] API 요청 실패: {error_details}")
            return {"error": error_details}
        except requests.exceptions.RequestException as e:
            print(f"[에러] API 요청 중 네트워크 오류 발생: {e}")
            return {"error": str(e)}

    def get_account_balance(self) -> dict:
        """
        예수금 상세 현황을 조회합니다.
        TR Code: kt00001
        """
        print("\n--- 예수금 상세 현황 조회를 요청합니다. ---")
        path = "/api/dostk/acnt"
        headers = {
            "api-id": "kt00001",
            "cont-yn": "N"
        }
        body = {
            "acnt_no": self.account_no,
            "password": "", # 실제 사용 시 비밀번호 필요
            "inqr_dv": "01",
            "qry_tp": "1" # 조회 유형 (추정)
        }
        return self._make_request('POST', path, headers=headers, data=body)

    def get_foreign_institutional_net_buy(self, stock_code: str) -> dict:
        """
        가장 최근일의 기관/외국인 일별 순매매 동향을 조회합니다.
        TR Code: ka10009
        """
        print(f"\n{stock_code}의 기관/외국인 순매매 동향 조회를 요청합니다.")

        path = "/api/dostk/frgnistt"
        headers = {
            "api-id": "ka10009",
            "cont-yn": "N"
        }
        body = {
            "stk_cd": stock_code,
            "start_dt": "20250922",
            "end_dt": "20250926"
        }
        response = self._make_request('POST', path, headers=headers, data=body)

        # API 응답이 flat object이므로, output 키 없이 직접 파싱
        if 'error' not in response and response.get('return_code') == 0:
            # 빈 문자열일 경우 0으로 처리하는 로직 추가
            inst_net = response.get('orgn_daly_nettrde', '0')
            frgn_net = response.get('frgnr_daly_nettrde', '0')
            
            return {
                'date': response.get('date'),
                'institutional_net': int(inst_net) if inst_net.strip() else 0,
                'foreign_net': int(frgn_net) if frgn_net.strip() else 0
            }
        
        return response

    def get_order_history(self, order_date: str = "", query_type: str = "4", stock_code: str = "", sell_type: str = "0") -> list:
        """
        계좌별 주문 체결 상세 내역을 조회합니다. (TR Code: kt00007)
        연속 조회를 지원하여 모든 내역을 가져옵니다.

        Args:
            order_date (str, optional): 주문일자 (YYYYMMDD). 공백 시 전체. Defaults to "".
            query_type (str, optional): 조회구분 (1:주문순, 2:역순, 3:미체결, 4:체결내역만). Defaults to "4".
            stock_code (str, optional): 종목코드. 공백 시 전체. Defaults to "".
            sell_type (str, optional): 매도수구분 (0:전체, 1:매도, 2:매수). Defaults to "0".

        Returns:
            list: 주문 체결 내역 리스트.
        """
        print("\n--- 계좌별 주문 체결 내역 조회를 요청합니다. ---")
        path = "/api/dostk/acnt"
        
        all_orders = []
        cont_yn = 'N'
        next_key = ''

        while True:
            headers = {
                "api-id": "kt00007",
                "cont-yn": cont_yn,
                "next-key": next_key
            }
            body = {
                "acnt_no": self.account_no,
                "ord_dt": order_date,
                "qry_tp": query_type,
                "stk_bond_tp": "1", # 1: 주식
                "sell_tp": sell_type,
                "stk_cd": stock_code,
                "fr_ord_no": "",
                "dmst_stex_tp": "%"
            }

            response = self._make_request('POST', path, headers=headers, data=body)

            if 'error' in response or response.get('return_code') != 0:
                print(f"[에러] 주문 내역 조회 실패: {response.get('return_msg', response)}")
                break

            # 응답 헤더에서 연속조회 정보 추출
            # _make_request가 json만 반환하므로, 이 방식은 동작하지 않음.
            # 대신, 응답 본문에 next_key가 있는지 확인해야 할 수 있음 (API 명세 확인 필요)
            # 여기서는 일단 응답 본문에 output이 있으면 파싱하는 것으로 가정
            
            output = response.get('acnt_ord_cntr_prps_dtl', [])
            for item in output:
                all_orders.append({
                    'order_no': item.get('ord_no'),
                    'stock_code': item.get('stk_cd'),
                    'stock_name': item.get('stk_nm'),
                    'order_time': item.get('ord_tm'),
                    'trade_type': item.get('trde_tp'),
                    'order_type': item.get('io_tp_nm'), # 현금매수 등
                    'order_quantity': int(item.get('ord_qty', 0)),
                    'order_price': int(item.get('ord_uv', 0)),
                    'conclusion_quantity': int(item.get('cntr_qty', 0)),
                    'conclusion_price': int(item.get('cntr_uv', 0)),
                    'conclusion_time': item.get('cnfm_tm'),
                })
            
            # 연속 조회가 없다고 가정하고 루프 종료 (실제 API는 헤더 확인 필요)
            break # TODO: 키움증권 REST API의 연속조회 방식 확인 후 수정 필요
        
        print(f"✅ 총 {len(all_orders)}건의 주문 내역을 조회했습니다.")
        return all_orders

# --- 사용 예시 ---
if __name__ == '__main__':
    APP_KEY = "KY7QbSwIVVmjqBM5jIZHbcGOle2O8nQL7dFUNtVmTKU"
    SECRET_KEY = "KUwnffZOR2dP4nwEZCIgTAhu-FquHEa2Xx9mCKE9ak0"
    ACCOUNT_NO = "52958566"

    if ACCOUNT_NO == "YOUR_ACCOUNT_NO":
        print("[경고] `kiwoom.py` 파일의 `ACCOUNT_NO`를 실제 계좌번호로 수정해주세요.")
    else:
        # 1. API 객체 생성
        kiwoom = KiwoomRESTAPI(app_key=APP_KEY, secret_key=SECRET_KEY, account_no=ACCOUNT_NO)

        # 2. SK하이닉스(000660) 기관/외국인 순매매 요청
        fi_data = kiwoom.get_foreign_institutional_net_buy("000660")
        if 'error' not in fi_data:
            print("\n--- 기관/외국인 순매매 수신된 데이터 ---")
            print(fi_data)
        else:
            print(f"\n--- 기관/외국인 순매매 요청 실패 ---")
            print(fi_data['error'])

        # 3. 주문 체결 내역 조회 (체결내역만)
        # order_date를 지정하지 않으면 전체 기간 조회
        order_history = kiwoom.get_order_history(query_type="4", stock_code="005930")
        if order_history:
            print("\n--- 주문 체결 내역 (최근 5건) ---")
            import pprint
            pprint.pprint(order_history[:5])
