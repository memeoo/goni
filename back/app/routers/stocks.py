from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import sys
import os
import pandas as pd

# analyze 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..', 'analyze'))

from app.database import get_database
from app import schemas
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[schemas.Stock])
async def get_stocks(
    skip: int = 0, 
    limit: int = 100
):
    """주식 목록 조회"""
    # 실제 구현에서는 데이터베이스에서 주식 정보 조회
    # 주요 종목들의 실시간 데이터를 반환
    major_stocks = [
        {"id": 1, "symbol": "005930", "name": "삼성전자", "market": "KOSPI"},
        {"id": 2, "symbol": "035420", "name": "NAVER", "market": "KOSPI"},
        {"id": 3, "symbol": "000660", "name": "SK하이닉스", "market": "KOSPI"},
        {"id": 4, "symbol": "207940", "name": "삼성바이오로직스", "market": "KOSPI"},
        {"id": 5, "symbol": "051910", "name": "LG화학", "market": "KOSPI"},
    ]
    
    # 각 종목의 실시간 가격 정보 조회 (실제 KIS API만 사용)
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..', 'analyze'))
    
    try:
        from lib.hantu import get_current_price_data
    except ImportError:
        raise HTTPException(status_code=500, detail="KIS API 모듈을 불러올 수 없습니다.")
    
    result = []
    failed_stocks = []
    
    for stock_info in major_stocks:
        try:
            # 실제 현재가 데이터 조회
            price_data = get_current_price_data(stock_info["symbol"])
            result.append({
                "id": stock_info["id"],
                "symbol": stock_info["symbol"],
                "name": stock_info["name"],
                "market": stock_info["market"],
                "current_price": price_data["current_price"],
                "change_rate": price_data["change_rate"],
                "change_price": price_data.get("change_price", 0),
                "volume": price_data["volume"],
                "updated_at": price_data["updated_at"]
            })
        except Exception as e:
            print(f"주식 {stock_info['symbol']} 현재가 조회 실패: {e}")
            failed_stocks.append(stock_info['symbol'])
    
    # 모든 종목이 실패한 경우 오류 반환
    if not result:
        raise HTTPException(status_code=500, detail="모든 종목의 데이터 조회가 실패했습니다.")
    
    # 일부 종목이 실패한 경우 성공한 종목만 반환
    if failed_stocks:
        print(f"⚠️ 실패한 종목들: {', '.join(failed_stocks)}")
    
    return result


@router.get("/{stock_id}", response_model=schemas.Stock)
async def get_stock(
    stock_id: int,
    current_user: schemas.TokenData = Depends(get_current_user),
    db = Depends(get_database)
):
    """특정 주식 정보 조회"""
    # 실제 구현에서는 데이터베이스에서 특정 주식 정보 조회
    return {
        "id": stock_id,
        "symbol": "005930",
        "name": "삼성전자",
        "market": "KOSPI",
        "current_price": 70000,
        "change_rate": 1.5,
        "volume": 1000000,
        "updated_at": "2024-01-01T00:00:00"
    }


@router.post("/", response_model=schemas.Stock)
async def create_stock(
    stock: schemas.StockCreate,
    current_user: schemas.TokenData = Depends(get_current_user),
    db = Depends(get_database)
):
    """새 주식 정보 생성"""
    # 실제 구현에서는 데이터베이스에 주식 정보 저장
    return {"message": "Stock creation endpoint - implementation needed"}


@router.put("/{stock_id}", response_model=schemas.Stock)
async def update_stock(
    stock_id: int,
    stock: schemas.StockCreate,
    current_user: schemas.TokenData = Depends(get_current_user),
    db = Depends(get_database)
):
    """주식 정보 업데이트"""
    # 실제 구현에서는 데이터베이스의 주식 정보 업데이트
    return {"message": "Stock update endpoint - implementation needed"}


