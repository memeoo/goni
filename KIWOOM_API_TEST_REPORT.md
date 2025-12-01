# 키움 API TR ID (ka10172, ka10173) 호출 테스트 보고서

## 테스트 일시
- 2025년 12월 1일 14:19 ~ 14:26 (KST)
- 프로젝트: goni
- 테스트 파일: `test_kiwoom_tr_v2.py`, `test_kiwoom_tr_v3.py`

## 테스트 개요

키움 Open REST API의 조건검색 TR ID 두 가지를 테스트했습니다:

| TR ID | 이름 | API Parameter | 상태 |
|-------|------|---------------|------|
| **ka10172** | 조건검색 일반 조회 | `search_type='0'` | ❌ 실패 |
| **ka10173** | 조건검색 실시간 조회 | `search_type='1'` | ❌ 실패 |

## 테스트 결과 요약

### ✅ 성공한 부분

1. **토큰 발급 (OAuth2)**
   - 엔드포인트: `/oauth2/token`
   - 상태: ✓ 성공
   - 토큰 유효기간: 24시간

2. **조건식 목록 조회 (CNSRLST)**
   - WebSocket 메시지: `{'trnm': 'CNSRLST'}`
   - 응답: ✓ 성공 (100% 성공률)
   - 조회된 조건식: 8개
   ```
   1. ID=0, 장기횡보1_이격도기준
   2. ID=1, 장기횡보2_대상변경
   3. ID=2, 단타_BASIC_SIMPLE01
   4. ID=3, 단타_BASIC_SIMPLE01_코스피
   5. ID=4, 단타_BASIC_SIMPLE01_코스피_02
   6. ID=5, 대왕개미단타
   7. ID=6, 창원개미_단타
   8. ID=7, 신고가 돌파
   ```

### ❌ 실패한 부분

#### 1. ka10172 (일반 조회) 실패 - 모든 조건식에서 타임아웃

**테스트 대상**: 8개 조건식 모두
- ID=0: 장기횡보1_이격도기준
- ID=1: 장기횡보2_대상변경
- ID=2: 단타_BASIC_SIMPLE01
- ID=3: 단타_BASIC_SIMPLE01_코스피
- ID=4: 단타_BASIC_SIMPLE01_코스피_02
- ID=5: 대왕개미단타
- ID=6: 창원개미_단타
- ID=7: 신고가 돌파

**요청 정보 (예시 - ID=0):**
```json
{
  "trnm": "CNSRREQ",
  "seq": "0",
  "search_type": "0",
  "stex_tp": "K",
  "cont_yn": "N",
  "next_key": ""
}
```

**결과:**
- 상태: ❌ **응답 타임아웃 (0% 성공률)**
- 성공: 0건 / 실패: 0건 / 타임아웃: 8건
- 모든 조건식에서 응답 없음 (15초 대기 후 타임아웃)

**WebSocket 로그 분석:**
```
[14:22:30] > 요청 전송: {"trnm": "CNSRREQ", "seq": "0", "search_type": "0", ...}
[14:22:30~14:22:45] ← 응답 없음 (PING 주고받기만 수행)
[14:22:45] WebSocket 연결 서버에 의해 강제 종료
[타임아웃] CNSRREQ 응답 미수신
```

#### 2. ka10173 (실시간 조회) 실패 - 모든 조건식에서 타임아웃

**테스트 대상**: 8개 조건식 모두 (ka10172와 동일)

**요청 정보 (예시 - ID=0):**
```json
{
  "trnm": "CNSRREQ",
  "seq": "0",
  "search_type": "1"
}
```

**결과:**
- 상태: ❌ **응답 타임아웃 (0% 성공률)**
- 성공: 0건 / 실패: 0건 / 타임아웃: 8건
- 모든 조건식에서 응답 없음 (15초 대기 후 타임아웃)

**WebSocket 로그 분석:**
```
[14:22:45] > 요청 전송: {"trnm": "CNSRREQ", "seq": "0", "search_type": "1"}
[14:22:45~14:23:01] ← 응답 없음 (PING 주고받기만 수행)
[14:23:01] WebSocket 연결 서버에 의해 강제 종료
[타임아웃] CNSRREQ 응답 미수신
```

## 원인 분석

### 핵심 발견 사항

1. **CNSRLST(조건식 목록) vs CNSRREQ(조건검색 요청)**
   - CNSRLST: ✓ **정상 작동** (응답 빠름)
   - CNSRREQ: ❌ **응답 없음** (모든 경우에 타임아웃)
   - → 서버가 특정 메시지 타입을 처리하지 않을 가능성

