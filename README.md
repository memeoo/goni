# Goni - 주식 매매 계획 및 복기 일지

타짜급 트레이더로 성장하기 위한 매매 계획 수립과 복기 시스템

## 프로젝트 구조

```
goni/
├── back/           # FastAPI 백엔드
├── front/          # Next.js 15 프론트엔드  
├── analyze/        # Python 3.13 분석 서비스
├── init.sql
└── README.md
```

## 기술 스택

- **백엔드**: FastAPI (latest)
- **프론트엔드**: Next.js 15+
- **분석**: Python 3.13
- **데이터베이스**: PostgreSQL

## 주요 기능

### 1. 실시간 모니터링
- 관심 종목 차트, 수급, 뉴스 모니터링
- 실시간 가격 알림
- 시장 지수 추적

### 2. 매매 계획
- 체계적인 진입/청산 계획 수립
- 리스크 관리 도구
- 목표가 및 손절가 설정

### 3. 매매 복기
- 실행 결과 기록
- 수익/손실 분석
- 개선점 도출

### 4. 기술적 분석
- RSI, MACD, 볼린저 밴드
- 이동평균선 분석
- 지지/저항선 계산

### 5. 뉴스 감정 분석
- 종목별 뉴스 수집
- 감정 점수 계산
- 시장 분위기 분석

## 시작하기

### 1. 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd goni