@router.get("/{stock_code}/chart-data")
async def get_stock_chart_data(
    stock_code: str,
    days: int = 25
) -> Dict[str, Any]:
    """
    주식 차트 데이터 조회 (OHLC + 거래량 + 이동평균선)
    
    Args:
        stock_code (str): 종목코드 (6자리)
        days (int): 화면 표시 기간 (기본값: 25일)
        
    Returns:
        Dict: 차트 데이터 (OHLC, 거래량, 이동평균선)
    """
    try:
        # .env 파일 경로 설정
        import os
        from dotenv import load_dotenv
        analyze_env_path = os.path.join(os.path.dirname(__file__), '../../../analyze/.env')
        load_dotenv(analyze_env_path)
        
        try:
            # hantu.py 모듈 import 및 실제 데이터 조회
            from lib.hantu import get_combined_data
            print(f"🔍 KIS API 호출 시작: {stock_code}, {days}일")
            df = get_combined_data(stock_code, days)
            
            if df.empty:
                print(f"❌ KIS API 응답이 비어있음: {stock_code}")
                raise HTTPException(status_code=500, detail=f"종목 {stock_code}의 차트 데이터를 조회할 수 없습니다.")
            else:
                print(f"✅ KIS API 실제 데이터 사용: {stock_code}, {len(df)}개 행")
                
        except HTTPException:
            raise  # HTTPException은 그대로 전달
        except Exception as api_error:
            # API 오류 시 에러 반환
            print(f"❌ KIS API 오류: {api_error}")
            raise HTTPException(status_code=500, detail=f"차트 데이터 조회 중 API 오류가 발생했습니다: {str(api_error)}")
        
        # 거래량 변화 계산 (전일 대비)
        df['volume_change'] = df['volume'].pct_change()
        
        # JSON 직렬화를 위해 데이터 변환
        chart_data = []
        for _, row in df.iterrows():
            chart_data.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume']),
                'trade_amount': int(row['trade_amount']),
                'volume_change': float(row['volume_change']) if not pd.isna(row['volume_change']) else None
            })
        
        return {
            "stock_code": stock_code,
            "days": days,
            "data": chart_data,
            "total_records": len(chart_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"차트 데이터 조회 중 오류가 발생했습니다: {str(e)}")


# Mock 데이터 함수 제거 - 실제 KIS API만 사용


@router.get("/{stock_code}/ohlc")
async def get_stock_ohlc(
    stock_code: str,
    days: int = 60
) -> Dict[str, Any]:
    """
    주식 OHLC 데이터만 조회
    
    Args:
        stock_code (str): 종목코드 (6자리)
        days (int): 조회 기간 (기본값: 60일)
        
    Returns:
        Dict: OHLC 데이터
    """
    try:
        from lib.hantu import get_ohlc_data
        
        df = get_ohlc_data(stock_code, days)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="OHLC 데이터를 찾을 수 없습니다")
        
        ohlc_data = []
        for _, row in df.iterrows():
            ohlc_data.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close'])
            })
        
        return {
            "stock_code": stock_code,
            "days": days,
            "data": ohlc_data,
            "total_records": len(ohlc_data)
        }
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"한국투자증권 API 모듈을 불러올 수 없습니다: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OHLC 데이터 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/{stock_code}/volume")
async def get_stock_volume(
    stock_code: str,
    days: int = 60
) -> Dict[str, Any]:
    """
    주식 거래량 데이터만 조회
    
    Args:
        stock_code (str): 종목코드 (6자리)
        days (int): 조회 기간 (기본값: 60일)
        
    Returns:
        Dict: 거래량 데이터
    """
    try:
        from lib.hantu import get_volume_data
        
        df = get_volume_data(stock_code, days)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="거래량 데이터를 찾을 수 없습니다")
        
        # 거래량 변화 계산
        df['volume_change'] = df['volume'].pct_change()
        
        volume_data = []
        for _, row in df.iterrows():
            volume_data.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'volume': int(row['volume']),
                'trade_amount': int(row['trade_amount']),
                'volume_change': float(row['volume_change']) if not pd.isna(row['volume_change']) else None
            })
        
        return {
            "stock_code": stock_code,
            "days": days,
            "data": volume_data,
            "total_records": len(volume_data)
        }
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"한국투자증권 API 모듈을 불러올 수 없습니다: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"거래량 데이터 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/{stock_code}/current-price")
async def get_stock_current_price(
    stock_code: str
) -> Dict[str, Any]:
    """
    종목 현재가 및 등락률 조회
    
    Args:
        stock_code (str): 종목코드 (6자리)
        
    Returns:
        Dict: 현재가, 등락률, 등락금액 등의 정보
    """
    try:
        # .env 파일 경로 설정
        import os
        from dotenv import load_dotenv
        analyze_env_path = os.path.join(os.path.dirname(__file__), '../../../analyze/.env')
        load_dotenv(analyze_env_path)
        
        try:
            # hantu.py 모듈 import 및 실제 데이터 조회
            from lib.hantu import get_current_price_data
            price_data = get_current_price_data(stock_code)
            
            return price_data
                
        except Exception as api_error:
            # API 오류 시 에러 반환
            print(f"❌ KIS API 오류: {api_error}")
            raise HTTPException(status_code=500, detail=f"종목 {stock_code}의 현재가 조회 중 API 오류가 발생했습니다: {str(api_error)}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"현재가 조회 중 오류가 발생했습니다: {str(e)}")


# Mock 현재가 함수도 제거 - 실제 KIS API만 사용


@router.get("/{stock_code}/foreign-institutional")
async def get_stock_foreign_institutional_data(
    stock_code: str
) -> Dict[str, Any]:
    """
    종목 외국인·기관 순매매 데이터 조회 (네이버 금융 크롤링)
    
    Args:
        stock_code (str): 종목코드 (6자리)
        
    Returns:
        Dict: 외국인·기관 순매매 데이터
        {
            'stock_code': '005930',
            'stock_name': '삼성전자',
            'date': '2024-12-20',
            'institutional_net': 12345,
            'foreign_net': -6789,
            'individual_net': -5556
        }
    """
    try:
        # .env 파일 경로 설정
        import os
        from dotenv import load_dotenv
        analyze_env_path = os.path.join(os.path.dirname(__file__), '../../../analyze/.env')
        load_dotenv(analyze_env_path)
        
        try:
            # naver.py 모듈 import 및 크롤링
            from lib.naver import get_foreign_institutional_data
            print(f"📊 외국인·기관 수급 데이터 조회 시작: {stock_code}")
            
            fi_data = get_foreign_institutional_data(stock_code)
            print(f"📊 크롤링 결과: {fi_data}")
            
            if 'error' in fi_data:
                print(f"❌ 크롤링 오류: {fi_data['error']}")
                raise HTTPException(status_code=500, detail=f"외국인·기관 데이터 크롤링 실패: {fi_data['error']}")
            
            print(f"✅ 외국인·기관 수급 데이터 조회 완료: {stock_code}")
            return fi_data
                
        except ImportError as import_error:
            print(f"❌ 모듈 import 오류: {import_error}")
            raise HTTPException(status_code=500, detail=f"네이버 크롤링 모듈을 불러올 수 없습니다: {str(import_error)}")
        except HTTPException:
            raise  # HTTPException은 그대로 전달
        except Exception as api_error:
            # 크롤링 오류 시 에러 반환
            print(f"❌ 네이버 금융 크롤링 오류: {api_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"종목 {stock_code}의 외국인·기관 순매매 데이터 조회 중 오류가 발생했습니다: {str(api_error)}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"외국인·기관 순매매 데이터 조회 중 오류가 발생했습니다: {str(e)}")