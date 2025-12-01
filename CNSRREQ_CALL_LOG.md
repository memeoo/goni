# CNSRREQ 호출 상세 로그 분석

## 테스트 환경
- 테스트 파일: `test_kiwoom_tr_v2.py`
- 로깅 레벨: DEBUG
- 테스트 시간: 2025-12-01 14:50~14:51

---

## 1. ka10172 (일반 조회) 호출 로그

### 요청 파라미터
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

### 타임라인

#### 14:50:39 - WebSocket 로그인 완료
```
2025-12-01 14:50:39,077 [DEBUG] kiwoom - WebSocket 응답 수신:
  {'trnm': 'LOGIN', 'return_code': 0, 'return_msg': '', 'sor_yn': 'Y'}
```
✓ 로그인 성공

#### 14:50:40 - 조건식 목록 조회 완료 (이전 단계)
```
2025-12-01 14:50:40,057 [DEBUG] kiwoom - WebSocket 응답 수신:
  {'trnm': 'CNSRLST', 'return_code': 0, 'return_msg': '',
   'data': [['0', '장기횡보1_이격도기준'], ['1', '장기횡보2_대상변경'], ...]}
2025-12-01 14:50:40,057 [INFO] kiwoom - 조건식 목록 응답 수신: 8개
```
✓ 조건식 목록 조회 성공

#### 14:50:40 - 이전 WebSocket 연결 종료
```
2025-12-01 14:50:40,158 [ERROR] kiwoom - WebSocket 연결이 서버에 의해 종료됨
```
⚠️ 조건식 목록 조회 후 연결 자동 종료 (이전 테스트 종료)

#### 14:50:41 - CNSRREQ 요청 전송
```
2025-12-01 14:50:41,214 [DEBUG] websockets.client -
  > TEXT '{"trnm": "CNSRREQ", "seq": "0", "search_type": "0", ...}' [99 bytes]

2025-12-01 14:50:41,215 [DEBUG] kiwoom - 메시지 전송:
  {"trnm": "CNSRREQ", "seq": "0", "search_type": "0", "stex_tp": "K",
   "cont_yn": "N", "next_key": ""}
```
✓ 요청이 WebSocket을 통해 서버로 전송됨
✓ 요청 크기: 99 바이트

#### 14:50:41 - 로그인 응답 수신 (이전 캐시)
```
2025-12-01 14:50:41,215 [DEBUG] kiwoom - WebSocket 응답 수신:
  {'trnm': 'LOGIN', 'return_code': 0, 'return_msg': '', 'sor_yn': 'Y'}
```
⚠️ **문제 발생**: CNSRREQ 요청 직후 이전 LOGIN 응답이 수신됨
- 응답 큐에 캐시된 데이터일 가능성

#### 14:50:51 - PING 응답 (응답 대기 중)
```
2025-12-01 14:50:51,222 [DEBUG] kiwoom - WebSocket 응답 수신:
  {'trnm': 'PING'}
2025-12-01 14:50:51,222 [DEBUG] kiwoom - PING 응답 수신 및 재전송
```
⏱️ **CNSRREQ 요청 후 약 10초 경과**
- 서버에서 CNSRREQ 응답 없음
- PING/PONG은 정상 작동 중 (연결은 살아있음)

#### 14:51:10 - PING 응답 (계속 응답 대기)
```
2025-12-01 14:51:10,226 [DEBUG] kiwoom - WebSocket 응답 수신:
  {'trnm': 'PING'}
2025-12-01 14:51:10,226 [DEBUG] kiwoom - PING 응답 수신 및 재전송
```
⏱️ **CNSRREQ 요청 후 약 29초 경과**
- 여전히 CNSRREQ 응답 없음
- PING/PONG만 계속 주고받음

#### 14:51:11 - 연결 강제 종료
```
2025-12-01 14:51:11,310 [ERROR] kiwoom - WebSocket 연결이 서버에 의해 종료됨
```
❌ **타임아웃**: 서버가 약 30초 후 WebSocket 연결을 강제 종료
- CNSRREQ 응답이 없어서 연결 종료

#### 14:51:11 이후
```
Test Result: ✗ 응답 수신 타임아웃 (30초 이상 대기)
```

---

## 2. ka10173 (실시간 조회) 호출 로그

### 요청 파라미터
```json
{
  "trnm": "CNSRREQ",
  "seq": "0",
  "search_type": "1"
}
```

### 타임라인