# 환경 변수 설정
cp back/.env.example back/.env
cp front/.env.example front/.env
cp analyze/.env.example analyze/.env
```

### 3. 개발 환경에서 실행

#### 백엔드 (FastAPI)
```bash
cd back
pip install -r requirements.txt
uvicorn main:app --reload
```

#### 프론트엔드 (Next.js)
```bash
cd front
npm install
npm run dev
```

#### 분석 서비스 (Python)
```bash
cd analyze
pip install -r requirements.txt
python main.py
```

## 서비스 접속

- **웹 애플리케이션**: http://localhost:3000
- **API 문서**: http://localhost:8000/docs

## 데이터베이스

### 접속 정보
- Host: localhost
- Port: 5432
- Database: goni
- User: goniadmin
- Password: shsbsy70

### 주요 테이블
- `users`: 사용자 정보
- `stocks`: 주식 종목 정보
- `trading_plans`: 매매 계획 및 복기

## ADDED or MODIFIED

### 2025-11-01: 복기 대시보드 데이터 소스 변경 (키움 API → Trading DB)

#### 1. 매매 내역 조회 API 변경 (back/app/routers/trading_plans.py)
- **파일**: `back/app/routers/trading_plans.py`
- **엔드포인트**: `GET /api/trading-plans/trades/recent`
- **변경 사항**:
  - **이전**: 키움증권 API에서 실시간으로 매매 기록 조회
  - **현재**: Trading 테이블(DB)에서 최근 매매 기록 조회
  - **장점**:
    - 더 빠른 응답 속도 (API 호출 제거)
    - 안정적인 데이터 제공 (키움 API 오류 영향 없음)
    - 사용자별 동기화된 데이터만 표시

- **매개변수**: `limit` (기본값: 20건)
- **동작**:
  1. 현재 사용자의 Trading 테이블에서 최신순으로 조회
  2. 최신순 20개 기록 반환
  3. 각 기록별 복기 완료 여부 확인
  4. 프론트 호환성을 위해 데이터 포맷 변환:
     - trade_type: 'buy' → '매수', 'sell' → '매도'
     - executed_at (datetime) → datetime (YYYYMMDDHHmmss)

- **응답 포맷** (기존 형식 유지):
  ```json
  {
    "limit": 20,
    "data": [
      {
        "stock_code": "005930",
        "stock_name": "삼성전자",
        "trade_type": "매수",
        "price": 70500,
        "quantity": 10,
        "datetime": "20251101143000",
        "order_no": "12345678",
        "has_recap": false
      }
    ],
    "total_records": 1
  }
  ```

#### 2. 프론트엔드 API 호출 변경 (front/src/lib/api.ts)
- **파일**: `front/src/lib/api.ts`
- **함수**: `tradingPlansAPI.getRecentTrades(limit = 20)`
- 쿼리 파라미터: `limit=20` (이전: `days=10`)

#### 3. 대시보드 페이지 수정 (front/src/app/dashboard/page.tsx)
- **파일**: `front/src/app/dashboard/page.tsx`
- **변경 사항**:
  - fetchRecentTrades 함수에서 `getRecentTrades(20)` 호출 (이전: 10)
  - 주석 업데이트: "Trading DB에서 조회"로 명시

**동작 흐름**:
1. 대시보드 복기 모드 진입
2. `GET /api/trading-plans/trades/recent?limit=20` 호출
3. Trading 테이블에서 최신순 20개 기록 조회
4. 포맷팅하여 프론트로 반환
5. 복기 모드 그리드에 표시

### 2025-11-01: 로그인 후 매매 기록 자동 동기화 기능 추가

#### 1. 매매 기록 동기화 API 엔드포인트 추가 (back/app/routers/trading_plans.py)
- **파일**: `back/app/routers/trading_plans.py`
- **새로운 엔드포인트**: `POST /api/trading-plans/trades/sync`
  - 키움증권 Open API를 통해 최근 거래 기록 조회
  - Trading 테이블에 새로운 기록만 추가 (중복 체크: order_no 기반)
  - 쿼리 파라미터: `limit` (기본값: 20건) - 최근 순서로 20개 거래 기록 조회
  - 응답 포맷:
    ```json
    {
      "status": "success",
      "message": "3건의 새로운 매매기록이 추가되었습니다.",
      "synced_count": 3,
      "duplicate_count": 2,
      "total_count": 5
    }
    ```

#### 2. 동기화 기능 상세 설명
- **중복 체크**: order_no 기반으로 기존 기록 확인
  - order_no가 이미 존재하면 스킵 (새로 추가하지 않음)
  - order_no가 없는 기록도 처리 가능
- **데이터 변환**:
  - 날짜/시간: YYYYMMDDHHmmss → datetime 형식
  - 매매구분: "매수" → "buy", "매도" → "sell"
  - 체결금액 자동 계산: 가격 × 수량
- **에러 처리**:
  - 개별 레코드 오류 발생 시 해당 기록만 스킵, 나머지는 계속 처리
  - 전체 동기화 실패 시 롤백 처리
  - 키움 API 미설정 시 경고 반환

#### 3. 프론트엔드 API 함수 추가 (front/src/lib/api.ts)
- **파일**: `front/src/lib/api.ts`
- **새 함수**: `tradingPlansAPI.syncRecentTrades(limit = 20)`
  - POST `/api/trading-plans/trades/sync` 호출

#### 4. 대시보드 자동 동기화 (front/src/app/dashboard/page.tsx)
- **파일**: `front/src/app/dashboard/page.tsx`
- **변경 사항**:
  - useEffect 훅에서 대시보드 진입 시 자동으로 `syncRecentTrades` 호출
  - 로그인 후 처음 대시보드에 진입할 때만 수행
  - 동기화 실패 시 콘솔 로그만 출력, 대시보드는 정상 진행

**동작 흐름**:
1. 사용자 로그인
2. 대시보드 페이지 이동
3. 자동으로 `/api/trading-plans/trades/sync` 호출 (기본값: 최근 20개 거래 기록)
4. 키움증권 API에서 최근 30일 매매 기록 조회 후 최신순 20개만 선택
5. 새로운 기록만 Trading 테이블에 추가
6. 기존 기록(order_no 기반)은 업데이트하지 않음

### 2025-11-01: Trading 테이블 및 API 엔드포인트 추가

#### 1. Trading 모델 추가 (back/app/models.py)
- **파일**: `back/app/models.py`
- **새 모델**: `Trading` 클래스
  - `id`: 기본 키
  - `user_id`: 사용자 외래키 (인덱싱)
  - `executed_at`: 체결 시각 (DateTime, 인덱싱)
  - `trade_type`: 매매구분 ('buy' or 'sell')
  - `order_no`: 주문번호 (인덱싱)
  - `stock_name`: 종목명
  - `stock_code`: 종목코드 (인덱싱)
  - `executed_price`: 체결 가격
  - `executed_quantity`: 체결 수량
  - `executed_amount`: 체결 금액 (BigInteger)
  - `broker`: 증권사 (ex: 'kiwoom', 'kis')
  - `created_at`, `updated_at`: 시스템 타임스탬프

#### 2. Trading 스키마 추가 (back/app/schemas.py)
- **파일**: `back/app/schemas.py`
- **새 스키마**:
  - `TradingBase`: 기본 필드 정의
  - `TradingCreate`: 생성용 스키마
  - `Trading`: 조회용 스키마 (id, user_id, created_at, updated_at 포함)

#### 3. Trading API 라우터 생성 (back/app/routers/trading.py)
- **파일**: `back/app/routers/trading.py` (신규)
- **엔드포인트**:
  - `POST /api/trading/`: 매매 기록 생성
  - `GET /api/trading/`: 매매 기록 조회 (페이징, 필터링 지원)
    - 쿼리 파라미터: limit, offset, trade_type, stock_code, start_date, end_date
  - `GET /api/trading/{trading_id}`: 특정 매매 기록 조회
  - `PUT /api/trading/{trading_id}`: 매매 기록 수정
  - `DELETE /api/trading/{trading_id}`: 매매 기록 삭제
  - `GET /api/trading/stats/summary`: 매매 통계 요약
    - 총 거래 수, 매수/매도 거래 수, 총 거래 금액

#### 4. 라우터 등록 (back/main.py)
- **파일**: `back/main.py`
- **변경 사항**:
  - trading 라우터 import 추가
  - `app.include_router(trading.router)` 추가

**사용 예시**:
```bash
# 매매 기록 생성
curl -X POST http://localhost:8000/api/trading/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "executed_at": "2025-11-01T14:30:00",
    "trade_type": "buy",
    "order_no": "12345678",
    "stock_name": "삼성전자",
    "stock_code": "005930",
    "executed_price": 70500,
    "executed_quantity": 10,
    "executed_amount": 705000,
    "broker": "kiwoom"
  }'

