# KRX Price Tests

이 디렉토리는 Python의 내장 `unittest` 프레임워크와 `unittest.mock`을 사용한 테스트를 포함합니다.

## 사전 요구사항

테스트를 실행하기 전에 필요한 의존성을 설치해야 합니다:

```bash
pip install -r requirements.txt
```

## 테스트 실행 방법

### 모든 테스트 실행
```bash
python -m unittest discover tests -v
```

### 특정 모듈 테스트 실행
```bash
# symbol.py 테스트
python -m unittest tests.test_symbol -v

# day.py 테스트
python -m unittest tests.test_day -v

# minute.py 테스트
python -m unittest tests.test_minute -v
```

### 특정 테스트 클래스 실행
```bash
python -m unittest tests.test_symbol.TestParseSymbols -v
```

### 특정 테스트 메서드 실행
```bash
python -m unittest tests.test_symbol.TestParseSymbols.test_parse_symbols_success -v
```

### 간단한 실행 (verbose 없이)
```bash
python -m unittest discover tests
```

## 테스트 구조

### test_symbol.py
symbol.py 모듈의 심볼 수집 기능 테스트

- `TestParseSymbols`: JSON 응답에서 심볼 파싱 테스트
- `TestFetchSymbols`: KOSPI/KOSDAQ 심볼 비동기 fetch 테스트
- `TestMainAsync`: 메인 실행 로직 테스트
- `TestConstants`: 모듈 상수 검증

### test_day.py
day.py 모듈의 일별 OHLCV 데이터 수집 테스트

- `TestParseDayData`: HTML에서 일별 데이터 파싱 테스트
- `TestFetchDaySymbol`: 개별 심볼의 일별 데이터 fetch 테스트
- `TestCollectDayData`: 여러 심볼의 데이터 수집 테스트
- `TestMainAsync`: 메인 실행 로직 테스트
- `TestConstants`: 모듈 상수 검증

### test_minute.py
minute.py 모듈의 분봉 데이터 수집 테스트

- `TestParseMinuteRows`: HTML에서 분봉 데이터 파싱 테스트
- `TestFetchMinutePage`: 단일 페이지 분봉 데이터 fetch 테스트
- `TestFetchMinuteSymbol`: 전체 분봉 데이터 수집 및 중복 제거 테스트
- `TestCollectMinuteData`: 여러 심볼의 분봉 데이터 수집 테스트
- `TestMainAsync`: 메인 실행 로직 테스트
- `TestConstants`: 모듈 상수 검증

## 테스트 커버리지

각 테스트 파일은 다음을 포함합니다:

- ✅ **정상 케이스**: 성공적인 데이터 수집 및 파싱
- ✅ **에러 처리**: HTTP 에러, 네트워크 예외 처리
- ✅ **엣지 케이스**: 빈 데이터, 불완전한 데이터, 중복 데이터
- ✅ **비동기 처리**: AsyncMock을 사용한 비동기 함수 테스트
- ✅ **파일 I/O**: mock_open을 사용한 파일 저장 테스트
- ✅ **외부 의존성 격리**: Mock을 사용한 HTTP 요청 격리

## 사용된 기술

- **unittest**: Python 내장 테스트 프레임워크
- **unittest.mock**: Mock 객체 생성 및 패칭
  - `Mock`: 일반 객체 모킹
  - `MagicMock`: 매직 메서드를 지원하는 Mock
  - `AsyncMock`: 비동기 함수 및 코루틴 모킹
  - `patch`: 함수 및 객체 패칭
  - `mock_open`: 파일 I/O 모킹
- **unittest.IsolatedAsyncioTestCase**: 비동기 함수 테스트를 위한 베이스 클래스

## 테스트 작성 패턴

### 동기 함수 테스트
```python
class TestMyFunction(unittest.TestCase):
    def test_success_case(self):
        result = my_function()
        self.assertEqual(result, expected_value)
```

### 비동기 함수 테스트
```python
class TestMyAsyncFunction(unittest.IsolatedAsyncioTestCase):
    async def test_async_success(self):
        result = await my_async_function()
        self.assertEqual(result, expected_value)
```

### Mock을 사용한 HTTP 요청 테스트
```python
async def test_with_mock_http(self):
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"data": []}')
    
    with patch('module.aiohttp.ClientSession') as mock_session:
        mock_session.return_value.get.return_value = mock_response
        result = await fetch_data()
```

## 주의사항

- **Unit Tests**: 실제 네트워크 요청을 하지 않습니다 (모두 Mock 사용)
- **Integration Tests**: 실제 API를 호출하여 테스트합니다
- 테스트는 독립적으로 실행 가능하며 순서에 의존하지 않습니다
- 각 테스트는 격리된 환경에서 실행됩니다

## 통합 테스트 (Integration Tests)

### test_integration.py
실제 API를 호출하여 모듈이 실제 데이터와 잘 작동하는지 검증합니다.

**실행 방법:**
```bash
# 통합 테스트만 실행
python -m unittest tests.test_integration -v

# 또는 직접 실행
python tests/test_integration.py
```

**포함된 테스트:**
- `TestSymbolIntegration`: 실제 KOSPI/KOSDAQ 심볼 fetch 테스트
- `TestDayIntegration`: 실제 일별 OHLCV 데이터 fetch 테스트
- `TestMinuteIntegration`: 실제 분봉 데이터 fetch 및 중복 제거 테스트
- `TestDataConsistency`: 데이터 형식 검증 테스트

**주의사항:**
- 실제 네트워크 요청을 하므로 시간이 걸릴 수 있습니다
- 시장이 닫혀있거나 네트워크가 불안정하면 일부 테스트가 skip될 수 있습니다
- 주말이나 공휴일에는 일별/분봉 데이터 테스트가 skip됩니다

## 테스트 유형 비교

| 특성 | Unit Tests | Integration Tests |
|------|-----------|-------------------|
| 네트워크 요청 | ❌ Mock 사용 | ✅ 실제 API 호출 |
| 실행 속도 | 빠름 (~0.2초) | 느림 (~1초) |
| 안정성 | 항상 통과 | 환경에 따라 skip 가능 |
| 목적 | 로직 검증 | 실제 동작 검증 |
| 파일 | test_symbol.py, test_day.py, test_minute.py | test_integration.py |
