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

### 3. 데이터 병합 (Merge)
*   **월별 병합**: 일별 파일을 월별 파일로 자동 병합 (5일 경과 후)
*   **연별 병합**: 월별 파일을 연별 파일로 자동 병합 (과거 연도)
*   **자동 검증**: 병합 후 데이터 무결성 자동 검증
*   **공간 절약**: 병합 완료 후 원본 파일 자동 삭제

### 4. 주요 장점
*   **압축률**: 80-85% (텍스트 대비)
*   **단순성**: 별도 ingest 과정 불필요
*   **성능**: 컬럼 기반 고속 쿼리
*   **타입 안정성**: 정수/실수 타입 보존

---

## 📂 프로젝트 구조

```text
marketdata/
├── data/                   # 💾 Parquet 데이터 저장소
│   ├── KR-1m/YYYY/         # 한국 1분 데이터 (일별 → 월별 → 연별)
│   ├── KR-1d/YYYY/         # 한국 일별 데이터 (일별 → 월별 → 연별)
│   └── US-5m/YYYY/         # 미국 5분 데이터 (일별 → 월별 → 연별)
├── src/                    # 📦 핵심 로직
│   ├── run.sh              # 데이터 수집 오케스트레이터
│   ├── fetch_kr1m.py       # 한국 1분 데이터 수집
│   ├── fetch_kr1d.py       # 한국 일별 데이터 수집
│   ├── fetch_us5m.py       # 미국 5분 데이터 처리
│   ├── symbol_kr.py        # 종목 리스트 관리
│   └── extract.py          # 통합 데이터 추출 (CLI/모듈)
├── scripts/                # 🛠️ 유틸리티
│   ├── setup-dev.sh/bat    # 개발 환경 설정
│   ├── install-systemd.sh  # 프로덕션 배포
│   ├── merge-monthly/      # 월별 병합 스크립트
│   │   ├── merge_kr1d.py   # 일별 → 월별 병합 (KR Day)
│   │   ├── merge_kr1m.py   # 일별 → 월별 병합 (KR 1m)
│   │   └── merge_us5m.py   # 일별 → 월별 병합 (US 5m)
│   ├── merge-yearly/       # 연별 병합 스크립트
│   │   ├── merge_kr1d.py   # 월별 → 연별 병합 (KR Day)
│   │   ├── merge_kr1m.py   # 월별 → 연별 병합 (KR 1m)
│   │   └── merge_us5m.py   # 월별 → 연별 병합 (US 5m)
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

## 📊 데이터 수집 및 관리

### 1. 데이터 수집
```bash
# 가상환경 활성화
source .venv/bin/activate

# 특정 날짜 데이터 수집
bash src/run.sh -d 2026-01-17

# 오늘 데이터 수집 (기본값)
bash src/run.sh
```

### 2. 데이터 병합

#### 월별 병합 (일별 → 월별)
5일이 경과한 일별 파일을 자동으로 월별 파일로 병합합니다.

```bash
# KR Day 데이터 월별 병합
python scripts/merge-monthly/merge_kr1d.py

# KR 1m 데이터 월별 병합
python scripts/merge-monthly/merge_kr1m.py

# US 5m 데이터 월별 병합
python scripts/merge-monthly/merge_us5m.py
```

#### 연별 병합 (월별 → 연별)
과거 연도의 월별 파일을 자동으로 연별 파일로 병합합니다.

```bash
# KR Day 데이터 연별 병합
python scripts/merge-yearly/merge_kr1d.py

# KR 1m 데이터 연별 병합
python scripts/merge-yearly/merge_kr1m.py

# US 5m 데이터 연별 병합
python scripts/merge-yearly/merge_us5m.py
```

**병합 프로세스:**
1. 조건에 맞는 파일 자동 탐색
2. 데이터 병합 및 중복 제거
3. 병합 데이터 검증 (원본과 비교)
4. 검증 성공 시 원본 파일 삭제
5. 디스크 공간 절약 및 쿼리 성능 향상

---

## 🧪 테스트 실행

본 프로젝트는 총 **64개의 테스트 케이스**를 포함하고 있습니다.

*   **전체 테스트 실행**: `python -m unittest discover tests -v`
*   **단위 테스트 (Mock)**: `python -m unittest tests.test_symbol tests.test_day tests.test_minute -v`
*   **통합 테스트 (Real API)**: `python -m unittest tests.test_integration -v`

---

## 🚀 프로덕션 배포 (Linux)

### Systemd Timer를 이용한 자동 수집

```bash
# 배포 스크립트 실행 (서비스 및 타이머 설치)
sudo ./scripts/install-systemd.sh
```

*   **스케줄**: 매 평일(월-금) 17:00에 자동 실행
*   **동작**: 데이터 수집 후 자동 종료
*   **로그**: `journalctl --user -u marketdata-fetch.service -f`로 확인

### 수동 실행
```bash
# 서비스 즉시 실행
systemctl --user start marketdata-fetch.service

# 서비스 상태 확인
systemctl --user status marketdata-fetch.service
```

---

## 💾 데이터 저장 구조

*   **저장 경로**: `data/` 디렉토리
*   **디렉토리 구조**:
    ```
    data/
    ├── KR-1d/
    │   ├── 2025.parquet           # 연별 파일 (과거 연도, KR-1d 루트에 생성)
    │   └── 2026/
    │       ├── 2026-01-17.parquet # 일별 파일
    │       └── 2026-01.parquet    # 월별 파일 (5일 경과 후)
    ├── KR-1m/
    │   └── 2026/
    │       ├── 2026-01-17.parquet # 일별 파일
    │       └── 2026-01.parquet    # 월별 파일 (5일 경과 후)
    └── US-5m/
        └── 2026/
            ├── 2026-01-17.parquet # 일별 파일
            └── 2026-01.parquet    # 월별 파일 (5일 경과 후)
    ```

*   **파일 수명 주기**:
    1. **일별 파일**: 수집 직후 생성 (`YYYY/YYYY-MM-DD.parquet`)
    2. **월별 파일**: 5일 경과 후 일별 파일 병합 → 원본 삭제 (`YYYY/YYYY-MM.parquet`)
    3. **연별 파일**: 과거 연도의 월별 파일 병합 → 원본 삭제 (`YYYY.parquet`, KR-1d만 해당)