# 매매 기록 조회 (최신순)
curl -X GET "http://localhost:8000/api/trading/?limit=20&offset=0" \
  -H "Authorization: Bearer {token}"

# 특정 기간의 매매 기록 조회
curl -X GET "http://localhost:8000/api/trading/?start_date=2025-11-01T00:00:00&end_date=2025-11-01T23:59:59" \
  -H "Authorization: Bearer {token}"

# 매매 통계 조회
curl -X GET "http://localhost:8000/api/trading/stats/summary" \
  -H "Authorization: Bearer {token}"
```

### 2025-11-01: 프론트엔드 포트 설정 정리 (3000: 운영, 3001: 개발)

#### 1. Package.json 수정 (front/package.json)
- **파일**: `front/package.json`
- **변경 사항**:
  - `start` 스크립트에 포트 명시: `"start": "next start -p 3000"`
  - 이제 `npm start`를 실행하면 자동으로 포트 3000에서 시작

#### 2. Ecosystem.config.js 수정 (ecosystem.config.js)
- **파일**: `ecosystem.config.js`
- **변경 사항**:
  - PM2 `goni-frontend` 프로세스 설정 간소화
  - `args: 'start'` (포트는 package.json에서 관리)
  - NODE_ENV: production 유지

#### 3. CLAUDE.md 업데이트 (CLAUDE.md)
- **파일**: `CLAUDE.md`
- **추가 섹션**: `# Port Configuration`
  - 포트 3000 (운영/Production): PM2 `goni-frontend` 실행
  - 포트 3001 (개발/Development): `npm run dev` 명령으로 개발 서버 실행

#### 4. daily-chart.tsx 타입 에러 수정 (front/src/components/daily-chart.tsx)
- **파일**: `front/src/components/daily-chart.tsx`
- **변경 사항**:
  - `datetimeStr?.toString()` → `String(datetimeStr)` (2개 위치)
  - TypeScript 타입 에러 해결 (never 타입 에러)

**설정 완료**:
- 포트 3000: 운영 환경 (PM2 프로세스, 빌드된 Next.js)
- 포트 3001: 개발 환경 (npm run dev, 핫 리로드)

### 2025-10-31: 복기 모달에서 차트 Buy/Sell 마커 클릭 시 입력 필드 자동 포커스 기능 추가