2. **WebSocket 연결 상태**
   - 로그인: ✓ 성공
   - PING/PONG: ✓ 정상 작동
   - 조건식 목록 조회: ✓ 성공
   - 조건검색 요청: ❌ 응답 없음 → 약 15초 후 서버가 연결 강제 종료

3. **모든 조건식에서 동일한 현상**
   - 조건식의 종류나 ID와 무관하게 모두 타임아웃
   - → 조건식 문제가 아님 (요청 방식 문제일 가능성 높음)

### 가능한 원인들

| 원인 | 가능성 | 설명 |
|------|--------|------|
| **API 버전 불일치** | **매우 높음** | 웹소켓 프로토콜 또는 메시지 형식이 변경되었을 수 있음 |
| **메시지 형식 오류** | **높음** | `seq` 필드 타입 (string vs int), 추가 필드 필요 등 |
| **API 엔드포인트 변경** | **중간** | WebSocket URL이 변경되었거나 새로운 엔드포인트 필요 |
| **권한 부족** | **중간** | 모의투자/실전투자 계정의 권한 제한 |
| **조건식 기능 미지원** | **낮음** | 조건검색 조회가 특정 라이센스에서 비활성화됨 |
| **서버 버그** | **낮음** | 키움 서버 측 CNSRREQ 처리 오류 |

## 상세 테스트 데이터

### WebSocket 연결 정보
```
프로토콜: WebSocket (wss://)
호스트: api.kiwoom.com:10000
엔드포인트: /api/dostk/websocket
연결 상태: ✓ 정상 (OPEN)
```

### 메시지 타입 및 상태

| 메시지 타입 | 설명 | 상태 |
|------------|------|------|
| LOGIN | 웹소켓 로그인 | ✓ 성공 |
| CNSRLST | 조건식 목록 조회 | ✓ 성공 |
| CNSRREQ | 조건검색 요청 | ❌ 응답 없음 |
| PING | 서버 핑 | ✓ 정상 |
| PONG | 클라이언트 응답 | ✓ 정상 |

## 권장 조치사항

### 우선순위 1: 키움 API 기술 문의 (필수)

**문의 내용:**
```
제목: WebSocket CNSRREQ 메시지 응답 안 됨 (ka10172/ka10173)

환경:
- 앱키/시크릿키: 정상 작동 (토큰 발급 성공)
- WebSocket 연결: 정상 (PING/PONG 작동)
- 조건식 목록 조회(CNSRLST): 정상 (8개 조건식 조회)
- 조건검색 요청(CNSRREQ): 응답 없음

요청 파라미터:
{
  "trnm": "CNSRREQ",
  "seq": "0",
  "search_type": "0",
  "stex_tp": "K",
  "cont_yn": "N",
  "next_key": ""
}

증상:
- 모든 조건식에서 동일하게 CNSRREQ 응답 없음
- 약 15초 후 서버가 WebSocket 연결 강제 종료
- 오류 메시지 없음 (단순히 응답 미수신)
```

**연락처:**
- 키움증권 API 기술 지원팀
- 키움증권 Open API 공식 문서 및 커뮤니티

### 우선순위 2: 메시지 형식 변경 시도

**시도 1: seq 필드를 정수로 변경**
```python
request = {
    'trnm': 'CNSRREQ',
    'seq': 0,          # "0" → 0 (string → int)
    'search_type': '0'
}
```

**시도 2: stex_tp 필드명 변경**
```python
# stex_tp → stock_exchange_type 또는 다른 필드명
request = {
    'trnm': 'CNSRREQ',
    'seq': '0',
    'search_type': '0',
    'stk_ex_tp': 'K'  # 필드명 변경
}
```

**시도 3: 최소 필드만 전송**
```python
# 추가 파라미터 모두 제거
request = {
    'trnm': 'CNSRREQ',
    'seq': '0'
}
```

### 우선순위 3: REST API 대체 확인

키움 API가 CNSRREQ를 REST API로도 제공하는지 확인:
```bash
# REST API 엔드포인트가 있는지 확인
# /api/dostk/search 등의 엔드포인트 확인
```

### 우선순위 4: 모의투자 환경 테스트

```python
api = KiwoomAPI(..., use_mock=True)  # 모의투자로 재시도
```

