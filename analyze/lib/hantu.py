# -*- coding: utf-8 -*-
"""
한국투자증권(KIS) Open API Wrapper Functions
주식 OHLC 데이터 및 거래량 데이터 조회 기능 제공
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import pandas as pd
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class KISApi:
    """한국투자증권 Open API 클래스"""
    
    def __init__(self):
        """API 클라이언트 초기화"""
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.app_key = os.getenv('PROD_APP_KEY')
        self.app_secret = os.getenv('PROD_APP_SECRET')
        self.account_no = os.getenv('PROD_ACCOUNT_NO')
        self.access_token = None
        
        if not all([self.app_key, self.app_secret, self.account_no]):
            raise ValueError("KIS API 설정 정보가 부족합니다. .env 파일을 확인해주세요.")
        
        # 접근 토큰 발급
        self.get_access_token()
    
    def get_access_token(self) -> str:
        """접근 토큰 발급 (캐싱 포함)"""
        import json
        from datetime import datetime
        
        token_file = "kis_token.json"
        
        # 🔥 강제 토큰 갱신 - 데이터 최신화를 위해 항상 새 토큰 발급
        print("🔑 새로운 토큰 발급 시작 (데이터 최신화를 위해 강제 갱신)")
        
        # 기존 토큰 확인 로직은 주석 처리
        # try:
        #     if os.path.exists(token_file):
        #         with open(token_file, 'r') as f:
        #             token_data = json.load(f)
        #         
        #         # 토큰 만료 시간 확인 (30분 여유를 두고 갱신)
        #         expire_time = datetime.fromisoformat(token_data['expires_at'])
        #         if datetime.now() < expire_time:
        #             self.access_token = token_data['access_token']
        #             print("기존 토큰 재사용")
        #             return self.access_token
        # except Exception:
        #     pass  # 토큰 파일 오류 시 새로 발급
        
        # 새 토큰 발급
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"Content-Type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('access_token'):
                self.access_token = result['access_token']
                
                # 토큰을 파일에 저장 (23시간 30분 유효)
                expire_time = datetime.now() + timedelta(hours=23, minutes=30)
                token_data = {
                    'access_token': self.access_token,
                    'expires_at': expire_time.isoformat()
                }
                
                with open(token_file, 'w') as f:
                    json.dump(token_data, f)
                
                print("새 토큰 발급 및 저장")
                return self.access_token
            else:
                raise Exception(f"토큰 발급 실패: {result}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 호출 중 오류 발생: {e}")
    
    def _get_headers(self, tr_id: str) -> Dict[str, str]:
        """API 호출용 헤더 생성"""
        return {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id
        }
    
    def get_stock_ohlc(self, stock_code: str, days: int = 30) -> pd.DataFrame:
        """
        주식 OHLC 데이터 조회 (일별 시세 조회 API 사용)
        
        Args:
            stock_code (str): 종목코드 (6자리)
            days (int): 조회 기간 (일 수, 기본값: 30일)
            
        Returns:
            pd.DataFrame: 날짜, 시가, 고가, 저가, 종가 데이터
        """
        # KIS API 문서 참고: inquire-daily-price 엔드포인트 사용
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        headers = self._get_headers("FHKST03010100")  # 국내주식기간별시세(일/주/월/년) TR_ID
        
        # 최근 days일 데이터를 위해 충분한 범위로 설정 (주말, 공휴일 고려)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 10)  # 여유분 추가
        
        params = {
            "fid_cond_mrkt_div_code": "J",  # 시장분류코드 (J: 주식)
            "fid_input_iscd": stock_code,   # 종목코드
            "fid_input_date_1": start_date.strftime("%Y%m%d"),  # 조회시작일자
            "fid_input_date_2": end_date.strftime("%Y%m%d"),    # 조회종료일자
            "fid_period_div_code": "D",     # 기간분류코드 (D: 일봉)
            "fid_org_adj_prc": "0"          # 수정주가원주가가격 (0: 수정주가 반영)
        }
        
        print(f"🔍 OHLC API 호출: {url}")
        print(f"📋 파라미터: {params}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            print(f"📊 OHLC API 응답: rt_cd={result.get('rt_cd')}, msg1={result.get('msg1')}")
            print(f"📈 응답 키들: {list(result.keys())}")
            
            if result.get('rt_cd') != '0' and result.get('rt_cd') != '':
                print(f"🔴 API 오류 응답 전체: {result}")
                raise Exception(f"API 호출 실패: {result.get('msg1', 'Unknown error')}")
            
            # output 또는 output2에서 데이터 추출 시도
            output_data = result.get('output', result.get('output2', []))
            
            if not output_data:
                print("⚠️ output 데이터가 비어있음")
                return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close'])
            
            print(f"✅ {len(output_data)}개 데이터 포인트 처리 중...")
            
            # 데이터 변환 (필드명이 다를 수 있으므로 여러 패턴 시도)
            ohlc_data = []
            for item in output_data:
                try:
                    # 가능한 날짜 필드명들
                    date_field = item.get('stck_bsop_date') or item.get('bsop_date') or item.get('date')
                    if date_field:
                        date_obj = datetime.strptime(str(date_field), '%Y%m%d')
                    else:
                        continue
                    
                    # 가능한 OHLC 필드명들
                    open_price = float(item.get('stck_oprc') or item.get('oprc') or item.get('open') or 0)
                    high_price = float(item.get('stck_hgpr') or item.get('hgpr') or item.get('high') or 0)
                    low_price = float(item.get('stck_lwpr') or item.get('lwpr') or item.get('low') or 0)
                    close_price = float(item.get('stck_clpr') or item.get('clpr') or item.get('close') or 0)
                    
                    if close_price > 0:  # 유효한 데이터만 추가
                        ohlc_data.append({
                            'date': date_obj,
                            'open': open_price,
                            'high': high_price,
                            'low': low_price,
                            'close': close_price
                        })
                        
                except (ValueError, TypeError) as e:
                    print(f"⚠️ 데이터 파싱 오류 (건너뜀): {e}, 데이터: {item}")
                    continue
            
            if not ohlc_data:
                print("❌ 파싱된 유효 데이터가 없음")
                return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close'])
            
            df = pd.DataFrame(ohlc_data)
            df = df.sort_values('date', ascending=False).head(days)  # 최신 days개만
            df = df.sort_values('date').reset_index(drop=True)  # 날짜순 정렬
            
            print(f"🎯 최종 OHLC DataFrame: {len(df)}개 행")
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"🌐 네트워크 오류: {e}")
            raise Exception(f"OHLC 데이터 조회 중 오류 발생: {e}")
        except Exception as e:
            print(f"💥 처리 오류: {e}")
            raise Exception(f"데이터 처리 중 오류 발생: {e}")
    
    def get_stock_volume(self, stock_code: str, days: int = 30) -> pd.DataFrame:
        """
        주식 거래량 데이터 조회
        
        Args:
            stock_code (str): 종목코드 (6자리)
            days (int): 조회 기간 (일 수, 기본값: 30일)
            
        Returns:
            pd.DataFrame: 날짜, 거래량, 거래대금 데이터
        """
        # 날짜 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        headers = self._get_headers("FHKST03010100")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장구분코드 (J: 주식)
            "FID_INPUT_ISCD": stock_code,   # 종목코드
            "FID_INPUT_DATE_1": start_date.strftime("%Y%m%d"),  # 시작일자
            "FID_INPUT_DATE_2": end_date.strftime("%Y%m%d"),    # 종료일자
            "FID_PERIOD_DIV_CODE": "D"      # 기간분류코드 (D: 일봉)
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('rt_cd') != '0':
                raise Exception(f"API 호출 실패: {result.get('msg1', 'Unknown error')}")
            
            # 데이터 추출 및 DataFrame 생성
            output_data = result.get('output2', [])
            
            if not output_data:
                return pd.DataFrame(columns=['date', 'volume', 'trade_amount'])
            
            # 데이터 변환
            volume_data = []
            for item in output_data:
                volume_data.append({
                    'date': datetime.strptime(item['stck_bsop_date'], '%Y%m%d'),
                    'volume': int(item['acml_vol']),           # 누적거래량
                    'trade_amount': int(item['acml_tr_pbmn'])  # 누적거래대금
                })
            
            df = pd.DataFrame(volume_data)
            df = df.sort_values('date').reset_index(drop=True)
            
            return df
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"거래량 데이터 조회 중 오류 발생: {e}")
        except Exception as e:
            raise Exception(f"데이터 처리 중 오류 발생: {e}")
    
    def get_current_price(self, stock_code: str) -> Dict[str, Any]:
        """
        종목 현재가 및 등락률 조회
        
        Args:
            stock_code (str): 종목코드 (6자리)
            
        Returns:
            Dict: 현재가, 등락률, 등락금액 등의 정보
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = self._get_headers("FHKST01010100")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장구분코드 (J: 주식)
            "FID_INPUT_ISCD": stock_code     # 종목코드
        }
        
        print(f"💰 현재가 API 호출: {stock_code}")
        print(f"⏰ API 호출 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            print(f"💵 현재가 API 응답: rt_cd={result.get('rt_cd')}, msg1={result.get('msg1')}")
            
            if result.get('rt_cd') != '0':
                print(f"🔴 현재가 API 오류: {result}")
                raise Exception(f"API 호출 실패: {result.get('msg1', 'Unknown error')}")
            
            # 데이터 추출
            output = result.get('output', {})
            
            if not output:
                print("⚠️ 현재가 데이터가 비어있음")
                raise Exception("현재가 데이터를 찾을 수 없습니다")
            
            # 현재가 정보 파싱
            current_price = int(output.get('stck_prpr', 0))                    # 현재가
            prev_close = int(output.get('stck_sdpr', 0))                       # 전일종가
            change_price_abs = int(output.get('prdy_vrss', 0))                 # 등락금액 (절댓값)
            change_rate_abs = float(output.get('prdy_ctrt', 0))                # 등락률 (절댓값)
            change_sign = output.get('prdy_vrss_sign', '3')                    # 등락부호
            volume = int(output.get('acml_vol', 0))                            # 누적거래량
            trade_amount = int(output.get('acml_tr_pbmn', 0))                  # 누적거래대금
            
            # 등락부호에 따라 부호 적용
            # 1: 상한, 2: 상승, 3: 보합, 4: 하한, 5: 하락
            if change_sign in ['1', '2']:  # 상승
                change_price = change_price_abs
                change_rate = change_rate_abs
            elif change_sign in ['4', '5']:  # 하락
                change_price = -change_price_abs
                change_rate = -change_rate_abs
            else:  # 보합
                change_price = 0
                change_rate = 0.0
            
            result_data = {
                'stock_code': stock_code,
                'current_price': current_price,
                'prev_close': prev_close,
                'change_price': change_price,
                'change_rate': change_rate,
                'volume': volume,
                'trade_amount': trade_amount,
                'updated_at': datetime.now().isoformat()
            }
            
            print(f"✅ 현재가 데이터 파싱 완료: 현재가={current_price}원, 등락률={change_rate}%")
            return result_data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"현재가 조회 중 오류 발생: {e}")
        except Exception as e:
            raise Exception(f"데이터 처리 중 오류 발생: {e}")
    
    def get_stock_data_combined(self, stock_code: str, days: int = 30) -> pd.DataFrame:
        """
        주식 OHLC + 거래량 통합 데이터 조회 (수정된 API 엔드포인트 사용)
        
        Args:
            stock_code (str): 종목코드 (6자리)
            days (int): 조회 기간 (일 수, 기본값: 30일)
            
        Returns:
            pd.DataFrame: 날짜, 시가, 고가, 저가, 종가, 거래량, 거래대금 데이터
        """
        # KIS API 문서 참고: inquire-daily-price 엔드포인트 사용
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        headers = self._get_headers("FHKST03010100")  # 국내주식기간별시세(일/주/월/년) TR_ID
        
        # 최근 days일 데이터를 위해 충분한 범위로 설정 (주말, 공휴일 고려)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 10)  # 여유분 추가
        
        params = {
            "fid_cond_mrkt_div_code": "J",  # 시장분류코드 (J: 주식)
            "fid_input_iscd": stock_code,   # 종목코드
            "fid_input_date_1": start_date.strftime("%Y%m%d"),  # 조회시작일자
            "fid_input_date_2": end_date.strftime("%Y%m%d"),    # 조회종료일자
            "fid_period_div_code": "D",     # 기간분류코드 (D: 일봉)
            "fid_org_adj_prc": "0"          # 수정주가원주가가격 (0: 수정주가 반영)
        }
        
        print(f"🔍 차트 API 호출: {stock_code}, {start_date.strftime('%Y%m%d')} ~ {end_date.strftime('%Y%m%d')}")
        print(f"⏰ API 호출 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            print(f"📊 차트 API 응답: rt_cd={result.get('rt_cd')}, msg1={result.get('msg1')}")
            print(f"📋 응답 키들: {list(result.keys())}")
            
            # 응답 데이터의 첫 번째와 마지막 항목의 날짜 확인
            output_data = result.get('output', result.get('output2', []))
            if output_data:
                first_date = output_data[0].get('stck_bsop_date', 'Unknown')
                last_date = output_data[-1].get('stck_bsop_date', 'Unknown') 
                print(f"📅 API 데이터 범위: {first_date} ~ {last_date} (총 {len(output_data)}개)")
            else:
                print("⚠️ API 응답에 데이터가 없음")
            
            if result.get('rt_cd') != '0' and result.get('rt_cd') != '':
                print(f"🔴 API 오류 응답: {result}")
                raise Exception(f"API 호출 실패: {result.get('msg1', 'Unknown error')}")
            
            # output 또는 output2에서 데이터 추출 시도
            output_data = result.get('output', result.get('output2', []))
            
            if not output_data:
                print("⚠️ output 데이터가 비어있음")
                return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume', 'trade_amount'])
            
            print(f"✅ {len(output_data)}개 데이터 포인트 처리 중...")
            
            # 데이터 변환 (필드명이 다를 수 있으므로 여러 패턴 시도)
            combined_data = []
            for item in output_data:
                try:
                    # 가능한 날짜 필드명들
                    date_field = item.get('stck_bsop_date') or item.get('bsop_date') or item.get('date')
                    if date_field:
                        date_obj = datetime.strptime(str(date_field), '%Y%m%d')
                    else:
                        continue
                    
                    # 가능한 OHLC 필드명들
                    open_price = float(item.get('stck_oprc') or item.get('oprc') or item.get('open') or 0)
                    high_price = float(item.get('stck_hgpr') or item.get('hgpr') or item.get('high') or 0)
                    low_price = float(item.get('stck_lwpr') or item.get('lwpr') or item.get('low') or 0)
                    close_price = float(item.get('stck_clpr') or item.get('clpr') or item.get('close') or 0)
                    
                    # 가능한 거래량 필드명들
                    volume = int(item.get('acml_vol') or item.get('vol') or item.get('volume') or 0)
                    trade_amount = int(item.get('acml_tr_pbmn') or item.get('tr_pbmn') or item.get('trade_amount') or volume * close_price)
                    
                    if close_price > 0:  # 유효한 데이터만 추가
                        combined_data.append({
                            'date': date_obj,
                            'open': open_price,
                            'high': high_price,
                            'low': low_price,
                            'close': close_price,
                            'volume': volume,
                            'trade_amount': trade_amount
                        })
                        
                except (ValueError, TypeError) as e:
                    print(f"⚠️ 데이터 파싱 오류 (건너뜀): {e}, 데이터: {item}")
                    continue
            
            if not combined_data:
                print("❌ 파싱된 유효 데이터가 없음")
                return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume', 'trade_amount'])
            
            df = pd.DataFrame(combined_data)
            df = df.sort_values('date', ascending=False).head(days)  # 최신 days개만
            df = df.sort_values('date').reset_index(drop=True)  # 날짜순 정렬
            
            print(f"🎯 최종 차트 DataFrame: {len(df)}개 행")
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"🌐 네트워크 오류: {e}")
            raise Exception(f"주식 데이터 조회 중 오류 발생: {e}")
        except Exception as e:
            print(f"💥 처리 오류: {e}")
            raise Exception(f"데이터 처리 중 오류 발생: {e}")