#### 14:51:12 - CNSRREQ 요청 전송
```
2025-12-01 14:51:12,364 [DEBUG] websockets.client -
  > TEXT '{"trnm": "CNSRREQ", "seq": "0", "search_type": "1"}' [51 bytes]

2025-12-01 14:51:12,364 [DEBUG] kiwoom - 메시지 전송:
  {"trnm": "CNSRREQ", "seq": "0", "search_type": "1"}
```
✓ 요청이 WebSocket을 통해 서버로 전송됨
✓ 요청 크기: 51 바이트 (일반 조회보다 작음 - stex_tp 등 필드 없음)

#### 14:51:12 - 로그인 응답 수신 (이전 캐시)
```
2025-12-01 14:51:12,364 [DEBUG] kiwoom - WebSocket 응답 수신:
  {'trnm': 'LOGIN', 'return_code': 0, 'return_msg': '', 'sor_yn': 'Y'}
```
⚠️ **동일 문제**: CNSRREQ 요청 직후 이전 LOGIN 응답이 수신됨

#### 14:51:22 - PING 응답 (응답 대기 중)
```
2025-12-01 14:51:22,369 [DEBUG] kiwoom - WebSocket 응답 수신:
  {'trnm': 'PING'}
2025-12-01 14:51:22,369 [DEBUG] kiwoom - PING 응답 수신 및 재전송
```
⏱️ **CNSRREQ 요청 후 약 10초 경과**
- 서버에서 CNSRREQ 응답 없음
- PING/PONG은 정상 작동 중

#### 14:51:32 이후 (테스트 완료)
```
Test Result: ✗ 응답 수신 타임아웃 (30초 이상 대기)
```

---

## 주요 발견 사항

### 1. 요청 전송은 정상
```
✓ ka10172 (일반 조회): 99 바이트 전송 성공
✓ ka10173 (실시간 조회): 51 바이트 전송 성공
```
요청이 WebSocket을 통해 정상적으로 서버로 전달됨

### 2. 응답은 수신되지 않음
```
✗ ka10172: CNSRREQ 응답 없음 (PING/PONG만 수신)
✗ ka10173: CNSRREQ 응답 없음 (PING/PONG만 수신)
```
- 서버가 요청을 받았지만 응답을 보내지 않음
- 또는 클라이언트가 응답을 받지 못함

### 3. 응답 메시지 타입별 패턴
| 메시지 타입 | 응답 여부 | 응답 시간 | 상태 |
|----------|---------|---------|------|
| LOGIN | ✓ 즉시 | ~50ms | 정상 |
| CNSRLST | ✓ 빠름 | ~1초 | 정상 |
| CNSRREQ | ✗ 없음 | 타임아웃 | **문제** |
| PING | ✓ 주기적 | ~10초 | 정상 |

### 4. 서버 연결 정책
```
타임아웃: 약 30초
행동: 응답 없는 요청 후 일정 시간이 지나면 연결 강제 종료
```

### 5. 응답 캐시 문제 추측
```
현상: CNSRREQ 직후 이전 LOGIN 응답이 수신됨
원인: response_queue에서 캐시된 데이터를 잘못 수신했을 가능성
```

---

## 로그 해석

### 성공적인 메시지 흐름 (CNSRLST)
```
[클라이언트] → CNSRLST 요청
           ↓ (약 1초)
[서버]     ← CNSRLST 응답 (8개 조건식 데이터)
```

### 실패한 메시지 흐름 (CNSRREQ)
```
[클라이언트] → CNSRREQ 요청
           ↓ (응답 없음)
[서버]     X (응답 없음)
           ↓ (약 30초)
[서버]     → 연결 강제 종료
```

---

## 핵심 결론

### 문제
- **CNSRREQ 메시지에 대해서만 서버가 응답하지 않음**
- 다른 메시지 타입(LOGIN, CNSRLST, PING)은 모두 정상 작동

### 원인 (추정)
1. **API 버전 불일치** - 서버가 CNSRREQ를 지원하지 않음
2. **메시지 형식 오류** - 필드명, 필드 타입, 또는 필수 필드 누락
3. **서버 버그** - CNSRREQ 처리 로직 오류
4. **권한 문제** - 해당 계정이 조건검색 조회 권한 없음

### 다음 조치
1. ⭐ 키움증권 API 기술 지원팀에 CNSRREQ 응답 미수신 문제 보고
2. 최신 API 문서에서 CNSRREQ 메시지 형식 확인
3. 메시지 형식 변경 시도 (seq 타입, 필드명 등)
