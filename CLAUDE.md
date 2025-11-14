# Structure
- back-end 소스 폴더 : root/back
- front-end 소스 폴더 : root/front
- 종목 분석 및 추천 서비스 소스 폴더: root/analyze

# Tech Stack
- back-end : fast api(latest)
- front-end : next.js v.15 이상
- analyze: python v.3.13
- DB : postgresql (db name:goni, port:5432, user:goniadmin, password:shsbsy70)
- 프로세스 관리: pm2. name: goni-backend(backend), goni-frontend(frontend)

# Port Configuration
- **포트 3000 (운영/Production)**: PM2 `goni-frontend` 프로세스가 실행하는 포트. `npm start -- -p 3000` 명령으로 빌드된 Next.js를 실행
- **포트 3001 (개발/Development)**: `npm run dev` 명령으로 개발 서버 시작. 로컬 개발 및 테스트 용도

# Project description
- 이름:  Goni(영화 타짜의 주인공 ‘고니’ 처럼 타짜 급의 탑 트레이더가 되기 위한 매매 계획 및 복기 일지 프로그램)
- 개요: 여러 주식 종목의 당일 정보(차트 및 수급, 뉴스 등)를 모니터링 할 수 있는 대쉬 보드 형태의 웹 페이지. 모니터링 목적 이외에, 종목을 매매 하는 플랜을 세우고, 매매 이유와 복기(결과 및 반성)를 입력해서 매매 계획과 복기 등의 일지를 작성해 트레이딩의 실력을 높히는게 주 목적. 

# Not To do.
- 절대 Mock 데이터를 만들어서 표시하지 말 것. 데이터가 없거나 가져올 수 없으면 그냥 없다고 표시할 것. Dummy 데이터나 Mock 데이터를 절대로 만들어서 표시하지 말 것. 

# README.md Update.
- 새로운 기능이 추가되거나 변경이 일어나면 항상 README.md 파일의 ## ADDED or MODIFIED 아래에 내용을 적어서 계속 업데이트 상태를 유지하시오.
- 프로젝트를 처음 시작할 때, 항상 README.md 파일을 먼저 읽어서 project의 진행 상황을 파악하시오.

# Database Schema & Models

## trading_plans 테이블

**용도**: 사용자가 입력하는 매매 계획을 저장 (실제 매매 실행은 Trading/TradingHistory 테이블에서 관리)

**필드 구성**:

### 핵심 필드
- `id` (PK): 매매 계획 ID
- `user_id` (FK): 사용자 ID
- `stock_code` (VARCHAR, INDEX): 종목코드 (예: '005930')
- `stock_name` (VARCHAR): 종목명 (예: '삼성전자')
- `trading_type` (VARCHAR): 거래 종류 ('buy' or 'sell')
- `created_at`, `updated_at`: 시스템 타임스탐프

### 매매 계획 정보
- `condition` (TEXT): 매매 조건 (사용자 입력, 예: "20일 이동평균선 지지 시")
- `target_price` (FLOAT): 매매 계획 가격 (매수가 또는 매도가)
- `amount` (BIGINT): 매매 금액 (가격 × 수량)
- `reason` (TEXT): 매매 이유 (사용자 입력)

### 매도 계획 필드
- `proportion` (FLOAT): 매도 비중 (%) - 매도 시에만 사용

### 익절(Stop Profit) 설정
- `sp_condition` (TEXT): 익절 조건 (예: "3% 수익")
- `sp_price` (FLOAT): 익절 가격
- `sp_ratio` (FLOAT): 익절 수익률 (%)

### 손절(Stop Loss) 설정
- `sl_condition` (TEXT): 손절 조건 (예: "-2% 손실")
- `sl_price` (FLOAT): 손절 가격
- `sl_ratio` (FLOAT): 손절 손실률 (%)

**주의사항**:
- `stock_id` → `stock_code`로 변경 (Foreign Key 제거)
- 실제 매매 실행은 Trading/TradingHistory 테이블에서 관리
- 복기 정보는 Recap 테이블에서 분리 관리

## API Endpoints

### POST /api/trading-plans
매매 계획 저장 (새로 생성)

**요청**:
```json
{
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "trading_type": "buy",
  "condition": "20일 이동평균선 지지 시",
  "target_price": 70500,
  "amount": 705000,
  "reason": "긍정적인 뉴스 + 기술적 지지",
  "sp_condition": "3% 수익",
  "sp_price": 72655,
  "sp_ratio": 3.0,
  "sl_condition": "-2% 손실",
  "sl_price": 69090,
  "sl_ratio": -2.0
}
```

**응답**: TradingPlan 객체 (생성된 매매 계획)

### GET /api/trading-plans/plan-mode
계획 모드 종목 목록 (사용자가 계획을 세운 종목들)

### GET /api/trading-plans/{plan_id}
특정 매매 계획 조회

### PUT /api/trading-plans/{plan_id}
매매 계획 수정

### DELETE /api/trading-plans/{plan_id}
매매 계획 삭제

## Frontend Components

### TradingPlanFormModal (front/src/components/trading-plan-form-modal.tsx)

**역할**: 매매 계획 입력 및 저장 모달

**주요 기능**:
1. 매수/매도 구분 선택
2. 입력 필드 동적 표시 (매수/매도에 따라 다른 필드)
3. 자동 계산:
   - 금액 = 가격 × 수량
   - 익절가 ↔ 익절률 자동 계산
   - 손절가 ↔ 손절률 자동 계산
   - 매도 비중 ↔ 수량 자동 계산
4. 입력값 유효성 검증
5. 백엔드 API 호출 및 저장

**Props**:
- `isOpen` (boolean): 모달 열림 여부
- `onClose` (function): 모달 닫기 콜백
- `stockCode` (string): 종목코드
- `stockName` (string): 종목명

**상태 관리**:
- `tradeType`: 'buy' | 'sell'
- 매수 관련: `buyPrice`, `buyQuantity`, `buyAmount`, `buyCondition`, `buyReason`, `profitTarget`, `profitCondition`, `profitRate`, `lossTarget`, `lossCondition`, `lossRate`
- 매도 관련: `sellPrice`, `sellRatio`, `sellQuantity`, `sellCondition`, `sellReason`
- 보유 정보: `holdingQuantity`, `isHolding`

**마이그레이션 이후 변경사항**:
- `handleSave()` 함수 구현으로 백엔드 저장 기능 추가
- 입력 필드 → API 데이터로 자동 매핑

## Frontend API Functions

### tradingPlansAPI.saveTradingPlan(planData)
매매 계획 저장

```typescript
saveTradingPlan: (planData: any) =>
  api.post('/api/trading-plans', planData)
```

## 마이그레이션 파일

**파일**: `back/update_trading_plans_schema.sql`

**설명**: trading_plans 테이블 스키마 변경

**실행 방법**:
```bash
# PostgreSQL 접속 후
\i /home/ubuntu/goni/back/update_trading_plans_schema.sql

# 또는 명령줄에서
psql -U goniadmin -d goni -h localhost -f /home/ubuntu/goni/back/update_trading_plans_schema.sql
```

**주의**:
- 기존 trading_plans 테이블이 삭제되고 재생성됨
- 기존 데이터가 필요하면 사전에 백업할 것
- 마이그레이션 후 백엔드 서버 재시작 필수: `pm2 restart goni-backend`