# MarketData

MarketData는 한국 주식 시장(KRX) 및 미국 주식 시장(US) 데이터를 효율적으로 수집, 저장 및 추출하기 위한 고성능 데이터 수집 도구입니다. Parquet 포맷을 활용하여 퀀트 분석 및 백테스팅에 최적화된 데이터 환경을 제공합니다.

> [!CAUTION]
> ### 법적·이용 주의사항 (중요)
> *   **목적**: 본 프로젝트는 **개인 학습 및 비영리 목적**으로만 사용하시기를 권장합니다.
> *   **설계**: Naver 금융 및 기타 공개 데이터를 활용한 개인 개발 도구로 설계되었습니다.
> *   **책임**: 상업적 거래, 알고리즘 트레이딩, 영리 목적 이용 등 금융투자업법 및 서비스 이용약관 위반시 **모든 법적 책임은 사용자 본인**에게 있습니다.
> *   **권장**: KRX/나스닥 정식 데이터 서비스 이용을 강력히 권장합니다.

---

## 🚀 주요 기능

### 1. 데이터 수집 (Fetch)
*   **KR Day**: 네이버 금융을 통한 한국 주식 일별 OHLCV 수집 → Parquet 저장
*   **KR 1m**: 한국 주식 1분 단위 인트라데이 데이터 수집 → Parquet 저장
*   **US 5m**: 미국 주식 5분 단위 데이터 처리 → Parquet 저장
*   **Symbol**: KOSPI, KOSDAQ 전 종목 리스트 자동 관리

### 2. 데이터 추출 (Extract)
*   Pandas DataFrame 기반의 직관적인 데이터 추출 API 제공
*   일별 Parquet 파일에서 고속 쿼리
*   백테스팅 라이브러리와 직접 연동 가능

### 3. 주요 장점
*   **압축률**: 80-85% (텍스트 대비)
*   **단순성**: 별도 ingest 과정 불필요
*   **성능**: 컬럼 기반 고속 쿼리
*   **타입 안정성**: 정수/실수 타입 보존

---

## 📂 프로젝트 구조

```text
marketdata/
├── data/                   # 💾 Parquet 데이터 저장소
│   ├── KR-1m/YYYY/         # 한국 1분 데이터 (일별 Parquet)
│   ├── KR-1d/YYYY/         # 한국 일별 데이터 (일별 Parquet)
│   └── US-5m/YYYY/         # 미국 5분 데이터 (일별 Parquet)
├── src/                    # 📦 핵심 로직
│   ├── fetch_kr1m.py       # 한국 1분 데이터 수집
│   ├── fetch_kr1d.py       # 한국 일별 데이터 수집
│   ├── fetch_us5m.py       # 미국 5분 데이터 처리
│   ├── symbol_kr.py        # 종목 리스트 관리
│   └── extract.py          # 통합 데이터 추출 (CLI/모듈)
├── scripts/                # 🛠️ 유틸리티
│   ├── fetch.sh            # 데이터 수집 오케스트레이터
│   ├── setup-dev.sh/bat    # 개발 환경 설정
│   ├── install-systemd-timer.sh  # 프로덕션 배포
│   ├── converter/          # 텍스트→Parquet 변환 도구
│   └── systemd/            # Systemd 서비스 파일
└── tests/                  # 🧪 테스트 스위트
```

---

## 🔧 설치 및 설정

### 1. 개발 환경 설정

**Linux/Mac:**
```bash
bash scripts/setup-dev.sh
```

**Windows:**
```cmd
scripts\setup-dev.bat
```

### 2. 의존성
*   Python 3.11+
*   pandas
*   pyarrow (Parquet 지원)
*   aiohttp, beautifulsoup4, lxml

---

## 📊 사용법

### 데이터 수집

**전체 수집 (심볼 + 일별 + 1분):**
```bash
bash scripts/fetch.sh -d 2026-01-17
```

**개별 수집:**
```bash
# 한국 일별 데이터
python src/fetch_kr1d.py -d 2026-01-17

# 한국 1분 데이터
python src/fetch_kr1m.py -d 2026-01-17 -c 20

# 종목 리스트
python src/symbol_kr.py
```

### 데이터 추출

**CLI 사용:**
```bash
# 한국 1분 데이터
python src/extract.py min 005930 2021-06-01 2021-06-30

# 한국 일별 데이터
python src/extract.py day 005930 2021-01-01 2021-12-31

# 미국 5분 데이터
python src/extract.py min AAPL 2021-12-01 2021-12-31
```

**Python 모듈로 사용:**
```python
from src.extract import extract_kr_1min, extract_kr_day

# 삼성전자 1분 데이터
df = extract_kr_1min('005930', '2021-06-01 09:00:00', '2021-06-30 15:30:00')

# 삼성전자 일별 데이터
df = extract_kr_day('005930', '2021-01-01', '2021-12-31')
```

---

## 🚀 프로덕션 배포

### Systemd 타이머로 자동 수집

```bash
sudo bash scripts/install-systemd-timer.sh
```

**타이머 설정:**
*   평일(월~금) 오후 5시 자동 실행
*   현재 레포지토리에서 직접 실행
*   데이터는 `data/` 폴더에 저장

**관리 명령:**
```bash
# 타이머 상태 확인
systemctl status marketdata-fetch.timer

# 마지막 실행 확인
systemctl status marketdata-fetch.service

# 로그 확인
journalctl -u marketdata-fetch.service
```

---

## 🧪 테스트

```bash
# 전체 테스트
python -m unittest discover tests -v

# Round-trip 테스트
python -m unittest tests.test_roundtrip -v
```

---

## 📈 성능

| 항목 | 텍스트 + zstd | Parquet |
|------|---------------|---------|
| 파일 크기 | 4.5MB | 2-3MB |
| 압축률 | 28% | 80-85% |
| 쿼리 속도 | 느림 (전체 스캔) | 빠름 (컬럼 기반) |
| 타입 안정성 | 없음 | 있음 |

---

## 📝 라이선스

MIT License

---

## ⚠️ 면책 조항

본 소프트웨어는 "있는 그대로" 제공되며, 명시적이든 묵시적이든 어떠한 종류의 보증도 제공하지 않습니다. 저자 또는 저작권 보유자는 본 소프트웨어 사용으로 인해 발생하는 어떠한 청구, 손해 또는 기타 책임에 대해서도 책임을 지지 않습니다.