# 전역 API 인스턴스
_kis_api = None

def get_kis_api() -> KISApi:
    """KIS API 인스턴스 반환 (싱글톤 패턴)"""
    global _kis_api
    if _kis_api is None:
        _kis_api = KISApi()
    return _kis_api


# 편의 함수들
def get_ohlc_data(stock_code: str, days: int = 30) -> pd.DataFrame:
    """
    주식 OHLC 데이터 조회 (편의 함수)
    
    Args:
        stock_code (str): 종목코드 (6자리)
        days (int): 조회 기간 (일 수, 기본값: 30일)
        
    Returns:
        pd.DataFrame: OHLC 데이터
    """
    api = get_kis_api()
    return api.get_stock_ohlc(stock_code, days)


def get_volume_data(stock_code: str, days: int = 30) -> pd.DataFrame:
    """
    주식 거래량 데이터 조회 (편의 함수)
    
    Args:
        stock_code (str): 종목코드 (6자리)
        days (int): 조회 기간 (일 수, 기본값: 30일)
        
    Returns:
        pd.DataFrame: 거래량 데이터
    """
    api = get_kis_api()
    return api.get_stock_volume(stock_code, days)


def get_combined_data(stock_code: str, days: int = 30) -> pd.DataFrame:
    """
    주식 OHLC + 거래량 통합 데이터 조회 (편의 함수)
    
    Args:
        stock_code (str): 종목코드 (6자리)
        days (int): 조회 기간 (일 수, 기본값: 30일)
        
    Returns:
        pd.DataFrame: OHLC + 거래량 통합 데이터
    """
    api = get_kis_api()
    return api.get_stock_data_combined(stock_code, days)