### 우선순위 5: 다른 WebSocket 메시지 타입 테스트

조건검색 외 다른 WebSocket API가 정상 작동하는지 확인하여
CNSRREQ 특정 문제인지 WebSocket 통신 전체 문제인지 판단

## 코드 위치

### 관련 파일
- **API 클래스**: `analyze/lib/kiwoom.py`
  - `KiwoomAPI.search_condition()` - 고수준 API
  - `KiwoomWebSocketClient.request_condition_search()` - 저수준 WebSocket

- **테스트 파일**
  - `test_kiwoom_tr.py` - 초기 테스트
  - `test_kiwoom_tr_v2.py` - 상세 디버깅 테스트

### 주요 메서드

#### KiwoomAPI.search_condition()
```python
def search_condition(
    condition_id: str,
    search_type: str = '0',           # '0': ka10172, '1': ka10173
    stock_exchange_type: str = 'K',
    use_mock: bool = False
) -> Optional[List[Dict[str, Any]]]
```

#### KiwoomWebSocketClient.request_condition_search()
```python
async def request_condition_search(
    condition_id: str,
    search_type: str = '0',
    stock_exchange_type: str = 'K',
    cont_yn: str = 'N',
    next_key: str = ''
) -> Optional[Dict[str, Any]]
```

## 다음 단계

### 우선 순위

1. **HIGH**: 다른 조건식 ID로 재시도 테스트
2. **HIGH**: 모의투자 환경에서 테스트
3. **MEDIUM**: 키움 API 기술 지원팀 문의
4. **MEDIUM**: 응답 대기 시간 증가 후 재시도
5. **LOW**: 다른 API 엔드포인트 테스트 (REST API)

### 테스트 명령어

```bash
# v2 상세 테스트 재실행
source venv/bin/activate
python test_kiwoom_tr_v2.py

# 로그 레벨 변경 (더 상세한 디버깅)
# logging.basicConfig(level=logging.DEBUG)
```

## 결론

### 테스트 결과 정리

| 항목 | 상태 | 설명 |
|------|------|------|
| **OAuth2 토큰 발급** | ✓ 성공 | `/oauth2/token` 정상 작동 |
| **WebSocket 연결** | ✓ 성공 | wss://api.kiwoom.com:10000 정상 |
| **WebSocket 로그인** | ✓ 성공 | LOGIN 메시지 정상 응답 |
| **조건식 목록 조회 (CNSRLST)** | ✓ 성공 | 8개 조건식 정상 조회 |
| **ka10172 (일반 조회)** | ❌ 실패 | CNSRREQ 응답 없음 (0/8) |
| **ka10173 (실시간 조회)** | ❌ 실패 | CNSRREQ 응답 없음 (0/8) |

### 주요 발견

1. **핵심 문제**: CNSRREQ 메시지에 대해 서버가 응답하지 않음
   - 모든 조건식에서 동일 증상
   - 요청은 정상 전송되나 응답 수신 불가
   - 약 15초 후 서버가 연결 강제 종료

2. **부분 성공**: CNSRLST와 기본 WebSocket 통신은 정상
   - 토큰 발급, 로그인, PING/PONG 모두 정상
   - 조건식 목록 조회도 성공 (응답 시간 약 1초)

3. **원인 추정**: API 버전 불일치 또는 메시지 형식 오류 (가능성 높음)
   - WebSocket 프로토콜 변경
   - 필드명 또는 필드 타입 변경
   - 계정 권한/라이센스 제한

### 다음 조치

**즉시 필요한 조치:**
1. ⭐ 키움증권 API 기술 지원팀에 문의
2. 최신 API 문서 및 변경 사항 확인
3. 메시지 형식 변경 시도 (seq 정수 변환, 필드명 변경 등)

**추가 테스트:**
- 모의투자 환경에서 재시도
- 다른 WebSocket 메시지 타입 테스트
- REST API 대체 엔드포인트 확인

### 테스트 자료

생성된 테스트 파일:
- `test_kiwoom_tr.py` - 초기 테스트 (asyncio.run 오류)
- `test_kiwoom_tr_v2.py` - 상세 디버깅 테스트
- `test_kiwoom_tr_v3.py` - 전수 테스트 (모든 조건식)
- `KIWOOM_API_TEST_REPORT.md` - 이 보고서

실행 방법:
```bash
source venv/bin/activate
python test_kiwoom_tr_v3.py  # 전수 테스트 (약 5분 소요)
```
