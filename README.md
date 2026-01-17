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

## 🧪 테스트 실행

본 프로젝트는 총 **55개의 테스트 케이스**를 포함하고 있습니다.

*   **전체 테스트 실행**: `python -m unittest discover tests -v`
*   **단위 테스트 (Mock)**: `python -m unittest tests.test_symbol tests.test_day tests.test_minute -v`
*   **통합 테스트 (Real API)**: `python -m unittest tests.test_integration -v`

---

## 🐳 Docker & 배포

이 프로젝트는 Docker 컨테이너와 호스트의 **systemd timer**를 연동하여 자동 수집 환경을 구축합니다.

### 1. 배포 및 시스템 자동화 설정 (Linux)
제공된 배포 스크립트를 통해 소스 코드 복사, Docker 빌드, 서비스/타이머 등록이 한 번에 진행됩니다.
```bash
sudo ./scripts/deploy.sh
```
*   **스케줄**: 매 평일(월-금) 17:00에 자동 실행
*   **동작**: 컨테이너 실행 후 수집 태스크가 완료되면 즉시 종료 (`--rm`)

### 2. 수동 실행
```bash
docker compose run --rm app
```

---

## 💾 데이터 관리

*   **저장 경로**: 호스트의 `/srv/krx-price` 경로에 데이터가 저장됩니다.
*   **디렉토리 구조**:
    *   `/srv/krx-price/day`: 일별 데이터
    *   `/srv/krx-price/minute`: 분 단위 데이터
*   **볼륨 설정**: `docker-compose.yml`을 통해 호스트 경로와 컨테이너 내부 경로가 동기화됩니다.