#### 1. DailyChart 컴포넌트 개선 (front/src/components/daily-chart.tsx)
- **파일**: `front/src/components/daily-chart.tsx`
- **변경 사항**:
  - `onMarkerClick` 콜백 props 추가
  - 차트 캔버스에 `onClick` 이벤트 핸들러 추가
  - `handleCanvasClick` 함수 구현:
    - 클릭 위치의 마커(Buy/Sell) 감지
    - 원형 마커 영역 내 클릭 판정 (반지름 10px)
    - 스케일 변환을 고려한 정확한 좌표 계산
    - 클릭된 마커의 거래 정보를 콜백으로 전달

#### 2. RecapModal 컴포넌트 개선 (front/src/components/recap-modal.tsx)
- **파일**: `front/src/components/recap-modal.tsx`
- **변경 사항**:
  - `useRef` import 추가
  - 텍스트 입력 필드에 대한 useRef 생성:
    - `priceChartRef`: "가격(차트)" 필드 참조
    - `volumeRef`: "거래량" 필드 참조
  - `handleMarkerClick` 함수 구현:
    - Buy(매수) 클릭 시:
      - "가격(차트)" 필드로 자동 포커스
      - 해당 필드로 부드러운 스크롤 (smooth scroll)
    - Sell(매도) 클릭 시:
      - "거래량" 필드로 자동 포커스
      - 해당 필드로 부드러운 스크롤
  - DailyChart 컴포넌트에 `onMarkerClick={handleMarkerClick}` 콜백 전달

**기능**:
- 차트에서 Buy/Sell 마커 클릭 시 관련 입력 필드로 자동 네비게이션
- 사용자 편의성 향상: 마커 클릭으로 바로 입력 가능
- 부드러운 스크롤로 시각적 피드백 제공

### 2025-10-31: 프로필 페이지에 APP KEY/SECRET 마스킹 기능 추가

#### 1. 프로필 페이지 개선 (front/src/app/profile/page.tsx)
- **파일**: `front/src/app/profile/page.tsx`
- **변경 사항**:
  - `maskString()` 함수 추가: 문자열을 입력된 문자 개수만큼 * 로 마스킹
  - APP KEY 입력 필드 개선:
    - 기본값으로 마스킹된 상태 표시 (예: 40자 키 → ****************************************)
    - 눈(Eye) 아이콘 클릭으로 실제 값과 마스킹 상태 전환
    - 값이 등록되어 있지 않으면 눈 아이콘 미표시
  - APP SECRET 입력 필드 개선:
    - APP KEY와 동일한 마스킹 로직 적용
    - 눈 아이콘 클릭으로 보이기/숨기기 토글
    - 등록된 값이 있을 때만 눈 아이콘 표시
  - 사용성 향상:
    - 빈 입력 필드에는 플레이스홀더 표시
    - 값이 있는 경우 플레이스홀더 숨김 (마스킹 텍스트와의 혼동 방지)
    - 눈 아이콘에 title 속성 추가 (호버 시 "표시"/"숨기기" 표시)

**기능**:
- DB에 등록되어 있는 APP KEY와 APP SECRET이 정상적으로 저장되어 있음을 사용자에게 알림
- 비밀번호 입력 필드처럼 기본값으로 마스킹 처리되어 보안 강화
- 필요시 눈 아이콘으로 실제 값 확인 가능

### 2025-10-25: 복기 모달에 일봉 차트 시각화 추가

