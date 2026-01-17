#!/usr/bin/env python3
"""
Convert ticker-based files from https://stooq.com/db/h/ into date-based files
"""

import argparse
from collections import namedtuple, defaultdict
from collections.abc import Generator
from datetime import datetime, date, timedelta
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor # 병렬 처리를 위해 추가
from functools import partial 
from itertools import groupby


FIELDS = ['TICKER', 'PER', 'DATE', 'TIME', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOL', 'OPENINT']
Record = namedtuple('Record', ['ticker', 'price', 'volume', 'datetime'])

# --- 병렬 처리를 위한 헬퍼 함수 ---

def _process_single_file(file: Path, earliest_date: date) -> list[Record]:
    """하나의 파일을 읽고 파싱하여 Record 리스트를 반환 (병렬 작업용)"""
    print(f'Loading {file.name}')
    records = []
    earliest_str = earliest_date.strftime('%Y%m%d')
    
    for line in read(file):
        parts = line.split(',')
        if len(parts) < 10: continue
        
        # 조기 필터링: 파일의 날짜(Index 2)가 목표 날짜 문자열보다 작으면 파싱 생략
        # (시차를 고려해도 폴란드 기준 90일 이전이면 미국 기준도 무조건 이전임)
        if parts[2] < earliest_str:
            continue
            
        d = parse(parts) # 이제 텍스트 라인이 아닌 split된 리스트를 받음
        if d.datetime.date() < earliest_date:
            continue
        records.append(d)
    print(f'Found {len(records)} records in {file.name}')
    return records

def _write_single_day_file(args: tuple[Path, str, list[Record]]):
    """하나의 날짜에 해당하는 데이터를 파일에 씀 (병렬 작업용)"""
    output_dir, filename, records = args
    print(f'Writing {filename}')
    with Path(output_dir / filename).open('w', encoding='utf-8') as f:
        for r in records:
            line = f"{r.ticker}\t{r.price}\t{r.volume}\t{r.datetime.strftime('%H:%M')}\n"
            f.write(line)
    return filename

def read(file: Path) -> Generator[str]:
    # Stooq data is typically UTF-8 or ASCII. Explicitly set encoding to avoid CP949 errors on Windows.
    with file.open(encoding='utf-8', errors='ignore') as f:
        _ = f.readline()  # header line
        while line := f.readline():
            yield line

# DST transition cache to avoid redundant calculations
_DST_CACHE = {}

def get_offset(dt_date: date) -> int:
    """Fast offset calculation with year-based caching."""
    year = dt_date.year
    if year not in _DST_CACHE:
        def nth_sun(m, n):
            if n > 0:
                d = date(year, m, 1)
                return d + timedelta(days=(6 - d.weekday()) % 7 + (n - 1) * 7)
            # Last Sunday of month
            last = date(year, m+1, 1) - timedelta(days=1) if m < 12 else date(year, 12, 31)
            return last - timedelta(days=(last.weekday() - 6) % 7)
        
        _DST_CACHE[year] = (nth_sun(3, 2), nth_sun(3, -1), nth_sun(10, -1), nth_sun(11, 1))
    
    us_s, pl_s, pl_e, us_e = _DST_CACHE[year]
    if us_s <= dt_date < pl_s or pl_e <= dt_date < us_e:
        return 5
    return 6

def parse(v: list[str]) -> Record:
    """Optimized parser: now receives already split list."""
    # 20211012, 153000 -> direct slicing and int conversion
    d_str, t_str = v[2], v[3]
    y, m, d = int(d_str[:4]), int(d_str[4:6]), int(d_str[6:8])
    H, M, S = int(t_str[:2]), int(t_str[2:4]), int(t_str[4:6])
    
    dt = datetime(y, m, d, H, M, S)
    
    # Fast offset check using the date object
    dt = dt - timedelta(hours=get_offset(dt.date()))

    return Record(
        v[0][:-3] if v[0].endswith('.US') else v[0], # Fast ticker cleaning
        v[7], # Close
        v[8], # Vol
        dt
    )

def load_files(path: Path, earliest_date: datetime) -> list:
    """Phase 1: 여러 소스 파일을 병렬로 읽어들임"""
    print(f'Looking for txt files in {path}')
    files_to_process = [f for f in path.glob('**/*.txt') if not f.name.startswith('.')]
    print(f'Found {len(files_to_process)} files to process in parallel.')

    all_records = []

    with ProcessPoolExecutor() as executor:
        process_func = partial(_process_single_file, earliest_date=earliest_date)
        results = executor.map(process_func, files_to_process)

        for file_records in results:
            all_records.extend(file_records)

    print(f'Total records loaded: {len(all_records)}')
    
    return sorted(all_records, key=lambda r: r.datetime)


def write_files(path: Path, records: list[Record]):
    """Phase 2: 메모리의 레코드를 날짜별 파일에 병렬로 저장 (groupby로 최적화)"""
    print(f'Grouping {len(records)} records by date...')

    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    # 그룹화의 기준이 되는 key 함수 정의 (날짜 객체 자체를 키로 사용)
    key_func = lambda r: r.datetime.date()

    # 1. itertools.groupby로 레코드 그룹화
    # groupby는 정렬된 데이터를 매우 빠르게 그룹화합니다.
    # (날짜, 해당 날짜의 레코드 이터레이터) 형태의 튜플을 생성합니다.
    grouped_records = groupby(records, key=key_func)

    # 2. 병렬 쓰기를 위한 인자 생성
    # 각 그룹에서 파일명과 레코드 리스트를 추출하여 병렬 처리 함수에 전달할 인자를 만듭니다.
    write_args = []
    for day_date, record_group in grouped_records:
        filename = day_date.strftime('%Y-%m-%d') + '.txt'
        # record_group은 이터레이터이므로 list로 변환해야 함
        write_args.append((path, filename, list(record_group)))
    
    print(f'Exporting {len(write_args)} daily files in parallel...')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert Stooq ticker-based files to date-based Parquet files.")
    parser.add_argument('-s', '--source_dir', default=Path.home() / 'Downloads/5_us_txt', type=Path)
    parser.add_argument('-o', '--output_dir', help='Output directory (default: data/US-5m/YYYY/)', type=Path)
    parser.add_argument('-e', '--earliest_date', default='2021-12-01', type=date.fromisoformat)
    args = parser.parse_args()

    # Determine output directory
    if not args.output_dir:
        year = args.earliest_date.year
        project_root = Path(__file__).resolve().parent.parent
        args.output_dir = project_root / "data" / "US-5m" / str(year)
        args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Phase 1: Load files
    records = load_files(args.source_dir, args.earliest_date)
    
    # Phase 2: Convert to Parquet by day
    if records:
        import pandas as pd
        from itertools import groupby
        
        key_func = lambda r: r.datetime.date()
        grouped_records = groupby(records, key=key_func)
        
        for day_date, record_group in grouped_records:
            filename = day_date.strftime('%Y-%m-%d') + '.parquet'
            file_path = args.output_dir / filename
            
            # Convert to DataFrame
            day_records = list(record_group)
            df = pd.DataFrame([{
                'symbol': r.ticker,
                'dt': r.datetime,
                'price': float(r.price),
                'volume': int(r.volume)
            } for r in day_records])
            
            # Save as Parquet
            df.to_parquet(file_path, compression='snappy', index=False)
            print(f'Saved {len(df)} records to {filename}')