def get_current_price_data(stock_code: str) -> Dict[str, Any]:
    """
    종목 현재가 및 등락률 조회 (편의 함수)
    
    Args:
        stock_code (str): 종목코드 (6자리)
        
    Returns:
        Dict: 현재가, 등락률, 등락금액 등의 정보
    """
    api = get_kis_api()
    return api.get_current_price(stock_code)


if __name__ == "__main__":
    # 테스트 코드
    try:
        # 삼성전자 (005930) 30일 데이터 조회 테스트
        stock_code = "005930"
        days = 30
        
        print(f"=== {stock_code} {days}일 데이터 조회 테스트 ===")
        
        # OHLC 데이터 조회
        print("\n1. OHLC 데이터 조회:")
        ohlc_df = get_ohlc_data(stock_code, days)
        print(ohlc_df.head())
        print(f"총 {len(ohlc_df)}일 데이터 조회됨")
        
        # 거래량 데이터 조회
        print("\n2. 거래량 데이터 조회:")
        volume_df = get_volume_data(stock_code, days)
        print(volume_df.head())
        print(f"총 {len(volume_df)}일 데이터 조회됨")
        
        # 통합 데이터 조회
        print("\n3. 통합 데이터 조회:")
        combined_df = get_combined_data(stock_code, days)
        print(combined_df.head())
        print(f"총 {len(combined_df)}일 데이터 조회됨")
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")