#### 1. DailyChart 컴포넌트 개발 (front/src/components/daily-chart.tsx)
- **파일**: `front/src/components/daily-chart.tsx` (신규)
- **기능**:
  - Canvas API를 사용한 고성능 차트 렌더링
  - 최근 50일 일봉 캔들스틱 차트 표시
    - 양봉: 빨간색 (#ff4444), 음봉: 파란색 (#4444ff)
    - 심지(High-Low)와 몸통(Open-Close) 렌더링
  - 거래량 바 차트 (일봉 차트 아래)
    - 양봉 색상은 빨강, 음봉 색상은 파랑
  - 가격 축 (오른쪽):
    - 최저가에서 10% 낮은 값부터 최고가에서 10% 높은 값까지
    - 5등분하여 표시 (최소값, 최대값 포함)
  - 거래량 축 (오른쪽):
    - 0부터 최대 거래량까지 5등분
    - 1000단위는 'K', 백만 단위는 'M'으로 표시
  - X축 (날짜):
    - 5일 단위로 표시 (월/일 형식, 년도 제외)
  - 높이 비율: 가격 차트 330px : 거래량 차트 100px (약 3.3:1)

#### 2. RecapModal 컴포넌트 개선 (front/src/components/recap-modal.tsx)
- **파일**: `front/src/components/recap-modal.tsx`
- **변경 사항**:
  - DailyChart 컴포넌트 임포트 및 통합
  - stockCode prop 추가
  - 일봉 차트 데이터 조회 useQuery 추가:
    - 엔드포인트: `/api/stocks/{stock_code}/daily-chart`
    - 주식 선택 시 자동으로 50일간의 일봉 데이터 로딩
  - 모달 내 차트 배치:
    - 모달 상단에 일봉 차트 표시
    - 입력 필드는 차트 아래에 배치
  - 차트 로딩 상태 표시

#### 3. Dashboard 페이지 수정 (front/src/app/dashboard/page.tsx)
- **파일**: `front/src/app/dashboard/page.tsx`
- **변경 사항**:
  - selectedStockCode 상태 추가
  - handleStockCardClick에서 stockCode 저장
  - RecapModal에 stockCode prop 전달

#### 4. API 스키마 추가 (back/app/schemas.py)
- **파일**: `back/app/schemas.py`
- **추가 스키마**:
  - ChartDataPoint: 일봉 차트 데이터 포인트
  - DailyChartResponse: 일봉 차트 조회 응답

### 2025-10-25: 키움증권 API ka10081을 이용한 일봉 차트 조회 기능 추가

#### 1. KiwoomAPI 클래스 확장 (analyze/lib/kiwoom.py)
- **파일**: `analyze/lib/kiwoom.py`
- **추가된 메서드**: `get_daily_chart()`
  - 키움증권 Open REST API ka10081 TR 사용
  - 주식 일봉 차트 데이터 조회 (OHLC, 거래량, 거래대금)
  - 파라미터:
    - `stock_code` (str): 종목코드 (6자리, 예: '005930')
    - `base_dt` (str): 기준일자 YYYYMMDD (공백: 금일데이터)
    - `upd_stkpc_tp` (str): 수정주가구분 ('0': 미수정, '1': 수정, 기본값: '1')
  - 반환 데이터: 일봉 차트 데이터 리스트

#### 2. 백엔드 API 엔드포인트 추가 (back/app/routers/stocks.py)
- **파일**: `back/app/routers/stocks.py`
- **새로운 엔드포인트**: `GET /api/stocks/{stock_code}/daily-chart`
  - 쿼리 파라미터:
    - `stock_code`: 종목코드 (필수)
    - `base_dt`: 기준일자 (선택, 기본값: 금일)
    - `upd_stkpc_tp`: 수정주가구분 (선택, 기본값: '1')
  - 응답 포맷:
    ```json
    {
      "stock_code": "005930",
      "data": [
        {
          "date": "2025-09-08",
          "open": 69800,
          "high": 70500,
          "low": 69600,
          "close": 70100,
          "volume": 9263135,
          "trade_amount": 648525
        },
        ...
      ],
      "total_records": 100
    }
    ```
  - 기능:
    - 환경변수에서 키움증권 API 자격증명 자동 로드
    - 키움증권 API 호출 및 에러 처리
    - 응답 데이터 포맷 변환 (YYYYMMDD -> YYYY-MM-DD, 문자열 -> 숫자)
    - 상세 로깅 및 디버깅 정보 제공

#### 3. 환경변수 설정 필요
- `KIWOOM_APP_KEY`: 키움증권 앱 키
- `KIWOOM_SECRET_KEY`: 키움증권 시크릿 키
- `KIWOOM_ACCOUNT_NO`: 키움증권 계좌번호
- `KIWOOM_USE_MOCK`: 모의투자 여부 (True/False, 기본값: False)

### 2025-10-25: 복기 모달 UI 레이아웃 개선

#### 복기 상세 팝업 (recap-modal.tsx)
- **파일**: `front/src/components/recap-modal.tsx`
- **변경 사항**:
  - 모달 폭을 전체 화면의 80%로 확장 (`w-[80%]`)
  - 마진 및 불필요한 제약 제거로 최적 레이아웃 구현
  - 입력 필드를 2열 그리드로 재배치하여 한 행에 2개씩 배치:
    - Row 1: 재료 & 시황
    - Row 2: 가격(차트) & 거래량
    - Row 3: 수급(외국인/기관) & 심리(매매 당시의 감정)
    - Row 4: 평가 (라디오 버튼, 전체 폭)
    - Row 5: 평가이유 & 기타(자유 기술)
  - 더 나은 공간 활용과 시각적 일관성 제공

### 2025-10-22: 프로젝트 초기 구축 완료

#### 1. 백엔드 (FastAPI) - 완전 구현

##### 인증 시스템 (`/api/auth`)
- **파일**: `back/app/routers/auth.py`
- **기능**:
  - `POST /api/auth/token`: OAuth2 폼 기반 로그인
  - `POST /api/auth/login`: JSON 기반 로그인
  - `POST /api/auth/register`: 회원가입 (이메일/사용자명 중복 검사)
  - `GET /api/auth/me`: 현재 사용자 프로필 조회
  - `PUT /api/auth/update-kiwoom`: 키움증권 API 인증정보 업데이트
- **보안**: JWT 토큰 (HS256 알고리즘), bcrypt 비밀번호 해싱, 8시간 토큰 만료

##### 주식 데이터 API (`/api/stocks`)
- **파일**: `back/app/routers/stocks.py`
- **데이터 소스**: KIS API (한국투자증권), Naver Finance (웹 스크래핑)
- **엔드포인트**:
  - `GET /api/stocks/`: 주요 종목 목록 및 실시간 가격 조회
  - `GET /api/stocks/{stock_code}/chart-data`: OHLC + 거래량 + 이동평균선 (60일)
  - `GET /api/stocks/{stock_code}/ohlc`: OHLC 데이터
  - `GET /api/stocks/{stock_code}/volume`: 거래량 데이터 (전일 대비 변화율 포함)
  - `GET /api/stocks/{stock_code}/current-price`: 현재가 및 변동률
  - `GET /api/stocks/{stock_code}/foreign-institutional`: 외국인/기관 수급 정보
- **통합 모듈**: `analyze/lib/hantu.py` (KIS API), `analyze/lib/naver.py` (네이버 증권)

##### 매매 내역 API (`/api/trading-plans`)
- **파일**: `back/app/routers/trading_plans.py`
- **구현 완료**:
  - `GET /api/trading-plans/trades/recent`: 키움증권 API를 통한 최근 실제 매매 내역 조회 (10일)
    - Mock/실제 거래 지원
    - 사용자별 키움 API 인증정보 사용
    - 반환 데이터: 종목코드, 종목명, 매수/매도, 체결가, 수량, 체결시각, 주문번호, 복기 작성 여부
- **통합 모듈**: `analyze/lib/kiwoom.py`
- **미구현**: CRUD 엔드포인트는 스텁 상태

##### 복기(Recap) API (`/api/recap`)
- **파일**: `back/app/routers/recap.py`
- **완전 구현**:
  - `POST /api/recap/`: 복기 생성 (trading_plan_id 또는 order_no 지원)
  - `GET /api/recap/{trading_plan_id}`: 매매 계획 ID로 복기 조회
  - `GET /api/recap/by-order/{order_no}`: 주문번호로 복기 조회
  - `GET /api/recap/`: 사용자의 전체 복기 목록 (페이징 지원)
  - `PUT /api/recap/{trading_plan_id}`: 복기 수정
  - `PUT /api/recap/by-order/{order_no}`: 주문번호 기반 복기 수정
  - `DELETE /api/recap/{trading_plan_id}`: 복기 삭제

##### 데이터베이스 모델
- **파일**: `back/app/models.py`
- **테이블**:
  - `users`: 사용자 정보 (JWT 인증, 키움 API 인증정보 저장)
  - `stocks`: 종목 정보 (종목코드, 종목명, 시장구분, 가격정보)
  - `trading_plans`: 매매 계획 및 실행 기록
  - `recap`: 상세 매매 복기 데이터 (재료, 시황, 차트, 거래량, 수급, 심리, 평가 등)

#### 2. 프론트엔드 (Next.js 15) - 핵심 기능 구현

##### 페이지
- **파일 위치**: `front/src/app/`
- **구현 완료**:
  - `/page.tsx`: 홈 (로그인 상태에 따라 /dashboard 또는 /login으로 리다이렉트)
  - `/login/page.tsx`: 로그인 (Zod 유효성 검사, 비밀번호 표시/숨김 토글)
  - `/register/page.tsx`: 회원가입 (이메일/사용자명/비밀번호 검증, 비밀번호 확인)
  - `/dashboard/page.tsx`: 메인 대시보드
    - **계획 모드**: 관심 종목 모니터링 (미구현)
    - **복기 모드**: 최근 매매 내역 표시 및 복기 작성 (구현 완료)
    - 4열 그리드 레이아웃 (반응형)
    - React Query 기반 데이터 페칭 (자동 갱신: 복기 모드 5분)
    - 로딩/에러 상태 처리
  - `/profile/page.tsx`: 사용자 프로필 및 설정
    - 이메일/사용자명 표시 (읽기 전용)
    - 키움증권 API 인증정보 입력 및 저장
    - 비밀번호 가시성 토글

##### 컴포넌트
- **파일 위치**: `front/src/components/`
- **구현 완료**:
  - `header.tsx`: 헤더 (앱 타이틀, 계획/복기 모드 토글, 날짜, 프로필, 로그아웃 버튼)
  - `trade-card.tsx`: 매매 내역 카드
    - 종목명, 종목코드, 매수/매도 표시 (색상 구분)
    - 체결가, 수량, 거래금액, 체결시각
    - 복기 완료 여부 표시 (초록색 테두리 + 체크마크)
  - `recap-modal.tsx`: 복기 작성/수정 모달
    - 9개 입력 필드: 재료, 시황, 가격(차트), 거래량, 수급, 심리, 평가, 평가이유, 기타
    - 평가: 라디오 버튼 (Good/So-So/Bad)
    - 생성/수정 기능
    - React Query 뮤테이션 + 캐시 무효화
  - `stock-candlestick-chart.tsx`: 캔들스틱 차트 (Recharts, 부분 구현)
  - UI 컴포넌트 (`ui/`): button, input, card, badge (Shadcn UI 스타일)

##### API 통합
- **파일**: `front/src/lib/api.ts`
- **기능**:
  - Axios 인스턴스 (baseURL, 타임아웃 10초)
  - 요청 인터셉터: JWT 토큰 자동 주입 (쿠키 우선, localStorage 대체)
  - 응답 인터셉터: 401 에러 시 자동 로그인 페이지 리다이렉트 및 토큰 삭제
  - API 함수:
    - `authAPI`: login, register, getMe
    - `stocksAPI`: getStocks, getChartData, getOHLCData, getVolumeData, getCurrentPrice, getForeignInstitutionalData
    - `tradingPlansAPI`: 기본 CRUD + **getRecentTrades** (완전 구현)

##### 커스텀 훅
- **파일**: `front/src/lib/hooks/use-auth.ts`
- **훅**:
  - `useAuth()`: 현재 사용자 정보 조회 (React Query)
  - `useLogin()`: 로그인 뮤테이션 (성공 시 /dashboard 리다이렉트)
  - `useRegister()`: 회원가입 뮤테이션
  - `useLogout()`: 로그아웃 뮤테이션 (토큰 삭제 + 캐시 초기화)

##### 미들웨어
- **파일**: `front/src/middleware.ts`
- **기능**:
  - 보호된 경로 (`/dashboard`, `/profile`): 토큰 없으면 `/login`으로 리다이렉트
  - 공개 경로 (`/login`, `/register`): 토큰 있으면 `/dashboard`로 리다이렉트

##### Next.js API 라우트
- **파일**: `front/src/app/api/trading-plans/trades/recent/route.ts`
- **기능**: 서버사이드에서 쿠키의 토큰을 읽어 백엔드 API에 전달 (프록시 역할)

#### 3. 분석 서비스 (Python) - 데이터 제공 모듈

##### KIS API 래퍼
- **파일**: `analyze/lib/hantu.py`
- **클래스**: `KISApi`
- **함수**:
  - `get_combined_data(stock_code, days)`: OHLC + 거래량 + 이동평균선
  - `get_ohlc_data(stock_code, days)`: OHLC 데이터만
  - `get_volume_data(stock_code, days)`: 거래량 + 전일대비 변화율
  - `get_current_price_data(stock_code)`: 현재가 + 등락률
- **기능**: 토큰 캐싱 및 자동 갱신, 에러 처리, Pandas DataFrame 반환

##### 네이버 증권 스크래퍼
- **파일**: `analyze/lib/naver.py`
- **함수**: `get_foreign_institutional_data(stock_code)`
- **반환**: 외국인/기관/개인 순매수, 상위 5개 매수/매도 증권사
- **기술**: BeautifulSoup HTML 파싱, User-Agent 스푸핑

##### 키움증권 API 래퍼
- **파일**: `analyze/lib/kiwoom.py`
- **클래스**: `KiwoomAPI`
- **주요 메서드**: `get_recent_trades(days)` - 최근 N일간 실제 매매내역 조회
- **기능**: OAuth2 토큰 관리, Mock/실거래 지원, 토큰 캐싱

##### 기술적 분석 프레임워크
- **파일**: `analyze/src/technical_analyzer.py`
- **지표**: RSI, MACD, 볼린저밴드, 이동평균선, 지지/저항선
- **상태**: 프레임워크 구현, UI 통합 미완

##### 뉴스 감정 분석
- **파일**: `analyze/src/news_analyzer.py`
- **기능**: 네이버/다음 뉴스 수집, 긍정/부정 키워드 기반 감정 점수 계산
- **상태**: 프레임워크 구현, UI 통합 미완

#### 4. 인프라 및 설정

##### 프로세스 관리
- **도구**: PM2
- **프로세스**:
  - `goni-backend`: FastAPI 백엔드 (포트 8000)
  - `goni-frontend`: Next.js 프론트엔드 (포트 3000)

##### CORS 설정
- **허용 오리진**: localhost:3000-3003, AWS 서버 (3.34.102.218)

##### 환경 변수
- 백엔드: `SECRET_KEY`, DB 연결정보, KIS API 인증정보
- 프론트엔드: `NEXT_PUBLIC_API_URL`
- 분석 서비스: 키움 계좌번호, Mock 모드 설정

#### 5. 최근 버그 수정 (2025-10-22)

##### 토큰 만료 문제 해결
- **문제**: JWT 토큰 30분 만료로 인한 잦은 401 에러
- **해결**: 토큰 만료 시간을 8시간(480분)으로 연장 (`back/app/routers/auth.py:19`)
- **영향**: 사용자 경험 개선, 재로그인 빈도 감소

##### 자동 로그인 리다이렉트 구현
- **문제**: 토큰 만료 시 수동으로 로그인 페이지 이동 필요
- **해결**:
  - `dashboard/page.tsx`에서 직접 fetch 대신 axios API 함수 사용 (`tradingPlansAPI.getRecentTrades`)
  - axios 인터셉터가 401 에러 감지 시 자동으로 토큰 삭제 및 `/login`으로 리다이렉트
- **파일 수정**:
  - `front/src/lib/api.ts`: `tradingPlansAPI.getRecentTrades` 함수 추가
  - `front/src/app/dashboard/page.tsx`: `fetchRecentTrades` 함수를 axios 사용하도록 변경

#### 6. 미구현 기능

- 계획 모드 UI 및 매매 계획 CRUD
- 종목 추가/관리 UI
- 전략 관리 UI
- 캔들스틱 차트에 이동평균선 렌더링
- 기술적 분석 UI 통합
- 뉴스 감정 분석 UI 통합

#### 7. 다음 단계

1. 매매 계획 작성 기능 구현 (계획 모드 활성화)
2. 차트 컴포넌트 완성 (이동평균선 표시)
3. 기술적 분석 지표를 차트에 통합
4. 뉴스 감정 분석 결과를 대시보드에 표시
5. 종목 추가/삭제 기능 구현
6. 전략 관리 기능 구현